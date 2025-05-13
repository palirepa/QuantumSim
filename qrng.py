from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsScene, QGraphicsView, QVBoxLayout, QLabel, QPushButton, \
    QGraphicsPixmapItem
from PyQt6.QtCore import QTimer, QPointF, Qt
from PyQt6.QtGui import QPixmap
import random


class QRNG(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white;")

        # Hlavný vertikálny layout
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)  # Make sure layout is set to self

        # Title with more prominent styling
        title_label = QLabel("Kvantové generovanie náhodných čísel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 15px 0; color: #333;")
        self.main_layout.addWidget(title_label)

        # Label pre generované bity hore
        self.output_label = QLabel("Generované bity:")
        self.output_label.setStyleSheet("color: black; font-size: 18px;")

        # Graphics View uprostred
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background-color: white;")
        self.view.setMinimumSize(800, 400)

        # Vytvoríme vertikálny layout, do ktorého vložíme label aj view
        label_and_view_layout = QVBoxLayout()
        label_and_view_layout.addWidget(self.output_label)
        label_and_view_layout.addWidget(self.view)

        # Vytvoríme nový widget, ktorý bude obsahovať tento layout
        container_widget = QWidget()
        container_widget.setLayout(label_and_view_layout)

        # Nakoniec tento widget pridáme do main_layout
        self.main_layout.addWidget(container_widget)

        # Tlačidlo dole
        self.generate_button = QPushButton("Generovať sekvenciu bitov")
        self.generate_button.setStyleSheet("background-color: gray; color: black; font-size: 16px;")
        self.generate_button.clicked.connect(self.start_animation)
        self.main_layout.addWidget(self.generate_button)

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

        # Animation variables
        self.num_bits = 10
        self.current_bit = 0
        self.random_bits = []
        self.photons = []
        self.photon_in_flight = None

        # Animation step timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_photon_step)
        self.animation_steps = 100
        self.current_step = 0
        self.animation_total_steps = 100
        self.animation_phase = None  # 'to_polarizer' or 'to_detector'

        # Static elements positions
        self.source_pos = QPointF(100, 200)
        self.splitter_pos = QPointF(400, 200)
        self.detector_0_pos = QPointF(600, 100)
        self.detector_1_pos = QPointF(600, 300)

        self.draw_static_elements()

    def draw_static_elements(self):
        # Photon source
        source_svg_renderer = QSvgRenderer("icon/zdroj_fotonov.svg")
        source_item = QGraphicsSvgItem()
        source_item.setSharedRenderer(source_svg_renderer)
        source_item.setPos(self.source_pos.x() - 20, self.source_pos.y() - 20)
        self.scene.addItem(source_item)

        # Polarizer
        splitter_svg_renderer = QSvgRenderer("icon/splitter.svg")
        splitter_item = QGraphicsSvgItem()
        splitter_item.setSharedRenderer(splitter_svg_renderer)
        splitter_item.setPos(self.splitter_pos.x() - 20, self.splitter_pos.y() - 20)
        self.scene.addItem(splitter_item)

        # Detector 0
        detector_0_svg_renderer = QSvgRenderer("icon/D0.svg")
        detector_0_item = QGraphicsSvgItem()
        detector_0_item.setSharedRenderer(detector_0_svg_renderer)
        detector_0_item.setPos(self.detector_0_pos.x() - 35, self.detector_0_pos.y() - 20)
        self.scene.addItem(detector_0_item)

        # Detector 1
        svg_renderer = QSvgRenderer("icon/D1.svg")
        detector_1_item = QGraphicsSvgItem()
        detector_1_item.setSharedRenderer(svg_renderer)
        detector_1_item.setPos(self.detector_1_pos.x() - 35, self.detector_1_pos.y() - 20)
        self.scene.addItem(detector_1_item)

    def start_animation(self):
        self.output_label.setText("Generované bity:")
        self.random_bits = []
        self.current_bit = 0
        self.photons = []
        self.timer.start(800)

    def update_animation(self):
        if self.current_bit < self.num_bits and not self.photon_in_flight:
            bit = random.choice([0, 1])
            photon_image = QPixmap("icon/B.svg")
            photon = QGraphicsPixmapItem(photon_image)
            photon.setScale(1)
            photon.setPos(self.source_pos)
            self.scene.addItem(photon)
            self.photons.append((photon, bit))
            self.photon_in_flight = photon

            self.animation_steps = 0
            self.current_step = 0
            self.bit = bit
            self.photon = photon

            self.animation_phase = 'to_polarizer'
            self.animation_timer.start(10)
        elif self.current_bit >= self.num_bits:
            self.timer.stop()

    def animate_photon_step(self):
        if self.animation_steps >= self.animation_total_steps:
            self.animation_timer.stop()
            if self.animation_phase == 'to_polarizer':
                # Determine next phase
                if self.bit == 0:
                    self.photon.setPixmap(QPixmap("icon/B0.svg"))
                else:
                    self.photon.setPixmap(QPixmap("icon/B1.svg"))
                self.animation_phase = 'to_detector'
                self.animation_steps = 0
                self.current_step = 0
                self.animation_timer.start(10)
            elif self.animation_phase == 'to_detector':
                self.scene.removeItem(self.photon)
                self.random_bits.append(self.bit)
                self.output_label.setText(f"Generované bity: {''.join(map(str, self.random_bits))}")
                self.photon_in_flight = None
                self.current_bit += 1
            return

        t = self.current_step / self.animation_total_steps

        if self.animation_phase == 'to_polarizer':
            start_pos = self.source_pos
            end_pos = self.splitter_pos
        elif self.animation_phase == 'to_detector':
            start_pos = self.splitter_pos
            end_pos = self.detector_0_pos if self.bit == 0 else self.detector_1_pos
        else:
            self.animation_timer.stop()
            return

        new_x = (1 - t) * start_pos.x() + t * end_pos.x()
        new_y = (1 - t) * start_pos.y() + t * end_pos.y()
        self.photon.setPos(new_x, new_y)

        self.current_step += 1
        self.animation_steps += 1
