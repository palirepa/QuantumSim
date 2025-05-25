from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QSpinBox, QTableWidget,
                             QTableWidgetItem, QGroupBox, QGraphicsView,
                             QGraphicsScene, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPainterPath

import random
import math


class QuantumByzantineAgreement(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_animation_step)
        self.animation_speed = 500  # ms medzi krokmi animácie

        # Stav protokolu
        self.sender_value = None  # Bit vysielaný odosielateľom
        self.receiver_values = [None, None]  # Hodnoty v R0 a R1
        self.quantum_states = {}  # Kvantové stavy na každom uzle
        self.byzantine_player = None  # Ktorý hráč je byzantský (ak niekto)
        self.entanglement_links = []  # Sleduje previazanie qutritov medzi uzlami
        self.messages = []  # Správy posielané v aktuálnom kroku animácie
        self.phase = "init"  # Aktuálna fáza protokolu
        self.protocol_complete = False

        # Množiny indexov pre merania v Z-báze
        self.index_sets = {}

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Pridanie hlavného nadpisu na vrch aplikácie
        title_label = QLabel("Kvantová byzantská dohoda")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
               font-size: 20px;
               font-weight: bold;
               color: white;
               margin: 4px;
           """)
        main_layout.addWidget(title_label)

        controls_group = QGroupBox("Ovládacie prvky protokolu")
        controls_layout = QHBoxLayout()

        self.init_button = QPushButton("Inicializovať protokol")
        self.init_button.clicked.connect(self.initialize_protocol)
        controls_layout.addWidget(self.init_button)

        self.step_button = QPushButton("Ďalší krok")
        self.step_button.clicked.connect(self.step_animation)
        self.step_button.setEnabled(False)
        controls_layout.addWidget(self.step_button)

        self.play_button = QPushButton("Spustiť animáciu")
        self.play_button.clicked.connect(self.play_animation)
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_protocol)
        controls_layout.addWidget(self.reset_button)

        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        config_group = QGroupBox("Konfigurácia")
        config_layout = QHBoxLayout()

        bit_layout = QVBoxLayout()
        bit_layout.addWidget(QLabel("Bit odosielateľa:"))
        self.bit_combo = QComboBox()
        self.bit_combo.addItems(["0", "1"])
        bit_layout.addWidget(self.bit_combo)
        config_layout.addLayout(bit_layout)

        byz_layout = QVBoxLayout()
        byz_layout.addWidget(QLabel("Byzantský účastník:"))
        self.byz_combo = QComboBox()
        self.byz_combo.addItems(["Žiadny", "Odosielateľ (S)", "Prijímateľ (R0)", "Prijímateľ (R1)"])
        byz_layout.addWidget(self.byz_combo)
        config_layout.addLayout(byz_layout)

        byz_behavior_layout = QVBoxLayout()
        byz_behavior_layout.addWidget(QLabel("Byzantské správanie:"))
        self.byzantine_behavior_combo = QComboBox()
        self.byzantine_behavior_combo.addItems([
            "Odoslanie rozdielnych hodnôt",
            "Falošné indexy",
            "Odmietnutie dohody"
        ])
        byz_behavior_layout.addWidget(self.byzantine_behavior_combo)
        config_layout.addLayout(byz_behavior_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Horizontálny layout pre vizualizáciu a stav
        viz_status_layout = QHBoxLayout()

        viz_group = QGroupBox("Vizualizácia protokolu")
        viz_layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(300)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        viz_layout.addWidget(self.view)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setPlaceholderText("Stav protokolu sa zobrazí tu...")
        viz_layout.addWidget(self.info_text)

        viz_group.setLayout(viz_layout)
        viz_status_layout.addWidget(viz_group)

        status_group = QGroupBox("Stav protokolu")
        status_layout = QVBoxLayout()

        phase_layout = QHBoxLayout()
        phase_layout.addWidget(QLabel("Aktuálna fáza:"))
        self.phase_label = QLabel("Nespustený")
        phase_layout.addWidget(self.phase_label)
        phase_layout.addStretch()

        phase_layout.addWidget(QLabel("Krok:"))
        self.step_label = QLabel("0")
        phase_layout.addWidget(self.step_label)
        phase_layout.addStretch()

        phase_layout.addWidget(QLabel("Konsenzus:"))
        self.consensus_label = QLabel("Nedosiahnutý")
        self.consensus_label.setStyleSheet("font-weight: bold;")
        phase_layout.addWidget(self.consensus_label)

        status_layout.addLayout(phase_layout)

        self.state_table = QTableWidget(3, 3)
        self.state_table.setHorizontalHeaderLabels(["Uzol", "Hodnota", "Kvantový stav"])
        self.state_table.horizontalHeader().setStretchLastSection(True)

        # Nastavenie tabuľky stavov uzlov
        self.state_table.setStyleSheet("""
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
            }
        """)

        self.state_table.setItem(0, 0, QTableWidgetItem("Odosielateľ (S)"))
        self.state_table.setItem(1, 0, QTableWidgetItem("Prijímateľ (R0)"))
        self.state_table.setItem(2, 0, QTableWidgetItem("Prijímateľ (R1)"))

        # Nastavenie bielej farby pre inicializačné položky
        for row in range(3):
            item = self.state_table.item(row, 0)
            if item:
                item.setForeground(QBrush(QColor("white")))

        status_layout.addWidget(self.state_table)

        status_group.setLayout(status_layout)
        viz_status_layout.addWidget(status_group)

        main_layout.addLayout(viz_status_layout)

        self.setLayout(main_layout)

        self.draw_network()
        self.update_info_text("Protokol nespustený. Stlačte 'Inicializovať protokol' pre začatie. Cieľom je dosiahnutie dohody aj v prítomnosti zradcov.")

        self.initialize_index_sets()

        # Jednorázový časovač na korekciu zobrazenia po spustení
        QTimer.singleShot(100, self.fix_initial_view)

    def fix_initial_view(self):
        """Zabezpečí správne počiatočné nastavenie zobrazenia scény."""
        if hasattr(self, 'scene') and self.scene.sceneRect().isValid():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def initialize_index_sets(self):
        """Inicializuje množiny indexov pre Z-bázu."""
        self.index_sets = {
            "J0": [("S", 0), ("R0", 1), ("R1", 2),  # Trieda I
                   ("S", 0), ("R0", 2), ("R1", 1)],  # Trieda II
            "J1": [("S", 1), ("R0", 2), ("R1", 0),  # Trieda III
                   ("S", 1), ("R0", 0), ("R1", 2)]  # Trieda IV
        }

        # Triedy V a VI sa používajú na detekciu byzantského účastníka
        self.index_sets["V"] = [("S", 2), ("R0", 1), ("R1", 0)]
        self.index_sets["VI"] = [("S", 2), ("R0", 0), ("R1", 1)]

    def initialize_protocol(self):
        self.sender_value = int(self.bit_combo.currentText())

        byzantine_selection = self.byz_combo.currentText()
        if byzantine_selection == "Žiadny":
            self.byzantine_player = None
        elif byzantine_selection == "Odosielateľ (S)":
            self.byzantine_player = "S"
        elif byzantine_selection == "Prijímateľ (R0)":
            self.byzantine_player = "R0"
        elif byzantine_selection == "Prijímateľ (R1)":
            self.byzantine_player = "R1"

        self.current_step = 0
        self.phase = "preparation"
        self.protocol_complete = False

        self.receiver_values = [None, None]

        # Inicializácia kvantových stavov (Aharonov stav)
        self.quantum_states = {
            "S": "Aharonov",
            "R0": "Aharonov",
            "R1": "Aharonov"
        }

        # Vytvorenie previazaní medzi všetkými troma uzlami
        self.entanglement_links = [
            ("S", "R0"), ("S", "R1"), ("R0", "R1")
        ]

        self.update_phase_display()
        self.update_node_table()
        self.draw_network()
        self.update_info_text("Protokol inicializovaný. Začína fáza prípravy a distribúcie kvantového previazania.")

        self.step_button.setEnabled(True)
        self.play_button.setEnabled(True)
        self.init_button.setEnabled(False)

    def reset_protocol(self):
        self.current_step = 0
        self.sender_value = None
        self.receiver_values = [None, None]
        self.quantum_states = {}
        self.byzantine_player = None
        self.entanglement_links = []
        self.messages = []
        self.phase = "init"
        self.protocol_complete = False

        self.update_phase_display()
        self.update_node_table()
        self.draw_network()
        self.update_info_text("Protokol resetovaný. Stlačte 'Inicializovať protokol' pre začatie. Cieľom je dosiahnutie dohody aj v prítomnosti zradcov.")

        self.consensus_label.setText("Nedosiahnutý")
        self.consensus_label.setStyleSheet("font-weight: bold;")

        self.step_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.init_button.setEnabled(True)
        self.animation_timer.stop()
        self.play_button.setText("Spustiť animáciu")

    def play_animation(self):
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_button.setText("Spustiť animáciu")
            self.step_button.setEnabled(True)
        else:
            self.animation_timer.start(self.animation_speed)
            self.play_button.setText("Pozastaviť animáciu")
            self.step_button.setEnabled(False)

    def step_animation(self):
        if self.protocol_complete:
            self.update_info_text("Protokol je dokončený. Resetujte ho pre nové spustenie.")
            return

        self.current_step += 1
        self.messages = []

        # Spracovanie fáz protokolu
        if self.phase == "preparation":
            self.handle_preparation_phase()
        elif self.phase == "transmission":
            self.handle_transmission_phase()
        elif self.phase == "verification":
            self.handle_verification_phase()
        elif self.phase == "detection":
            self.handle_detection_phase()
        elif self.phase == "agreement":
            self.handle_agreement_phase()

        self.update_phase_display()
        self.update_node_table()
        self.draw_network()

    def next_animation_step(self):
        self.step_animation()

        if self.protocol_complete:
            self.animation_timer.stop()
            self.play_button.setText("Spustiť animáciu")
            self.play_button.setEnabled(False)
            self.step_button.setEnabled(False)

    def handle_preparation_phase(self):
        """Spracovanie fázy prípravy a distribúcie"""
        if self.current_step == 1:
            # Náhodne vyberieme uzol, ktorý pripraví qutrity
            preparer = random.choice(["S", "R0", "R1"])
            recipients = [node for node in ["S", "R0", "R1"] if node != preparer]

            # Vytvorenie správ o distribúcii qutritov
            self.messages = [
                {"from": preparer, "to": recipients[0], "type": "quantum", "label": "qutrit"},
                {"from": preparer, "to": recipients[1], "type": "quantum", "label": "qutrit"}
            ]

            aharonov_state = "|A⟩ = (|0,1,2⟩ + |1,2,0⟩ + |2,0,1⟩ - |0,2,1⟩ - |1,0,2⟩ - |2,1,0⟩) · 1/√6"
            self.update_info_text(f"Fáza 1: Príprava a distribúcia qutritov v Aharonovom stave:\n{aharonov_state}\n"
                                  f"Uzol {preparer} pripravuje qutrity a distribuuje ich ostatným uzlom.")

        elif self.current_step == 2:
            self.phase = "transmission"
            self.current_step = 0
            self.update_info_text("Príprava a distribúcia qutritov dokončená. Prechádzame do fázy prenosu.")

    def handle_transmission_phase(self):
        """Spracovanie fázy prenosu"""
        if self.current_step == 1:
            # Prijímatelia získavajú hodnoty od odosielateľa
            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # Byzantský odosielateľ posiela rozdielne bity
                # Náhodne vyberieme, ktorý prijímateľ dostane konzistentné údaje
                consistent_receiver = random.choice([0, 1])

                if consistent_receiver == 0:
                    # R0 dostáva bit zodpovedajúci indexom, R1 dostáva opačný bit
                    self.receiver_values[0] = self.sender_value
                    self.receiver_values[1] = 1 - self.sender_value
                else:
                    # R1 dostáva bit zodpovedajúci indexom, R0 dostáva opačný bit
                    self.receiver_values[0] = 1 - self.sender_value
                    self.receiver_values[1] = self.sender_value

                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
                ]

                self.update_info_text(f"Fáza 2: Byzantský odosielateľ posiela rozdielne bity prijímateľom. "
                                      f"R0 dostáva {self.receiver_values[0]}, R1 dostáva {self.receiver_values[1]}.")
            else:
                # Poctivý odosielateľ posiela rovnaký bit obom prijímateľom
                self.receiver_values[0] = self.sender_value
                self.receiver_values[1] = self.sender_value

                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
                ]

                self.update_info_text(f"Fáza 2: Odosielateľ posiela bit {self.sender_value} obom prijímateľom.")

        elif self.current_step == 2:
            # Odosielateľ meria qutrity v Z-báze
            self.quantum_states["S"] = f"Zmeraný: {self.sender_value}"

            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # Byzantský odosielateľ posiela falošné indexy
                wrong_bit = 1 - self.sender_value

                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"indexy J{wrong_bit}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"indexy J{wrong_bit}"}
                ]
                self.update_info_text("Fáza 2: Byzantský odosielateľ meria svoje qutrity v Z-báze, "
                                      f"ale posiela falošné indexy z množiny J{wrong_bit} namiesto J{self.sender_value}.")
            else:
                # Odosielateľ posiela správne indexy zodpovedajúce jeho bitu
                # Aj byzantský odosielateľ pri "Odoslanie rozdielnych hodnôt" posiela správne indexy
                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"indexy J{self.sender_value}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"indexy J{self.sender_value}"}
                ]

                if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                    self.update_info_text("Fáza 2: Byzantský odosielateľ meria svoje qutrity v Z-báze a posiela "
                                          f"obom prijímateľom rovnaké indexy J{self.sender_value} zodpovedajúce jeho bitu.")
                else:
                    self.update_info_text("Fáza 2: Odosielateľ meria svoje qutrity v Z-báze a posiela "
                                          f"prijímateľom indexy qutritov z množiny J{self.sender_value} zodpovedajúce jeho bitu.")

            self.phase = "verification"
            self.current_step = 0

    def handle_verification_phase(self):
        """Spracovanie fázy overenia"""
        if self.current_step == 1:
            # Prijímatelia merajú svoje qutrity a kontrolujú konzistenciu s indexami

            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # Odosielateľ poslal falošné indexy - obaja prijímatelia zistia nekonzistenciu
                self.quantum_states["R0"] = f"Nekonzistentné s J{1 - self.sender_value}"
                self.quantum_states["R1"] = f"Nekonzistentné s J{1 - self.sender_value}"
                self.update_info_text("Fáza 3: Prijímatelia merajú svoje qutrity v Z-báze a zisťujú "
                                      f"nekonzistenciu s indexami J{1 - self.sender_value} od odosielateľa. "
                                      "Výsledky meraní nezodpovedajú Aharonovmu stavu.")

            elif self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # Byzantský odosielateľ poslal správne indexy, ale rozdielne hodnoty
                # Jeden prijímateľ má konzistentné merania, druhý nie
                consistent_receiver_idx = 0 if self.receiver_values[0] == self.sender_value else 1

                if consistent_receiver_idx == 0:
                    self.quantum_states["R0"] = f"Zmeraný: {self.receiver_values[0]}"
                    self.quantum_states["R1"] = f"Nekonzistentné s J{self.sender_value}"
                    self.update_info_text(
                        "Fáza 3: Prijímateľ R0 meria svoje qutrity v Z-báze a potvrdzuje konzistenciu "
                        f"s indexami J{self.sender_value}. Prijímateľ R1 zisťuje nekonzistenciu "
                        f"medzi svojím bitom {self.receiver_values[1]} a indexami J{self.sender_value}.")
                else:
                    self.quantum_states["R0"] = f"Nekonzistentné s J{self.sender_value}"
                    self.quantum_states["R1"] = f"Zmeraný: {self.receiver_values[1]}"
                    self.update_info_text(
                        "Fáza 3: Prijímateľ R1 meria svoje qutrity v Z-báze a potvrdzuje konzistenciu "
                        f"s indexami J{self.sender_value}. Prijímateľ R0 zisťuje nekonzistenciu "
                        f"medzi svojím bitom {self.receiver_values[0]} a indexami J{self.sender_value}.")

            elif self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # R0 predstiera falošné výsledky meraní
                self.quantum_states["R0"] = f"Falošné meranie pre bit {1 - self.receiver_values[0]}"
                self.quantum_states["R1"] = f"Zmeraný: {self.receiver_values[1]}"
                self.update_info_text("Fáza 3: Byzantský prijímateľ R0 falošne hlási merania, "
                                      f"ktoré nezodpovedajú indexom J{self.sender_value} od odosielateľa.")

            elif self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # R1 predstiera falošné výsledky meraní
                self.quantum_states["R0"] = f"Zmeraný: {self.receiver_values[0]}"
                self.quantum_states["R1"] = f"Falošné meranie pre bit {1 - self.receiver_values[1]}"
                self.update_info_text("Fáza 3: Byzantský prijímateľ R1 falošne hlási merania, "
                                      f"ktoré nezodpovedajú indexom J{self.sender_value} od odosielateľa.")

            else:
                # Normálne meranie - konzistentné s Aharonovym stavom
                self.quantum_states["R0"] = f"Zmeraný: {self.receiver_values[0]}"
                self.quantum_states["R1"] = f"Zmeraný: {self.receiver_values[1]}"
                self.update_info_text("Fáza 3: Prijímatelia merajú svoje qutrity v Z-báze "
                                      f"a potvrdzujú konzistenciu s indexami J{self.sender_value} od odosielateľa.")

        elif self.current_step == 2:
            # Výmena informácií o prijatých bitoch
            if self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # Byzantský R0 posiela R1 opačnú hodnotu než prijal
                self.messages = [
                    {"from": "R0", "to": "R1", "type": "classical", "label": f"bit={1 - self.receiver_values[0]}"},
                    {"from": "R1", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
                ]
                self.update_info_text("Fáza 3: Byzantský prijímateľ R0 posiela opačnú hodnotu než prijal. "
                                      f"R0 tvrdí, že dostal bit {1 - self.receiver_values[0]} namiesto {self.receiver_values[0]}.")
            elif self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # Byzantský R1 posiela R0 opačnú hodnotu než prijal
                self.messages = [
                    {"from": "R0", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                    {"from": "R1", "to": "R0", "type": "classical", "label": f"bit={1 - self.receiver_values[1]}"}
                ]
                self.update_info_text("Fáza 3: Byzantský prijímateľ R1 posiela opačnú hodnotu než prijal. "
                                      f"R1 tvrdí, že dostal bit {1 - self.receiver_values[1]} namiesto {self.receiver_values[1]}.")
            else:
                # Normálna výmena
                self.messages = [
                    {"from": "R0", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                    {"from": "R1", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
                ]
                self.update_info_text("Fáza 3: Prijímatelia si vymieňajú informácie o prijatých bitoch.")

            self.phase = "detection"
            self.current_step = 0

    def handle_detection_phase(self):
        """Spracovanie fázy detekcie zradcu"""
        if self.current_step == 1:
            # Detekcia byzantského odosielateľa
            if self.byzantine_player == "S":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                    # Ak majú prijímatelia rozdielne hodnoty, jeden z nich zistil aj nekonzistenciu
                    # s indexami - to indikuje byzantského odosielateľa
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "nekonzistentné"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Prijímatelia zistili rozdielne bity. "
                                          "Jeden z nich zistil nekonzistenciu medzi prijatým bitom a indexami. "
                                          "Vlastnosti Aharonovho stavu naznačujú, že odosielateľ je byzantský.")

                elif self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    # Obaja prijímatelia zistili nekonzistenciu s indexami
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "falošné indexy"},
                        {"from": "R1", "to": "R0", "type": "classical", "label": "falošné indexy"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Prijímatelia zistili nekonzistenciu "
                                          "v indexoch qutritov, čo odhalilo byzantského odosielateľa.")

                else:  # "Odmietnutie dohody"
                    self.update_info_text("Fáza 4: Prijímatelia kontrolujú konzistenciu. "
                                          "Zatiaľ nezistili žiadnu nekonzistenciu.")

            # Detekcia byzantského prijímateľa (R0 alebo R1) pri režime "Odoslanie rozdielnych hodnôt"
            elif self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # R0 je byzantský, R1 a S môžu porovnať hodnoty a detekovať ho
                self.messages = [
                    {"from": "R1", "to": "S", "type": "classical", "label": "rozdielne hodnoty"},
                    {"from": "S", "to": "R1", "type": "classical", "label": "R0 je byzantský"}
                ]
                self.update_info_text("Fáza 4: Detekcia zradcu - Prijímateľ R1 a odosielateľ S zistili, "
                                      "že hodnota hlásená prijímateľom R0 je rozdielna od hodnoty, ktorú "
                                      "poslal odosielateľ. Odhalili, že R0 je byzantský.")

            elif self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # R1 je byzantský, R0 a S môžu porovnať hodnoty a detekovať ho
                self.messages = [
                    {"from": "R0", "to": "S", "type": "classical", "label": "rozdielne hodnoty"},
                    {"from": "S", "to": "R0", "type": "classical", "label": "R1 je byzantský"}
                ]
                self.update_info_text("Fáza 4: Detekcia zradcu - Prijímateľ R0 a odosielateľ S zistili, "
                                      "že hodnota hlásená prijímateľom R1 je rozdielna od hodnoty, ktorú "
                                      "poslal odosielateľ. Odhalili, že R1 je byzantský.")

            # Detekcia byzantského prijímateľa pri falošných indexoch
            elif self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                self.messages = [
                    {"from": "R0", "to": "R1", "type": "classical", "label": "falošná nekonzistencia"}
                ]
                self.update_info_text("Fáza 4: Detekcia zradcu - Byzantský prijímateľ R0 sa pokúša "
                                      "podviesť, ale Aharonov stav odhalí jeho nečestné správanie.")

            elif self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                self.messages = [
                    {"from": "R1", "to": "R0", "type": "classical", "label": "falošná nekonzistencia"}
                ]
                self.update_info_text("Fáza 4: Detekcia zradcu - Byzantský prijímateľ R1 sa pokúša "
                                      "podviesť, ale Aharonov stav odhalí jeho nečestné správanie.")

            # Žiadny byzantský účastník alebo byzantský účastník zatiaľ neodhalený
            else:
                self.update_info_text("Fáza 4: Žiadny zradca nebol detekovaný, všetky hodnoty sú konzistentné.")

        elif self.current_step == 2:
            self.phase = "agreement"
            self.current_step = 0
            self.update_info_text("Prechádzame do fázy dosiahnutia dohody.")


    def handle_agreement_phase(self):
        """Spracovanie fázy dosiahnutia dohody"""
        if self.current_step == 1:
            # Byzantský odosielateľ s rozdielnymi bitmi
            if self.byzantine_player == "S":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":

                    # Určenie, ktorý prijímateľ má konzistentné merania
                    consistent_receiver_idx = 0 if self.receiver_values[0] == self.sender_value else 1
                    inconsistent_receiver_idx = 1 - consistent_receiver_idx

                    # Prijímatelia sa dohodnú na hodnote prijímateľa s konzistentnými meraniami
                    agreed_value = self.receiver_values[consistent_receiver_idx]
                    # Obaja prijímatelia nastavia svoju hodnotu na hodnotu dohody
                    self.receiver_values[0] = agreed_value
                    self.receiver_values[1] = agreed_value

                    self.messages = [
                        {"from": f"R{consistent_receiver_idx}", "to": f"R{inconsistent_receiver_idx}",
                         "type": "classical", "label": f"dohoda={agreed_value}"}
                    ]

                    self.update_info_text(f"Fáza 5: Prijímatelia detekovali byzantského odosielateľa. "
                                          f"R{consistent_receiver_idx} má konzistentné merania s hodnotou "
                                          f"{agreed_value}, zatiaľ čo R{inconsistent_receiver_idx} zistil "
                                          f"nekonzistenciu. Vďaka vlastnostiam Aharonovho stavu sa obaja "
                                          f"dohodli na hodnote {agreed_value}.")

                    # Nastavenie, že konsenzus bol dosiahnutý
                    self.consensus_label.setText(f"Dosiahnutý: {agreed_value}")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: green;")

                elif self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    # Obaja prijímatelia zistili nekonzistenciu s falošnými indexami
                    # Nemôžu dôverovať odosielateľovi, ale môžu sa pokúsiť o konsenzus medzi sebou

                    if self.receiver_values[0] == self.receiver_values[1]:
                        # Ak majú prijímatelia rovnaké hodnoty, môžu sa dohodnúť
                        agreed_value = self.receiver_values[0]
                        self.update_info_text(
                            f"Fáza 5: Prijímatelia detekovali falošné indexy od byzantského odosielateľa. "
                            f"Keďže majú rovnaké hodnoty ({agreed_value}), dohodli sa na tejto hodnote.")
                        self.consensus_label.setText(f"Dosiahnutý: {agreed_value}")
                        self.consensus_label.setStyleSheet("font-weight: bold; color: green;")
                    else:
                        # Inak nedôjde k dohode
                        self.update_info_text("Fáza 5: Prijímatelia detekovali falošné indexy od byzantského odosielateľa. "
                                              "Keďže majú rozdielne hodnoty, nedokážu dosiahnuť konsenzus.")
                        self.consensus_label.setText("Nedosiahnutý")
                        self.consensus_label.setStyleSheet("font-weight: bold; color: red;")

                elif self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # Odosielateľ odmietne dohodu
                    self.messages = [
                        {"from": "S", "to": "R0", "type": "classical", "label": "odmietam"},
                        {"from": "S", "to": "R1", "type": "classical", "label": "odmietam"}
                    ]

                    # Prijímatelia si vymenia hodnoty, ktoré dostali od odosielateľa
                    # Ak sú zhodné, majú konsenzus aj bez odosielateľa
                    if self.receiver_values[0] == self.receiver_values[1]:
                        agreed_value = self.receiver_values[0]
                        self.update_info_text(f"Fáza 5: Byzantský odosielateľ odmieta dohodu, ale prijímatelia "
                                              f"si vymenia informácie a zistia, že dostali rovnaké hodnoty {agreed_value}. "
                                              f"Dosiahli konsenzus bez odosielateľa.")
                        self.consensus_label.setText(f"Dosiahnutý: {agreed_value}")
                        self.consensus_label.setStyleSheet("font-weight: bold; color: green;")
                    else:
                        # Prijímatelia dostali rozdielne hodnoty, nemôžu dosiahnuť konsenzus
                        self.update_info_text(f"Fáza 5: Byzantský odosielateľ odmieta dohodu. "
                                              f"Prijímatelia zistili, že dostali rozdielne hodnoty "
                                              f"({self.receiver_values[0]} a {self.receiver_values[1]}). "
                                              f"Nedokážu dosiahnuť konsenzus.")
                        self.consensus_label.setText("Nedosiahnutý")
                        self.consensus_label.setStyleSheet("font-weight: bold; color: red;")

            # Byzantský prijímateľ R0
            elif self.byzantine_player == "R0":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                    agreed_value = self.sender_value
                    # R1 nastaví svoju hodnotu
                    self.receiver_values[1] = agreed_value
                    self.messages = [
                        {"from": "S", "to": "R1", "type": "classical", "label": f"dohoda={agreed_value}"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R0 bol odhalený ako zradca. "
                                          f"Odosielateľ S a prijímateľ R1 sa dohodli na hodnote {agreed_value}.")
                    self.consensus_label.setText(f"Čiastočný: {agreed_value}")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: orange;")

                elif self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # R0 odmieta dohodu
                    agreed_value = self.receiver_values[1]
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "odmietam"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R0 odmieta dohodu. "
                                          f"R1 si ponecháva hodnotu {agreed_value} od odosielateľa.")
                    self.consensus_label.setText("Nedosiahnutý")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: red;")

                else:
                    # Byzantský R0 je odhalený
                    agreed_value = self.receiver_values[1]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R0 je detekovaný. "
                                          f"R1 si ponecháva pôvodnú hodnotu {agreed_value} od odosielateľa.")
                    # R1 a S majú konsenzus
                    self.consensus_label.setText(f"Čiastočný: {agreed_value}")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: orange;")

            # Byzantský prijímateľ R1
            elif self.byzantine_player == "R1":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                    agreed_value = self.sender_value
                    # R0 nastaví svoju hodnotu
                    self.receiver_values[0] = agreed_value
                    self.messages = [
                        {"from": "S", "to": "R0", "type": "classical", "label": f"dohoda={agreed_value}"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R1 bol odhalený ako zradca. "
                                          f"Odosielateľ S a prijímateľ R0 sa dohodli na hodnote {agreed_value}.")
                    self.consensus_label.setText(f"Čiastočný: {agreed_value}")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: orange;")

                elif self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # R1 odmieta dohodu
                    agreed_value = self.receiver_values[0]
                    self.messages = [
                        {"from": "R1", "to": "R0", "type": "classical", "label": "odmietam"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R1 odmieta dohodu. "
                                          f"R0 si ponecháva hodnotu {agreed_value} od odosielateľa.")
                    self.consensus_label.setText("Nedosiahnutý")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: red;")

                else:
                    # Byzantský R1 je odhalený
                    agreed_value = self.receiver_values[0]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R1 je detekovaný. "
                                          f"R0 si ponecháva pôvodnú hodnotu {agreed_value} od odosielateľa.")
                    # R0 a S majú konsenzus
                    self.consensus_label.setText(f"Čiastočný: {agreed_value}")
                    self.consensus_label.setStyleSheet("font-weight: bold; color: orange;")

            # Žiadny byzantský hráč
            else:
                agreed_value = self.sender_value
                self.update_info_text(f"Fáza 5: Všetci účastníci sú poctiví. "
                                      f"Dohoda na hodnote {agreed_value} bola dosiahnutá.")
                # Nastavenie konsenzu
                self.consensus_label.setText(f"Dosiahnutý: {agreed_value}")
                self.consensus_label.setStyleSheet("font-weight: bold; color: green;")

        elif self.current_step == 2:
            # Kontrola kritérií úspešnosti protokolu
            honest_nodes = []
            honest_values = []

            if self.byzantine_player != "S":
                honest_nodes.append("S")
                honest_values.append(self.sender_value)

            if self.byzantine_player != "R0":
                honest_nodes.append("R0")
                honest_values.append(self.receiver_values[0])

            if self.byzantine_player != "R1":
                honest_nodes.append("R1")
                honest_values.append(self.receiver_values[1])

            # Kritérium 1: Všetci poctiví hráči sa zhodli
            criterion1 = len(set(honest_values)) == 1

            # Kritérium 2: Ak je odosielateľ poctivý, zhodli sa na jeho hodnote
            criterion2 = True
            if "S" in honest_nodes:
                criterion2 = all(v == self.sender_value for v in honest_values)

            result_text = "Protokol dokončený.\n"
            result_text += f"Kritérium 1 (poctiví účastníci sa zhodli): {'✓' if criterion1 else '✗'}\n"
            result_text += f"Kritérium 2 (zhodli sa na hodnote odosielateľa): {'✓' if criterion2 else '✗'}"

            self.update_info_text(result_text)
            self.protocol_complete = True

    def update_phase_display(self):
        # Aktualizácia zobrazenia fázy a kroku
        phase_text = {
            "init": "Nespustený",
            "preparation": "Príprava a distribúcia",
            "transmission": "Prenos",
            "verification": "Overenie",
            "detection": "Detekcia zradcu",
            "agreement": "Dosiahnutie dohody"
        }.get(self.phase, self.phase)

        self.phase_label.setText(phase_text)
        self.step_label.setText(str(self.current_step))

    def update_node_table(self):
        # Aktualizácia tabuľky stavov uzlov
        sender_value = "-" if self.sender_value is None else str(self.sender_value)
        sender_qstate = "-" if "S" not in self.quantum_states else self.quantum_states["S"]
        self.state_table.setItem(0, 1, QTableWidgetItem(sender_value))
        self.state_table.setItem(0, 2, QTableWidgetItem(sender_qstate))

        r0_value = "-" if self.receiver_values[0] is None else str(self.receiver_values[0])
        r0_qstate = "-" if "R0" not in self.quantum_states else self.quantum_states["R0"]
        self.state_table.setItem(1, 1, QTableWidgetItem(r0_value))
        self.state_table.setItem(1, 2, QTableWidgetItem(r0_qstate))

        r1_value = "-" if self.receiver_values[1] is None else str(self.receiver_values[1])
        r1_qstate = "-" if "R1" not in self.quantum_states else self.quantum_states["R1"]
        self.state_table.setItem(2, 1, QTableWidgetItem(r1_value))
        self.state_table.setItem(2, 2, QTableWidgetItem(r1_qstate))

        # Zvýraznenie byzantského hráča
        for row in range(3):
            for col in range(3):
                item = self.state_table.item(row, col)
                if item:
                    if (row == 0 and self.byzantine_player == "S") or \
                            (row == 1 and self.byzantine_player == "R0") or \
                            (row == 2 and self.byzantine_player == "R1"):
                        item.setForeground(QBrush(QColor("red")))
                    else:
                        item.setForeground(QBrush(QColor("white")))

    def update_info_text(self, text):
        self.info_text.setText(text)

    def draw_network(self):
        self.scene.clear()

        # Pozície uzlov v trojuholníku
        positions = {
            "S": QPointF(0, -120),  # Hore
            "R0": QPointF(-120, 60),  # Vľavo dole
            "R1": QPointF(120, 60)  # Vpravo dole
        }

        node_radius = 30

        # Nakreslenie kvantových previazaní
        pen = QPen(QColor(50, 200, 50))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashDotLine)

        for link in self.entanglement_links:
            p1 = positions[link[0]]
            p2 = positions[link[1]]

            # Vytvorenie vlnitej čiary pre kvantové previazanie
            path = QPainterPath()
            path.moveTo(p1)

            # Výpočet stredového bodu a kolmého vektora pre vlnenie
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.sqrt(dx * dx + dy * dy)

            # Normalizovaný kolmý vektor
            perpx = -dy / length * 15
            perpy = dx / length * 15

            # Vytvorenie vlnitej čiary pomocou kubických Beziérových kriviek
            path.cubicTo(
                p1.x() + (mid.x() - p1.x()) * 0.25 + perpx,
                p1.y() + (mid.y() - p1.y()) * 0.25 + perpy,
                p1.x() + (mid.x() - p1.x()) * 0.75 - perpx,
                p1.y() + (mid.y() - p1.y()) * 0.75 - perpy,
                mid.x(), mid.y()
            )
            path.cubicTo(
                mid.x() + (p2.x() - mid.x()) * 0.25 + perpx,
                mid.y() + (p2.y() - mid.y()) * 0.25 + perpy,
                mid.x() + (p2.x() - mid.x()) * 0.75 - perpx,
                mid.y() + (p2.y() - mid.y()) * 0.75 - perpy,
                p2.x(), p2.y()
            )

            self.scene.addPath(path, pen)

        # Identifikácia komunikácie medzi R0 a R1
        r0_r1_messages = []
        for msg_index, msg in enumerate(self.messages):
            if (msg["from"] == "R0" and msg["to"] == "R1") or (msg["from"] == "R1" and msg["to"] == "R0"):
                r0_r1_messages.append(msg_index)

        # Nakreslenie správ
        for msg_index, msg in enumerate(self.messages):
            p1 = positions[msg["from"]]
            p2 = positions[msg["to"]]

            # Výpočet pozície správy (40% cesty od zdroja k cieľu)
            msg_pos = QPointF(
                p1.x() + (p2.x() - p1.x()) * 0.4,
                p1.y() + (p2.y() - p1.y()) * 0.4
            )

            # Nakreslenie čiary správy
            if msg["type"] == "classical":
                pen = QPen(QColor(255, 0, 0))
                pen.setWidth(1)
                self.scene.addLine(p1.x(), p1.y(), msg_pos.x(), msg_pos.y(), pen)
            else:  # quantum
                pen = QPen(QColor(50, 100, 250))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DotLine)
                self.scene.addLine(p1.x(), p1.y(), msg_pos.x(), msg_pos.y(), pen)

            # Nakreslenie popisu správy
            text = self.scene.addText(msg["label"])
            text.setDefaultTextColor(QColor(255, 255, 255))

            # Zabránenie prekrývaniu popiskov
            if msg_index in r0_r1_messages:
                # Zisti poradie aktuálnej správy medzi R0-R1 správami
                current_position = r0_r1_messages.index(msg_index)

                # Vypočítaj vertikálny posun na základe počtu správ a aktuálnej pozície
                if len(r0_r1_messages) > 1:
                    # Prvá správa ide nad čiaru, druhá pod čiaru
                    if current_position == 0:
                        vertical_offset = -30  # Vyššie nad šípkou
                    else:
                        vertical_offset = 30  # Nižšie pod šípkou

                    text.setPos(msg_pos.x() - text.boundingRect().width() / 2,
                                msg_pos.y() + vertical_offset)
                else:
                    # Ak je len jedna správa, umiestni ju pod šípku
                    text.setPos(msg_pos.x() - text.boundingRect().width() / 2,
                                msg_pos.y() + 15)
            else:
                # Pre ostatné správy štandardné umiestnenie pod šípkou
                text.setPos(msg_pos.x() - text.boundingRect().width() / 2,
                            msg_pos.y() + 15)

            # Pridanie šípky na koniec správy
            angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            arrow_p1 = QPointF(
                msg_pos.x() - 10 * math.cos(angle - math.pi / 6),
                msg_pos.y() - 10 * math.sin(angle - math.pi / 6)
            )
            arrow_p2 = QPointF(
                msg_pos.x() - 10 * math.cos(angle + math.pi / 6),
                msg_pos.y() - 10 * math.sin(angle + math.pi / 6)
            )

            if msg["type"] == "classical":
                pen = QPen(QColor(255, 0, 0))
            else:
                pen = QPen(QColor(50, 100, 250))

            self.scene.addLine(msg_pos.x(), msg_pos.y(), arrow_p1.x(), arrow_p1.y(), pen)
            self.scene.addLine(msg_pos.x(), msg_pos.y(), arrow_p2.x(), arrow_p2.y(), pen)

        # Nakreslenie uzlov
        for name, pos in positions.items():
            # Určenie farby uzla podľa stavu a byzantskosti
            if name == self.byzantine_player:
                brush = QBrush(QColor(255, 200, 200))  # Svetločervená pre byzantského
            else:
                if name == "S":
                    value = self.sender_value
                elif name == "R0":
                    value = self.receiver_values[0]
                else:  # R1
                    value = self.receiver_values[1]

                if value is None:
                    brush = QBrush(QColor(240, 240, 240))  # Svetlošedá pre bez hodnoty
                elif value == 0:
                    brush = QBrush(QColor(200, 230, 255))  # Svetlomodrá pre 0
                else:
                    brush = QBrush(QColor(255, 230, 200))  # Svetlooranžová pre 1

            # Nakreslenie kruhu uzla
            self.scene.addEllipse(
                pos.x() - node_radius, pos.y() - node_radius,
                2 * node_radius, 2 * node_radius,
                QPen(Qt.PenStyle.SolidLine), brush
            )

            # Popis uzla
            node_labels = {"S": "Odosielateľ (S)", "R0": "Prijímateľ (R0)", "R1": "Prijímateľ (R1)"}
            label = node_labels[name]
            text = self.scene.addText(name)
            text.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            text.setPos(pos.x() - text.boundingRect().width() / 2,
                        pos.y() - text.boundingRect().height() / 2)

            # Popis hodnoty ak je prítomná
            if name == "S" and self.sender_value is not None:
                value_text = self.scene.addText(f"Bit: {self.sender_value}")
            elif name == "R0" and self.receiver_values[0] is not None:
                value_text = self.scene.addText(f"Bit: {self.receiver_values[0]}")
            elif name == "R1" and self.receiver_values[1] is not None:
                value_text = self.scene.addText(f"Bit: {self.receiver_values[1]}")
            else:
                value_text = self.scene.addText("Bit: ?")

            value_text.setFont(QFont("Arial", 8))
            value_text.setPos(pos.x() - value_text.boundingRect().width() / 2,
                              pos.y() + node_radius + 5)

        # Škálovanie pohľadu pre vhodné zobrazenie scény s okrajmi
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))

        # Zabezpečenie správneho škálovania
        if self.isVisible():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        """Obsluha udalosti zmeny veľkosti pre správne škálovanie vizualizácie siete."""
        super().resizeEvent(event)
        if hasattr(self, 'scene') and self.scene.sceneRect().isValid():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)