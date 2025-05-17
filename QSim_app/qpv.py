from PyQt6.QtWidgets import (QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QTextEdit, QGroupBox, QTabWidget, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

# Qiskit importy pre kvantovú simuláciu
from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Statevector

import sys
import math
import random
import numpy as np
import time

# Nastavenie exception hook pre lepšie zobrazenie chýb
import traceback


def exception_hook(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)


sys.excepthook = exception_hook


class ClassicalChannel:
    def __init__(self):
        """Inicializácia klasického komunikačného kanála."""
        self.messages = []  # História správ
        self.is_authenticated = True  # Či je kanál autentifikovaný

    def send_message(self, sender, recipient, message_type, content, timestamp=None):
        """Odoslanie správy klasickým kanálom."""
        if timestamp is None:
            timestamp = time.time()

        message = {
            'sender': sender,
            'recipient': recipient,
            'type': message_type,
            'content': content,
            'timestamp': timestamp
        }

        self.messages.append(message)
        return message

    def get_messages(self, recipient=None, message_type=None):
        """Získanie správ podľa príjemcu a typu."""
        filtered = self.messages

        if recipient:
            filtered = [m for m in filtered if m['recipient'] == recipient]

        if message_type:
            filtered = [m for m in filtered if m['type'] == message_type]

        return filtered

    def clear(self):
        """Vyčistenie histórie správ."""
        self.messages = []


class QuantumPositionVerification(QWidget):
    def __init__(self, parent=None):
        """Inicializácia protokolu QPV widgetu"""
        super().__init__(parent)

        # Nastavenia protokolu
        self.distance_v1_to_prover = 100  # v kilometroch
        self.distance_prover_to_v2 = 100  # v kilometroch
        self.c = 299792.458  # rýchlosť svetla v km/s
        self.round_count = 10  # počet verifikačných kôl
        self.time_window = 0.001  # akceptovateľné časové okno v sekundách
        self.qber_threshold = 0.25  # prah pre detekciu podvodu (25% chybovosť)

        # Skutočná poloha nečestného dôkazníka (odlišná od deklarovanej)
        self.actual_distance_v1_to_prover = 150  # v kilometroch
        self.actual_distance_prover_to_v2 = 50  # v kilometroch

        # Stav protokolu
        self.current_round = 0
        self.protocol_step = 0
        self.basis = 0  # 0: standardná báza {|0⟩, |1⟩}, 1: Hadamardova báza {|+⟩, |−⟩}
        self.is_honest_prover = True
        self.verification_result = False
        self.mode = "single"  # single alebo dishonest_prover

        # Časy odpovede a očakávané časy
        self.response_time_v1 = 0  # Skutočný čas odpovede pre V1
        self.response_time_v2 = 0  # Skutočný čas odpovede pre V2
        self.expected_time_v1 = 0  # Očakávaný čas odpovede pre V1
        self.expected_time_v2 = 0  # Očakávaný čas odpovede pre V2

        # Výsledky overenia
        self.timing_verification_v1 = False  # Časové overenie V1
        self.timing_verification_v2 = False  # Časové overenie V2
        self.quantum_verification = False  # Kvantové overenie
        self.time_difference_v1 = 0  # Časový rozdiel v sekundách pre V1
        self.time_difference_v2 = 0  # Časový rozdiel v sekundách pre V2
        self.qber = 0.0  # Quantum Bit Error Rate

        # Kvantové stavy a merania
        self.original_state = None
        self.measurement_result = None
        self.qubit_type = 0  # 0:|0⟩, 1:|1⟩, 2:|+⟩, 3:|−⟩
        self.expected_measurement = 0  # Očakávaný výsledok merania

        # Sledovanie výsledkov
        self.successful_rounds = 0
        self.round_results = []

        # Stav animácie
        self.animation_time = 0.0
        self.animation_v1_signal_start_time = 0.0  # Čas začiatku signálu od V1
        self.animation_v2_signal_start_time = 0.0  # Čas začiatku signálu od V2
        self.animation_response_v1_start_time = 0.0  # Čas začiatku odpovede k V1
        self.animation_response_v2_start_time = 0.0  # Čas začiatku odpovede k V2
        self.dt = 0.05  # časový krok animácie
        self.signal_position_v1 = 0  # Pozícia signálu od V1 (0-100%)
        self.signal_position_v2 = 0  # Pozícia signálu od V2 (0-100%)
        self.response_position_v1 = 0  # Pozícia odpoveďového signálu k V1 (0-100%)
        self.response_position_v2 = 0  # Pozícia odpoveďového signálu k V2 (0-100%)
        self.response_active_v1 = False  # Či sa zobrazuje odpoveďový signál k V1
        self.response_active_v2 = False  # Či sa zobrazuje odpoveďový signál k V2
        self.v1_signal_active = False  # Indikátor, či je signál od V1 aktívny
        self.v2_signal_active = False  # Indikátor, či je signál od V2 aktívny

        # Pridanie klasického kanála
        self.classical_channel = ClassicalChannel()
        self.classical_messages = []  # Správy na zobrazenie v UI

        # Definície krokov protokolu
        self.protocol_steps = [
            "Inicializácia overovateľov a dôkazníka",
            "Overovateľ 1 posiela kvantový stav ψ",
            "Overovateľ 2 posiela bázu merania",
            "Dôkazník prijíma signály a meria kvantový stav",
            "Dôkazník posiela výsledok merania obom overovateľom",
            "Overovatelia prijímajú a overujú odpoveď",
            "Stanovenie výsledku overenia a výpočet QBER"
        ]

        # Kroky pre režim nečestného dôkazníka
        self.dishonest_prover_steps = [
            "Inicializácia overovateľov a nečestného dôkazníka",
            "Overovateľ 1 posiela kvantový stav ψ",
            "Overovateľ 2 posiela bázu merania",
            "Nečestný dôkazník prijíma signály a meria kvantový stav",
            "Nečestný dôkazník posiela výsledok merania obom overovateľom",
            "Overovatelia prijímajú a overujú odpoveď",
            "Stanovenie výsledku overenia - podvod odhalený"
        ]

        # Časovač animácie
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.setInterval(50)  # 50ms = 20fps

        # Inicializácia kvantových obvodov
        self.prepare_quantum_circuits()

        # Nastavenie používateľského rozhrania
        self.setup_ui()

    def setup_ui(self):
        """Nastavenie používateľského rozhrania"""
        main_layout = QVBoxLayout(self)

        # Nadpis
        title_label = QLabel("Kvantového overovania polohy")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Ovládací panel
        control_box = QGroupBox("Ovládanie protokolu")
        control_layout = QHBoxLayout(control_box)

        # Ovládače vzdialeností - kombinované deklarované a skutočné
        distance_layout = QVBoxLayout()

        # Prvý riadok - V1 k dôkazníkovi (deklarovaná a skutočná vzdialenosť)
        distance_v1_layout = QHBoxLayout()

        # Deklarovaná vzdialenosť V1
        distance_v1_layout.addWidget(QLabel("Deklarovaná vzdialenosť V1 k dôkazníkovi (km):"))
        self.v1_distance_input = QLineEdit(str(self.distance_v1_to_prover))
        distance_v1_layout.addWidget(self.v1_distance_input)

        # Skutočná vzdialenosť V1 - spočiatku skrytá
        self.actual_v1_label = QLabel("Skutočná vzdialenosť V1 k dôkazníkovi (km):")
        self.actual_v1_label.setVisible(False)
        distance_v1_layout.addWidget(self.actual_v1_label)

        self.actual_v1_distance_input = QLineEdit(str(self.actual_distance_v1_to_prover))
        self.actual_v1_distance_input.setVisible(False)
        distance_v1_layout.addWidget(self.actual_v1_distance_input)

        # Druhý riadok - dôkazník k V2 (deklarovaná a skutočná vzdialenosť)
        distance_v2_layout = QHBoxLayout()

        # Deklarovaná vzdialenosť V2
        distance_v2_layout.addWidget(QLabel("Deklarovaná vzdialenosť dôkazníka k V2 (km):"))
        self.v2_distance_input = QLineEdit(str(self.distance_prover_to_v2))
        distance_v2_layout.addWidget(self.v2_distance_input)

        # Skutočná vzdialenosť V2 - spočiatku skrytá
        self.actual_v2_label = QLabel("Skutočná vzdialenosť dôkazníka k V2 (km):")
        self.actual_v2_label.setVisible(False)
        distance_v2_layout.addWidget(self.actual_v2_label)

        self.actual_v2_distance_input = QLineEdit(str(self.actual_distance_prover_to_v2))
        self.actual_v2_distance_input.setVisible(False)
        distance_v2_layout.addWidget(self.actual_v2_distance_input)

        # Pridanie riadkov do layoutu
        distance_layout.addLayout(distance_v1_layout)
        distance_layout.addLayout(distance_v2_layout)

        control_layout.addLayout(distance_layout)

        # Ovládače dôkazníka
        prover_layout = QVBoxLayout()
        self.honest_button = QPushButton("Poctivý dôkazník")
        self.honest_button.setCheckable(True)
        self.honest_button.setChecked(True)
        self.honest_button.clicked.connect(self.set_honest_prover)

        self.dishonest_button = QPushButton("Nečestný dôkazník")
        self.dishonest_button.setCheckable(True)
        self.dishonest_button.clicked.connect(self.set_dishonest_prover)

        prover_layout.addWidget(self.honest_button)
        prover_layout.addWidget(self.dishonest_button)
        control_layout.addLayout(prover_layout)

        # Tlačidlá akcií protokolu
        button_layout = QVBoxLayout()
        self.start_button = QPushButton("Spustiť protokol")
        self.start_button.clicked.connect(self.start_protocol)

        self.next_step_button = QPushButton("Ďalší krok")
        self.next_step_button.clicked.connect(self.next_protocol_step)
        self.next_step_button.setEnabled(False)

        self.reset_button = QPushButton("Resetovať")
        self.reset_button.clicked.connect(self.reset_ui)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.next_step_button)
        button_layout.addWidget(self.reset_button)
        control_layout.addLayout(button_layout)

        main_layout.addWidget(control_box)

        # Oblasť vizualizácie
        self.visualization_area = QPVVisualizationWidget(self)
        self.visualization_area.setMinimumHeight(500)
        main_layout.addWidget(self.visualization_area)

    def set_honest_prover(self):
        """Nastavenie dôkazníka ako poctivého."""
        self.is_honest_prover = True
        self.mode = "single"
        self.honest_button.setChecked(True)
        self.dishonest_button.setChecked(False)

        # Skrytie polí pre skutočnú polohu
        self.actual_v1_label.setVisible(False)
        self.actual_v1_distance_input.setVisible(False)
        self.actual_v2_label.setVisible(False)
        self.actual_v2_distance_input.setVisible(False)

        self.visualization_area.set_mode("single")

    def set_dishonest_prover(self):
        """Nastavenie dôkazníka ako nečestného."""
        self.is_honest_prover = False
        self.mode = "dishonest_prover"
        self.honest_button.setChecked(False)
        self.dishonest_button.setChecked(True)

        # Zobrazenie polí pre skutočnú polohu
        self.actual_v1_label.setVisible(True)
        self.actual_v1_distance_input.setVisible(True)
        self.actual_v2_label.setVisible(True)
        self.actual_v2_distance_input.setVisible(True)

        self.visualization_area.set_mode("dishonest_prover")

    def prepare_quantum_circuits(self):
        """Inicializácia kvantových obvodov pre protokol."""
        # Základný jednoqubitový obvod
        self.circuit = QuantumCircuit(1)

    def start_protocol(self):
        """Spustenie protokolu s aktuálnymi nastaveniami."""
        try:
            # Získanie deklarovaných vzdialeností zo vstupných polí
            self.distance_v1_to_prover = float(self.v1_distance_input.text())
            self.distance_prover_to_v2 = float(self.v2_distance_input.text())

            # Získanie skutočných vzdialeností pre nečestného dôkazníka
            if self.mode == "dishonest_prover":
                self.actual_distance_v1_to_prover = float(self.actual_v1_distance_input.text())
                self.actual_distance_prover_to_v2 = float(self.actual_v2_distance_input.text())

            # Reset stavu protokolu
            self.reset_protocol()

            # Inicializácia klasického kanála
            self.classical_channel.clear()
            self.classical_messages = []

            # Pridanie deklarácie polohy dôkazníka cez klasický kanál
            self.classical_channel.send_message(
                sender="Dôkazník",
                recipient="Overovatelia",
                message_type="position_declaration",
                content=f"Deklarujem svoju polohu: V1→{self.distance_v1_to_prover} km, V2→{self.distance_prover_to_v2} km"
            )

            self.add_classical_message("Dôkazník → Overovatelia: Deklarácia polohy")

            # Inicializácia prvého kroku
            self.generate_challenge()

            # Aktualizácia UI
            self.start_button.setEnabled(False)
            self.next_step_button.setEnabled(True)

            # Spustenie animácie
            self.timer.start()

            # Aktualizácia vizualizácie
            self.visualization_area.set_protocol_state(self.get_current_state())
            self.visualization_area.update()

        except ValueError:
            # Neplatný vstup - nič nerobíme (bez výpisu do konzoly)
            pass

    def add_classical_message(self, message):
        """Pridanie správy do zoznamu klasickej komunikácie na zobrazenie."""
        self.classical_messages.append(message)
        # Obmedziť počet správ na zobrazenie
        if len(self.classical_messages) > 5:
            self.classical_messages = self.classical_messages[-5:]

    def next_protocol_step(self):
        """Prechod na ďalší krok protokolu."""
        # Podľa režimu sa volia rôzne postupnosti krokov
        if self.mode == "dishonest_prover":
            self.next_dishonest_step()
        else:

            self.next_honest_step()

        # Aktualizácia vizualizácie
        self.visualization_area.set_protocol_state(self.get_current_state())
        self.visualization_area.update()

    def next_honest_step(self):
        """Prechod na ďalší krok protokolu pre poctivého dôkazníka."""
        # Posun na ďalší krok
        self.protocol_step += 1

        if self.protocol_step >= len(self.protocol_steps):
            # Protokol dokončený, reset
            self.protocol_step = 0
            self.current_round += 1

            # Povolenie resetu pre ďalšie kolo
            self.next_step_button.setEnabled(False)
            self.start_button.setEnabled(True)
            return

        if self.protocol_step == 1:

            # V1 ↔ V2: Príprava parametrov protokolu
            self.add_classical_message("V1 ↔ V2: Príprava parametrov protokolu (kvantový stav a meracia báza)")

            # V1 informuje o kvantovom stave
            qubit_names = {0: "|0⟩", 1: "|1⟩", 2: "|+⟩", 3: "|−⟩"}
            qubit_name = qubit_names.get(self.qubit_type, "?")
            self.add_classical_message(f"V1 → Dôkazník: Informácia o vysielanom kvantovom stave ψ = {qubit_name}")

            # Aktivácia signálu od V1 (kvantový stav)
            self.v1_signal_active = True
            self.animation_v1_signal_start_time = self.animation_time


        elif self.protocol_step == 2:

            # V2 posiela informáciu o báze merania
            basis_name = "Z-báza {|0⟩,|1⟩}" if self.basis == 0 else "X-báza {|+⟩,|−⟩}"
            self.add_classical_message(f"V2 → Dôkazník: Meranie v {basis_name}")

            # Aktivácia signálu od V2 (báza merania)
            self.v2_signal_active = True
            self.animation_v2_signal_start_time = self.animation_time


        elif self.protocol_step == 4:

            # Simulácia merania a odpovede dôkazníka obom overovateľom
            self.simulate_prover_response()
            # Dôkazník posiela výsledok merania
            self.add_classical_message(f"Dôkazník → Overovatelia: Výsledok merania {self.measurement_result}")

            self.response_active_v1 = True
            self.response_active_v2 = True
            self.animation_response_v1_start_time = self.animation_time
            self.animation_response_v2_start_time = self.animation_time


        elif self.protocol_step == 5:

            # Overovatelia si vymieňajú časy
            self.add_classical_message("V1 ↔ V2: Výmena zaznamenaných časov príchodu odpovede")
            self.add_classical_message("V1 ↔ V2: Výpočet časových rozdielov a kvantovej chybovosti")


        elif self.protocol_step == 6:

            # Výsledok overenia
            self.verify_response()
            self.calculate_qber()

            # Overovatelia oznámia výsledok
            result_text = "ÚSPEŠNÉ" if self.verification_result else "NEÚSPEŠNÉ"
            self.add_classical_message(f"Overovatelia → Dôkazník: Výsledok overenia {result_text}")

            # Povolenie resetu pre ďalšie kolo
            self.next_step_button.setEnabled(False)
            self.start_button.setEnabled(True)

        # Aktualizácia vizualizácie
        self.visualization_area.set_protocol_state(self.get_current_state())
        self.visualization_area.update()

    def next_dishonest_step(self):
        """Prechod na ďalší krok protokolu pre nečestného dôkazníka."""
        # Posun na ďalší krok
        self.protocol_step += 1

        if self.protocol_step >= len(self.dishonest_prover_steps):
            # Protokol dokončený, reset
            self.protocol_step = 0
            self.current_round += 1

            # Povolenie resetu pre ďalšie kolo
            self.next_step_button.setEnabled(False)
            self.start_button.setEnabled(True)
            return

        # Spracovanie aktualizácií špecifických pre krok
        if self.protocol_step == 1:

            # V1 ↔ V2: Príprava parametrov protokolu
            self.add_classical_message("V1 ↔ V2: Príprava parametrov protokolu (kvantový stav a meracia báza)")

            # V1 informuje o kvantovom stave
            qubit_names = {0: "|0⟩", 1: "|1⟩", 2: "|+⟩", 3: "|−⟩"}
            qubit_name = qubit_names.get(self.qubit_type, "?")
            self.add_classical_message(
                f"V1 → Dôkazník: Informácia o vysielanom kvantovom stave ψ = {qubit_name}")

            # Aktivácia signálu od V1 (kvantový stav)
            self.v1_signal_active = True
            self.animation_v1_signal_start_time = self.animation_time

        elif self.protocol_step == 2:
            # V2 posiela informáciu o báze merania
            basis_name = "Z-báza {|0⟩,|1⟩}" if self.basis == 0 else "X-báza {|+⟩,|−⟩}"
            self.add_classical_message(f"V2 → Dôkazník: Meranie v {basis_name}")

            # Aktivácia signálu od V2 (báza merania)
            self.v2_signal_active = True
            self.animation_v2_signal_start_time = self.animation_time


        elif self.protocol_step == 4:

            # Simulácia merania a odpovede dôkazníka obom overovateľom
            self.simulate_prover_response()
            # Dôkazník posiela výsledok merania
            self.add_classical_message(f"Dôkazník → Overovatelia: Výsledok merania {self.measurement_result}")

            self.response_active_v1 = True
            self.response_active_v2 = True
            self.animation_response_v1_start_time = self.animation_time
            self.animation_response_v2_start_time = self.animation_time


        elif self.protocol_step == 5:

            # Overovatelia si vymieňajú časy
            self.add_classical_message("V1 ↔ V2: Výmena zaznamenaných časov príchodu odpovede")
            self.add_classical_message("V1 ↔ V2: Výpočet časových rozdielov a kvantovej chybovosti")


        elif self.protocol_step == 6:

            # Výsledok overenia
            self.verify_response()
            self.calculate_qber()

            # Overovatelia oznámia výsledok
            result_text = "ÚSPEŠNÉ" if self.verification_result else "NEÚSPEŠNÉ"
            self.add_classical_message(f"Overovatelia → Dôkazník: Výsledok overenia {result_text}")

            # Povolenie resetu pre ďalšie kolo
            self.next_step_button.setEnabled(False)
            self.start_button.setEnabled(True)

        # Aktualizácia vizualizácie
        self.visualization_area.set_protocol_state(self.get_current_state())
        self.visualization_area.update()

    def reset_ui(self):
        """Reset UI a stavu protokolu."""
        # Zastavenie časovača animácie
        if self.timer.isActive():
            self.timer.stop()

        # Reset stavu protokolu
        self.reset_protocol()

        # Aktualizácia UI
        self.start_button.setEnabled(True)
        self.next_step_button.setEnabled(False)

        # Reset vizualizácie
        self.visualization_area.reset()
        self.visualization_area.update()

    def update_animation(self):
        """Aktualizácia stavu animácie."""
        # Kontrola pre ukončenie animácie
        is_final_step = (self.protocol_step >= 6 and self.mode == "single") or \
                        (self.protocol_step >= 6 and self.mode == "dishonest_prover")

        if self.timer.isActive() and is_final_step:
            # Zastaviť animáciu po dokončení overenia
            self.timer.stop()

        self.animation_time += self.dt

        # Aktualizácia pozície signálu od V1 (kvantový stav)
        if self.v1_signal_active:
            # Škálovanie času na základe vzdialenosti
            if self.mode == "dishonest_prover":
                # Pre nečestného dôkazníka sa používa SKUTOČNÁ vzdialenosť
                distance_factor_v1 = self.actual_distance_v1_to_prover / 100.0
            else:
                # Pre poctivého dôkazníka sa používa deklarovanú vzdialenosť
                distance_factor_v1 = self.distance_v1_to_prover / 100.0

            animation_duration_v1 = min(5.0, max(1.0, 2.0 * distance_factor_v1))

            progress_time = self.animation_time - self.animation_v1_signal_start_time
            progress = min(1.0, progress_time / animation_duration_v1)
            self.signal_position_v1 = progress

        # Aktualizácia pozície signálu od V2 (báza)
        if self.v2_signal_active:
            # Škálovanie času na základe vzdialenosti
            if self.mode == "dishonest_prover":
                # Pre nečestného dôkazníka sa používa SKUTOČNÁ vzdialenosť
                distance_factor_v2 = self.actual_distance_prover_to_v2 / 100.0
            else:
                # Pre poctivého dôkazníka sa používa deklarovanú vzdialenosť
                distance_factor_v2 = self.distance_prover_to_v2 / 100.0

            animation_duration_v2 = min(5.0, max(1.0, 2.0 * distance_factor_v2))

            progress_time = self.animation_time - self.animation_v2_signal_start_time
            progress = min(1.0, progress_time / animation_duration_v2)
            self.signal_position_v2 = progress

        # Aktualizácia signálu odpovede k V1
        if self.response_active_v1:
            # Škálovanie času pre odpoveď na základe vzdialenosti
            if self.mode == "dishonest_prover":
                # Používa sa SKUTOČNÁ vzdialenosť pre nečestného dôkazníka
                distance_factor_v1 = self.actual_distance_v1_to_prover / 100.0
            else:
                distance_factor_v1 = self.distance_v1_to_prover / 100.0

            animation_duration_resp_v1 = min(5.0, max(1.0, 2.0 * distance_factor_v1))

            progress_time = self.animation_time - self.animation_response_v1_start_time
            progress = min(1.0, progress_time / animation_duration_resp_v1)
            self.response_position_v1 = progress

        # Aktualizácia signálu odpovede k V2
        if self.response_active_v2:
            # Škálovanie času pre odpoveď na základe vzdialenosti
            if self.mode == "dishonest_prover":
                # Používa sa SKUTOČNÁ vzdialenosť pre nečestného dôkazníka
                distance_factor_v2 = self.actual_distance_prover_to_v2 / 100.0
            else:
                distance_factor_v2 = self.distance_prover_to_v2 / 100.0

            animation_duration_resp_v2 = min(5.0, max(1.0, 2.0 * distance_factor_v2))

            progress_time = self.animation_time - self.animation_response_v2_start_time
            progress = min(1.0, progress_time / animation_duration_resp_v2)
            self.response_position_v2 = progress

        # Aktualizácia vizualizácie
        self.visualization_area.set_protocol_state(self.get_current_state())
        self.visualization_area.update()

    def generate_challenge(self):
        """Vygenerovanie náhodného kvantového stavu a bázy merania."""
        # Generovanie náhodného qubitového stavu (|0⟩, |1⟩, |+⟩, |−⟩)
        self.qubit_type = random.randint(0, 3)

        # Vytvorenie nového obvodu pre toto kolo
        self.circuit = QuantumCircuit(1)

        # Príprava stavu na základe typu
        if self.qubit_type == 0:  # |0⟩
            pass  # Predvolený stav je |0⟩
        elif self.qubit_type == 1:  # |1⟩
            self.circuit.x(0)
        elif self.qubit_type == 2:  # |+⟩
            self.circuit.h(0)
        elif self.qubit_type == 3:  # |−⟩
            self.circuit.x(0)
            self.circuit.h(0)

        # Uloženie pôvodného stavu
        self.original_state = self.circuit.copy()

        # Generovanie náhodnej bázy merania
        self.basis = random.randint(0, 1)  # 0: Z-báza {|0⟩, |1⟩}, 1: X-báza {|+⟩, |−⟩}

        # Výpočet očakávaného výsledku merania
        if self.basis == 0:  # Z-báza
            if self.qubit_type == 0:  # |0⟩
                self.expected_measurement = 0
            elif self.qubit_type == 1:  # |1⟩
                self.expected_measurement = 1
            elif self.qubit_type == 2:  # |+⟩
                # V Z-báze, |+⟩ dáva 0 alebo 1 s 50% pravdepodobnosťou
                self.expected_measurement = None
            elif self.qubit_type == 3:  # |−⟩
                # V Z-báze, |−⟩ dáva 0 alebo 1 s 50% pravdepodobnosťou
                self.expected_measurement = None
        else:  # X-báza
            if self.qubit_type == 0:  # |0⟩
                # V X-báze, |0⟩ dáva 0 alebo 1 s 50% pravdepodobnosťou
                self.expected_measurement = None
            elif self.qubit_type == 1:  # |1⟩
                # V X-báze, |1⟩ dáva 0 alebo 1 s 50% pravdepodobnosťou
                self.expected_measurement = None
            elif self.qubit_type == 2:  # |+⟩
                self.expected_measurement = 0
            elif self.qubit_type == 3:  # |−⟩
                self.expected_measurement = 1

        return self.qubit_type, self.basis

    def calculate_expected_timing(self):
        """Výpočet očakávaných časov odpovede na základe deklarovanej polohy."""
        # Čas pre signály dosiahnuť dôkazníka (v sekundách)
        time_v1_to_prover = self.distance_v1_to_prover / self.c
        time_v2_to_prover = self.distance_prover_to_v2 / self.c

        # Minimálny čas spracovania dôkazníkom
        processing_time = 0.000001  # 1 mikrosekunda

        # Dôkazník musí čakať na príchod oboch signálov
        measurement_time = max(time_v1_to_prover, time_v2_to_prover) + processing_time

        # Čas návratu k obom overovateľom
        time_to_v1 = self.distance_v1_to_prover / self.c
        time_to_v2 = self.distance_prover_to_v2 / self.c

        # Očakávané časy príchodu odpovede k overovateľom
        expected_time_v1 = measurement_time + time_to_v1
        expected_time_v2 = measurement_time + time_to_v2

        return expected_time_v1, expected_time_v2

    def simulate_prover_response(self):
        """Simulácia merania a odpovede dôkazníka."""
        # Meranie kvantového stavu
        measurement_circuit = self.original_state.copy()
        if self.basis == 1:  # X-báza
            measurement_circuit.h(0)

        measurement_circuit.measure_all()

        # Vykonanie merania
        backend = Aer.get_backend('qasm_simulator')
        job = execute(measurement_circuit, backend, shots=1)
        result = job.result()
        counts = result.get_counts()
        self.measurement_result = int(list(counts.keys())[0])

        # DEKLAROVANÁ POLOHA-očakávané časy podľa deklarovanej polohy
        # Signál od V1 k dôkazníkovi
        decl_time_v1_to_prover = self.distance_v1_to_prover / self.c
        # Signál od V2 k dôkazníkovi
        decl_time_v2_to_prover = self.distance_prover_to_v2 / self.c
        # Čas spracovania-keď prídu oba signály
        decl_processing_time = 0.000001  # 1 mikrosekunda
        # Čas odoslania odpovede späť
        decl_time_prover_to_v1 = self.distance_v1_to_prover / self.c
        decl_time_prover_to_v2 = self.distance_prover_to_v2 / self.c

        # Celkový očakávaný čas pre oba overovateľov
        self.expected_time_v1 = decl_time_v1_to_prover + decl_processing_time + decl_time_prover_to_v1
        self.expected_time_v2 = decl_time_v2_to_prover + decl_processing_time + decl_time_prover_to_v2

        if self.mode == "dishonest_prover":
            # SKUTOČNÁ POLOHA-skutočné časy
            # Signál od V1 k skutočnej polohe
            actual_time_v1_to_prover = self.actual_distance_v1_to_prover / self.c
            # Signál od V2 k skutočnej polohe
            actual_time_v2_to_prover = self.actual_distance_prover_to_v2 / self.c
            # Čas spracovania-keď prídu oba signály
            actual_processing_time = 0.000001  # 1 mikrosekunda
            # Čas odoslania odpovede späť
            actual_time_prover_to_v1 = self.actual_distance_v1_to_prover / self.c
            actual_time_prover_to_v2 = self.actual_distance_prover_to_v2 / self.c

            # Celkový skutočný čas pre oba overovateľov
            self.response_time_v1 = actual_time_v1_to_prover + actual_processing_time + actual_time_prover_to_v1
            self.response_time_v2 = actual_time_v2_to_prover + actual_processing_time + actual_time_prover_to_v2

            # Výpočet rozdielu so znamienkom (kladné = neskôr, záporné = skôr)
            time_diff_v1 = self.response_time_v1 - self.expected_time_v1
            time_diff_v2 = self.response_time_v2 - self.expected_time_v2

        else:
            # Pre poctivého dôkazníka - časy sú rovnaké ako očakávané s malou odchýlkou
            self.response_time_v1 = self.expected_time_v1 + random.normalvariate(0, 0.000001)
            self.response_time_v2 = self.expected_time_v2 + random.normalvariate(0, 0.000001)

    def verify_response(self):
        """Overenie odpovede dôkazníka."""
        # Výpočet časových rozdielov so znamienkom
        self.time_difference_v1 = self.response_time_v1 - self.expected_time_v1
        self.time_difference_v2 = self.response_time_v2 - self.expected_time_v2

        # Pre kontrolu časovania používame absolútnu hodnotu rozdielu
        absolute_diff_v1 = abs(self.time_difference_v1)
        absolute_diff_v2 = abs(self.time_difference_v2)

        # Akceptovateľné časové okno
        self.time_window = 0.000010  # 0.01 ms

        # Kontrola časovania - používa absolútnu hodnotu pre porovnanie s oknom
        self.timing_verification_v1 = absolute_diff_v1 <= self.time_window
        self.timing_verification_v2 = absolute_diff_v2 <= self.time_window

        # Kontrola kvantového výsledku
        if self.expected_measurement is None:
            # Ak výsledok nie je deterministický (50/50), považujeme oba výsledky za správne
            self.quantum_verification = True
        else:
            # Kontrola, či výsledok zodpovedá očakávanému
            self.quantum_verification = (self.measurement_result == self.expected_measurement)

        # V režime nečestného dôkazníka zabezpečiť konzistentné zobrazenie QBER s kvantovým overením
        if self.mode == "dishonest_prover" and not self.quantum_verification:
            self.qber = 1.0  # 100%, ak kvantové overenie zlyhá

        # Celkový výsledok overenia
        self.verification_result = (self.timing_verification_v1 and
                                    self.timing_verification_v2 and
                                    self.quantum_verification)

        # Uloženie výsledku kola
        result_details = {
            'timing_v1_correct': self.timing_verification_v1,
            'timing_v2_correct': self.timing_verification_v2,
            'quantum_correct': self.quantum_verification,
            'overall': self.verification_result,
            'expected_time_v1': self.expected_time_v1,
            'expected_time_v2': self.expected_time_v2,
            'actual_time_v1': self.response_time_v1,
            'actual_time_v2': self.response_time_v2,
            'time_difference_v1': self.time_difference_v1,
            'time_difference_v2': self.time_difference_v2,
            'qubit_type': self.qubit_type,
            'basis': self.basis,
            'measurement_result': self.measurement_result,
            'expected_measurement': self.expected_measurement
        }

        self.round_results.append(result_details)

        # Uloženie výsledku kola
        if self.verification_result:
            self.successful_rounds += 1

        return result_details

    def calculate_qber(self):
        """Výpočet QBER (Quantum Bit Error Rate) z dostupných výsledkov."""
        if not self.round_results:
            self.qber = 0.0
            return self.qber

        # Počet kvantových chýb (len kvantové merania, nie časové)
        quantum_errors = sum(1 for r in self.round_results if not r['quantum_correct'])

        # Výpočet QBER
        total_rounds = len(self.round_results)

        # V prvom kole pri nečestnom dôkazníkovi, nastavíme QBER na 100% ak je kvantové overenie neúspešné
        if self.mode == "dishonest_prover" and total_rounds == 1 and not self.quantum_verification:
            self.qber = 1.0  # 100%
        else:
            self.qber = quantum_errors / total_rounds

        # Ak QBER presahuje prah, detekuje sa podvod
        if self.qber > self.qber_threshold and total_rounds >= 1:
            # V skutočnosti stačí jedno kolo na detekciu podvodu
            self.verification_result = False

        return self.qber

    def reset_animation_state(self):
        """Reset stavov animácie."""
        self.signal_position_v1 = 0
        self.signal_position_v2 = 0
        self.response_position_v1 = 0
        self.response_position_v2 = 0
        self.response_active_v1 = False
        self.response_active_v2 = False
        self.v1_signal_active = False
        self.v2_signal_active = False

    def reset_protocol(self):
        """Reset stavu protokolu pre nový beh."""
        self.current_round = 0
        self.protocol_step = 0
        self.successful_rounds = 0
        self.round_results = []
        self.animation_time = 0.0
        self.animation_v1_signal_start_time = 0.0
        self.animation_v2_signal_start_time = 0.0
        self.animation_response_v1_start_time = 0.0
        self.animation_response_v2_start_time = 0.0
        self.qber = 0.0
        self.reset_animation_state()

        # Reset klasického kanála
        self.classical_channel.clear()
        self.classical_messages = []

        # Reset výsledkov overenia
        self.timing_verification_v1 = False
        self.timing_verification_v2 = False
        self.quantum_verification = False
        self.time_difference_v1 = 0
        self.time_difference_v2 = 0

    def get_current_state(self):
        """Získanie aktuálneho stavu protokolu pre zobrazenie."""
        if self.mode == "single":
            step_names = self.protocol_steps
        elif self.mode == "dishonest_prover":
            step_names = self.dishonest_prover_steps

        current_step_name = step_names[self.protocol_step] if self.protocol_step < len(step_names) else "Dokončené"

        return {
            'round': self.current_round,
            'total_rounds': self.round_count,
            'step': self.protocol_step,
            'step_name': current_step_name,
            'basis': self.basis,
            'qubit_type': self.qubit_type,
            'measurement_result': self.measurement_result,
            'expected_measurement': self.expected_measurement,
            'is_honest': self.is_honest_prover,
            'verification_result': self.verification_result,
            'successful_rounds': self.successful_rounds,
            'success_rate': self.successful_rounds / max(1, self.current_round) if self.current_round > 0 else 0,
            'animation_time': self.animation_time,
            'signal_position_v1': self.signal_position_v1,
            'signal_position_v2': self.signal_position_v2,
            'response_position_v1': self.response_position_v1,
            'response_position_v2': self.response_position_v2,
            'response_active_v1': self.response_active_v1,
            'response_active_v2': self.response_active_v2,
            'expected_time_v1': self.expected_time_v1,
            'expected_time_v2': self.expected_time_v2,
            'response_time_v1': self.response_time_v1,
            'response_time_v2': self.response_time_v2,
            'mode': self.mode,
            'v1_signal_active': self.v1_signal_active,
            'v2_signal_active': self.v2_signal_active,
            # Pridané detaily overenia
            'timing_verification_v1': self.timing_verification_v1,
            'timing_verification_v2': self.timing_verification_v2,
            'quantum_verification': self.quantum_verification,
            'time_difference_v1': self.time_difference_v1,
            'time_difference_v2': self.time_difference_v2,
            'qber': self.qber,
            # Pridané informácie o skutočnej polohe pre nečestného dôkazníka
            'distance_v1_to_prover': self.distance_v1_to_prover,
            'distance_prover_to_v2': self.distance_prover_to_v2,
            'actual_distance_v1_to_prover': self.actual_distance_v1_to_prover,
            'actual_distance_prover_to_v2': self.actual_distance_prover_to_v2,
            # Pridané správy klasického kanála
            'classical_messages': self.classical_messages
        }

    def get_qubit_state_name(self, qubit_type):
        """Získanie názvu qubitového stavu pre zobrazenie."""
        states = {
            0: "|0⟩",
            1: "|1⟩",
            2: "|+⟩",
            3: "|−⟩"
        }
        return states.get(qubit_type, "Neznámy")

    def get_basis_name(self, basis):
        """Získanie názvu bázy pre zobrazenie."""
        bases = {
            0: "Z-báza {|0⟩,|1⟩}",
            1: "X-báza {|+⟩,|−⟩}"
        }
        return bases.get(basis, "Neznáma")

class QPVVisualizationWidget(QWidget):
    """Widget pre vizualizáciu protokolu kvantového overovania polohy."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 300)
        self.setStyleSheet("background-color: #fafafa; border: 1px solid #ccc;")

        # Inicializácia stavu
        self.protocol_state = {
            'step': 0,
            'basis': 0,
            'qubit_type': 0,
            'signal_position_v1': 0,
            'signal_position_v2': 0,
            'response_position_v1': 0,
            'response_position_v2': 0,
            'response_active_v1': False,
            'response_active_v2': False,
            'verification_result': False,
            'is_honest': True,
            'mode': 'single',
            'v1_signal_active': False,
            'v2_signal_active': False,
            'timing_verification_v1': False,
            'timing_verification_v2': False,
            'quantum_verification': False,
            'time_difference_v1': 0,
            'time_difference_v2': 0,
            'qber': 0.0,
            'distance_v1_to_prover': 100,
            'distance_prover_to_v2': 100,
            'actual_distance_v1_to_prover': 150,
            'actual_distance_prover_to_v2': 50,
            'classical_messages': []
        }

        # Režim vizualizácie (single/dishonest_prover)
        self.mode = "single"

    def set_mode(self, mode):
        """Nastavenie režimu vizualizácie."""
        self.mode = mode
        self.update()

    def set_protocol_state(self, state):
        """Aktualizácia vizualizácie s novým stavom protokolu."""
        self.protocol_state = state
        if 'mode' in state:
            self.mode = state['mode']
        self.update()

    def reset(self):
        """Reset stavu vizualizácie."""
        self.protocol_state = {
            'step': 0,
            'basis': 0,
            'qubit_type': 0,
            'signal_position_v1': 0,
            'signal_position_v2': 0,
            'response_position_v1': 0,
            'response_position_v2': 0,
            'response_active_v1': False,
            'response_active_v2': False,
            'verification_result': False,
            'is_honest': True,
            'mode': self.mode,
            'v1_signal_active': False,
            'v2_signal_active': False,
            'timing_verification_v1': False,
            'timing_verification_v2': False,
            'quantum_verification': False,
            'time_difference_v1': 0,
            'time_difference_v2': 0,
            'qber': 0.0,
            'distance_v1_to_prover': 100,
            'distance_prover_to_v2': 100,
            'actual_distance_v1_to_prover': 150,
            'actual_distance_prover_to_v2': 50,
            'classical_messages': []
        }
        self.update()

    def paintEvent(self, event):
        """Kreslenie vizualizácie QPV."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            w = self.width()
            h = self.height()

            # Kreslenie pozadia
            painter.fillRect(0, 0, w, h, QColor(250, 250, 250))

            if self.mode == "single":
                self.draw_single_mode(painter, w, h)
            elif self.mode == "dishonest_prover":
                self.draw_dishonest_mode(painter, w, h)

            # Kreslenie vysvetlenia protokolu
            self.draw_protocol_explanation(painter, w, h)

            # Kreslenie správ klasického kanála
            if 'classical_messages' in self.protocol_state and self.protocol_state['classical_messages']:
                self.draw_classical_communication(painter, w, h)

        except Exception as e:
            # Kreslenie chybovej správy, ak niečo zlyhá
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawText(10, 30, f"Chyba vizualizácie: {str(e)}")

    def draw_classical_communication(self, painter, w, h):
        """Kreslenie správ klasického komunikačného kanála."""
        messages = self.protocol_state['classical_messages']
        message_y = h * 0.7  # Presne rovnaká výška ako vysvetlenie protokolu
        message_x = w * 0.53  # Väčší odstup od ľavej časti
        message_width = w * 0.45  # Trochu širší priestor pre klasický kanál
        line_height = 18  # Definujeme line_height priamo v tejto metóde

        # Pridanie nadpisu pre sekciu klasického kanálu
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(message_x, message_y - 25, message_width, 20),
                         Qt.AlignmentFlag.AlignLeft, "Klasický komunikačný kanál:")

        # Ak nie sú žiadne správy, zobraziť základné kroky klasického kanálu
        if not messages or len(messages) == 0:
            default_messages = [
                "1. Dôkazník → Overovatelia: Deklarácia polohy",
                "2. V1 ↔ V2: Synchronizácia hodín a výmena parametrov protokolu",
                "3. V1 → Dôkazník: Informácia o vysielanom kvantovom stave ψ"
                "4. V2 → Dôkazník: Informácia o meracej báze",
                "5. Dôkazník → Overovatelia: Výsledok merania",
                "6. V1 ↔ V2: Výmena zaznamenaných časov príchodu odpovede"
                "7. V1 ↔ V2: Výpočet časových rozdielov a kvantovej chybovosti",
                "8. Overovatelia → Dôkazník: Výsledok overenia"
            ]
            painter.setFont(QFont("Arial", 9))
            for i, msg in enumerate(default_messages):
                painter.drawText(QRectF(message_x, message_y + i * line_height, message_width, line_height),
                                 Qt.AlignmentFlag.AlignLeft, msg)
        else:
            # Kreslenie skutočných správ klasického kanálu
            painter.setFont(QFont("Arial", 9))
            for i, msg in enumerate(messages):
                painter.drawText(QRectF(message_x, message_y + i * line_height, message_width, line_height),
                                 Qt.AlignmentFlag.AlignLeft, msg)

    def draw_single_mode(self, painter, w, h):
        """Kreslenie režimu s jedným dôkazníkom."""
        # Výpočet pozícií
        v1_x = w * 0.1
        v2_x = w * 0.9
        prover_x = w * 0.5
        entity_y = h * 0.4
        timeline_y = h * 0.6

        # Kreslenie časovej osi
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(int(v1_x), int(timeline_y), int(v2_x), int(timeline_y))

        # Kreslenie entít
        self.draw_entity(painter, v1_x, entity_y, "Overovateľ 1", QColor(0, 100, 200))
        self.draw_entity(painter, v2_x, entity_y, "Overovateľ 2", QColor(0, 100, 200))

        # Kreslenie dôkazníka s farbou na základe poctivosti
        prover_color = QColor(0, 150, 0) if self.protocol_state['is_honest'] else QColor(200, 0, 0)
        self.draw_entity(painter, prover_x, entity_y, "Dôkazník", prover_color)

        # Zobrazenie deklarovaných vzdialeností
        dist_v1 = self.protocol_state.get('distance_v1_to_prover', 100)
        dist_v2 = self.protocol_state.get('distance_prover_to_v2', 100)

        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(int((v1_x + prover_x) / 2 - 50), int(timeline_y + 20),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"{dist_v1} km")
        painter.drawText(int((prover_x + v2_x) / 2 - 50), int(timeline_y + 20),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"{dist_v2} km")

        # Kreslenie vertikálnych pozičných značiek
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(v1_x), int(entity_y + 30), int(v1_x), int(timeline_y))
        painter.drawLine(int(prover_x), int(entity_y + 30), int(prover_x), int(timeline_y))
        painter.drawLine(int(v2_x), int(entity_y + 30), int(v2_x), int(timeline_y))

        # Získanie aktuálneho kroku protokolu
        step = self.protocol_state['step']

        # Zobrazenie vysielaného kvantového stavu nad Overovateľom 1
        if step >= 1:
            qubit_type = self.protocol_state['qubit_type']
            qubit_names = {0: "|0⟩", 1: "|1⟩", 2: "|+⟩", 3: "|−⟩"}
            qubit_state = qubit_names.get(qubit_type, "?")

            # Pridať vysvetľujúci nadpis "Vysiela:"
            painter.setPen(QPen(QColor(200, 0, 0), 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(int(v1_x - 40), int(entity_y - 90), 80, 20, Qt.AlignmentFlag.AlignCenter, "Vysiela:")

            # Zobraziť samotný kvantový stav s výraznejším fontom
            painter.setPen(QPen(QColor(200, 0, 0), 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(v1_x - 40), int(entity_y - 70), 80, 20, Qt.AlignmentFlag.AlignCenter,
                             f"ψ = {qubit_state}")

        # Kreslenie qubitového signálu od V1 k dôkazníkovi
        if self.protocol_state.get('v1_signal_active', False):
            signal_pos_v1 = self.protocol_state['signal_position_v1']
            if signal_pos_v1 > 0:
                signal_x = v1_x + (prover_x - v1_x) * signal_pos_v1
                self.draw_signal(painter, signal_x, timeline_y, "ψ", QColor(255, 0, 0))

        # Kreslenie bázy od V2 k dôkazníkovi
        if self.protocol_state.get('v2_signal_active', False):
            signal_pos_v2 = self.protocol_state['signal_position_v2']
            if signal_pos_v2 > 0:
                signal_x = v2_x - (v2_x - prover_x) * signal_pos_v2
                basis_symbol = "Z" if self.protocol_state['basis'] == 0 else "X"
                self.draw_signal(painter, signal_x, timeline_y, basis_symbol, QColor(0, 0, 255))

        # Kreslenie signálov odpovede
        if self.protocol_state['response_active_v1']:
            response_pos = self.protocol_state['response_position_v1']
            if response_pos > 0:
                # Odpoveď k Overovateľovi 1
                signal_x = prover_x - (prover_x - v1_x) * response_pos
                self.draw_signal(painter, signal_x, timeline_y, str(self.protocol_state.get('measurement_result', '?')),
                                 QColor(255, 165, 0))

        if self.protocol_state['response_active_v2']:
            response_pos = self.protocol_state['response_position_v2']
            if response_pos > 0:
                # Odpoveď k Overovateľovi 2
                signal_x = prover_x + (v2_x - prover_x) * response_pos
                self.draw_signal(painter, signal_x, timeline_y, str(self.protocol_state.get('measurement_result', '?')),
                                 QColor(255, 165, 0))

        # Zobrazenie výsledkov overenia v jednom riadku
        if step >= 6:
            # Pozícia riadku s výsledkami
            result_y = 80  # Výška riadku s výsledkami pod textom kroku

            # Získanie všetkých výsledkov
            v1_result = "✓ ČASOVÉ OVERENIE V1" if self.protocol_state[
                'timing_verification_v1'] else "✗ ČASOVÉ OVERENIE V1"
            v1_time = f"({self.protocol_state.get('time_difference_v1', 0) * 1000:.3f} ms)"

            v2_result = "✓ ČASOVÉ OVERENIE V2" if self.protocol_state[
                'timing_verification_v2'] else "✗ ČASOVÉ OVERENIE V2"
            v2_time = f"({self.protocol_state.get('time_difference_v2', 0) * 1000:.3f} ms)"

            qm_result = "✓ KVANTOVÉ OVERENIE" if self.protocol_state['quantum_verification'] else "✗ KVANTOVÉ OVERENIE"

            overall = "OVERENÉ" if self.protocol_state['verification_result'] else "NEÚSPEŠNÉ"
            qber = f"QBER: {self.protocol_state.get('qber', 0.0):.0%}"

            # Farby výsledkov
            v1_color = QColor(0, 150, 0) if self.protocol_state['timing_verification_v1'] else QColor(200, 0, 0)
            v2_color = QColor(0, 150, 0) if self.protocol_state['timing_verification_v2'] else QColor(200, 0, 0)
            qm_color = QColor(0, 150, 0) if self.protocol_state['quantum_verification'] else QColor(200, 0, 0)
            overall_color = QColor(0, 150, 0) if self.protocol_state['verification_result'] else QColor(200, 0, 0)
            qber_color = QColor(0, 150, 0) if self.protocol_state.get('qber', 0.0) < 0.25 else QColor(200, 0, 0)

            # Kreslenie hlavného výsledku
            painter.setPen(QPen(overall_color, 2))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            painter.drawText(10, result_y - 30, w - 20, 30, Qt.AlignmentFlag.AlignCenter, overall)

            # Veľkosť celého priestoru na riadok
            total_width = w - 40  # 20px okraj z každej strany

            # Stred každého bloku
            center_v1 = 20 + total_width * 0.2
            center_v2 = 20 + total_width * 0.5
            center_qm = 20 + total_width * 0.8

            # Kreslenie výsledku V1 s časom
            painter.setPen(QPen(v1_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_v1 - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, v1_result)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(center_v1 - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, v1_time)

            # Kreslenie výsledku V2 s časom
            painter.setPen(QPen(v2_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_v2 - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, v2_result)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(center_v2 - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, v2_time)

            # Kreslenie výsledku QM a QBER
            painter.setPen(QPen(qm_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_qm - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, qm_result)
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(qber_color, 1))
            painter.drawText(int(center_qm - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, qber)

        # Kreslenie hodnoty bázy merania
        if step >= 2:
            basis_value = self.protocol_state['basis']
            basis_name = "Z-báza {|0⟩, |1⟩}" if basis_value == 0 else "X-báza {|+⟩, |−⟩}"

            painter.setPen(QPen(QColor(0, 0, 200), 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(int(v2_x - 80), int(entity_y - 90), 160, 20, Qt.AlignmentFlag.AlignCenter, "Vysiela:")

            painter.setPen(QPen(QColor(0, 0, 200), 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(v2_x - 80), int(entity_y - 70), 160, 20, Qt.AlignmentFlag.AlignCenter,
                             f"Báza: {basis_name}")

        # Kreslenie kroku protokolu
        if 'step_name' in self.protocol_state:
            step_name = self.protocol_state['step_name']
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(10, 20, w - 20, 30, Qt.AlignmentFlag.AlignCenter, f"Krok {step + 1}: {step_name}")

    def draw_dishonest_mode(self, painter, w, h):
        """Kreslenie režimu s nečestným dôkazníkom."""
        # Výpočet pozícií
        v1_x = w * 0.1
        v2_x = w * 0.9
        prover_x = w * 0.5
        entity_y = h * 0.4
        timeline_y = h * 0.6

        # Pozícia skutočného dôkazníka-vypočítanie na základe skutočných vzdialeností
        decl_dist_v1 = self.protocol_state.get('distance_v1_to_prover', 100)
        decl_dist_v2 = self.protocol_state.get('distance_prover_to_v2', 100)
        act_dist_v1 = self.protocol_state.get('actual_distance_v1_to_prover', 150)
        act_dist_v2 = self.protocol_state.get('actual_distance_prover_to_v2', 50)

        total_decl_dist = decl_dist_v1 + decl_dist_v2
        total_act_dist = act_dist_v1 + act_dist_v2

        # Vypočítanie x pozície skutočného dôkazníka na základe pomeru vzdialeností
        actual_prover_x_ratio = act_dist_v1 / max(1, total_act_dist)
        actual_prover_x = v1_x + (v2_x - v1_x) * actual_prover_x_ratio

        # Deklarovaná pozícia dôkazníka (stred)
        declared_prover_x = prover_x

        # Kreslenie časovej osi
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(int(v1_x), int(timeline_y), int(v2_x), int(timeline_y))

        # Kreslenie entít
        self.draw_entity(painter, v1_x, entity_y, "Overovateľ 1", QColor(0, 100, 200))
        self.draw_entity(painter, v2_x, entity_y, "Overovateľ 2", QColor(0, 100, 200))

        # Kreslenie deklarovanej pozície dôkazníka (prázdny obrys)
        painter.setPen(QPen(QColor(200, 0, 0), 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Hlava
        head_radius = 10
        painter.drawEllipse(int(declared_prover_x - head_radius), int(entity_y - 25 - head_radius),
                            head_radius * 2, head_radius * 2)
        # Telo
        painter.drawRect(int(declared_prover_x - 15), int(entity_y - 25), 30, 25)

        # Popis deklarovanej pozície
        painter.setPen(QPen(QColor(200, 0, 0), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Tučné písmo
        painter.drawText(int(declared_prover_x - 65), int(entity_y + 10), 130, 20,
                         Qt.AlignmentFlag.AlignCenter, "Deklarovaná poloha")

        # Kreslenie skutočného dôkazníka (plný)
        painter.setPen(QPen(QColor(200, 0, 0), 2))
        painter.setBrush(QColor(200, 0, 0, 100))

        # Hlava
        painter.drawEllipse(int(actual_prover_x - head_radius), int(entity_y - 25 - head_radius),
                            head_radius * 2, head_radius * 2)
        # Telo
        painter.drawRect(int(actual_prover_x - 15), int(entity_y - 25), 30, 25)

        # Popis skutočnej pozície
        painter.setPen(QPen(QColor(200, 0, 0), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Tučné písmo
        painter.drawText(int(actual_prover_x - 60), int(entity_y + 25), 120, 20,
                         Qt.AlignmentFlag.AlignCenter, "Nečestný dôkazník")

        # Zobrazenie deklarovaných vzdialeností
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(int((v1_x + declared_prover_x) / 2 - 50), int(timeline_y + 20),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"Dekl: {decl_dist_v1} km")
        painter.drawText(int((declared_prover_x + v2_x) / 2 - 50), int(timeline_y + 20),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"Dekl: {decl_dist_v2} km")

        # Zobrazenie skutočných vzdialeností
        painter.setPen(QPen(QColor(200, 0, 0), 1))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(int((v1_x + actual_prover_x) / 2 - 50), int(timeline_y + 35),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"Skut: {act_dist_v1} km")
        painter.drawText(int((actual_prover_x + v2_x) / 2 - 50), int(timeline_y + 35),
                         100, 20, Qt.AlignmentFlag.AlignCenter, f"Skut: {act_dist_v2} km")

        # Kreslenie vertikálnych pozičných značiek
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(v1_x), int(entity_y + 30), int(v1_x), int(timeline_y))
        painter.drawLine(int(declared_prover_x), int(entity_y + 30), int(declared_prover_x), int(timeline_y))
        painter.drawLine(int(v2_x), int(entity_y + 30), int(v2_x), int(timeline_y))
        painter.drawLine(int(actual_prover_x), int(entity_y + 30), int(actual_prover_x), int(timeline_y))

        # Získanie aktuálneho kroku protokolu
        step = self.protocol_state['step']

        # Zobrazenie vysielaného kvantového stavu nad Overovateľom 1
        if step >= 1:
            qubit_type = self.protocol_state['qubit_type']
            qubit_names = {0: "|0⟩", 1: "|1⟩", 2: "|+⟩", 3: "|−⟩"}
            qubit_state = qubit_names.get(qubit_type, "?")

            # Pridať vysvetľujúci nadpis "Vysiela:"
            painter.setPen(QPen(QColor(200, 0, 0), 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(int(v1_x - 40), int(entity_y - 90), 80, 20, Qt.AlignmentFlag.AlignCenter, "Vysiela:")

            # Zobraziť samotný kvantový stav s výraznejším fontom
            painter.setPen(QPen(QColor(200, 0, 0), 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(v1_x - 40), int(entity_y - 70), 80, 20, Qt.AlignmentFlag.AlignCenter,
                             f"ψ = {qubit_state}")

        # Kreslenie qubitového signálu od V1 k dôkazníkovi
        if self.protocol_state.get('v1_signal_active', False):
            signal_pos_v1 = self.protocol_state['signal_position_v1']
            if signal_pos_v1 > 0:
                # Signál cestuje k SKUTOČNEJ polohe
                signal_x = v1_x + (actual_prover_x - v1_x) * signal_pos_v1
                self.draw_signal(painter, signal_x, timeline_y, "ψ", QColor(255, 0, 0))

        # Kreslenie bázy od V2 k dôkazníkovi
        if self.protocol_state.get('v2_signal_active', False):
            signal_pos_v2 = self.protocol_state['signal_position_v2']
            if signal_pos_v2 > 0:
                # Signál cestuje k SKUTOČNEJ polohe
                signal_x = v2_x - (v2_x - actual_prover_x) * signal_pos_v2
                basis_symbol = "Z" if self.protocol_state['basis'] == 0 else "X"
                self.draw_signal(painter, signal_x, timeline_y, basis_symbol, QColor(0, 0, 255))

        # Kreslenie signálov odpovede
        if self.protocol_state['response_active_v1']:
            response_pos = self.protocol_state['response_position_v1']
            if response_pos > 0:
                # Odpoveď k Overovateľovi 1 od SKUTOČNEJ polohy
                signal_x = actual_prover_x - (actual_prover_x - v1_x) * response_pos
                self.draw_signal(painter, signal_x, timeline_y, str(self.protocol_state.get('measurement_result', '?')),
                                 QColor(255, 165, 0))

        if self.protocol_state['response_active_v2']:
            response_pos = self.protocol_state['response_position_v2']
            if response_pos > 0:
                # Odpoveď k Overovateľovi 2 od SKUTOČNEJ polohy
                signal_x = actual_prover_x + (v2_x - actual_prover_x) * response_pos
                self.draw_signal(painter, signal_x, timeline_y, str(self.protocol_state.get('measurement_result', '?')),
                                 QColor(255, 165, 0))

        # Zobrazenie výsledkov v jednom riadku-režim podvodu
        if step >= 6 and self.mode == "dishonest_prover":
            # Posunutie výsledkov nižšie pod text kroku
            result_y = 80

            # Získanie všetkých výsledkov
            v1_result = "✓ ČASOVÉ OVERENIE V1" if self.protocol_state[
                'timing_verification_v1'] else "✗ ČASOVÉ OVERENIE V1"
            v1_time = f"({self.protocol_state.get('time_difference_v1', 0) * 1000:.3f} ms)"

            v2_result = "✓ ČASOVÉ OVERENIE V2" if self.protocol_state[
                'timing_verification_v2'] else "✗ ČASOVÉ OVERENIE V2"
            v2_time = f"({self.protocol_state.get('time_difference_v2', 0) * 1000:.3f} ms)"

            qm_result = "✓ KVANTOVÉ OVERENIE" if self.protocol_state['quantum_verification'] else "✗ KVANTOVÉ OVERENIE"

            overall = "OVERENÉ" if self.protocol_state['verification_result'] else "NEÚSPEŠNÉ"
            qber = f"QBER: {self.protocol_state.get('qber', 0.0):.0%}"

            # Farby výsledkov
            v1_color = QColor(0, 150, 0) if self.protocol_state['timing_verification_v1'] else QColor(200, 0, 0)
            v2_color = QColor(0, 150, 0) if self.protocol_state['timing_verification_v2'] else QColor(200, 0, 0)
            qm_color = QColor(0, 150, 0) if self.protocol_state['quantum_verification'] else QColor(200, 0, 0)
            overall_color = QColor(0, 150, 0) if self.protocol_state['verification_result'] else QColor(200, 0, 0)
            qber_color = QColor(0, 150, 0) if self.protocol_state.get('qber', 0.0) < 0.25 else QColor(200, 0, 0)

            # Kreslenie hlavného výsledku
            painter.setPen(QPen(overall_color, 2))
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            painter.drawText(10, result_y - 30, w - 20, 30, Qt.AlignmentFlag.AlignCenter, overall)

            # Veľkosť celého priestoru na riadok
            total_width = w - 40

            # Stred každého bloku
            center_v1 = 20 + total_width * 0.2
            center_v2 = 20 + total_width * 0.5
            center_qm = 20 + total_width * 0.8

            # Kreslenie výsledku V1 s časom
            painter.setPen(QPen(v1_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_v1 - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, v1_result)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(center_v1 - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, v1_time)

            # Kreslenie výsledku V2 s časom
            painter.setPen(QPen(v2_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_v2 - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, v2_result)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(center_v2 - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, v2_time)

            # Kreslenie výsledku QM a QBER
            painter.setPen(QPen(qm_color, 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(center_qm - 150), result_y, 300, 20, Qt.AlignmentFlag.AlignCenter, qm_result)
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(qber_color, 1))
            painter.drawText(int(center_qm - 150), result_y + 20, 300, 15, Qt.AlignmentFlag.AlignCenter, qber)

        # Kreslenie hodnoty bázy merania
        if step >= 2:
            basis_value = self.protocol_state['basis']
            basis_name = "Z-báza {|0⟩, |1⟩}" if basis_value == 0 else "X-báza {|+⟩, |−⟩}"

            # Pridať vysvetľujúci nadpis "Vysiela:"
            painter.setPen(QPen(QColor(0, 0, 200), 1))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(int(v2_x - 80), int(entity_y - 90), 160, 20, Qt.AlignmentFlag.AlignCenter, "Vysiela:")

            # Zobraziť hodnotu bázy s výraznejším fontom
            painter.setPen(QPen(QColor(0, 0, 200), 1))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(v2_x - 80), int(entity_y - 70), 160, 20, Qt.AlignmentFlag.AlignCenter,
                             f"Báza: {basis_name}")

        # Kreslenie kroku protokolu
        if 'step_name' in self.protocol_state:
            step_name = self.protocol_state['step_name']
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(10, 20, w - 20, 30, Qt.AlignmentFlag.AlignCenter, f"Krok {step + 1}: {step_name}")

    def draw_protocol_explanation(self, painter, w, h):
        """Kreslenie vysvetlenia protokolu v spodnej časti."""
        explanation_y = h * 0.7
        explanation_width = w * 0.47 - 20  # Trochu zúžiť pre lepšie oddelenie

        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 9))

        if self.mode == "single":
            explanation_text = [
                "Kvantové overovanie polohy (QPV) umožňuje dôkaz geografickej polohy na základe kvantových princípov.",
                "1. Overovateľ 1 posiela kvantový stav ψ (jeden zo stavov |0⟩, |1⟩, |+⟩, |−⟩)",
                "2. Overovateľ 2 posiela bázu merania (Z-báza {|0⟩,|1⟩} alebo X-báza {|+⟩,|−⟩})",
                "3. Dôkazník musí zmerať kvantový stav v zadanej báze a poslať výsledok (0/1) obom overovateľom",
                "4. Overenie je založené na presnom časovaní a správnosti výsledku merania",
                "5. Viaceré kolá sú potrebné pre štatistické vyhodnotenie pomocou QBER (Quantum Bit Error Rate)"
            ]
        elif self.mode == "dishonest_prover":
            explanation_text = [
                "Nečestný dôkazník sa nachádza na inej pozícii, než deklaruje:",
                "1. Dôkazník klame o svojej polohe, ale prijíma a meria kvantový stav správne",
                "2. Pri presune signálov dochádza k časovým rozdielom oproti očakávaným hodnotám",
                "3. Odchýlka medzi skutočnou a deklarovanou polohou spôsobuje oneskorenie alebo skorší príchod odpovede",
                "4. Čím väčší je rozdiel medzi deklarovanou a skutočnou polohou, tým ľahšie je podvod odhaliť",
                "5. Detekcia podvodu sa opiera o presné meranie času (nanosekúndové rozdiely)",
                "6. Kvantový stav je meraný správne, ale časovanie odpovede odhalí nepravdivú polohu"
            ]

        # Pridanie nadpisu pre sekciu kvantového protokolu
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(20, explanation_y - 25, explanation_width, 20),
                         Qt.AlignmentFlag.AlignLeft, "Kvantový protokol:")

        # Kreslenie vysvetlenia
        painter.setFont(QFont("Arial", 9))
        line_height = 18
        for i, line in enumerate(explanation_text):
            painter.drawText(QRectF(20, explanation_y + i * line_height, explanation_width, line_height),
                             Qt.AlignmentFlag.AlignLeft, line)

    def draw_entity(self, painter, x, y, label, color):
        """Kreslenie entity (overovateľ alebo dôkazník) vo vizualizácii."""
        # Kreslenie ikony osoby
        painter.setPen(QPen(color, 2))
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), 100))

        # Hlava
        head_radius = 10
        painter.drawEllipse(int(x - head_radius), int(y - 25 - head_radius), head_radius * 2, head_radius * 2)

        # Telo
        painter.drawRect(int(x - 15), int(y - 25), 30, 25)

        # Popis
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(int(x - 40), int(y + 10), 80, 20, Qt.AlignmentFlag.AlignCenter, label)

    def draw_signal(self, painter, x, y, label, color):
        """Kreslenie signálu (kvantového alebo klasického) vo vizualizácii."""
        # Kreslenie kruhu pre signál
        painter.setPen(QPen(color, 2))
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), 150))
        painter.drawEllipse(int(x - 10), int(y - 10), 20, 20)

        # Kreslenie popisu
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(int(x - 8), int(y - 8), 16, 16, Qt.AlignmentFlag.AlignCenter, label)