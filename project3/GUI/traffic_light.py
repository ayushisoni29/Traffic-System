import pygame, random, os
from collections import deque

# ---------------- Configuration -----------------------
SCREEN_W, SCREEN_H = 1200, 720
FPS = 60

GREEN_TIME = 6.0
YELLOW_TIME = 2.0

ROAD_WIDTH = 220
LANE_WIDTH = ROAD_WIDTH // 2

# ---------------- Init pygame ------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Smart City – One Signal at a Time (with Green Corridor 🚑🚒)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)

# ---------------- Image Loader ----------------------
def load_image(filename, size=None):
    path = os.path.join(os.path.dirname(__file__), filename)
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

# ---------------- Load Assets -----------------------
BACKGROUND = load_image("city.jpg", (SCREEN_W, SCREEN_H))

# Colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

# ---------------- Directions ------------------------
NORTH, SOUTH, EAST, WEST = "N", "S", "E", "W"
DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

# Traffic light positions
LIGHT_POS = {
    NORTH: (SCREEN_W // 2 - 30, SCREEN_H // 2 - ROAD_WIDTH // 2 - 70),
    SOUTH: (SCREEN_W // 2 - 30, SCREEN_H // 2 + ROAD_WIDTH // 2),
    EAST:  (SCREEN_W // 2 + ROAD_WIDTH // 2 - 20, SCREEN_H // 2 - 20),
    WEST:  (SCREEN_W // 2 - ROAD_WIDTH // 2 - 20, SCREEN_H // 2 - 20),
}

# ---------------- Vehicle Types ---------------------
VEHICLE_TYPES = {
    "car": {"image": load_image("car1.png", (50, 100)), "length": 50, "width": 100},
    "bus": {"image": load_image("bus2.png", (60, 140)), "length": 60, "width": 140},
    "truck": {"image": load_image("truc.png", (70, 150)), "length": 70, "width": 150},
    "ambulance": {"image": load_image("ambulance1.png", (50, 110)), "length": 50, "width": 110},
}

# ---------------- Traffic Light Class ----------------
class TrafficLight:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.state = "red"
        self.light_radius = 6

        # Load traffic light image
        self.image = load_image("traffic_signal.png")
        self.width, self.height = 40, 100
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

        # Colors
        self.colors = {
            "red": (255, 0, 0),
            "yellow": (255, 255, 0),
            "green": (0, 255, 0),
            "dark": (30, 30, 30)
        }

        spacing = self.height // 4
        self.light_positions = {
            "red": (self.width // 2, spacing),
            "yellow": (self.width // 2, spacing * 2),
            "green": (self.width // 2, spacing * 3)
        }

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        for color_name, pos in self.light_positions.items():
            x, y = self.x + pos[0], self.y + pos[1]
            color = self.colors[color_name] if color_name == self.state else self.colors["dark"]

            if color_name == self.state:
                glow_surface = pygame.Surface((self.light_radius * 3, self.light_radius * 3), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*color[:3], 80), (self.light_radius * 1.5, self.light_radius * 1.5), self.light_radius * 1.5)
                screen.blit(glow_surface, (x - self.light_radius * 1.5, y - self.light_radius * 1.5))

            pygame.draw.circle(screen, color, (x, y), self.light_radius)
            pygame.draw.circle(screen, (255, 255, 255), (x - self.light_radius//4, y - self.light_radius//4), self.light_radius//4)

# ---------------- Vehicle Class ---------------------
class Vehicle:
    def __init__(self, kind, direction):
        self.kind = kind
        self.image = VEHICLE_TYPES[kind]["image"]
        self.dir = direction
        self.base_speed = 4 if kind == "ambulance" else 3  # Slightly reduced ambulance speed for safety
        self.speed = self.base_speed
        self.in_intersection = False
        self.emergency = kind == "ambulance"
        self.braking = False
        self.target_lane = None  # Target lane for smooth movement
        self.original_lane = None  # Remember original lane position
        self.yielding_to_ambulance = False  # Flag to track if yielding to ambulance
        self.safe_to_move = True  # Flag to control movement
        
        # Initialize lane position
        if self.dir in [NORTH, SOUTH]:
            self.lane = "center" if self.emergency else ("left" if random.random() < 0.5 else "right")
        else:
            self.lane = "center" if self.emergency else ("top" if random.random() < 0.5 else "bottom")
        self.original_lane = self.lane

        if self.dir == NORTH:
            self.image = pygame.transform.rotate(self.image, 180)
        elif self.dir == EAST:
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.dir == WEST:
            self.image = pygame.transform.rotate(self.image, -90)

        if direction == NORTH:
            self.x, self.y = SCREEN_W // 2 - 40, 0 - 120
        elif direction == SOUTH:
            self.x, self.y = SCREEN_W // 2 + 20, SCREEN_H + 50
        elif direction == EAST:
            self.x, self.y = SCREEN_W + 60, SCREEN_H // 2 - 40
        elif direction == WEST:
            self.x, self.y = -120, SCREEN_H // 2 + 20

        self.rect = self.image.get_rect(center=(self.x, self.y))

    def check_collision(self, vehicles):
        safe_distance = 80
        emergency_safe_distance = 120  # Increased safety margin
        
        # Predict positions for collision detection
        future_x = self.x
        future_y = self.y
        if self.dir == NORTH: future_y += self.speed * 10
        elif self.dir == SOUTH: future_y -= self.speed * 10
        elif self.dir == EAST: future_x -= self.speed * 10
        elif self.dir == WEST: future_x += self.speed * 10

        # Check for nearby ambulance and predict its path
        nearby_ambulance = None
        for vehicle in vehicles:
            if vehicle.emergency:
                dx = abs(self.x - vehicle.x)
                dy = abs(self.y - vehicle.y)
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance < 300:  # Extended detection range
                    nearby_ambulance = vehicle
                    # Calculate time to potential collision
                    time_to_collision = distance / (self.speed + vehicle.speed)
                    if time_to_collision < 2.0:  # If collision possible within 2 seconds
                        self.safe_to_move = False
                        return True

        for vehicle in vehicles:
            if vehicle == self:
                continue

            # Calculate actual distance between vehicles
            dx = abs(self.x - vehicle.x)
            dy = abs(self.y - vehicle.y)
            
            # Use larger safe distance if ambulance is nearby
            current_safe_distance = emergency_safe_distance if nearby_ambulance else safe_distance

            # Check for potential collisions in all directions
            if dx < current_safe_distance and dy < current_safe_distance:
                # If there's immediate danger of collision
                if dx < 40 or dy < 40:  # Minimum safety threshold
                    return True

            if self.dir == vehicle.dir:
                # Move aside for ambulance with more careful positioning
                if vehicle.emergency and not self.emergency:
                    target_x = self.x
                    target_y = self.y
                    
                    if self.dir == NORTH and vehicle.y < self.y:
                        target_x = SCREEN_W // 2 + 35 if self.x >= SCREEN_W // 2 else SCREEN_W // 2 - 55
                    elif self.dir == SOUTH and vehicle.y > self.y:
                        target_x = SCREEN_W // 2 + 35 if self.x >= SCREEN_W // 2 else SCREEN_W // 2 - 55
                    elif self.dir == EAST and vehicle.x > self.x:
                        target_y = SCREEN_H // 2 + 35 if self.y >= SCREEN_H // 2 else SCREEN_H // 2 - 55
                    elif self.dir == WEST and vehicle.x < self.x:
                        target_y = SCREEN_H // 2 + 35 if self.y >= SCREEN_H // 2 else SCREEN_H // 2 - 55
                    
                    # Gradually move to target position
                    if self.dir in [NORTH, SOUTH]:
                        self.x += (target_x - self.x) * 0.1  # Smooth movement
                    else:
                        self.y += (target_y - self.y) * 0.1  # Smooth movement
                
                # Check for collision with safe distance
                if self.dir == NORTH:
                    if vehicle.y > self.y and vehicle.y - (self.y + self.rect.height) < safe_distance:
                        return True
                elif self.dir == SOUTH:
                    if vehicle.y < self.y and self.y - (vehicle.y + vehicle.rect.height) < safe_distance:
                        return True
                elif self.dir == EAST:
                    if vehicle.x < self.x and self.x - (vehicle.x + vehicle.rect.width) < safe_distance:
                        return True
                elif self.dir == WEST:
                    if vehicle.x > self.x and vehicle.x - (self.x + self.rect.width) < safe_distance:
                        return True
        return False

    def should_stop(self, green_dir, vehicles):
        stop_points = {
            NORTH: SCREEN_H // 2 - ROAD_WIDTH // 2 - 20,
            SOUTH: SCREEN_H // 2 + ROAD_WIDTH // 2 + 20,
            EAST: SCREEN_W // 2 + ROAD_WIDTH // 2 + 20,
            WEST: SCREEN_W // 2 - ROAD_WIDTH // 2 - 20
        }

        # Don't stop if we're already in the intersection
        if self.in_intersection:
            return False

        # Check if we're at the intersection
        if self.dir == NORTH:
            at_intersection = self.y + self.rect.height >= stop_points[NORTH]
        elif self.dir == SOUTH:
            at_intersection = self.y <= stop_points[SOUTH]
        elif self.dir == EAST:
            at_intersection = self.x <= stop_points[EAST]
        else:  # WEST
            at_intersection = self.x + self.rect.width >= stop_points[WEST]

        # If at intersection and light is red
        if at_intersection:
            if self.dir != green_dir:
                return True
            else:
                # Check for safe crossing
                for vehicle in vehicles:
                    if vehicle != self and vehicle.is_near_intersection():
                        if self.dir != vehicle.dir:  # Different directions
                            dx = abs(self.x - vehicle.x)
                            dy = abs(self.y - vehicle.y)
                            if dx < 80 or dy < 80:  # Close to potential collision
                                return True
                # If safe, mark as in intersection
                self.in_intersection = True
                return False

        if self.check_collision(vehicles):
            return True

        if self.dir == NORTH:
            at_intersection = self.y + self.rect.height >= stop_points[NORTH]
        elif self.dir == SOUTH:
            at_intersection = self.y <= stop_points[SOUTH]
        elif self.dir == EAST:
            at_intersection = self.x <= stop_points[EAST]
        else:
            at_intersection = self.x + self.rect.width >= stop_points[WEST]

        if at_intersection and not self.in_intersection:
            if self.dir != green_dir:
                return True
            else:
                self.in_intersection = True

        return False

    def move(self, green_dir, vehicles):
        # Reset safe_to_move flag each frame
        self.safe_to_move = True
        
        # Check if we should stop at traffic light
        at_traffic_light = self.should_stop(green_dir, vehicles)
        
        # Calculate lane positions
        if self.dir in [NORTH, SOUTH]:
            center_x = SCREEN_W // 2
            lane_positions = {
                "left": center_x - 55,
                "center": center_x,
                "right": center_x + 35
            }
        else:
            center_y = SCREEN_H // 2
            lane_positions = {
                "top": center_y - 55,
                "center": center_y,
                "bottom": center_y + 35
            }
            
        # Check if we can move safely
        can_move = True
        if not self.emergency:
            # Check for immediate collisions
            for vehicle in vehicles:
                if vehicle != self:
                    dx = abs(self.x - vehicle.x)
                    dy = abs(self.y - vehicle.y)
                    min_safe_distance = 40
                    
                    # If too close to another vehicle, stop temporarily
                    if dx < min_safe_distance and dy < min_safe_distance:
                        can_move = False
                        break

        # Ambulance behavior
        if self.emergency:
            self.lane = "center"  # Always stay in center
            for vehicle in vehicles:
                if vehicle != self and not vehicle.emergency:
                    dx = self.x - vehicle.x
                    dy = self.y - vehicle.y
                    distance = (dx * dx + dy * dy) ** 0.5
                    
                    if distance < 300:  # Extended range for early warning
                        if vehicle.dir == self.dir:
                            # Make sure vehicles ahead move
                            vehicle.safe_to_move = True
                            if not vehicle.yielding_to_ambulance:
                                vehicle.yielding_to_ambulance = True
                                # Choose the nearest side to move to
                                if self.dir in [NORTH, SOUTH]:
                                    vehicle.target_lane = "right" if vehicle.x >= center_x else "left"
                                else:
                                    vehicle.target_lane = "bottom" if vehicle.y >= center_y else "top"
                            
                            # Keep moving but at adjusted speed
                            if distance < 100:
                                vehicle.speed = max(2, vehicle.base_speed * 0.7)
                            elif distance < 200:
                                vehicle.speed = max(2.5, vehicle.base_speed * 0.85)
                            else:
                                vehicle.speed = vehicle.base_speed
                                
                            # Ensure vehicles keep moving
                            vehicle.safe_to_move = True

        # Only stop if at traffic light and not emergency vehicle
        if at_traffic_light and not self.emergency:
            return

        # If we can move safely or we're an emergency vehicle
        if (can_move or self.emergency) and (self.safe_to_move or self.emergency):
            # Update lane position smoothly
            target_pos = 0
            if self.dir in [NORTH, SOUTH]:
                target_pos = lane_positions[self.target_lane if self.target_lane else self.lane]
                # More responsive lane changing
                self.x += (target_pos - self.x) * 0.15
            else:
                target_pos = lane_positions[self.target_lane if self.target_lane else self.lane]
                self.y += (target_pos - self.y) * 0.15

            # Move in direction with current speed
            if self.dir == NORTH:
                self.y += self.speed
            elif self.dir == SOUTH:
                self.y -= self.speed
            elif self.dir == EAST:
                self.x -= self.speed
            elif self.dir == WEST:
                self.x += self.speed

            # Return to original lane if not yielding to ambulance
            if not self.yielding_to_ambulance and self.target_lane:
                self.target_lane = None
                self.lane = self.original_lane
                self.speed = self.base_speed

        # Move the vehicle with smoother lane positioning
        if self.dir == NORTH:
            self.y += self.speed
            if self.emergency:
                # Ambulance stays exactly in center lane
                self.x = SCREEN_W // 2 - 15
            elif abs(self.x - (SCREEN_W // 2 + 35)) < 5:  # If in right lane
                self.x = SCREEN_W // 2 + 35  # Stay in right lane
            elif abs(self.x - (SCREEN_W // 2 - 55)) < 5:  # If in left lane
                self.x = SCREEN_W // 2 - 55  # Stay in left lane
                
        elif self.dir == SOUTH:
            self.y -= self.speed
            if self.emergency:
                self.x = SCREEN_W // 2 - 15
            elif abs(self.x - (SCREEN_W // 2 + 35)) < 5:
                self.x = SCREEN_W // 2 + 35
            elif abs(self.x - (SCREEN_W // 2 - 55)) < 5:
                self.x = SCREEN_W // 2 - 55
                
        elif self.dir == EAST:
            self.x -= self.speed
            if self.emergency:
                self.y = SCREEN_H // 2 - 15
            elif abs(self.y - (SCREEN_H // 2 + 35)) < 5:
                self.y = SCREEN_H // 2 + 35
            elif abs(self.y - (SCREEN_H // 2 - 55)) < 5:
                self.y = SCREEN_H // 2 - 55
                
        elif self.dir == WEST:
            self.x += self.speed
            if self.emergency:
                self.y = SCREEN_H // 2 - 15
            elif abs(self.y - (SCREEN_H // 2 + 35)) < 5:
                self.y = SCREEN_H // 2 + 35
            elif abs(self.y - (SCREEN_H // 2 - 55)) < 5:
                self.y = SCREEN_H // 2 - 55

        self.rect.center = (self.x, self.y)

    def is_near_intersection(self):
        # Check if vehicle is near the intersection
        intersection_x = SCREEN_W // 2
        intersection_y = SCREEN_H // 2
        distance_to_intersection = ((self.x - intersection_x) ** 2 + 
                                  (self.y - intersection_y) ** 2) ** 0.5
        return distance_to_intersection < ROAD_WIDTH

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# ---------------- Traffic System --------------------
class TrafficSystem:
    def __init__(self):
        self.queues = {d: deque() for d in DIRECTIONS}
        self.green_dir = NORTH
        self.phase_timer = GREEN_TIME

        self.traffic_lights = {}
        for direction, (x, y) in LIGHT_POS.items():
            self.traffic_lights[direction] = TrafficLight(x, y, direction)
            self.traffic_lights[direction].state = "red"
        self.traffic_lights[self.green_dir].state = "green"

        self.emergency_override = False

    def update(self, dt):
        all_vehicles = []
        emergency_vehicle_dir = None

        # Check for emergency vehicles
        for d in DIRECTIONS:
            for v in self.queues[d]:
                if v.emergency and (abs(v.x - SCREEN_W//2) < 200 or abs(v.y - SCREEN_H//2) < 200):
                    emergency_vehicle_dir = v.dir
            all_vehicles.extend(self.queues[d])

        # 🚨 Green Corridor
        if emergency_vehicle_dir:
            if self.green_dir != emergency_vehicle_dir:
                for d in DIRECTIONS:
                    self.traffic_lights[d].state = "red"
                self.traffic_lights[emergency_vehicle_dir].state = "green"
                self.green_dir = emergency_vehicle_dir
            self.emergency_override = True
            self.phase_timer = GREEN_TIME
        else:
            self.emergency_override = False

        # Normal cycle
        if not self.emergency_override:
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                current_light = self.traffic_lights[self.green_dir]
                if current_light.state == "green":
                    current_light.state = "yellow"
                    self.phase_timer = YELLOW_TIME
                elif current_light.state == "yellow":
                    current_light.state = "red"
                    idx = DIRECTIONS.index(self.green_dir)
                    self.green_dir = DIRECTIONS[(idx + 1) % len(DIRECTIONS)]
                    self.traffic_lights[self.green_dir].state = "green"
                    self.phase_timer = GREEN_TIME

        for d in DIRECTIONS:
            for v in self.queues[d]:
                v.move(self.green_dir, all_vehicles)

        for d in DIRECTIONS:
            self.queues[d] = deque([v for v in self.queues[d] if -200 < v.x < SCREEN_W + 200 and -200 < v.y < SCREEN_H + 200])

    def spawn_vehicle(self, direction):
        kind = random.choices(
            population=list(VEHICLE_TYPES.keys()),
            weights=[50, 20, 15, 15],  # Regular vehicles more common than ambulance
            k=1
        )[0]
        v = Vehicle(kind, direction)
        self.queues[direction].appendleft(v)

    def draw(self, surf):
        surf.blit(BACKGROUND, (0, 0))
        for d, light in self.traffic_lights.items():
            light.draw(surf)
        for d in DIRECTIONS:
            for v in self.queues[d]:
                v.draw(surf)
        txt = f"Dir {self.green_dir} | {self.traffic_lights[self.green_dir].state} | Timer {self.phase_timer:.1f}s"
        surf.blit(font.render(txt, True, (0, 0, 0)), (20, 20))

# ---------------- Main Loop ------------------------
def main():
    system = TrafficSystem()
    spawn_timer = 0
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        spawn_timer += dt
        if spawn_timer > 2.5:
            system.spawn_vehicle(random.choice(DIRECTIONS))
            spawn_timer = 0

        system.update(dt)
        system.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
