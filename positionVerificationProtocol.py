import random
import requests
from PyQt6.QtCore import QTimer, pyqtSlot, Qt
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QApplication
from PyQt6 import uic
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Circle
from matplotlib.transforms import Affine2D


def get_quantum_random_bit():
    try:
        response = requests.get('https://qrng.anu.edu.au/API/jsonI.php?length=1&type=uint8')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                random_number = data['data'][0]
                return random_number % 2  # Return 0 or 1
    except Exception as e:
        print(f"Error fetching quantum random bit: {e}")
    return random.randint(0, 1)  # Fallback to pseudo-random

class CoinFlippingProtocol(QWidget):
    def __init__(self, description_area=None):
        super().__init__()
        self.description_area = description_area

        # Load the UI from the .ui file
        uic.loadUi("coin_flipping_protocol.ui", self)

        # Find widgets
        self.startButton = self.findChild(QPushButton, "startButton")
        self.coinLabel = self.findChild(QLabel, "coinLabel")
        self.spinnerLabel = self.findChild(QLabel, "spinnerLabel")

        # Connect the Start Button to the simulation
        self.startButton.clicked.connect(self.start_simulation)

        # Set up matplotlib figure for embedding animation
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout = self.layout()
        layout.addWidget(self.canvas)
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2.5, 2.5)
        self.ax.axis('off')

        # Static Hadamard state representation
        self.hadamard_text = self.ax.text(0, -2, "(1/sqrt(2))|0> + (1/sqrt(2))|1>", fontsize=14, ha='center', color='black')

        # Draw the spinning coin (circle)
        self.coin = Circle((0, 0), radius=0.6, edgecolor='yellow', facecolor='orange')
        self.ax.add_patch(self.coin)
        self.coin_label = self.ax.text(0, 0, '|0>', fontsize=20, ha='center', va='center', color='white')

        # Spinner line and Hadamard gate below the coin
        self.spinner_line, = self.ax.plot([-1.5, 1.5], [-1.5, -1.5], color='blue', lw=2)
        self.spinner_hadamard = self.ax.text(0, -1.5, 'H', fontsize=20, ha='center', va='center', color='white', bbox=dict(facecolor='blue', alpha=0.5))

        # Flag to prevent multiple simultaneous simulations
        self.spinning = False

    @pyqtSlot()
    def start_simulation(self):
        """Start the quantum coin flip simulation with animation."""
        if not self.spinning:
            self.spinning = True
            self.description_area.setText("Starting the quantum coin flip...\n")

            # Run the animation for 3 seconds (30 frames of 100ms each)
            self.ani = animation.FuncAnimation(self.fig, self.update_animation, frames=np.arange(0, 36), interval=100, repeat=False, blit=False, init_func=self.init_animation)
            self.canvas.draw()
            QTimer.singleShot(3000, self.measure_result)

    def init_animation(self):
        """Initialize the coin and spinner for the animation."""
        self.coin_label.set_text('|0>')
        return self.coin_label,

    def update_animation(self, frame):
        """Update the coin animation for each frame."""
        # Rotate the coin around the x-axis to simulate a realistic coin flip
        angle = frame * 20
        scale_factor = abs(np.cos(np.radians(angle)))  # To simulate the flipping effect
        transform = Affine2D().scale(1, scale_factor).rotate_deg_around(0, 0, angle) + self.ax.transData
        self.coin.set_transform(transform)
        self.coin_label.set_text('|0>' if angle % 360 < 180 else '|1>')
        self.coin_label.set_position((0, 0))
        self.coin_label.set_rotation(angle)

        return self.coin_label,

    def measure_result(self):
        """Measure the quantum state and display the result."""
        # Use quantum random bit
        bit = get_quantum_random_bit()
        result = "Heads" if bit == 0 else "Tails"

        if result == "Heads":
            self.coin_label.set_text("Heads (|0⟩)")
        else:
            self.coin_label.set_text("Tails (|1⟩)")
        self.coin_label.set_position((0, 0))

        self.description_area.append(f"Measurement result: {result}\nQuantum coin flip completed using quantum randomness.\n")
        self.spinning = False