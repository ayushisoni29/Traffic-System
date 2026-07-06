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
pygame.display.set_caption("Smart City – One Signal at a Time")
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
DARK = (50, 50, 50)
GRAY = (100, 100, 100)

# ---------------- Directions ------------------------
NORTH, SOUTH, EAST, WEST = "N", "S", "E", "W"
DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

# Traffic light positions
LIGHT_POS = {
    NORTH: (SCREEN_W // 2 - 30, SCREEN_H // 2 - ROAD_WIDTH // 2 - 70),  # Centered above north crossing
    SOUTH: (SCREEN_W // 2 - 30, SCREEN_H // 2 + ROAD_WIDTH // 2),      # Centered below south crossing
    EAST:  (SCREEN_W // 2 + ROAD_WIDTH // 2 - 20, SCREEN_H // 2 - 20), # Centered at east zebra crossing
    WEST:  (SCREEN_W // 2 - ROAD_WIDTH // 2 - 20, SCREEN_H // 2 - 20), # Centered at west zebra crossing
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
        self.light_radius = 6  # Smaller radius for the light circles

        # Load traffic light image as background
        self.image = load_image("traffic_signal.png")  # Using the traffic light image
        # Scale the image to be more visible
        self.width, self.height = 40, 100  # Smaller overall size
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

        # Colors
        self.colors = {
            "red": (255, 0, 0),     # Bright red
            "yellow": (255, 255, 0), # Bright yellow
            "green": (0, 255, 0),    # Bright green
            "dark": (30, 30, 30)     # Darker when off
        }

        # Calculate light positions relative to image
        spacing = self.height // 4
        self.light_positions = {
            "red": (self.width // 2, spacing),
            "yellow": (self.width // 2, spacing * 2),
            "green": (self.width // 2, spacing * 3)
        }

    def draw(self, screen):
        # Draw the traffic light background image
        screen.blit(self.image, (self.x, self.y))

        # Draw the colored lights on top with a glow effect
        for color_name, pos in self.light_positions.items():
            x, y = self.x + pos[0], self.y + pos[1]
            color = self.colors[color_name] if color_name == self.state else self.colors["dark"]
            
            # Draw a smaller, semi-transparent circle for glow effect
            if color_name == self.state:
                glow_surface = pygame.Surface((self.light_radius * 3, self.light_radius * 3), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*color[:3], 80), (self.light_radius * 1.5, self.light_radius * 1.5), self.light_radius * 1.5)
                screen.blit(glow_surface, (x - self.light_radius * 1.5, y - self.light_radius * 1.5))
            
            # Draw the main light
            pygame.draw.circle(screen, color, (x, y), self.light_radius)
            # Draw a small white reflection
            pygame.draw.circle(screen, (255, 255, 255), (x - self.light_radius//4, y - self.light_radius//4), self.light_radius//4)

# ---------------- Vehicle Class ---------------------
class Vehicle:
    def __init__(self, kind, direction):
        self.kind = kind
        self.image = VEHICLE_TYPES[kind]["image"]
        self.dir = direction
        self.speed = 3
        self.in_intersection = False

        # Rotate depending on direction
        if self.dir == NORTH:
            self.image = pygame.transform.rotate(self.image, 180)
        elif self.dir == EAST:
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.dir == WEST:
            self.image = pygame.transform.rotate(self.image, -90)

        # Starting position
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
        safe_distance = 20
        for vehicle in vehicles:
            if vehicle == self:
                continue
            if self.dir == vehicle.dir:
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
        if self.should_stop(green_dir, vehicles):
            return
        if self.dir == NORTH:
            self.y += self.speed
        elif self.dir == SOUTH:
            self.y -= self.speed
        elif self.dir == EAST:
            self.x -= self.speed
        elif self.dir == WEST:
            self.x += self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# ---------------- Traffic System --------------------
class TrafficSystem:
    def __init__(self):
        self.queues = {d: deque() for d in DIRECTIONS}
        self.green_dir = NORTH
        self.phase_timer = GREEN_TIME

        # Initialize traffic lights
        self.traffic_lights = {}
        for direction, (x, y) in LIGHT_POS.items():
            self.traffic_lights[direction] = TrafficLight(x, y, direction)
            self.traffic_lights[direction].state = "red"
        self.traffic_lights[self.green_dir].state = "green"

    def update(self, dt):
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

        all_vehicles = []
        for d in DIRECTIONS:
            all_vehicles.extend(self.queues[d])

        for d in DIRECTIONS:
            for v in self.queues[d]:
                v.move(self.green_dir, all_vehicles)

        for d in DIRECTIONS:
            self.queues[d] = deque([v for v in self.queues[d] if -200 < v.x < SCREEN_W + 200 and -200 < v.y < SCREEN_H + 200])

    def spawn_vehicle(self, direction):
        kind = random.choice(list(VEHICLE_TYPES.keys()))
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
