import pygame
import random
from collections import deque
import cv2
import numpy as np

# ---------------- Configuration -----------------------
SCREEN_W, SCREEN_H = 1200, 720
FPS = 60

BASE_GREEN_TIME = 6.0
MIN_GREEN_TIME = 3.0
MAX_GREEN_TIME = 10.0

ROAD_WIDTH = 220

# ---------------- Init pygame ------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Smart City – Adaptive Traffic Management")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)

# ---------------- Directions ------------------------
NORTH, SOUTH, EAST, WEST = "N", "S", "E", "W"
DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

# Traffic light positions
LIGHT_POS = {
    NORTH: (SCREEN_W // 2 - 15, SCREEN_H // 2 - ROAD_WIDTH // 2 - 50),
    SOUTH: (SCREEN_W // 2 - 15, SCREEN_H // 2 + ROAD_WIDTH // 2 + 10),
    EAST:  (SCREEN_W // 2 + ROAD_WIDTH // 2 + 10, SCREEN_H // 2 - 15),
    WEST:  (SCREEN_W // 2 - ROAD_WIDTH // 2 - 50, SCREEN_H // 2 - 15),
}

# ---------------- Vehicle Images ---------------------
VEHICLE_COLORS = {
    "car": (200, 50, 50),
    "bus": (50, 50, 200),
    "truck": (200, 200, 50),
    "ambulance": (255, 50, 50),
}

VEHICLE_SIZES = {
    "car": (50, 30),
    "bus": (70, 35),
    "truck": (80, 40),
    "ambulance": (60, 30),
}

# Increased speeds for faster movement
VEHICLE_SPEEDS = {
    "car": 4.5,       # increased from 3
    "bus": 3.75,      # increased from 2.5
    "truck": 3.0,     # increased from 2
    "ambulance": 5.25 # increased from 3.5
}

# ---------------- Traffic Light Class ----------------
class TrafficLight:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.state = "red"
        self.light_radius = 10

    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), (self.x, self.y, 30, 90), border_radius=8)
        positions = {
            "red": (self.x + 15, self.y + 20),
            "yellow": (self.x + 15, self.y + 45),
            "green": (self.x + 15, self.y + 70),
        }
        colors = {
            "red": (255, 0, 0),
            "yellow": (255, 255, 0),
            "green": (0, 255, 0),
            "off": (30, 30, 30),
        }
        for color_name, pos in positions.items():
            color = colors[color_name] if self.state == color_name else colors["off"]
            pygame.draw.circle(screen, color, pos, self.light_radius)

# ---------------- Vehicle Class ---------------------
class Vehicle:
    _id_counter = 1
    def __init__(self, kind, direction):
        self.kind = kind
        self.dir = direction
        self.speed = VEHICLE_SPEEDS[kind]
        self.length, self.width = VEHICLE_SIZES[kind]
        self.color = VEHICLE_COLORS[kind]
        self.stopped = False

        self.image = pygame.Surface((self.length, self.width))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()

        id_num = Vehicle._id_counter
        Vehicle._id_counter += 1
        r = (id_num & 0xFF0000) >> 16
        g = (id_num & 0x00FF00) >> 8
        b = (id_num & 0x0000FF)
        if r == 0 and g == 0 and b == 0:
            r = 1
        self.detection_color = (r, g, b)

        if direction == NORTH:
            self.x, self.y = SCREEN_W // 2 - 40, -self.length
        elif direction == SOUTH:
            self.x, self.y = SCREEN_W // 2 + 20, SCREEN_H + self.length
        elif direction == EAST:
            self.x, self.y = SCREEN_W + self.length, SCREEN_H // 2 - 40
        elif direction == WEST:
            self.x, self.y = -self.length, SCREEN_H // 2 + 20

        self.rect.center = (self.x, self.y)

    def move(self, green_dir, traffic_lights):
        stop_line = {
            NORTH: SCREEN_H // 2 - ROAD_WIDTH // 2 - 20,
            SOUTH: SCREEN_H // 2 + ROAD_WIDTH // 2 + 20,
            EAST: SCREEN_W // 2 + ROAD_WIDTH // 2 + 20,
            WEST: SCREEN_W // 2 - ROAD_WIDTH // 2 - 20,
        }
        light_state = traffic_lights[self.dir].state

        if self.dir == NORTH and self.y + self.length >= stop_line[NORTH] and light_state != "green":
            self.stopped = True
        elif self.dir == SOUTH and self.y <= stop_line[SOUTH] and light_state != "green":
            self.stopped = True
        elif self.dir == EAST and self.x <= stop_line[EAST] and light_state != "green":
            self.stopped = True
        elif self.dir == WEST and self.x + self.length >= stop_line[WEST] and light_state != "green":
            self.stopped = True
        else:
            self.stopped = False

        if not self.stopped:
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

    def draw_detection(self, surf):
        rect = pygame.Rect(0, 0, self.length, self.width)
        rect.center = (self.x, self.y)
        pygame.draw.rect(surf, self.detection_color, rect)

# ---------------- Computer Vision ---------------------
class ComputerVision:
    def __init__(self, traffic_system):
        self.traffic_system = traffic_system
        self.color_to_vehicle = {}

    def update_color_map(self):
        self.color_to_vehicle.clear()
        for direction in DIRECTIONS:
            for vehicle in self.traffic_system.queues[direction]:
                c = vehicle.detection_color
                self.color_to_vehicle[(c[2], c[1], c[0])] = vehicle

    def detect_vehicles(self, detection_surface):
        raw_str = pygame.image.tostring(detection_surface, 'RGB')
        img = np.frombuffer(raw_str, dtype=np.uint8)
        img = img.reshape((SCREEN_H, SCREEN_W, 3))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        counts = {d: 0 for d in DIRECTIONS}
        boxes = []

        self.update_color_map()

        unique_colors = np.unique(img.reshape(-1, 3), axis=0)
        for color in unique_colors:
            if np.all(color == [0, 0, 0]):
                continue

            mask = cv2.inRange(img, color, color)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                vehicle = self.color_to_vehicle.get(tuple(color), None)
                if vehicle:
                    counts[vehicle.dir] += 1
                    boxes.append((x, y, w, h, vehicle.dir))

        return counts, boxes

# ---------------- Traffic System ---------------------
class TrafficSystem:
    def __init__(self):
        self.queues = {d: deque() for d in DIRECTIONS}
        self.green_dir = NORTH
        self.phase_timer = BASE_GREEN_TIME
        self.green_times = {d: BASE_GREEN_TIME for d in DIRECTIONS}
        self.traffic_lights = {}
        for direction, (x, y) in LIGHT_POS.items():
            self.traffic_lights[direction] = TrafficLight(x, y, direction)
            self.traffic_lights[direction].state = "red"
        self.traffic_lights[self.green_dir].state = "green"

    def switch_light(self, new_green_dir):
        for d in DIRECTIONS:
            self.traffic_lights[d].state = "red"
        self.green_dir = new_green_dir
        self.traffic_lights[new_green_dir].state = "green"
        self.phase_timer = self.green_times[new_green_dir]

    def update(self, dt, vision_counts=None):
        self.phase_timer -= dt
        if vision_counts:
            density = vision_counts.get(self.green_dir, 0)
            if density == 0:
                self.green_times[self.green_dir] = MIN_GREEN_TIME
            elif density >= 5:
                self.green_times[self.green_dir] = MAX_GREEN_TIME
            else:
                self.green_times[self.green_dir] = MIN_GREEN_TIME + (density / 5) * (MAX_GREEN_TIME - MIN_GREEN_TIME)

        if self.phase_timer <= 0:
            order = [NORTH, EAST, SOUTH, WEST]
            idx = order.index(self.green_dir)
            next_idx = (idx + 1) % len(order)
            self.switch_light(order[next_idx])

    def spawn_vehicle(self):
        for direction in DIRECTIONS:
            if len(self.queues[direction]) < 10:
                kind = random.choice(list(VEHICLE_COLORS.keys()))
                vehicle = Vehicle(kind, direction)
                self.queues[direction].append(vehicle)

# ---------------- Main Loop --------------------------
def main():
    traffic_system = TrafficSystem()
    computer_vision = ComputerVision(traffic_system)
    detection_surface = pygame.Surface((SCREEN_W, SCREEN_H))
    spawn_timer = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        spawn_timer += dt
        if spawn_timer > 1.0:
            traffic_system.spawn_vehicle()
            spawn_timer = 0

        detection_surface.fill((0, 0, 0))
        for direction in DIRECTIONS:
            for vehicle in traffic_system.queues[direction]:
                vehicle.draw_detection(detection_surface)

        vision_counts, detected_boxes = computer_vision.detect_vehicles(detection_surface)

        traffic_system.update(dt, vision_counts)

        for direction in DIRECTIONS:
            for vehicle in list(traffic_system.queues[direction]):
                vehicle.move(traffic_system.green_dir, traffic_system.traffic_lights)
                if (vehicle.x < -100 or vehicle.x > SCREEN_W + 100 or
                    vehicle.y < -100 or vehicle.y > SCREEN_H + 100):
                    traffic_system.queues[direction].remove(vehicle)

        screen.fill((50, 120, 50))
        pygame.draw.rect(screen, (80, 80, 80), (0, SCREEN_H//2 - ROAD_WIDTH//2, SCREEN_W, ROAD_WIDTH))
        pygame.draw.rect(screen, (80, 80, 80), (SCREEN_W//2 - ROAD_WIDTH//2, 0, ROAD_WIDTH, SCREEN_H))

        for i in range(0, SCREEN_W, 40):
            pygame.draw.rect(screen, (240, 240, 240), (i, SCREEN_H//2 - 2, 20, 4))
        for i in range(0, SCREEN_H, 40):
            pygame.draw.rect(screen, (240, 240, 240), (SCREEN_W//2 - 2, i, 4, 20))

        for direction in DIRECTIONS:
            for vehicle in traffic_system.queues[direction]:
                vehicle.draw(screen)

        color_map = {
            NORTH: (0, 255, 0),
            SOUTH: (0, 0, 255),
            EAST: (255, 0, 0),
            WEST: (255, 255, 0),
        }
        for (x, y, w, h, direction) in detected_boxes:
            pygame.draw.rect(screen, color_map.get(direction, (255, 255, 255)), (x, y, w, h), 2)

        for light in traffic_system.traffic_lights.values():
            light.draw(screen)

        info_text = f"Green Light: {traffic_system.green_dir} | Timer: {traffic_system.phase_timer:.1f}s"
        text_surf = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surf, (10, 10))

        y_offset = 40
        for d in DIRECTIONS:
            count_text = f"{d} vehicles detected: {vision_counts.get(d, 0)}"
            count_surf = font.render(count_text, True, (255, 255, 255))
            screen.blit(count_surf, (10, y_offset))
            y_offset += 20

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
