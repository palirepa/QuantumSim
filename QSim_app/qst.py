from PyQt6.QtWidgets import (QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QGroupBox, QTabWidget, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Statevector

import sys
import math
import random


class BlochSphereWidget(QWidget):
    """Vlastný widget pre kreslenie Blochových sfér"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(350)
        self.setStyleSheet("background-color: #fafafa; border: 1px solid #ccc;")

        # Parametre
        self.omega = 6.28  # približne 2*pi, zaokrúhlené na 2 desatinné miesta
        self.delta = 0.79  # približne pi/4, zaokrúhlené na 2 desatinné miesta
        self.current_time = 0.0
        self.synced = False
        self.entanglement_prepared = False
        self.protocol_step = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            w = self.width()
            h = self.height()
            r = min(w, h) * 0.2
            r_i = int(r)

            cy_i = int(h * 0.5)
            cxA_i = int(w * 0.25)
            cxB_i = int(w * 0.75)

            # Kreslenie Blochovej sféry pre Alicu
            self.draw_bloch_sphere(painter, cxA_i, cy_i, r_i, "Alice")

            # Kreslenie Blochovej sféry pre Boba
            self.draw_bloch_sphere(painter, cxB_i, cy_i, r_i, "Bob")

            # Výpočet fázových uhlov
            phiA = (self.omega * self.current_time) % (2 * math.pi)
            phiB = (self.omega * self.current_time + self.delta) % (2 * math.pi)

            # Kreslenie stavových vektorov s celočíselnými súradnicami
            self.draw_state_vector(painter, cxA_i, cy_i, r_i, phiA, "blue")
            self.draw_state_vector(painter, cxB_i, cy_i, r_i, phiB, "orange")

            # Kreslenie indikátora fázového rozdielu delta ak nie je synchronizované
            # Zobrazovanie fázového rozdielu až po vytvorení previazania (v kroku 4, nie 3)
            if not self.synced and self.protocol_step >= 4 and self.protocol_step < 5:
                painter.setPen(QPen(QColor(255, 0, 0, 180), 2, Qt.PenStyle.DashLine))

                # Kreslenie oblúka zobrazujúceho fázový rozdiel
                angle_span = phiB - phiA if phiB > phiA else phiB + 2 * math.pi - phiA
                arc_radius = r_i * 0.7

                # Použitie QRectF pre drawArc
                painter.drawArc(
                    QRectF(cxB_i - arc_radius, cy_i - arc_radius, 2 * arc_radius, 2 * arc_radius),
                    int(16 * (-phiA * 180 / math.pi)),
                    int(16 * (-angle_span * 180 / math.pi))
                )

            # Kreslenie indikátora previazania, ak je aktívny
            # Zobrazovanie previazania už od kroku 3, nie až od kroku 4
            if self.entanglement_prepared and self.protocol_step >= 3:
                painter.setPen(QPen(QColor(128, 0, 128), 2, Qt.PenStyle.DashLine))
                painter.drawLine(cxA_i, cy_i, cxB_i, cy_i)

                # Kreslenie symbolu previazania v strede
                entanglement_x = (cxA_i + cxB_i) // 2
                painter.setPen(QPen(QColor(128, 0, 128), 2))
                painter.setBrush(QColor(230, 200, 255))

                # Použitie QRectF pre drawEllipse
                painter.drawEllipse(
                    QRectF(entanglement_x - 15, cy_i - 15, 30, 30)
                )

                # Kreslenie symbolu nekonečna
                painter.setPen(QPen(QColor(80, 0, 80), 2))
                path_size = 10

                # Ľavá slučka - Použitie QRectF pre drawEllipse
                painter.drawEllipse(
                    QRectF(entanglement_x - path_size, cy_i - path_size // 2, path_size, path_size)
                )

                # Pravá slučka - Použitie QRectF pre drawEllipse
                painter.drawEllipse(
                    QRectF(entanglement_x, cy_i - path_size // 2, path_size, path_size)
                )

        except Exception as e:
            # Spracovanie chýb pri kreslení
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawText(10, 30, f"Chyba v animácii: {str(e)}")

    def draw_bloch_sphere(self, painter, cx, cy, radius, label):
        """Kreslenie Blochovej sféry"""
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QColor(255, 255, 255, 180))

        # Použitie QRectF pre drawEllipse
        painter.drawEllipse(
            QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        )

        # Kreslenie rovníkovej roviny svetlomodrou farbou
        painter.setPen(QPen(QColor(200, 220, 255), 1))
        painter.setBrush(QColor(220, 235, 255, 80))

        # Použitie QRectF pre drawEllipse
        painter.drawEllipse(
            QRectF(cx - radius, cy - radius // 5, 2 * radius, radius // 2.5)
        )

        # Kreslenie osí x-y
        painter.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
        painter.drawLine(cx - radius, cy, cx + radius, cy)  # os x
        painter.drawLine(cx, cy - radius, cx, cy + radius)  # os y

        # Označenie stavov |0⟩ a |1⟩ tučným písmom
        painter.setPen(QPen(Qt.GlobalColor.white, 1))

        # Nastavenie tučného písma pre označenie stavov
        bold_font = QFont("Arial", 10)
        bold_font.setBold(True)
        painter.setFont(bold_font)

        # Kreslenie označení stavov tučným písmom
        painter.drawText(cx - 10, cy - radius - 15, "|0⟩")
        painter.drawText(cx - 10, cy + radius + 15, "|1⟩")

        # Návrat k normálnemu písmu pre označenie sféry
        normal_font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(normal_font)
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawText(cx - 30, cy + radius + 35, 60, 20, Qt.AlignmentFlag.AlignCenter, label)

    def draw_state_vector(self, painter, cx, cy, radius, angle, color_name):
        """Kreslenie stavového vektora"""
        # Výpočet koncového bodu
        x2 = cx + radius * math.cos(angle)
        y2 = cy - radius * math.sin(angle)
        x2_i = int(x2)
        y2_i = int(y2)

        # Úprava farby na základe parametra
        if color_name == "blue":
            # Pre Alicu: modrá šípka
            arrow_color = QColor(0, 205, 0)  # Modrá farba pre šípku Alice
            text_color = QColor(30, 100, 230)  # Zelená farba pre rovnicu Alice
        elif color_name == "orange":
            # Pre Boba: oranžová šípka
            arrow_color = QColor(255, 140, 0)  # Jasnejšia oranžová pre šípku Boba
            text_color = QColor(200, 0, 0)  # Červená farba pre rovnicu Boba
        else:
            arrow_color = QColor(color_name)
            text_color = QColor(0, 0, 0)  # Predvolená čierna farba textu

        painter.setPen(QPen(arrow_color, 3))
        painter.drawLine(int(cx), int(cy), x2_i, y2_i)

        # Hrot šípky
        head_len = 10
        angle1 = angle + math.pi * 3 / 4
        angle2 = angle - math.pi * 3 / 4
        xh1 = int(x2 + head_len * math.cos(angle1))
        yh1 = int(y2 - head_len * math.sin(angle1))
        xh2 = int(x2 + head_len * math.cos(angle2))
        yh2 = int(y2 - head_len * math.sin(angle2))
        painter.drawLine(x2_i, y2_i, xh1, yh1)
        painter.drawLine(x2_i, y2_i, xh2, yh2)

        # Kreslenie popisku uhla s inou farbou pre text
        label_radius = radius * 0.7
        label_x = cx + label_radius * math.cos(angle)
        label_y = cy - label_radius * math.sin(angle)

        # Nastavovanie farby textu podľa typu kreslenej šípky
        painter.setPen(QPen(text_color, 1))

        if color_name == "blue":
            painter.drawText(int(label_x) - 5, int(label_y) + 5, "Ω·t")
        elif color_name == "orange":
            painter.drawText(int(label_x) - 5, int(label_y) + 5, "Ω·t+δ")


class DiagramWidget(QWidget):
    """Vlastný widget pre kreslenie diagramu protokolu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
        self.setStyleSheet("background-color: #fafafa; border: 1px solid #ccc;")

        # Krok protokolu
        self.protocol_step = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            w = self.width()
            h = self.height()

            # Definovanie polí vývojového diagramu na základe obrázkov
            box_width = 200
            box_height = 60

            # Kreslenie diagramu protokolu podobného Obrázku 1 a Obrázku 3
            boxes = [
                {"x": 50, "y": 50, "text": "Príprava qubitu v\nrovnomernej\nsuperpozícii 0 a 1",
                 "active": self.protocol_step >= 0},
                {"x": 300, "y": 50, "text": "Periodická precesia\nna Blochovej sfére v\nrovine x-y",
                 "active": self.protocol_step >= 1},
                {"x": 550, "y": 50, "text": "Sledovanie počtu\nprecesných cyklov", "active": self.protocol_step >= 2},
                {"x": 550, "y": 150, "text": "Fázový rozdiel\nmedzi qubitmi", "active": self.protocol_step >= 3},
                {"x": 300, "y": 150, "text": "Zdieľanie maximálne\nprepleteného stavu",
                 "active": self.protocol_step >= 4},
                {"x": 50, "y": 150, "text": "Kompenzácia\nfázového posunu", "active": self.protocol_step >= 5},
                {"x": 50, "y": 250, "text": "Stanovenie\nglobálneho\nčasového rámca",
                 "active": self.protocol_step >= 6},
                {"x": 300, "y": 250, "text": "Synchronizované\nqubitové hodiny", "active": self.protocol_step >= 7}
            ]

            # Kreslenie spojovacích šípok
            painter.setPen(QPen(Qt.GlobalColor.black, 2))

            # Horizontálne šípky
            self.draw_arrow_line(painter, 50 + box_width, 50 + box_height // 2, 300, 50 + box_height // 2)
            self.draw_arrow_line(painter, 300 + box_width, 50 + box_height // 2, 550, 50 + box_height // 2)
            self.draw_arrow_line(painter, 550, 150 + box_height // 2, 300 + box_width, 150 + box_height // 2)
            self.draw_arrow_line(painter, 300, 150 + box_height // 2, 50 + box_width, 150 + box_height // 2)
            self.draw_arrow_line(painter, 50 + box_width, 250 + box_height // 2, 300, 250 + box_height // 2)

            # Vertikálne šípky
            self.draw_arrow_line(painter, 550 + box_width // 2, 50 + box_height, 550 + box_width // 2, 150)
            self.draw_arrow_line(painter, 50 + box_width // 2, 150 + box_height, 50 + box_width // 2, 250)

            # Kreslenie obdĺžnikov
            for box in boxes:
                if box["active"]:
                    # Aktívny obdĺžnik s gradientom
                    gradient = QLinearGradient(box["x"], box["y"], box["x"], box["y"] + box_height)
                    gradient.setColorAt(0, QColor(230, 240, 255))
                    gradient.setColorAt(1, QColor(180, 200, 255))
                    painter.setBrush(QBrush(gradient))
                    pen_color = QColor(0, 80, 180)
                else:
                    # Neaktívny obdĺžnik
                    painter.setBrush(QColor(240, 240, 240))
                    pen_color = QColor(150, 150, 150)

                painter.setPen(QPen(pen_color, 2))
                painter.drawRoundedRect(box["x"], box["y"], box_width, box_height, 10, 10)

                # Kreslenie textu
                painter.setPen(QPen(Qt.GlobalColor.black if box["active"] else QColor(100, 100, 100), 1))
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold if box["active"] else QFont.Weight.Normal))
                painter.drawText(box["x"] + 10, box["y"] + 10, box_width - 20, box_height - 20,
                                 Qt.AlignmentFlag.AlignCenter, box["text"])

            # Zvýraznenie aktuálneho kroku
            if 0 <= self.protocol_step < len(boxes):
                current_box = boxes[self.protocol_step]
                painter.setPen(QPen(QColor(255, 140, 0), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(current_box["x"] - 5, current_box["y"] - 5,
                                        box_width + 10, box_height + 10, 12, 12)

        except Exception as e:
            # Spracovanie chýb pri kreslení
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawText(10, 30, f"Chyba v diagrame: {str(e)}")

    def draw_arrow_line(self, painter, x1, y1, x2, y2):
        """Kreslenie šípky medzi bodmi"""
        try:
            # Kreslenie čiary
            painter.drawLine(x1, y1, x2, y2)

            # Kreslenie hrotu šípky
            angle = math.atan2(y2 - y1, x2 - x1)
            arrow_size = 10

            x_arrow1 = x2 - arrow_size * math.cos(angle - math.pi / 6)
            y_arrow1 = y2 - arrow_size * math.sin(angle - math.pi / 6)

            x_arrow2 = x2 - arrow_size * math.cos(angle + math.pi / 6)
            y_arrow2 = y2 - arrow_size * math.sin(angle + math.pi / 6)

            # Vytvorenie bodov QPoint priamo
            arrow_points = [
                QPoint(int(x2), int(y2)),
                QPoint(int(x_arrow1), int(y_arrow1)),
                QPoint(int(x_arrow2), int(y_arrow2))
            ]

            painter.setBrush(QColor(0, 0, 0))
            painter.drawPolygon(arrow_points)

        except Exception as e:
            print(f"Chyba pri kreslení šípky: {e}")
            # Kreslenie zjednodušenej šípky v prípade chyby
            painter.drawLine(x1, y1, x2, y2)


class QuantumTimeSync(QWidget):
    def __init__(self):
        """Inicializácia triedy pre kvantovú synchronizáciu času"""
        super().__init__()
        self.setWindowTitle("Kvantová synchronizácia času")
        self.setMinimumSize(800, 600)  # Menšia minimálna veľkosť, keďže sme odstránili diagram

        # Inicializácia parametrov pred nastavením používateľského rozhrania
        self.omega = 6.28  # uhlová frekvencia (rad/s) - približne 2π, zaokrúhlené na 2 desatinné miesta
        self.delta = 0.79  # počiatočný fázový posun pre Boba (rad) - približne π/4, zaokrúhlené na 2 desatinné miesta
        self.dt = 0.05  # časový krok na tik časovača (s)
        self.current_time = 0.0
        self.synced = False
        self.entanglement_prepared = False
        self.measurement_done = False

        # Sledovanie stavu protokolu
        self.protocol_step = 0
        self.protocol_steps = [
            "Priprava qubitu v rovnomernej superpozícii 0 a 1",
            "Periodická precesia na Blochovej sfére v rovine x-y",
            "Sledovanie počtu precesných cyklov",
            "Zdieľanie maximálne prepleteného stavu",
            "Detekcia fázového rozdielu medzi qubitmi",
            "Meranie a kompenzácia fázového posunu",
            "Stanovenie globálneho časového rámca",
            "Synchronizované qubitové hodiny"
        ]

        # Časovač pre animáciu (precesiu)
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_animation)
        self.timer.setInterval(50)  # ms

        # Kvantový obvod pre simuláciu
        self.prepare_quantum_circuits()

        self.setup_ui()

    def prepare_quantum_circuits(self):
        """Príprava kvantových obvodov pre simuláciu"""
        # Kvantový obvod pre Alicu
        self.alice_circuit = QuantumCircuit(1)
        self.alice_circuit.h(0)  # Uvedenie do superpozície

        # Kvantový obvod pre Boba
        self.bob_circuit = QuantumCircuit(1)
        self.bob_circuit.h(0)  # Uvedenie do superpozície
        self.bob_circuit.p(self.delta, 0)  # Pridanie fázového posunu

        # Obvod pre previazaný stav
        self.entangled_circuit = QuantumCircuit(2)
        self.entangled_circuit.h(0)
        self.entangled_circuit.cx(0, 1)  # Vytvorenie Bellovho stavu

    def setup_ui(self):
        """Nastavenie používateľského rozhrania"""
        main_layout = QVBoxLayout(self)

        # Pridanie hlavného nadpisu hore
        title_label = QLabel("Kvantová synchronizácia času")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Ovládací panel
        control_box = QGroupBox("Ovládanie protokolu")
        control_layout = QHBoxLayout(control_box)

        control_layout.addWidget(QLabel("Frekvencia Ω [rad/s]:"))
        self.freq_input = QLineEdit(f"{self.omega:.2f}")  # Formátovanie na 2 desatinné miesta
        control_layout.addWidget(self.freq_input)

        control_layout.addWidget(QLabel("Offset δ [rad]:"))
        self.delta_input = QLineEdit(f"{self.delta:.2f}")  # Formátovanie na 2 desatinné miesta
        control_layout.addWidget(self.delta_input)

        self.start_button = QPushButton("Začať protokol")
        self.start_button.clicked.connect(self.start_protocol)
        control_layout.addWidget(self.start_button)

        self.next_step_button = QPushButton("Ďalší krok")
        self.next_step_button.clicked.connect(self.next_protocol_step)
        self.next_step_button.setEnabled(False)
        control_layout.addWidget(self.next_step_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_protocol)
        control_layout.addWidget(self.reset_button)

        main_layout.addWidget(control_box)

        # Oblasť animácie pre Blochove sféry (použitie vlastného widgetu)
        self.animation_area = BlochSphereWidget()
        main_layout.addWidget(self.animation_area)

        # Stavová / logovacia oblasť
        log_box = QGroupBox("Protokolový log")
        # Nastavenie pevnej výšky pre logové pole na zníženie jeho veľkosti
        log_box.setFixedHeight(150)  # Znížená výška (upravte podľa potreby)

        log_layout = QVBoxLayout(log_box)
        # Zmenšenie okrajov pre maximalizáciu priestoru pre text
        log_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Nastavte parametre a spustite protokol.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        log_layout.addWidget(self.status_label)

        main_layout.addWidget(log_box)

        # Zabezpečenie kompatibility s existujúcim kódom pre volanie metód na log_area
        self.log_area = self.status_label

    def start_protocol(self):
        """Spustenie protokolu s aktuálnymi parametrami"""
        try:
            # Zaokrúhlenie na 2 desatinné miesta pre omega aj delta
            self.omega = round(float(self.freq_input.text()), 2)
            self.delta = round(float(self.delta_input.text()), 2)

            # Aktualizácia vstupných polí na zobrazenie zaokrúhlených hodnôt
            self.freq_input.setText(f"{self.omega:.2f}")
            self.delta_input.setText(f"{self.delta:.2f}")

            self.current_time = 0.0
            self.synced = False
            self.entanglement_prepared = False
            self.measurement_done = False
            self.protocol_step = 0

            # Aktualizácia kvantových obvodov s novými parametrami
            self.prepare_quantum_circuits()

            # Aktualizácia vlastných widgetov s novými hodnotami
            self.animation_area.omega = self.omega
            self.animation_area.delta = self.delta
            self.animation_area.current_time = self.current_time
            self.animation_area.synced = self.synced
            self.animation_area.entanglement_prepared = self.entanglement_prepared
            self.animation_area.protocol_step = self.protocol_step

            self.next_step_button.setEnabled(True)
            self.start_button.setEnabled(False)

            # Aktualizácia logovej oblasti s informáciami o spustení protokolu
            self.log_area.setText(f"Protokol spustený: Ω={self.omega:.2f} rad/s, δ={self.delta:.2f} rad")
            self.status_label.setText(f"Krok 1: {self.protocol_steps[0]}")

            self.animation_area.update()

        except ValueError:
            self.status_label.setText("Neplatné parametre. Zadajte čísla.")

    def next_protocol_step(self):
        """Prechod na ďalší krok protokolu"""
        self.protocol_step += 1

        if self.protocol_step >= len(self.protocol_steps):
            self.protocol_step = len(self.protocol_steps) - 1
            return

        step_text = self.protocol_steps[self.protocol_step]
        self.log_area.setText(f"Krok {self.protocol_step + 1}: {step_text}")
        self.status_label.setText(f"Krok {self.protocol_step + 1}: {step_text}")

        # Aktualizácia kroku protokolu vo vizualizačnom widgete
        self.animation_area.protocol_step = self.protocol_step

        # Spracovanie konkrétnych krokov protokolu
        if self.protocol_step == 1:  # Spustenie precesie
            self.timer.start()

        elif self.protocol_step == 3:  # Príprava previazania
            self.entanglement_prepared = True
            self.animation_area.entanglement_prepared = True

            # Vytvorenie Bellovho stavu pomocou Qiskit pre simuláciu
            self.entangled_circuit = QuantumCircuit(2)
            self.entangled_circuit.h(0)
            self.entangled_circuit.cx(0, 1)

            self.log_area.setText("Krok 4: Vytvorený maximálne prepletený stav (Bell state)")

        elif self.protocol_step == 4:  # Detekcia fázového rozdielu
            # Použitie Qiskit na výpočet fázového rozdielu na základe kvantového stavu
            alice_statevector, bob_statevector = self.simulate_quantum_state()

            if alice_statevector is not None and bob_statevector is not None:
                # Výpočet fázy zo stavového vektora
                # Extrahovanie informácií o fáze zo vzťahu medzi koeficientami u qubitu v superpozícii
                phase_diff = self.delta  # Predvolene použiť klasický výpočet
                try:
                    # V reálnej implementácii by ste extrahovali fázu zo stavových vektorov
                    # Toto je zjednodušený prístup
                    phase_diff = ((self.omega * self.current_time + self.delta) - (self.omega * self.current_time)) % (
                            2 * math.pi)
                except Exception as e:
                    print(f"Chyba pri extrakcii fázy: {e}")

                phase_diff = round(phase_diff, 2)  # Zaokrúhlenie na 2 desatinné miesta
                self.log_area.setText(f"Krok 5: K úspešnej synchoronizáci času je nutné aby:\n"
                                      f"• Alice a Bob zmerali svoje qubity v Pauliho bázach\n"
                                      f"• Vykonanie série meraní na získanie spojitej hodnoty fázového posunu δ\n"
                                      f"• Alice a Bob zdieľali svoje výsledky\n"
                                      f"• Z korelácií výsledkov počíta presná hodnota fázový posun δ\n"
                                      f"• Bob vypočíta časový rozdiel Δt = δ/Ω a upraví svoje hodiny\n")
            else:
                # Návrat ku klasickému výpočtu, ak kvantová simulácia zlyhá
                phase_diff = ((self.omega * self.current_time + self.delta) - (self.omega * self.current_time)) % (
                        2 * math.pi)
                phase_diff = round(phase_diff, 2)
                self.log_area.setText(f"Krok 5: K úspešnej synchoronizáci času je nutné aby:\n"
                                      f"• Alice a Bob zmerali svoje qubity v Pauliho bázach\n"
                                      f"• Vykonanie série meraní na získanie spojitej hodnoty fázového posunu δ\n"
                                      f"• Alice a Bob zdieľali svoje výsledky\n"
                                      f"• Z korelácií výsledkov počíta presná hodnota fázový posun δ\n"
                                      f"• Bob vypočíta časový rozdiel Δt = δ/Ω a upraví svoje hodiny\n")


        elif self.protocol_step == 5:  # Meranie a úprava fázy
            self.timer.stop()

            try:
                simulator = Aer.get_backend('qasm_simulator')
                # Vytvorenie obvodu pre meranie fázového rozdielu
                meas_circuit = self.entangled_circuit.copy()
                # Aplikácia fázovej korekcie na základe nameraného rozdielu
                meas_circuit.p(-self.delta, 1)  # Aplikácia inverznej fázy na korekciu
                meas_circuit.measure_all()

                # Vykonanie a získanie výsledku
                job = execute(meas_circuit, simulator, shots=1)
                result = job.result()

                measured_diff = self.delta % (2 * math.pi)
                measured_diff = round(measured_diff, 2)  # Zaokrúhlenie na 2 desatinné miesta
                measured_offset = measured_diff / self.omega if self.omega != 0 else 0
                measured_offset = round(measured_offset, 2)  # Zaokrúhlenie na 2 desatinné miesta

                self.log_area.setText(
                    f"Krok 6: Zmeraný fázový rozdiel: {measured_diff:.2f} rad => časový posun {measured_offset:.2f} s")
                self.delta = 0  # Vynulovanie delta (synchronizácia)
                self.animation_area.delta = 0
                self.measurement_done = True
            except Exception as e:
                print(f"Chyba pri kvantovom meraní: {e}")
                # Návrat ku klasickému výpočtu
                measured_diff = self.delta % (2 * math.pi)
                measured_diff = round(measured_diff, 2)
                measured_offset = measured_diff / self.omega if self.omega != 0 else 0
                measured_offset = round(measured_offset, 2)
                self.log_area.setText(
                    f"Zmeraný fázový rozdiel: {measured_diff:.2f} rad => časový posun {measured_offset:.2f} s")
                self.delta = 0
                self.animation_area.delta = 0
                self.measurement_done = True

        elif self.protocol_step == 7:  # Dokončenie synchronizácie
            self.synced = True
            self.animation_area.synced = True
            self.log_area.setText("Synchronizácia hodín dokončená.")
            self.next_step_button.setEnabled(False)
            self.start_button.setEnabled(True)

        self.animation_area.update()

    def reset_protocol(self):
        """Resetovanie protokolu do počiatočného stavu"""
        if self.timer.isActive():
            self.timer.stop()
        self.current_time = 0.0
        self.protocol_step = 0
        self.synced = False
        self.entanglement_prepared = False
        self.measurement_done = False

        # Aktualizácia vizualizačného widgetu
        self.animation_area.current_time = self.current_time
        self.animation_area.protocol_step = self.protocol_step
        self.animation_area.synced = self.synced
        self.animation_area.entanglement_prepared = self.entanglement_prepared

        self.log_area.setText("")  # Vyčistenie textu
        self.status_label.setText("Resetované. Nastavte parametre a spustite protokol.")
        self.next_step_button.setEnabled(False)
        self.start_button.setEnabled(True)

        self.animation_area.update()

    def advance_animation(self):
        """Posun animácie v čase"""
        self.current_time += self.dt
        self.animation_area.current_time = self.current_time
        self.animation_area.update()

    def simulate_quantum_state(self):
        """Simulácia kvantového stavu pre vizualizáciu"""
        try:
            # Pre Alicu
            simulator = Aer.get_backend('statevector_simulator')
            alice_rotated = self.alice_circuit.copy()
            alice_rotated.p(self.omega * self.current_time, 0)
            alice_job = execute(alice_rotated, simulator)
            alice_result = alice_job.result()
            alice_statevector = alice_result.get_statevector()

            # Pre Boba
            bob_rotated = self.bob_circuit.copy()
            bob_rotated.p(self.omega * self.current_time, 0)
            bob_job = execute(bob_rotated, simulator)
            bob_result = bob_job.result()
            bob_statevector = bob_result.get_statevector()

            return alice_statevector, bob_statevector

        except Exception as e:
            print(f"Chyba v kvantovej simulácii: {e}")
            return None, None