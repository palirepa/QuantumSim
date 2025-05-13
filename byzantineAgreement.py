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
        self.animation_speed = 500  # ms between animation steps

        # Protocol state
        self.sender_value = None  # Bit to be broadcast by sender
        self.receiver_values = [None, None]  # Values at R0 and R1
        self.quantum_states = {}  # Quantum states at each node
        self.byzantine_player = None  # Which player is Byzantine (if any)
        self.entanglement_links = []  # Tracks qutrit entanglement between nodes
        self.messages = []  # Messages being passed in current animation step
        self.phase = "init"  # Current protocol phase
        self.protocol_complete = False

        # Index sets for Z-basis measurements
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

        # Controls section - ponecháme ako je
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

        # Configuration section - ponecháme ako je
        config_group = QGroupBox("Konfigurácia")
        config_layout = QHBoxLayout()

        # Sender's bit value
        bit_layout = QVBoxLayout()
        bit_layout.addWidget(QLabel("Bit odosielateľa:"))
        self.bit_combo = QComboBox()
        self.bit_combo.addItems(["0", "1"])
        bit_layout.addWidget(self.bit_combo)
        config_layout.addLayout(bit_layout)

        # Byzantine player selection
        byz_layout = QVBoxLayout()
        byz_layout.addWidget(QLabel("Byzantský účastník:"))
        self.byz_combo = QComboBox()
        self.byz_combo.addItems(["Žiadny", "Odosielateľ (S)", "Prijímateľ (R0)", "Prijímateľ (R1)"])
        byz_layout.addWidget(self.byz_combo)
        config_layout.addLayout(byz_layout)

        # Byzantine behavior setting
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

        # NOVÉ: Horizontálny layout pre vizualizáciu a stav
        viz_status_layout = QHBoxLayout()

        # Animation view - teraz v horizontálnom layoute
        viz_group = QGroupBox("Vizualizácia protokolu")
        viz_layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(300)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        viz_layout.addWidget(self.view)

        # Protocol state description
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setPlaceholderText("Stav protokolu sa zobrazí tu...")
        viz_layout.addWidget(self.info_text)

        viz_group.setLayout(viz_layout)
        viz_status_layout.addWidget(viz_group)  # Pridať do horizontálneho layoutu

        # Status display - teraz v horizontálnom layoute
        status_group = QGroupBox("Stav protokolu")
        status_layout = QVBoxLayout()

        # Current phase
        phase_layout = QHBoxLayout()
        phase_layout.addWidget(QLabel("Aktuálna fáza:"))
        self.phase_label = QLabel("Nespustený")
        phase_layout.addWidget(self.phase_label)
        phase_layout.addStretch()

        # Current step
        phase_layout.addWidget(QLabel("Krok:"))
        self.step_label = QLabel("0")
        phase_layout.addWidget(self.step_label)
        phase_layout.addStretch()

        # Consensus status
        phase_layout.addWidget(QLabel("Konsenzus:"))
        self.consensus_label = QLabel("Nedosiahnutý")
        phase_layout.addWidget(self.consensus_label)

        status_layout.addLayout(phase_layout)

        # Node state table
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
        viz_status_layout.addWidget(status_group)  # Pridať do horizontálneho layoutu

        # Pridať horizontálny layout do hlavného layoutu
        main_layout.addLayout(viz_status_layout)

        self.setLayout(main_layout)

        # Initial drawing
        self.draw_network()
        self.update_info_text("Protokol nespustený. Stlačte 'Inicializovať protokol' pre začatie.")

        # Initialize index sets for Z-basis measurements
        self.initialize_index_sets()

        # PRIDANÉ: Jednorázový časovač na korekciu zobrazenia po spustení
        QTimer.singleShot(100, self.fix_initial_view)

    def fix_initial_view(self):
        """Zabezpečí správne počiatočné nastavenie zobrazenia scény."""
        if hasattr(self, 'scene') and self.scene.sceneRect().isValid():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def initialize_index_sets(self):
        """Initialize the index sets for Z-basis measurements as described in the paper table."""
        # This simulates the table from the protocol paper
        # Index sets J0 and J1 corresponding to bit values 0 and 1
        self.index_sets = {
            "J0": [("S", 0), ("R0", 1), ("R1", 2),  # Class I
                   ("S", 0), ("R0", 2), ("R1", 1)],  # Class II
            "J1": [("S", 1), ("R0", 2), ("R1", 0),  # Class III
                   ("S", 1), ("R0", 0), ("R1", 2)]  # Class IV
        }

        # Classes V and VI are used for Byzantine detection
        self.index_sets["V"] = [("S", 2), ("R0", 1), ("R1", 0)]
        self.index_sets["VI"] = [("S", 2), ("R0", 0), ("R1", 1)]

    def initialize_protocol(self):
        # Get configuration
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

        # Initialize protocol state
        self.current_step = 0
        self.phase = "preparation"
        self.protocol_complete = False

        # Prijímatelia na začiatku nemajú žiadne hodnoty
        self.receiver_values = [None, None]

        # Initialize quantum states (Aharonov state)
        self.quantum_states = {
            "S": "Aharonov",
            "R0": "Aharonov",
            "R1": "Aharonov"
        }

        # Create entanglement links between all three nodes
        self.entanglement_links = [
            ("S", "R0"), ("S", "R1"), ("R0", "R1")
        ]

        # Update UI
        self.update_phase_display()
        self.update_node_table()
        self.draw_network()
        self.update_info_text("Protokol inicializovaný. Začína fáza prípravy a distribúcie kvantového previazania.")

        # Enable controls
        self.step_button.setEnabled(True)
        self.play_button.setEnabled(True)
        self.init_button.setEnabled(False)

    def reset_protocol(self):
        # Reset protocol state
        self.current_step = 0
        self.sender_value = None
        self.receiver_values = [None, None]
        self.quantum_states = {}
        self.byzantine_player = None
        self.entanglement_links = []
        self.messages = []
        self.phase = "init"
        self.protocol_complete = False

        # Update UI
        self.update_phase_display()
        self.update_node_table()
        self.draw_network()
        self.update_info_text("Protokol resetovaný. Stlačte 'Inicializovať protokol' pre začatie.")

        # Reset controls
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
        self.messages = []  # Clear previous messages

        # Handle protocol phases based on Slovak text description
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

        # Update UI
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
        """Handle preparation and distribution phase"""
        # Phase 1: Prepare and distribute Aharonov state qutrit triplets
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

        # Move to transmission phase after preparation
        elif self.current_step == 2:
            self.phase = "transmission"
            self.current_step = 0
            self.update_info_text("Príprava a distribúcia qutritov dokončená. Prechádzame do fázy prenosu.")

    def handle_transmission_phase(self):
        """Handle transmission phase"""
        # Phase 2: Sender sends bit values to receivers
        if self.current_step == 1:
            # Prijímatelia získavajú hodnoty od odosielateľa
            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                # Byzantský odosielateľ posiela rozdielne bity - náhodne určí, ktorý prijímateľ dostane akú hodnotu
                if random.random() < 0.5:
                    # Variant 1: bit 0 k R0 a bit 1 k R1
                    self.receiver_values[0] = self.sender_value
                    self.receiver_values[1] = 1 - self.sender_value
                else:
                    # Variant 2: bit 1 k R0 a bit 0 k R1
                    self.receiver_values[0] = 1 - self.sender_value
                    self.receiver_values[1] = self.sender_value
            else:
                # Poctivý odosielateľ posiela rovnaký bit obom prijímateľom
                self.receiver_values[0] = self.sender_value
                self.receiver_values[1] = self.sender_value

            # Show the sender sending bits to receivers
            self.messages = [
                {"from": "S", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                {"from": "S", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
            ]

            # Different description based on byzantine behavior
            if self.byzantine_player == "S" and self.receiver_values[0] != self.receiver_values[1]:
                self.update_info_text(f"Fáza 2: Byzantský odosielateľ posiela rozdielne bity prijímateľom. "
                                      f"R0 dostáva {self.receiver_values[0]}, R1 dostáva {self.receiver_values[1]}.")
            else:
                self.update_info_text(f"Fáza 2: Odosielateľ posiela bit {self.sender_value} obom prijímateľom.")

        # Sender measures qutrits and sends indices
        elif self.current_step == 2:
            # Sender measures qutrits in Z-basis
            self.quantum_states["S"] = f"Zmeraný: {self.sender_value}"

            # Ak je odosielateľ byzantský s falošnými indexami
            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # Byzantský odosielateľ posiela falošné indexy
                # Posiela indexy z opačnej množiny (J₁ namiesto J₀ alebo naopak)
                wrong_bit = 1 - self.sender_value

                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"indexy J{wrong_bit}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"indexy J{wrong_bit}"}
                ]
                self.update_info_text("Fáza 2: Byzantský odosielateľ meria svoje qutrity v Z-báze, "
                                      f"ale posiela falošné indexy z množiny J{wrong_bit} namiesto J{self.sender_value}.")
            else:
                # Odosielateľ posiela správne indexy zodpovedajúce jeho bitu
                self.messages = [
                    {"from": "S", "to": "R0", "type": "classical", "label": f"indexy J{self.sender_value}"},
                    {"from": "S", "to": "R1", "type": "classical", "label": f"indexy J{self.sender_value}"}
                ]
                self.update_info_text("Fáza 2: Odosielateľ meria svoje qutrity v Z-báze a posiela "
                                      f"prijímateľom indexy qutritov z množiny J{self.sender_value} zodpovedajúce jeho bitu.")

            # Move to verification phase
            self.phase = "verification"
            self.current_step = 0

    def handle_verification_phase(self):
        """Handle verification phase"""
        # Phase 3: Receivers measure their qutrits and verify consistency
        if self.current_step == 1:
            # Byzantské správanie ovplyvňuje merania
            if self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                # Odosielateľ poslal falošné indexy, čo spôsobí nekonzistenciu v meraniach
                # Qutrity v Aharonovom stave by mali mať vždy rozdielne hodnoty
                self.quantum_states["R0"] = f"Nekonzistentné s J{1 - self.sender_value}"
                self.quantum_states["R1"] = f"Nekonzistentné s J{1 - self.sender_value}"
                self.update_info_text("Fáza 3: Prijímatelia merajú svoje qutrity v Z-báze a zisťujú "
                                      f"nekonzistenciu s indexami J{1 - self.sender_value} od odosielateľa. "
                                      "Výsledky meraní nezodpovedajú Aharonovmu stavu.")
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

        # Receivers exchange information
        elif self.current_step == 2:
            # Exchange information about received bits
            self.messages = [
                {"from": "R0", "to": "R1", "type": "classical", "label": f"bit={self.receiver_values[0]}"},
                {"from": "R1", "to": "R0", "type": "classical", "label": f"bit={self.receiver_values[1]}"}
            ]

            self.update_info_text("Fáza 3: Prijímatelia si vymieňajú informácie o prijatých bitoch.")

            # Move to detection phase
            self.phase = "detection"
            self.current_step = 0

    def handle_detection_phase(self):
        """Handle traitor detection phase"""
        # Phase 4: Detect byzantine player if present
        if self.current_step == 1:
            # Check for byzantine sender (different bits sent)
            if self.byzantine_player == "S":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt":
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "nekonzistentné"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Prijímatelia zistili rozdielne bity. "
                                          "Vlastnosti Aharonovho stavu naznačujú, že odosielateľ je byzantský.")
                elif self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "falošné indexy"},
                        {"from": "R1", "to": "R0", "type": "classical", "label": "falošné indexy"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Prijímatelia zistili nekonzistenciu "
                                          "v indexoch qutritov, čo odhalilo byzantského odosielateľa.")
                else:  # "Odmietnutie dohody"
                    self.update_info_text("Fáza 4: Prijímatelia kontrolujú konzistenciu. "
                                          "Zatiaľ nezistili žiadnu nekonzistenciu.")

            # Check for byzantine receiver
            elif self.byzantine_player == "R0":
                if self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "falošná nekonzistencia"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Byzantský prijímateľ R0 sa pokúša "
                                          "podviesť, ale Aharonov stav odhalí jeho nečestné správanie.")
                else:
                    self.update_info_text("Fáza 4: Prijímatelia kontrolujú konzistenciu. "
                                          "Byzantský R0 zatiaľ nie je odhalený.")

            elif self.byzantine_player == "R1":
                if self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    self.messages = [
                        {"from": "R1", "to": "R0", "type": "classical", "label": "falošná nekonzistencia"}
                    ]
                    self.update_info_text("Fáza 4: Detekcia zradcu - Byzantský prijímateľ R1 sa pokúša "
                                          "podviesť, ale Aharonov stav odhalí jeho nečestné správanie.")
                else:
                    self.update_info_text("Fáza 4: Prijímatelia kontrolujú konzistenciu. "
                                          "Byzantský R1 zatiaľ nie je odhalený.")

            else:
                self.update_info_text("Fáza 4: Žiadny zradca nebol detekovaný, všetky hodnoty sú konzistentné.")

        # Move to agreement phase
        elif self.current_step == 2:
            self.phase = "agreement"
            self.current_step = 0
            self.update_info_text("Prechádzame do fázy dosiahnutia dohody.")

    def handle_agreement_phase(self):
        """Handle agreement phase"""
        # Phase 5: Reach agreement on bit value
        if self.current_step == 1:
            # For byzantine sender with different bits
            if self.byzantine_player == "S":
                if self.byzantine_behavior_combo.currentText() == "Odoslanie rozdielnych hodnôt" or \
                        self.byzantine_behavior_combo.currentText() == "Falošné indexy":
                    # Receivers agree on a value (could be either R0's or R1's)
                    agreed_value = self.receiver_values[0]  # For simplicity, choose R0's value
                    self.receiver_values[1] = agreed_value  # R1 accepts R0's value

                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": f"dohoda={agreed_value}"}
                    ]

                    self.update_info_text(f"Fáza 5: Prijímatelia detekovali byzantského odosielateľa "
                                          f"a dohodli sa na hodnote {agreed_value}.")
                elif self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # Odosielateľ odmietne dohodu, ale prijímatelia sa môžu aj tak dohodnúť
                    self.messages = [
                        {"from": "S", "to": "R0", "type": "classical", "label": "odmietam"},
                        {"from": "S", "to": "R1", "type": "classical", "label": "odmietam"}
                    ]
                    agreed_value = self.receiver_values[0]  # Prijímatelia sa dohodnú
                    self.receiver_values[1] = agreed_value
                    self.update_info_text(f"Fáza 5: Byzantský odosielateľ odmieta dohodu, ale prijímatelia "
                                          f"sa napriek tomu dohodli na hodnote {agreed_value}.")

            # For byzantine receiver R0
            elif self.byzantine_player == "R0":
                if self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # R0 odmieta prijať hodnotu, ale R1 si ponecháva hodnotu od S
                    agreed_value = self.receiver_values[1]
                    self.messages = [
                        {"from": "R0", "to": "R1", "type": "classical", "label": "odmietam"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R0 odmieta dohodu. "
                                          f"R1 si ponecháva hodnotu {agreed_value} od odosielateľa.")
                else:
                    # Byzantine R0 tries to cheat but is detected
                    agreed_value = self.receiver_values[1]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R0 je detekovaný. "
                                          f"R1 si ponecháva pôvodnú hodnotu {agreed_value} od odosielateľa.")

            # For byzantine receiver R1
            elif self.byzantine_player == "R1":
                if self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                    # R1 odmieta prijať hodnotu, ale R0 si ponecháva hodnotu od S
                    agreed_value = self.receiver_values[0]
                    self.messages = [
                        {"from": "R1", "to": "R0", "type": "classical", "label": "odmietam"}
                    ]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R1 odmieta dohodu. "
                                          f"R0 si ponecháva hodnotu {agreed_value} od odosielateľa.")
                else:
                    # Byzantine R1 tries to cheat but is detected
                    agreed_value = self.receiver_values[0]
                    self.update_info_text(f"Fáza 5: Byzantský prijímateľ R1 je detekovaný. "
                                          f"R0 si ponecháva pôvodnú hodnotu {agreed_value} od odosielateľa.")

            # No byzantine player
            else:
                agreed_value = self.sender_value
                self.update_info_text(f"Fáza 5: Všetci účastníci sú poctiví. "
                                      f"Dohoda na hodnote {agreed_value} bola dosiahnutá.")

            # Set final values - upravíme pre správne znázornenie "Odmietnutie dohody"
            if self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                # R0 si ponecháva svoju hodnotu (odmieta dohodu)
                pass
            elif self.byzantine_player != "R0":
                self.receiver_values[0] = agreed_value

            if self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() == "Odmietnutie dohody":
                # R1 si ponecháva svoju hodnotu (odmieta dohodu)
                pass
            elif self.byzantine_player != "R1":
                self.receiver_values[1] = agreed_value

            # Set consensus achieved based on whether there was agreement
            if self.byzantine_player is None or (
                    self.byzantine_player == "S" and self.byzantine_behavior_combo.currentText() != "Odmietnutie dohody") or (
                    self.byzantine_player != "S" and (
                    self.byzantine_player == "R0" and self.byzantine_behavior_combo.currentText() != "Odmietnutie dohody" or
                    self.byzantine_player == "R1" and self.byzantine_behavior_combo.currentText() != "Odmietnutie dohody"
            )
            ):
                self.consensus_label.setText(f"Dosiahnutý: {agreed_value}")
            else:
                self.consensus_label.setText("Nedosiahnutý")

        # Verify protocol success criteria
        elif self.current_step == 2:
            # Check success criteria:
            # 1. All honest participants agree on the same value
            # 2. If sender is honest, they agree on sender's value

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

            # Criterion 1: All honest players agree
            criterion1 = len(set(honest_values)) == 1

            # Criterion 2: If sender is honest, agree on sender's value
            criterion2 = True
            if "S" in honest_nodes:
                agreed_value = honest_values[0]
                criterion2 = agreed_value == self.sender_value

            result_text = "Protokol dokončený.\n"
            result_text += f"Kritérium 1 (poctiví účastníci sa zhodli): {'✓' if criterion1 else '✗'}\n"
            result_text += f"Kritérium 2 (zhodli sa na hodnote odosielateľa): {'✓' if criterion2 else '✗'}"

            self.update_info_text(result_text)
            self.protocol_complete = True

    def update_phase_display(self):
        # Update phase and step labels
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
        # Update node state table
        # Sender
        sender_value = "-" if self.sender_value is None else str(self.sender_value)
        sender_qstate = "-" if "S" not in self.quantum_states else self.quantum_states["S"]
        self.state_table.setItem(0, 1, QTableWidgetItem(sender_value))
        self.state_table.setItem(0, 2, QTableWidgetItem(sender_qstate))

        # Receiver 0
        r0_value = "-" if self.receiver_values[0] is None else str(self.receiver_values[0])
        r0_qstate = "-" if "R0" not in self.quantum_states else self.quantum_states["R0"]
        self.state_table.setItem(1, 1, QTableWidgetItem(r0_value))
        self.state_table.setItem(1, 2, QTableWidgetItem(r0_qstate))

        # Receiver 1
        r1_value = "-" if self.receiver_values[1] is None else str(self.receiver_values[1])
        r1_qstate = "-" if "R1" not in self.quantum_states else self.quantum_states["R1"]
        self.state_table.setItem(2, 1, QTableWidgetItem(r1_value))
        self.state_table.setItem(2, 2, QTableWidgetItem(r1_qstate))

        # Highlight Byzantine player and set white text for others
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

        # Node positions in a triangle
        positions = {
            "S": QPointF(0, -120),  # Top
            "R0": QPointF(-120, 60),  # Bottom left
            "R1": QPointF(120, 60)  # Bottom right
        }

        node_radius = 30

        # Draw entanglement links first (as wavy lines)
        pen = QPen(QColor(50, 200, 50))  # Zmenené na zelenú farbu
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashDotLine)

        for link in self.entanglement_links:
            p1 = positions[link[0]]
            p2 = positions[link[1]]

            # Create a wavy line for quantum entanglement
            path = QPainterPath()
            path.moveTo(p1)

            # Calculate midpoint and perpendicular vector for the wave
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.sqrt(dx * dx + dy * dy)

            # Normalized perpendicular vector
            perpx = -dy / length * 15
            perpy = dx / length * 15

            # Create wavy line with cubic bezier curves
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

        # Identifikácia komunikácie medzi R0 a R1 (v oboch smeroch)
        r0_r1_messages = []
        for msg_index, msg in enumerate(self.messages):
            if (msg["from"] == "R0" and msg["to"] == "R1") or (msg["from"] == "R1" and msg["to"] == "R0"):
                r0_r1_messages.append(msg_index)

        # Draw messages
        for msg_index, msg in enumerate(self.messages):
            p1 = positions[msg["from"]]
            p2 = positions[msg["to"]]

            # Calculate message position (40% of the way from source to destination)
            msg_pos = QPointF(
                p1.x() + (p2.x() - p1.x()) * 0.4,
                p1.y() + (p2.y() - p1.y()) * 0.4
            )

            # Draw message line
            if msg["type"] == "classical":
                pen = QPen(QColor(255, 0, 0))
                pen.setWidth(1)
                self.scene.addLine(p1.x(), p1.y(), msg_pos.x(), msg_pos.y(), pen)
            else:  # quantum
                pen = QPen(QColor(50, 100, 250))
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.DotLine)
                self.scene.addLine(p1.x(), p1.y(), msg_pos.x(), msg_pos.y(), pen)

            # Draw message label
            text = self.scene.addText(msg["label"])
            # Nastavíme farbu textu bielu aby bol čitateľný na tmavom pozadí
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

            # Add arrow at end of message
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

        # Draw nodes
        for name, pos in positions.items():
            # Determine node color based on state and if Byzantine
            if name == self.byzantine_player:
                brush = QBrush(QColor(255, 200, 200))  # Light red for Byzantine
            else:
                if name == "S":
                    value = self.sender_value
                elif name == "R0":
                    value = self.receiver_values[0]
                else:  # R1
                    value = self.receiver_values[1]

                if value is None:
                    brush = QBrush(QColor(240, 240, 240))  # Light gray for no value
                elif value == 0:
                    brush = QBrush(QColor(200, 230, 255))  # Light blue for 0
                else:
                    brush = QBrush(QColor(255, 230, 200))  # Light orange for 1

            # Draw node circle
            self.scene.addEllipse(
                pos.x() - node_radius, pos.y() - node_radius,
                2 * node_radius, 2 * node_radius,
                QPen(Qt.PenStyle.SolidLine), brush
            )

            # Node label
            node_labels = {"S": "Odosielateľ (S)", "R0": "Prijímateľ (R0)", "R1": "Prijímateľ (R1)"}
            label = node_labels[name]
            text = self.scene.addText(name)
            text.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            text.setPos(pos.x() - text.boundingRect().width() / 2,
                        pos.y() - text.boundingRect().height() / 2)

            # Value label if present
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

        # Scale the view to fit the scene with some margin
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))

        # Zabezpečenie správneho škálovania
        if self.isVisible():  # Kontrola, či je widget viditeľný
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        """Handle resize event to keep the network visualization properly scaled."""
        super().resizeEvent(event)
        if hasattr(self, 'scene') and self.scene.sceneRect().isValid():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)