from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QLineF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QLinearGradient

import random
import math
import traceback

from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Statevector


class ParticleItem(QGraphicsItem):
    def __init__(self, color=Qt.GlobalColor.blue, radius=21, quantum_notation=False):
        super().__init__()
        self.color = color
        self.radius = radius
        self.setZValue(1)
        self.state = "0"
        self.basis = None
        self.measuring = False
        self.quantum_notation = quantum_notation

    def setState(self, state):
        # Ak už nie je v kvantovom stave (po meraní), odstránenie zátvorky
        self.state = state
        self.measuring = False  # Vždy vypnúť animáciu merania
        self.update()

    def setMeasurementBasis(self, basis):
        """Nastavenie meracej bázy pre qubit"""
        self.basis = basis
        if basis == "X":
            self.color = QColor(100, 200, 100)  # Zelená pre X-bázu
        elif basis == "Z":
            self.color = QColor(100, 100, 200)  # Modrá pre Z-bázu
        self.update()

    def startMeasurementAnimation(self):
        """Spustenie animácie merania"""
        self.measuring = True
        self.update()

    def stopMeasurementAnimation(self):
        """Zastavenie animácie merania"""
        self.measuring = False
        self.update()
        # Vynútiť aktualizáciu scény
        if self.scene():
            self.scene().update()

    def boundingRect(self):
        # Zjednodušené - vždy vrátiť konštantnú veľkosť
        return QRectF(-self.radius - 5, -self.radius - 5,
                      2 * self.radius + 10, 2 * self.radius + 10)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Kreslenie pulzujúceho efektu
        if self.measuring and self.state not in ["0", "1"]:
            glow_color = QColor(255, 255, 100, 100)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QPointF(0, 0), self.radius + 5, self.radius + 5)

        # Gradient pre qubit
        gradient = QLinearGradient(-self.radius, -self.radius, self.radius, self.radius)
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color)

        # Vykreslenie kruhu s gradientom
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius))

        # Vykreslenie stavu
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        # Zobrazovanie stavu podľa stavu merania qubitu
        display_text = self.state
        if self.basis is not None:  # Pri nastavenej báze, indikácia zmerania qubitu
            if self.state in ["0", "1"]:
                display_text = self.state  # Klasický stav (už po meraní)
            elif "GHZ" in self.state:
                # Extrahovanie len hodnoty z GHZ(0) -> "0"
                display_text = self.state.split("(")[1][0]

        painter.drawText(QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius),
                         Qt.AlignmentFlag.AlignCenter, display_text)

        # Vykreslenie bázy, ak je nastavená
        if self.basis:
            basis_radius = self.radius / 3
            basis_offset = self.radius * 1.2

            if self.basis == "X":
                basis_pos = QPointF(basis_offset, 0)
                basis_color = QColor(100, 200, 100)
            else:  # Z-báza
                basis_pos = QPointF(0, basis_offset)
                basis_color = QColor(100, 100, 200)

            painter.setPen(QPen(Qt.GlobalColor.black, 0.5))
            painter.setBrush(QBrush(basis_color))
            painter.drawEllipse(basis_pos, basis_radius, basis_radius)

            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            basis_rect = QRectF(
                basis_pos.x() - basis_radius,
                basis_pos.y() - basis_radius,
                2 * basis_radius,
                2 * basis_radius
            )
            painter.drawText(basis_rect, Qt.AlignmentFlag.AlignCenter, self.basis)


class EntanglementLine(QGraphicsItem):
    def __init__(self, particle1, particle2, color=Qt.GlobalColor.red):
        super().__init__()
        self.particle1 = particle1
        self.particle2 = particle2
        self.color = color
        self.setZValue(0)
        self.dash_offset = 0
        # Odstránený vlastný timer pre každú čiaru

    def update_animation(self):
        """Aktualizácia animácie prerušovanej čiary"""
        self.dash_offset = (self.dash_offset + 1) % 16
        self.update()

    def boundingRect(self):
        pos1 = self.particle1.pos()
        pos2 = self.particle2.pos()
        x = min(pos1.x(), pos2.x()) - 5
        y = min(pos1.y(), pos2.y()) - 5
        width = abs(pos1.x() - pos2.x()) + 10
        height = abs(pos1.y() - pos2.y()) + 10
        return QRectF(x, y, width, height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient pre čiaru
        pos1 = self.particle1.pos()
        pos2 = self.particle2.pos()
        gradient = QLinearGradient(pos1, pos2)
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color)

        # Čiara s gradientom a dash pattern
        pen = QPen(QBrush(gradient), 2, Qt.PenStyle.DashLine)
        pen.setDashPattern([5, 3])
        pen.setDashOffset(self.dash_offset)
        painter.setPen(pen)
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

        # Gradient pre telo
        body_gradient = QLinearGradient(
            -self.width / 3, -self.height / 4,
            self.width / 3, self.height / 2
        )
        body_gradient.setColorAt(0, self.color.lighter(120))
        body_gradient.setColorAt(1, self.color)

        # Kreslenie tela (obdĺžik) s gradientom
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(body_gradient))
        body_rect = QRectF(-self.width / 3, -self.height / 4, 2 * self.width / 3, 2 * self.height / 3)
        painter.drawRoundedRect(body_rect, 5, 5)

        # Gradient pre hlavu
        head_gradient = QLinearGradient(
            0, -self.height / 2,
            0, -self.height / 2 + self.width / 2
        )
        head_color = self.color.lighter(130)
        head_gradient.setColorAt(0, head_color.lighter(110))
        head_gradient.setColorAt(1, head_color)

        # Kreslenie hlavy (kruh) s gradientom
        head_radius = self.width / 4
        head_center = QPointF(0, -self.height / 2 + head_radius)
        painter.setBrush(QBrush(head_gradient))
        painter.drawEllipse(head_center, head_radius, head_radius)

        # Kreslenie mena s tieňom
        text_rect = QRectF(-self.width / 2, self.height / 3, self.width, self.height / 4)

        # Tieň textu
        painter.setPen(QPen(QColor(0, 0, 0, 50)))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        shadow_rect = text_rect.adjusted(1, 1, 1, 1)
        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, self.name)

        # Text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.name)


class QSSProtocolUI(QWidget):
    def __init__(self):
        """Inicializácia aplikácie pre kvantové zdieľanie tajomstva"""
        super().__init__()

        # Základné premenné protokolu
        self.n_participants = 3
        self.secret = 0
        self.measurements = []
        self.measurement_bases = []

        # Qiskit obvod a simulátor
        self.circuit = None
        self.simulator = None  # Inicializujeme neskôr

        # Animácia
        self.animation_step = 0
        self.distribution_timer = QTimer()
        self.distribution_timer.timeout.connect(self.next_distribution_step)
        self.measurement_timer = QTimer()

        # Timer pre všetky entanglement čiary
        self.entanglement_timer = QTimer()
        self.entanglement_timer.timeout.connect(self.update_all_entanglements)

        # Inicializácia UI a scény
        self.setup_ui()
        self.create_new_scene()

        # Nastavenie okna
        self.setWindowTitle("Kvantové zdieľanie tajomstva")
        self.resize(1000, 700)

        # Pripojenie signálu pre meranie
        self.measurement_timer.timeout.connect(self.next_measurement_step)

    def update_all_entanglements(self):
        """Aktualizácia všetkých entanglement čiar naraz"""
        for line in self.entanglement_lines:
            if line in self.scene.items():
                line.update_animation()

    def setup_ui(self):
        """Nastavenie používateľského rozhrania"""
        main_layout = QVBoxLayout()

        # Hlavička
        title_label = QLabel("Kvantové zdieľanie tajomstva")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        # Rozdelenie hlavného obsahu
        content_layout = QHBoxLayout()

        # Ľavý panel - konfigurácia
        left_panel = QVBoxLayout()
        left_panel.setSpacing(0)

        # Konfigurácia protokolu
        config_group = QGroupBox("Konfigurácia protokolu")
        config_layout = QGridLayout()

        self.n_label = QLabel("Celkový počet účastníkov (n):")
        self.n_spinner = QSpinBox()
        self.n_spinner.setRange(3, 10)
        self.n_spinner.setValue(3)
        self.n_spinner.valueChanged.connect(self.on_n_changed)
        config_layout.addWidget(self.n_label, 0, 0)
        config_layout.addWidget(self.n_spinner, 0, 1)

        self.secret_label = QLabel("Tajný bit:")
        self.secret_combo = QComboBox()
        self.secret_combo.addItems(["0", "1"])
        self.secret_combo.currentTextChanged.connect(self.update_secret_bit_display)
        config_layout.addWidget(self.secret_label, 1, 0)
        config_layout.addWidget(self.secret_combo, 1, 1)

        # Informácie o použitom GHZ stave
        ghz_label = QLabel("Použitý GHZ stav:")
        ghz_value = QLabel("1/√2(|000⟩ + |111⟩)")
        ghz_value.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        config_layout.addWidget(ghz_label, 2, 0)
        config_layout.addWidget(ghz_value, 2, 1)

        config_group.setLayout(config_layout)
        left_panel.addWidget(config_group)

        # Ovládacie tlačidlá
        controls_group = QGroupBox("Ovládanie")
        controls_layout = QVBoxLayout()

        self.prepare_btn = QPushButton("Pripraviť kvantový obvod")
        self.prepare_btn.clicked.connect(self.prepare_circuit_safe)
        controls_layout.addWidget(self.prepare_btn)

        self.distribute_btn = QPushButton("Distribuovať podiely")
        self.distribute_btn.clicked.connect(self.start_distribution)
        self.distribute_btn.setEnabled(False)
        controls_layout.addWidget(self.distribute_btn)

        self.reconstruct_btn = QPushButton("Zrekonštruovať tajomstvo")
        self.reconstruct_btn.clicked.connect(self.start_measurement)
        self.reconstruct_btn.setEnabled(False)
        controls_layout.addWidget(self.reconstruct_btn)

        self.reset_btn = QPushButton("Resetovať")
        self.reset_btn.clicked.connect(self.reset_protocol)
        controls_layout.addWidget(self.reset_btn)

        controls_group.setLayout(controls_layout)
        left_panel.addWidget(controls_group)

        # Panel pre chyby
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        left_panel.addWidget(self.error_label)

        # Informačný panel
        info_group = QGroupBox("Informácie o protokole")
        info_layout = QVBoxLayout()
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMinimumHeight(300)
        info_text.setHtml("""
        <p>Protokol používa GHZ stav: |GHZ₀₀₀⁺⟩ = 1/√2(|000⟩ + |111⟩)</p>
        <p><b>Postup protokolu:</b></p>
        <ol>
            <li>Alice pripraví <b>GHZ stav</b> a zakóduje doň tajný bit</li>
            <li>Alice pošle Bobovi a Charliemu po jednom qubite</li>
            <li>Účastníci <b>nezávisle zmerajú</b> svoje qubity v náhodných bázach (X alebo Z)</li>
            <li>Účastníci <b>verejne oznámia svoje meracie bázy</b>, ale utaja výsledky meraní</li>
            <li>Na základe známych korelácií GHZ stavu môžu spoločne zrekonštruovať tajomstvo</li>
        </ol>
        <p><b>Korelácie pre GHZ stav |000⟩ + |111⟩:</b></p>
        <ul>
            <li>Meranie v <b>Z-bázach</b>: Platí rovnica a=b=c (všetci majú rovnaký výsledok)</li>
            <li>Meranie v <b>X-bázach</b>: Parita výsledkov zodpovedá tajnému bitu</li>
            <li>Meranie v <b>rôznych bázach</b>: Využívajú sa korelačné vzťahy medzi bázami</li>
        </ul>
        """)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)

        content_layout.addLayout(left_panel, 1)

        # Pravý panel - vizualizácia
        right_panel = QVBoxLayout()

        # Animácia
        animation_group = QGroupBox("Animácia protokolu")
        animation_layout = QVBoxLayout()

        self.graphics_view = QGraphicsView()
        self.graphics_view.setMinimumHeight(300)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        animation_layout.addWidget(self.graphics_view)

        self.status_label = QLabel("Pripravené na začatie protokolu")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        animation_layout.addWidget(self.status_label)

        animation_group.setLayout(animation_layout)
        right_panel.addWidget(animation_group)

        # Tabuľka podielov
        shares_group = QGroupBox("Kvantové podiely")
        shares_layout = QVBoxLayout()

        self.shares_table = QTableWidget(0, 4)
        self.shares_table.setHorizontalHeaderLabels(["Účastník", "Kvantový stav", "Meracia báza", "Meranie"])
        header = self.shares_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        shares_layout.addWidget(self.shares_table)

        shares_group.setLayout(shares_layout)
        right_panel.addWidget(shares_group)

        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def update_secret_bit_display(self, text):
        """Aktualizácia zobrazenia tajného bitu v Alicinom qubite"""
        try:
            # Aktualizácia hodnoty tajného bitu
            self.secret = int(text)

            # Pri existencii vytvorenej scény a qubitov, ich aktualizovanie
            if hasattr(self, 'qubit_items') and len(self.qubit_items) > 0:
                # Odstránime starý qubit
                old_qubit = self.qubit_items[0]
                self.scene.removeItem(old_qubit)

                # Vytvorenie nového qubitu s aktuálnym tajným bitom
                qubit_color = QColor(50, 200, 50) if self.secret == 0 else QColor(200, 50, 50)
                alice_qubit = ParticleItem(qubit_color)
                alice_qubit.setPos(self.alice.pos() + QPointF(40, -30))
                # Nastavenie čísla, nie kvantového stavu
                alice_qubit.setState(str(self.secret))
                self.scene.addItem(alice_qubit)

                # Nahradenie starého qubitu v zozname
                self.qubit_items[0] = alice_qubit

                # Vynútenie prekreslenia scény
                self.scene.update()
                self.graphics_view.viewport().update()

                # Informácia o zmene v status bare
                self.status_label.setText(f"Tajný bit zmenený na: {self.secret}")
        except Exception as e:
            self.show_error(f"Chyba pri aktualizácii tajného bitu: {str(e)}")

    def create_new_scene(self):
        """Vytvorenie novej scény s účastníkmi"""
        # Inicializácia scény
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 600, 280)
        self.graphics_view.setScene(self.scene)

        # Vyčistenie zoznamov objektov
        self.participant_items = []
        self.qubit_items = []
        self.entanglement_lines = []

        # Pridanie účastníkov
        self.add_participants_to_scene()

    def add_participants_to_scene(self):
        """Pridanie účastníkov a ich qubitov do scény"""
        try:
            n = self.n_spinner.value()
            self.secret = int(self.secret_combo.currentText())

            # Pridanie Alice
            self.alice = PersonItem("Alice", QColor(150, 50, 100))
            self.alice.setPos(100, 140)
            self.scene.addItem(self.alice)
            self.participant_items.append(self.alice)

            # Vytvorenie qubitu pre Alice s farbou podľa tajného bitu
            qubit_color = QColor(50, 200, 50) if self.secret == 0 else QColor(200, 50, 50)
            alice_qubit = ParticleItem(qubit_color)
            alice_qubit.setPos(self.alice.pos() + QPointF(40, -30))
            # Zobrazenie čísla, nie kvantového stavu
            alice_qubit.setState(str(self.secret))
            alice_qubit.basis = None
            alice_qubit.measuring = False
            self.scene.addItem(alice_qubit)
            self.qubit_items.append(alice_qubit)

            # Rozloženie ostatných účastníkov
            if n <= 4:
                self._create_horizontal_participants(n)
            else:
                self._create_arc_participants(n)

        except Exception as e:
            self.show_error(f"Chyba pri vytváraní účastníkov: {str(e)}")

    def _create_horizontal_participants(self, n):
        """Vytvorenie účastníkov v horizontálnej línii"""
        spacing = 150
        start_x = 300
        y = 140

        for i in range(n - 1):
            x = start_x + i * spacing
            name = self.get_participant_name(i)

            # Vytvorenie účastníka
            participant = PersonItem(name, QColor(50, 100, 180))
            participant.setPos(x, y)
            self.scene.addItem(participant)
            self.participant_items.append(participant)

            # Vytvorenie qubitu (zatiaľ u Alice) s počiatočnou hodnotou "0"
            qubit = ParticleItem(QColor(100, 150, 255))
            qubit.setPos(self.alice.pos() + QPointF(40, -30))
            qubit.setState("0")  # Len číslo, nie kvantový stav
            qubit.basis = None
            qubit.measuring = False
            self.scene.addItem(qubit)
            self.qubit_items.append(qubit)

    def _create_arc_participants(self, n):
        """Vytvorenie účastníkov v polkruhovom rozmiestnení"""
        radius = 180
        center_x = 400
        center_y = 200
        angle_step = math.pi / (n)
        start_angle = math.pi / 6

        for i in range(n - 1):
            angle = start_angle + angle_step * i
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            name = self.get_participant_name(i)

            # Vytvorenie účastníka
            participant = PersonItem(name, QColor(50, 100, 180))
            participant.setPos(x, y)
            self.scene.addItem(participant)
            self.participant_items.append(participant)

            # Vytvorenie qubitu (zatiaľ u Alice)
            qubit = ParticleItem(QColor(100, 150, 255))
            qubit.setPos(self.alice.pos() + QPointF(40, -30))
            qubit.setState("0")
            self.scene.addItem(qubit)
            self.qubit_items.append(qubit)

    def get_participant_name(self, index):
        """Vrátenie mena účastníka podľa indexu"""
        names = ["Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
        return names[index] if index < len(names) else f"P{index + 1}"

    def on_n_changed(self):
        """Reakcia na zmenu počtu účastníkov"""
        self.create_new_scene()
        self.reset_protocol(recreate_scene=False)

    def get_ghz_state_notation(self, n_qubits, simplified=False):
        """Generovanie notácie GHZ stavu"""
        if simplified:
            return "GHZ"
        zeros = "0" * n_qubits
        ones = "1" * n_qubits
        return f"1/√2(|{zeros}⟩ + |{ones}⟩)"

    def prepare_circuit_safe(self):
        """Bezpečné volanie prípravy obvodu"""
        try:
            self.error_label.setText("")
            self.prepare_circuit()
        except Exception as e:
            error_msg = f"Chyba pri príprave obvodu: {str(e)}"
            self.show_error(error_msg)
            traceback.print_exc()

    def show_error(self, message):
        """Zobrazenie chybovej správy"""
        self.error_label.setText(message)
        self.status_label.setText("Nastala chyba! Skúste resetovať protokol.")

    def prepare_circuit(self):
        """Príprava kvantového obvodu"""
        self.status_label.setText("Alice pripravuje kvantový obvod...")
        self.animation_step = 0
        self.secret = int(self.secret_combo.currentText())
        n = self.n_spinner.value()

        # Inicializácia simulátora
        self.simulator = Aer.get_backend('statevector_simulator')

        # Vytvorenie obvodu
        self.circuit = QuantumCircuit(n, n)
        self.circuit.h(0)  # Krok 1: Stav |+⟩ na prvom qubite

        # Krok 2: CNOT na vytvorenie previazania
        for i in range(1, n):
            self.circuit.cx(0, i)

        # Krok 3: Zakódovanie tajného bitu
        if self.secret == 1:
            # X operácie pre merania v Z-báze
            for i in range(n):
                self.circuit.x(i)
            # Z-operácia pre merania v X-báze
            self.circuit.z(0)

        # Aktualizácia UI
        ghz_state_name = self.get_ghz_state_notation(n, simplified=True)
        ghz_with_secret = f"GHZ({self.secret})"
        color = QColor(100, 150, 255)

        # Aktualizácia qubitu
        for qubit in self.qubit_items[:n]:
            qubit.color = color
            qubit.setState(ghz_with_secret)

        # Aktualizácia tabuľky
        self.shares_table.setRowCount(n)
        for i in range(n):
            name = "Alice" if i == 0 else self.get_participant_name(i - 1)
            self.shares_table.setItem(i, 0, QTableWidgetItem(name))
            self.shares_table.setItem(i, 1, QTableWidgetItem(ghz_with_secret))
            self.shares_table.setItem(i, 2, QTableWidgetItem("—"))
            self.shares_table.setItem(i, 3, QTableWidgetItem("—"))

        # Vytvorenie kvantového previazania
        try:
            self.create_entanglement()
        except Exception as e:
            self.show_error(f"Chyba pri vytváraní kvantového previazania: {str(e)}")
            return

        # Aktualizácia UI
        self.prepare_btn.setEnabled(False)
        self.status_label.setText(f"Kvantový obvod pripravený: {n} qubitov v GHZ stave, tajomstvo: {self.secret}")
        self.distribute_btn.setEnabled(True)

    def create_entanglement(self):
        """Vytvorenie kvantového previazania medzi qubitmi"""
        # Zastavenie existujúcej animácie
        self.entanglement_timer.stop()

        # Odstránenie existujúcich entanglement lines
        for line in self.entanglement_lines:
            if line in self.scene.items():
                self.scene.removeItem(line)
        self.entanglement_lines.clear()

        # Vytvorenie nových entanglement lines
        alice_qubit = self.qubit_items[0]
        n = min(len(self.qubit_items), self.n_spinner.value())

        for i in range(1, n):
            other_qubit = self.qubit_items[i]
            line = EntanglementLine(alice_qubit, other_qubit, QColor(255, 50, 50))
            self.scene.addItem(line)
            self.entanglement_lines.append(line)

        # Spustenie animácie čiar ak existujú
        if self.entanglement_lines:
            self.entanglement_timer.start(100)

        self.status_label.setText("GHZ stav vytvorený: qubity sú kvantovo previazané")

    def start_distribution(self):
        """Spustenie distribúcie qubitov"""
        try:
            self.distribution_timer.stop()
            self.animation_step = 0
            self.distribute_btn.setEnabled(False)
            self.status_label.setText("Alice distribuuje kvantové podiely ostatným účastníkom...")
            self.distribution_timer.start(500)  # 500ms interval
        except Exception as e:
            self.show_error(f"Chyba pri distribúcii podielov: {str(e)}")

    def next_distribution_step(self):
        """Animácia distribúcie ďalšieho qubitu"""
        try:
            n = self.n_spinner.value()
            if self.animation_step < n - 1:
                # Získanie indexov ďalšieho qubitu a účastníka
                qubit_index = self.animation_step + 1  # Preskočiť Alicin qubit
                participant_index = self.animation_step + 1

                # Bezpečnostná kontrola indexov
                if qubit_index >= len(self.qubit_items) or participant_index >= len(self.participant_items):
                    self.show_error("Chyba: Neplatný index pre qubity alebo účastníkov")
                    self.distribution_timer.stop()
                    return

                # Získanie objektov pre animáciu
                qubit = self.qubit_items[qubit_index]
                participant = self.participant_items[participant_index]

                # Nastavenie novej pozície qubitu vedľa účastníka
                target_pos = participant.pos() + QPointF(40, -30)
                qubit.setPos(target_pos)

                # Aktualizácia statusu
                participant_name = self.get_participant_name(self.animation_step)
                self.status_label.setText(f"Alice posiela qubit účastníkovi {participant_name}")

                # Prejdeme na ďalší krok
                self.animation_step += 1
            else:
                # Všetky qubity distribuované
                self.distribution_timer.stop()
                self.status_label.setText("Všetky podiely distribuované. Pripravené na meranie.")
                self.reconstruct_btn.setEnabled(True)
        except Exception as e:
            self.distribution_timer.stop()
            self.show_error(f"Chyba pri distribúcii qubitov: {str(e)}")

    def start_measurement(self):
        """Spustenie merania qubitov"""
        try:
            self.measurement_timer.stop()
            self.reconstruct_btn.setEnabled(False)
            self.animation_step = 0

            # Príprava merania
            n = self.n_spinner.value()
            self.measurements = []
            self.measurement_bases = []

            # Aktualizovaná správa
            self.status_label.setText(
                "Alice, Bob a Charlie nezávisle merajú svoje qubity v náhodných bázach (X alebo Z)...")

            # Náhodný výber meracích báz
            self.measurement_bases = [random.choice(["X", "Z"]) for _ in range(n)]

            # Vytvorenie meracieho obvodu
            try:
                # Inicializácia simulátora, ak nie je
                if self.simulator is None:
                    self.simulator = Aer.get_backend('statevector_simulator')

                # Simulácia merania qubitu
                statevector_job = execute(self.circuit, self.simulator)
                statevector = statevector_job.result().get_statevector()

                # Vytvorenie meracieho obvodu
                measurement_circuit = QuantumCircuit(n, n)
                measurement_circuit.initialize(Statevector(statevector), range(n))

                # Aplikácia Hadamard pre X-bázu
                for i in range(n):
                    if self.measurement_bases[i] == "X":
                        measurement_circuit.h(i)

                # Meranie qubitov
                measurement_circuit.measure(range(n), range(n))
                qasm_simulator = Aer.get_backend('qasm_simulator')
                qasm_job = execute(measurement_circuit, qasm_simulator, shots=1)
                measurement_string = list(qasm_job.result().get_counts().keys())[0]
                measurement_bits = [int(bit) for bit in measurement_string]

                # Uloženie výsledkov merania
                self.measurements = measurement_bits
            except Exception as e:
                # Ak nastane chyba v simulácii, použijú sa náhodné výsledky
                self.show_error(f"Chyba v kvantovej simulácii: {str(e)}. Použité náhodné výsledky.")
                self.measurements = [random.randint(0, 1) for _ in range(n)]

            # Aktualizácia tabuľky s bázami
            for i in range(n):
                self.shares_table.setItem(i, 2, QTableWidgetItem(self.measurement_bases[i]))

            # Spustenie animácie merania
            self.measurement_timer.start(400)
        except Exception as e:
            self.show_error(f"Chyba pri meraní qubitov: {str(e)}")
            self.measurement_timer.stop()

    def next_measurement_step(self):
        """Animácia merania ďalšieho qubitu"""
        try:
            n = self.n_spinner.value()

            if self.animation_step < n:
                # Bezpečnostná kontrola indexov
                if self.animation_step >= len(self.qubit_items) or self.animation_step >= len(
                        self.measurements) or self.animation_step >= len(self.measurement_bases):
                    self.show_error("Chyba: Neplatný index pre meranie qubitov")
                    self.measurement_timer.stop()
                    return

                # Získanie údajov o meraní
                qubit = self.qubit_items[self.animation_step]
                result = self.measurements[self.animation_step]
                basis = self.measurement_bases[self.animation_step]

                # Aktualizácia statusu
                participant_name = "Alice" if self.animation_step == 0 else self.get_participant_name(
                    self.animation_step - 1)
                self.status_label.setText(f"{participant_name} meria svoj qubit v {basis}-báze...")

                # Spustenie animácie merania
                qubit.startMeasurementAnimation()

                # Po krátkom čase dokončíme meranie
                QTimer.singleShot(300, lambda q=qubit, r=result, b=basis, i=self.animation_step:
                self.finish_measurement_for_qubit(q, r, b, i))

                # Zastavenie timera počas animácie
                self.measurement_timer.stop()
            else:
                # Všetky qubity boli zmerané
                self.measurement_timer.stop()
                self.status_label.setText(
                    "Merania dokončené. Účastníci verejne oznámia svoje meracie bázy (nie výsledky merania)...")
                QTimer.singleShot(1500, self.show_reconstruction_result)
        except Exception as e:
            self.measurement_timer.stop()
            self.show_error(f"Chyba pri meraní qubitov: {str(e)}")

    def finish_measurement_for_qubit(self, qubit, result, basis, index):
        """Dokončenie merania qubitu a zobrazenie výsledku"""
        try:
            # Zastavenie animácie merania
            qubit.stopMeasurementAnimation()
            qubit.measuring = False

            # Nastavenie výsledného stavu - explicitne ako číslo
            result_colors = [QColor(50, 200, 50), QColor(200, 50, 50)]  # Zelená pre 0, červená pre 1
            qubit.color = result_colors[result]
            qubit.setState(str(result))  # Číselný výsledok bez špeciálneho formátovania
            qubit.setMeasurementBasis(basis)

            # Vynútenie prekreslenia
            qubit.update()
            if self.scene:
                self.scene.update()

            # Aktualizácia tabuľky
            if index < self.shares_table.rowCount():
                self.shares_table.setItem(index, 3, QTableWidgetItem(str(result)))

            # Ďalší krok
            self.animation_step += 1
            QTimer.singleShot(300, lambda: self.measurement_timer.start())
        except Exception as e:
            self.show_error(f"Chyba pri dokončení merania: {str(e)}")
            self.animation_step += 1
            QTimer.singleShot(300, lambda: self.measurement_timer.start())

    def show_reconstruction_result(self):
        """Zobrazenie výsledku rekonštrukcie tajomstva"""
        try:
            # Určenie typu rekonštrukcie podľa báz
            bases_set = set(self.measurement_bases)

            if len(bases_set) == 1:
                # Všetci merajú v rovnakej báze
                if self.measurement_bases[0] == "X":
                    # Výpočet parity X-meraní
                    parity = 0
                    for bit in self.measurements:
                        parity ^= bit
                    reconstructed = parity
                    method = "výpočtom parity X-meraní"
                else:  # Z-báza
                    # Z-merania dávajú priamo tajný bit
                    reconstructed = self.measurements[0]
                    method = "koreláciou v Z-báze (a=b=c)"
            else:
                # Rôzne bázy
                reconstructed = self.calculate_mixed_bases_secret()
                method = "komplexná korelácia pri rôznych bázach"

            # Kontrola úspešnosti rekonštrukcie
            result_correct = (reconstructed == self.secret)
            self.status_label.setText(
                f"Tajomstvo zrekonštruované ({method}): {reconstructed} (Pôvodné: {self.secret}) - " +
                f"{'Úspešné' if result_correct else 'Neúspešné'}"
            )

            # Prípravu nového obvodu
            self.prepare_btn.setEnabled(True)
        except Exception as e:
            self.show_error(f"Chyba pri rekonštrukcii tajomstva: {str(e)}")
            self.prepare_btn.setEnabled(True)

    def calculate_mixed_bases_secret(self):
        """Výpočet tajomstva z meraní v rôznych bázach

        Pre GHZ stav |000⟩ + |111⟩ platia tieto korelácie:
        - Ak všetci merajú v Z-báze: všetci dostanú rovnaký výsledok (0 alebo 1)
        - Ak všetci merajú v X-báze: parita výsledkov zodpovedá tajnému bitu
        - Pri zmiešaných bázach: aplikujú sa komplexnejšie korelačné vzťahy
        """
        try:
            n = self.n_spinner.value()

            # Kontrola hraníc polí
            if len(self.measurement_bases) < n or len(self.measurements) < n:
                n = min(len(self.measurement_bases), len(self.measurements))
                if n == 0:
                    return random.randint(0, 1)

            # Rozdelenie meraní podľa báz
            x_indices = [i for i in range(n) if self.measurement_bases[i] == "X"]
            z_indices = [i for i in range(n) if self.measurement_bases[i] == "Z"]

            # Ak máme aspoň jedno meranie v Z-báze
            if z_indices:
                # Kontrola konzistencie Z-meraní
                z_values = [self.measurements[i] for i in z_indices]
                z_consistent = all(z == z_values[0] for z in z_values)

                if not z_consistent:
                    return random.randint(0, 1)  # Nekonzistentné merania

                z_value = z_values[0]

                # Ak nie je k dispozícií X-merania
                if not x_indices:
                    return z_value

                # Kombinácia X a Z meraní
                x_parity = 0
                for i in x_indices:
                    x_parity ^= self.measurements[i]

                # Parita X-merania a hodnota Z určujú tajomstvo
                return x_parity if z_value == 0 else 1 - x_parity
            else:
                # Len X-merania
                x_parity = 0
                for i in x_indices:
                    x_parity ^= self.measurements[i]
                return x_parity
        except Exception as e:
            self.error_label.setText(f"Chyba pri výpočte tajomstva: {str(e)}")
            return random.randint(0, 1)

    def reset_protocol(self, recreate_scene=True):
        """Reset protokolu do počiatočného stavu"""
        try:
            # Zastavenie všetkých timerov
            self.distribution_timer.stop()
            self.measurement_timer.stop()
            self.entanglement_timer.stop()

            # Reset stavových premenných
            self.animation_step = 0
            self.circuit = None
            self.measurements = []
            self.measurement_bases = []

            # Reset UI
            self.prepare_btn.setEnabled(True)
            self.distribute_btn.setEnabled(False)
            self.reconstruct_btn.setEnabled(False)
            self.error_label.setText("")

            # Vyčistenie tabuľky
            self.shares_table.clearContents()
            self.shares_table.setRowCount(0)

            # Kompletné znovuvytvorenie scény
            if hasattr(self, 'scene'):
                # Úplné vyčistenie
                self.scene.clear()

            # Vyčistenie zoznamov objektov
            self.participant_items = []
            self.qubit_items = []
            self.entanglement_lines = []

            # Vytvorenie novej scény s čistými počiatočnými vlastnosťami
            self.scene = QGraphicsScene()
            self.scene.setSceneRect(0, 0, 600, 280)
            self.graphics_view.setScene(self.scene)

            # Pridanie účastníkov s počiatočnými stavmi
            self.add_participants_to_scene()

            # Zabezpečenie okamžitého prekreslenia scény
            self.scene.update()
            self.graphics_view.viewport().update()
            QApplication.processEvents()

            # Aktualizácia statusu
            self.status_label.setText("Pripravené na začatie kvantového zdieľania tajomstva")
        except Exception as e:
            self.error_label.setText(f"Chyba pri resetovaní: {str(e)}")
            traceback.print_exc()
            self.prepare_btn.setEnabled(True)