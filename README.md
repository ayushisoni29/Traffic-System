# Traffic Simulation System

## About the Project

The Traffic Simulation System is a Python-based project that simulates traffic flow at road intersections. It is designed to monitor vehicles, detect traffic density, and manage traffic signals efficiently. The project also includes support for emergency vehicle detection to improve traffic management during critical situations.

The main objective of this project is to demonstrate how computer vision and intelligent traffic control can be used to reduce congestion and improve road safety.

---

## Features

- Vehicle detection using computer vision.
- Traffic density monitoring.
- Intelligent traffic signal simulation.
- Emergency vehicle detection.
- Real-time traffic simulation.
- Simple and modular project structure.

---

## Technologies Used

- Python
- OpenCV
- NumPy
- Tkinter
- Haar Cascade Classifier
- XML Classifiers

---

## Project Structure

```text
Traffic-Simulation/
│
├── GUI/
│   ├── dashboard.py
│   ├── detector.py
│   ├── service.py
│   ├── simulation.py
│   ├── traffic_light.py
│   └── ...
│
├── app.py
├── main.py
├── detector.py
├── dashboard.py
├── simulation.py
├── service.py
├── cars.xml
├── requirements.txt
├── test.py
├── test1.py
└── README.md
```

## Modules

- **main.py** – Entry point of the project.
- **detector.py** – Detects vehicles from input.
- **simulation.py** – Simulates traffic movement.
- **dashboard.py** – Displays the traffic dashboard.
- **service.py** – Contains supporting services.
- **cars.xml** – Haar Cascade classifier used for vehicle detection.
- **GUI/** – Contains graphical interface and simulation components.

---

## Future Enhancements

- AI-based traffic signal optimization.
- Multiple intersection support.
- Live CCTV integration.
- Traffic analytics dashboard.
- Cloud deployment.

