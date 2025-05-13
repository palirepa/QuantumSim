from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QSpinBox, QGridLayout,
                             QGroupBox, QTextEdit, QGraphicsScene, QGraphicsView,
                             QGraphicsItem, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QLineF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF

import random
import numpy as np
import sys


# Custom graphics items for animation
class ParticleItem(QGraphicsItem):
    def __init__(self, color=Qt.GlobalColor.blue, radius=10):
        super().__init__()
        self.color = color
        self.radius = radius
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.state = "|0⟩"  # Default quantum state

    def setState(self, state):
        self.state = state
        self.update()

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(self.boundingRect())
        # Draw state label
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self.state)


class EntanglementLine(QGraphicsItem):
    def __init__(self, particle1, particle2, color=Qt.GlobalColor.red):
        super().__init__()
        self.particle1 = particle1
        self.particle2 = particle2
        self.color = color
        self.setZValue(0)  # Below particles

    def boundingRect(self):
        # Create bounding rectangle that encompasses both particles
        pos1 = self.particle1.pos()
        pos2 = self.particle2.pos()
        x = min(pos1.x(), pos2.x()) - 5
        y = min(pos1.y(), pos2.y()) - 5
        width = abs(pos1.x() - pos2.x()) + 10
        height = abs(pos1.y() - pos2.y()) + 10
        return QRectF(x, y, width, height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.color, 2, Qt.PenStyle.DashLine))
        pos1 = self.particle1.pos()
        pos2 = self.particle2.pos()
        painter.drawLine(QLineF(pos1, pos2))


class PersonItem(QGraphicsItem):
    def __init__(self, name="Osoba", color=Qt.GlobalColor.darkBlue):
        super().__init__()
        self.name = name
        self.color = color
        self.width = 60
        self.height = 80
        self.setZValue(1)

    def boundingRect(self):
        return QRectF(-self.width / 2, -self.height / 2, self.width, self.height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw body (rectangle)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QBrush(self.color))
        body_rect = QRectF(-self.width / 3, -self.height / 4, 2 * self.width / 3, 2 * self.height / 3)
        painter.drawRect(body_rect)

        # Draw head (circle)
        head_radius = self.width / 4
        painter.drawEllipse(QPointF(0, -self.height / 2 + head_radius),
                            head_radius, head_radius)

        # Draw name
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 8))
        text_rect = QRectF(-self.width / 2, self.height / 3, self.width, self.height / 4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.name)


class QSSProtocol(QWidget):
    def __init__(self, description_area=None):
        super().__init__()
        self.description_area = description_area

        # QSS Protocol variables
        self.n_participants = 3  # Default
        self.threshold = 2  # Default k out of n
        self.secret = 0  # Secret bit to share
        self.shares = []  # Will hold the quantum shares
        self.measurements = []  # Will hold measurement results

        # Animation state
        self.animation_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_animation_step)
        self.animation_speed = 500  # milliseconds

        # Initialize UI components
        self.setup_ui()

        # Create scene once
        self.create_new_scene()

        # Update the description
        self.update_description()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        """
        # Title
        title_label = QLabel("Protokol kvantového zdieľania tajomstva")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        """

        # Configuration group
        config_group = QGroupBox("Konfigurácia protokolu")
        config_layout = QGridLayout()

        # Number of participants (n)
        self.n_label = QLabel("Počet účastníkov (n):")
        self.n_spinner = QSpinBox()
        self.n_spinner.setRange(2, 10)
        self.n_spinner.setValue(3)
        self.n_spinner.valueChanged.connect(self.on_n_changed)
        config_layout.addWidget(self.n_label, 0, 0)
        config_layout.addWidget(self.n_spinner, 0, 1)

        # Threshold (k)
        self.k_label = QLabel("Prahová hodnota (k):")
        self.k_spinner = QSpinBox()
        self.k_spinner.setRange(2, 3)  # Will be updated based on n
        self.k_spinner.setValue(2)
        config_layout.addWidget(self.k_label, 1, 0)
        config_layout.addWidget(self.k_spinner, 1, 1)

        # Secret bit to share
        self.secret_label = QLabel("Tajný bit:")
        self.secret_combo = QComboBox()
        self.secret_combo.addItems(["0", "1"])
        config_layout.addWidget(self.secret_label, 2, 0)
        config_layout.addWidget(self.secret_combo, 2, 1)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Animation view
        self.view_group = QGroupBox("Animácia protokolu")
        view_layout = QVBoxLayout()
        self.graphics_view = QGraphicsView()
        self.graphics_view.setMinimumHeight(300)
        view_layout.addWidget(self.graphics_view)
        self.view_group.setLayout(view_layout)
        main_layout.addWidget(self.view_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.prepare_btn = QPushButton("Pripraviť podiely")
        self.prepare_btn.clicked.connect(self.prepare_shares)
        button_layout.addWidget(self.prepare_btn)

        self.distribute_btn = QPushButton("Distribuovať podiely")
        self.distribute_btn.clicked.connect(self.distribute_shares)
        self.distribute_btn.setEnabled(False)
        button_layout.addWidget(self.distribute_btn)

        self.reconstruct_btn = QPushButton("Zrekonštruovať tajomstvo")
        self.reconstruct_btn.clicked.connect(self.reconstruct_secret)
        self.reconstruct_btn.setEnabled(False)
        button_layout.addWidget(self.reconstruct_btn)

        self.reset_btn = QPushButton("Resetovať")
        self.reset_btn.clicked.connect(self.reset_protocol)
        button_layout.addWidget(self.reset_btn)

        main_layout.addLayout(button_layout)

        # Status display
        self.status_label = QLabel("Pripravené na začatie Kvantového zdieľania tajomstva")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white; font-weight: bold;")
        main_layout.addWidget(self.status_label)

        # Table for shares
        self.shares_group = QGroupBox("Kvantové podiely")
        shares_layout = QVBoxLayout()
        self.shares_table = QTableWidget(0, 3)  # Rows will be set dynamically
        self.shares_table.setHorizontalHeaderLabels(["Účastník", "Kvantový stav", "Meranie"])
        shares_layout.addWidget(self.shares_table)
        self.shares_group.setLayout(shares_layout)
        main_layout.addWidget(self.shares_group)

        self.setLayout(main_layout)

    def create_new_scene(self):
        """Create a completely new scene and initialize all graphics items."""
        # Create new scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 600, 250)
        self.graphics_view.setScene(self.scene)

        # Set background
        self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))

        # Create fresh collections
        self.participant_items = []
        self.qubit_items = []
        self.entanglement_lines = []

        # Add dealer
        self.dealer = PersonItem("Dealer", QColor(50, 100, 50))
        self.dealer.setPos(100, 125)
        self.scene.addItem(self.dealer)

        # Add participants and qubits
        self.add_participants_to_scene()

    def add_participants_to_scene(self):
        """Add participants and qubits to the scene based on current settings."""
        n = self.n_spinner.value()
        radius = 100  # Radius for positioning in a semicircle
        center_x = 350
        center_y = 200

        for i in range(n):
            # Calculate position on a semicircle
            angle = 3.14159 * i / max(1, n - 1)  # Avoid division by zero
            x = center_x + radius * np.cos(angle)
            y = center_y - radius * np.sin(angle)

            # Create participant
            participant = PersonItem(f"P{i + 1}", QColor(50, 50, 150))
            participant.setPos(x, y)
            self.scene.addItem(participant)
            self.participant_items.append(participant)

            # Create qubit for this participant (initially at dealer position)
            qubit = ParticleItem(QColor(0, 100, 200))
            qubit.setPos(self.dealer.pos())
            self.scene.addItem(qubit)
            self.qubit_items.append(qubit)

        # Update the k spinner's max value
        self.k_spinner.setRange(2, max(2, n))
        if self.k_spinner.value() > n:
            self.k_spinner.setValue(n)

    def on_n_changed(self):
        """Handle change in number of participants."""
        # Completely recreate the scene when n changes
        if self.animation_timer.isActive():
            self.animation_timer.stop()

        self.create_new_scene()
        self.reset_protocol(recreate_scene=False)

    def update_description(self):
        if self.description_area:
            description_text = """
            <h3>Protokol kvantového zdieľania tajomstva (QSS)</h3>
            <p>Kvantové zdieľanie tajomstva umožňuje dealerovi distribuovať kvantové tajomstvo medzi n účastníkov takým spôsobom, že k ľubovoľných účastníkov môže tajomstvo zrekonštruovať, ale k-1 alebo menej účastníkov nezíska žiadnu informáciu o tajomstve.</p>

            <h4>Kroky protokolu:</h4>
            <ol>
                <li><b>Príprava:</b> Dealer vytvorí GHZ stav n+1 qubitov.</li>
                <li><b>Distribúcia:</b> Dealer si ponechá jeden qubit a zvyšných n qubitov distribuuje účastníkom.</li>
                <li><b>Kódovanie:</b> Dealer zakóduje tajomstvo meraním svojho qubitu vo vhodnej báze.</li>
                <li><b>Rekonštrukcia:</b> Aspoň k účastníkov musí spolupracovať a zmerať svoje qubity na rekonštrukciu tajomstva.</li>
            </ol>

            <p>Táto implementácia demonštruje prahovú schému, kde presne k z n podielov je potrebných na rekonštrukciu tajného bitu.</p>
            """
            self.description_area.setHtml(description_text)

    def prepare_shares(self):
        """Prepare quantum shares for distribution."""
        try:
            self.status_label.setText("Pripravujem kvantové podiely...")

            # Reset animation state
            self.animation_step = 0
            self.secret = int(self.secret_combo.currentText())
            n = self.n_spinner.value()

            # Reset qubit states to |+⟩
            for qubit in self.qubit_items:
                qubit.setPos(self.dealer.pos())
                qubit.setState("|+⟩")

            # Update shares table
            self.shares_table.setRowCount(n)
            for i in range(n):
                # Participant name
                name_item = QTableWidgetItem(f"P{i + 1}")
                self.shares_table.setItem(i, 0, name_item)

                # Initial quantum state
                state_item = QTableWidgetItem("|+⟩")
                self.shares_table.setItem(i, 1, state_item)

                # Measurement (empty initially)
                meas_item = QTableWidgetItem("—")
                self.shares_table.setItem(i, 2, meas_item)

            # Create entanglement between qubits
            self.create_entanglement()

            # Enable next step
            self.distribute_btn.setEnabled(True)
            self.prepare_btn.setEnabled(False)

        except Exception as e:
            print(f"Error in prepare_shares: {e}", file=sys.stderr)
            self.status_label.setText(f"Chyba pri príprave podielov")

    def create_entanglement(self):
        """Create entanglement lines between qubits."""
        try:
            # Clear any existing entanglement lines
            for line in self.entanglement_lines:
                if line in self.scene.items():
                    self.scene.removeItem(line)
            self.entanglement_lines.clear()

            # Add new entanglement lines
            for i in range(len(self.qubit_items)):
                for j in range(i + 1, len(self.qubit_items)):
                    line = EntanglementLine(self.qubit_items[i], self.qubit_items[j])
                    self.scene.addItem(line)
                    self.entanglement_lines.append(line)

            # Update states to represent GHZ state
            for i, qubit in enumerate(self.qubit_items):
                qubit.setState("GHZ")
                if i < self.shares_table.rowCount():
                    self.shares_table.setItem(i, 1, QTableWidgetItem("GHZ"))

            self.status_label.setText(f"GHZ stav pripravený: {len(self.qubit_items)} qubitov previazaných")

        except Exception as e:
            print(f"Error in create_entanglement: {e}", file=sys.stderr)
            self.status_label.setText("Chyba pri vytváraní previazania")

    def distribute_shares(self):
        """Begin distribution of quantum shares."""
        self.status_label.setText("Distribuujem kvantové podiely účastníkom...")
        self.animation_timer.start(self.animation_speed)
        self.distribute_btn.setEnabled(False)

    def next_animation_step(self):
        """Handle next step in the animation sequence."""
        try:
            if self.animation_step < len(self.qubit_items):
                # Get current qubit and participant
                qubit_index = self.animation_step
                if qubit_index < len(self.qubit_items) and qubit_index < len(self.participant_items):
                    qubit = self.qubit_items[qubit_index]
                    participant = self.participant_items[qubit_index]

                    # Calculate position near participant
                    target_pos = participant.pos() + QPointF(-20, -20)
                    qubit.setPos(target_pos)

                    # Show encoding information for first qubit
                    if self.animation_step == 0:
                        basis = "X" if self.secret == 0 else "Z"
                        self.status_label.setText(f"Dealer kóduje tajný bit {self.secret} použitím {basis}-bázy")

                self.animation_step += 1
            else:
                # Animation complete
                self.animation_timer.stop()
                self.status_label.setText("Všetky podiely distribuované. Pripravené na rekonštrukciu tajomstva.")
                self.reconstruct_btn.setEnabled(True)

        except Exception as e:
            self.animation_timer.stop()
            print(f"Error in animation: {e}", file=sys.stderr)
            self.status_label.setText("Chyba pri animácii distribúcie")

    def reconstruct_secret(self):
        """Reconstruct the secret from quantum shares."""
        try:
            n = self.n_spinner.value()
            k = self.k_spinner.value()

            # Simulate measurements
            self.measurements = []
            for i in range(min(n, len(self.qubit_items))):
                # In real QSS, measurements would be coordinated
                # Here we simulate a consistent result for k participants
                if i < k:
                    measurement = self.secret
                else:
                    measurement = random.randint(0, 1)

                self.measurements.append(measurement)

                # Update table
                if i < self.shares_table.rowCount():
                    result_item = QTableWidgetItem(str(measurement))
                    self.shares_table.setItem(i, 2, result_item)

                # Update qubit state
                if i < len(self.qubit_items):
                    self.qubit_items[i].setState(f"|{measurement}⟩")

            # Calculate reconstructed secret using XOR of first k measurements
            reconstructed = 0
            for i in range(min(k, len(self.measurements))):
                reconstructed ^= self.measurements[i]  # XOR operation

            # Display result
            result_correct = reconstructed == self.secret
            result_color = "green" if result_correct else "red"

            self.status_label.setText(
                f"Tajomstvo zrekonštruované: {reconstructed} (Pôvodné: {self.secret}) - " +
                f"<span style='color: {result_color};'>{'Úspešné' if result_correct else 'Neúspešné'}</span>"
            )
            self.status_label.setTextFormat(Qt.TextFormat.RichText)

            # Disable reconstruction button
            self.reconstruct_btn.setEnabled(False)

        except Exception as e:
            print(f"Error in reconstruct_secret: {e}", file=sys.stderr)
            self.status_label.setText("Chyba pri rekonštrukcii tajomstva")

    def reset_protocol(self, recreate_scene=True):
        """Reset the protocol to initial state."""
        try:
            # Stop any ongoing animation
            if self.animation_timer.isActive():
                self.animation_timer.stop()

            # Reset UI state
            self.prepare_btn.setEnabled(True)
            self.distribute_btn.setEnabled(False)
            self.reconstruct_btn.setEnabled(False)

            # Reset animation state
            self.animation_step = 0

            # Clear data
            self.shares = []
            self.measurements = []

            # Clear shares table
            self.shares_table.setRowCount(0)

            # Safest approach: complete scene recreation
            if recreate_scene:
                self.create_new_scene()

            # Reset status
            self.status_label.setText("Pripravené na začatie Kvantového zdieľania tajomstva")

        except Exception as e:
            print(f"Error in reset_protocol: {e}", file=sys.stderr)
            # Create new scene as fallback
            self.create_new_scene()
            self.status_label.setText("Resetované po chybe")