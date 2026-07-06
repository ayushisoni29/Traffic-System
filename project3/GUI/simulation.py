import pygame, random, os
from collections import deque
import requests

# ---------------- Config -----------------
SCREEN_W, SCREEN_H = 1200, 720
FPS = 60
GREEN_TIME, YELLOW_TIME = 6, 2
ROAD_WIDTH = 220

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Traffic Simulation – Haar Cascade Version")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ---------------- Assets -----------------
def load_image(filename, size=None):
    img = pygame.image.load(filename).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

BACKGROUND = load_image("city.jpg", (SCREEN_W, SCREEN_H))
VEHICLE_TYPES = {
    "car": load_image("car1.png", (50, 100)),
    "bus": load_image("bus2.png", (60, 140)),
    "truck": load_image("truc.png", (70, 150)),
    "ambulance": load_image("ambulance1.png", (50, 110))
}

# ---------------- Directions -----------------
NORTH, SOUTH, EAST, WEST = "N", "S", "E", "W"
DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

# ---------------- Vehicle Class -----------------
class Vehicle:
    def __init__(self, kind, direction):
        self.kind = kind
        self.image = VEHICLE_TYPES[kind]
        self.dir = direction
        self.speed = 3 if kind != "ambulance" else 5
        self.x, self.y = self.start_pos()
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.priority = (kind == "ambulance")

    def start_pos(self):
        if self.dir == NORTH: return SCREEN_W//2 - 40, -100
        if self.dir == SOUTH: return SCREEN_W//2 + 40, SCREEN_H + 100
        if self.dir == EAST:  return SCREEN_W + 100, SCREEN_H//2 - 40
        if self.dir == WEST:  return -100, SCREEN_H//2 + 40

    def move(self, green_dir):
        if self.priority or self.dir == green_dir:  # Ambulance always moves
            if self.dir == NORTH: self.y += self.speed
            elif self.dir == SOUTH: self.y -= self.speed
            elif self.dir == EAST:  self.x -= self.speed
            elif self.dir == WEST:  self.x += self.speed
            self.rect.center = (self.x, self.y)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

# ---------------- Traffic System -----------------
class TrafficSystem:
    def __init__(self):
        self.queues = {d: deque() for d in DIRECTIONS}
        self.green_dir = NORTH
        self.timer = GREEN_TIME

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.green_dir = DIRECTIONS[(DIRECTIONS.index(self.green_dir)+1)%4]
            self.timer = GREEN_TIME

        for d in DIRECTIONS:
            for v in self.queues[d]:
                v.move(self.green_dir)

        for d in DIRECTIONS:
            self.queues[d] = deque([v for v in self.queues[d]
                                    if -200 < v.x < SCREEN_W+200 and -200 < v.y < SCREEN_H+200])

    def spawn(self, direction):
        kind = random.choice(list(VEHICLE_TYPES.keys()))
        v = Vehicle(kind, direction)
        self.queues[direction].append(v)

    def draw(self, surf):
        surf.blit(BACKGROUND, (0,0))
        for d in DIRECTIONS:
            for v in self.queues[d]:
                v.draw(surf)
        txt = f"Green: {self.green_dir} | Timer: {self.timer:.1f}s"
        surf.blit(font.render(txt, True, (0,0,0)), (20,20))

# ---------------- Main -----------------
def main():
    system = TrafficSystem()
    spawn_timer, running = 0, True

    while running:
        dt = clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        spawn_timer += dt
        if spawn_timer > 3:
            system.spawn(random.choice(DIRECTIONS))
            spawn_timer = 0

        # Update + Draw
        system.update(dt)
        system.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
