import cv2
import numpy as np
import random
import time

# Window settings
SCREEN_W, SCREEN_H = 1200, 720

# Load background
background = cv2.imread("assets/background.jpg")
background = cv2.resize(background, (SCREEN_W, SCREEN_H))

# Load traffic light images
traffic_light_red = cv2.imread("assets/red.png")
traffic_light_yellow = cv2.imread("assets/yellow.png")
traffic_light_green = cv2.imread("assets/green.png")

traffic_light_red = cv2.resize(traffic_light_red, (80, 180))
traffic_light_yellow = cv2.resize(traffic_light_yellow, (80, 180))
traffic_light_green = cv2.resize(traffic_light_green, (80, 180))

# Load vehicle images
car_img = cv2.imread("assets/car.png")
car_img = cv2.resize(car_img, (100, 60))

bike_img = cv2.imread("assets/bike.png")
bike_img = cv2.resize(bike_img, (70, 40))

# Vehicle class
class Vehicle:
    def __init__(self, x, y, img, speed):
        self.x = x
        self.y = y
        self.img = img
        self.speed = speed
    
    def move(self, signal_state):
        # Stop if red, slow if yellow, move if green
        if signal_state == "RED" and self.x > 500:  # stop before signal
            return
        elif signal_state == "YELLOW":
            self.x += int(self.speed / 2)
        else:  # GREEN
            self.x += self.speed

# Traffic Light Logic
class TrafficLight:
    def __init__(self):
        self.state = "RED"
        self.timer = 5
    
    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            if self.state == "RED":
                self.state = "GREEN"
                self.timer = 7
            elif self.state == "GREEN":
                self.state = "YELLOW"
                self.timer = 3
            elif self.state == "YELLOW":
                self.state = "RED"
                self.timer = 5

    def get_image(self):
        if self.state == "RED":
            return traffic_light_red
        elif self.state == "YELLOW":
            return traffic_light_yellow
        else:
            return traffic_light_green

# Initialize
vehicles = []
traffic_light = TrafficLight()
frame_count = 0

while True:
    frame = background.copy()

    # Update traffic light
    if frame_count % 30 == 0:  # update every second (assuming ~30fps)
        traffic_light.update()

    # Draw traffic light
    light_img = traffic_light.get_image()
    frame[50:230, 550:630] = light_img  # position

    # Randomly spawn vehicles
    if random.randint(0, 50) == 1:
        img = random.choice([car_img, bike_img])
        y_pos = random.choice([500, 550])
        vehicles.append(Vehicle(0, y_pos, img, random.randint(5, 10)))

    # Move and draw vehicles
    for v in vehicles:
        v.move(traffic_light.state)
        if v.x < SCREEN_W - 100:
            frame[v.y:v.y+v.img.shape[0], v.x:v.x+v.img.shape[1]] = v.img

    # Show state text
    cv2.putText(frame, f"Signal: {traffic_light.state} | Timer: {traffic_light.timer}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow("Traffic Simulation", frame)
    frame_count += 1

    # Quit
    if cv2.waitKey(30) & 0xFF == 27:
        break

cv2.destroyAllWindows()
