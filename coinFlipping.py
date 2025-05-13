import random
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt

class CoinFlipping(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.random_bits = []
        self.alice_orientation = None
        self.bob_orientation = None
        self.results = []
        self.measurement_results = []
        self.measurement_bases = []
        self.alice_bits = {'rektilineárna': [], 'diagonálna': []}

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        title_label = QLabel("Kvantový hod mincou")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title_label)

        self.info_label = QLabel("Spustite hru a pozrite si výsledky.")
        self.layout.addWidget(self.info_label)

        # Buttons
        self.button_layout = QHBoxLayout()

        self.start_button = QPushButton("Spustenie hry")
        self.start_button.clicked.connect(self.startGame)
        # Nastavíme pozadie pre start_button (napr. tmavošedá farba)
        self.start_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.start_button)

        self.alice_rect_button = QPushButton("Alice: Rektilineárna")
        self.alice_rect_button.clicked.connect(lambda: self.chooseAlice("rektilineárna"))
        # Nastavíme pozadie pre alice_rect_button (napr. modrá farba)
        self.alice_rect_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.alice_rect_button)

        self.alice_diag_button = QPushButton("Alice: Diagonálna")
        self.alice_diag_button.clicked.connect(lambda: self.chooseAlice("diagonálna"))
        # Nastavíme pozadie pre alice_diag_button (napr. zelená farba)
        self.alice_diag_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.alice_diag_button)

        self.measure_button = QPushButton("Meranie Boba")
        self.measure_button.clicked.connect(self.measureBob)
        # Nastavíme pozadie pre measure_button
        self.measure_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.measure_button)

        self.bob_rect_button = QPushButton("Bob: Rektilineárna")
        self.bob_rect_button.clicked.connect(lambda: self.chooseBob("rektilineárna"))
        # Nastavíme pozadie pre bob_rect_button
        self.bob_rect_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.bob_rect_button)

        self.bob_diag_button = QPushButton("Bob: Diagonálna")
        self.bob_diag_button.clicked.connect(lambda: self.chooseBob("diagonálna"))
        # Nastavíme pozadie pre bob_diag_button
        self.bob_diag_button.setStyleSheet("background-color: #4477cc; color: white;")
        self.button_layout.addWidget(self.bob_diag_button)

        self.layout.addLayout(self.button_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Aliciné bity", "Aliciná báza", "Bobová báza", "Bobové bity", "Meranie v rovnakej bázi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)  # Skryť vertikálnu hlavičku, aby sa neduplikovali čísla riadkov
        self.layout.addWidget(self.table)

    def opposite_orientation(self):
        if self.alice_orientation == 'rektilineárna':
            return 'diagonálna'
        elif self.alice_orientation == 'diagonálna':
            return 'rektilineárna'
        else:
            return None

    def start_game(self):
        self.random_bits = [random.choice([0, 1]) for _ in range(12)]
        self.alice_orientation = None
        self.bob_orientation = None
        self.results = []
        self.measurement_results = []
        self.measurement_bases = []
        self.alice_bits = {'rektilineárna': [], 'diagonálna': []}
        return {"Náhodné bity": self.random_bits}

    def startGame(self):
        data = self.start_game()
        self.info_label.setText("Alice vygenerovala sekvenciu bitov a volí si svoju bázu.")
        self.table.setRowCount(0)
        bits = data["Náhodné bity"]
        for i, b in enumerate(bits):
            self.table.insertRow(i)
            # Naplníme tabuľku
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 1, QTableWidgetItem(str(b)))
            self.table.setItem(i, 2, QTableWidgetItem("N/A"))
            self.table.setItem(i, 3, QTableWidgetItem("N/A"))
            self.table.setItem(i, 4, QTableWidgetItem("N/A"))
            self.table.setItem(i, 5, QTableWidgetItem("N/A"))

        # Vycentrujeme všetky položky v tabuľke
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def choose_alice_orientation(self, orientation):
        if orientation not in ['rektilineárna', 'diagonálna']:
            return "Neplatná orientácia."
        self.alice_orientation = orientation
        # Alice encodes bits in the chosen orientation
        self.alice_bits[orientation] = self.random_bits.copy()
        other_orientation = self.opposite_orientation()
        self.alice_bits[other_orientation] = [random.choice([0, 1]) for _ in self.random_bits]
        return f"Alice si vybrala bázu. Bob začne meranie."

    def chooseAlice(self, orientation):
        msg = self.choose_alice_orientation(orientation)
        self.info_label.setText(msg)

    def measure_bob(self):
        if self.alice_orientation is None:
            return "Alice ešte nevybrala svoju bázu."
        if len(self.measurement_results) > 0:
            return "Bob už vykonal meranie."

        self.measurement_results = [True]*6 + [False]*6
        random.shuffle(self.measurement_results)
        self.measurement_bases = [
            self.alice_orientation if correct else self.opposite_orientation()
            for correct in self.measurement_results
        ]
        return "Bob vykonal meranie polovice fotónov v správnej báze a polovice v nesprávnej báze. Háda správnu bázu."

    def measureBob(self):
        msg = self.measure_bob()
        self.info_label.setText(msg)

    def choose_bob_orientation(self, orientation):
        if orientation not in ['rektilineárna', 'diagonálna']:
            return "Neplatná orientácia."
        if not self.measurement_results:
            return "Bob musí najprv vykonať meranie."
        self.bob_orientation = orientation
        self.calculate_results()
        if self.bob_orientation == self.alice_orientation:
            outcome = f"Bob uhádol správnu bázu: {self.bob_orientation}."
        else:
            outcome = f"Bob uhádol nesprávnu bázu: {self.bob_orientation}."
        return outcome

    def chooseBob(self, orientation):
        msg = self.choose_bob_orientation(orientation)
        self.info_label.setText(msg)

        # Odhalíme Alicinu orientáciu
        alice_or = self.reveal_alice_orientation()
        data = json.loads(alice_or)
        self.info_label.setText(self.info_label.text())

        # Ak správa obsahuje "uhádol správnu bázu" alebo "uhádol nesprávnu bázu", odhalíme bity
        if "uhádol správnu bázu" in msg or "uhádol nesprávnu bázu" in msg:
            bits = self.reveal_alice_bits()
            bits_data = json.loads(bits)["Alice_bits"]
            self.info_label.setText(self.info_label.text() + " Alice odhalila svoje bity v zvolenej báze: " + ", ".join(map(str,bits_data)) + ".")

        self.updateResultsTable()

    def calculate_results(self):
        if self.alice_orientation is None or self.bob_orientation is None:
            return
        self.results = []
        for i, bit in enumerate(self.random_bits):
            if self.measurement_bases[i] == self.alice_orientation:
                # Bob meral v rovnakej báze ako Alice
                result_bit = self.alice_bits[self.alice_orientation][i]
            else:
                # Nesprávna báza
                result_bit = random.choice([0, 1])
            self.results.append(result_bit)

    def reveal_alice_orientation(self):
        if self.alice_orientation is None:
            return "Alice ešte nevybrala svoju bázu."
        return json.dumps({"Alice_orientation": self.alice_orientation})

    def reveal_alice_bits(self):
        if self.alice_orientation is None:
            return "Alice ešte nevybrala svoju bázu."
        return json.dumps({"Alice_bits": self.alice_bits[self.alice_orientation]})

    def reveal_all_alice_bits(self):
        if not self.random_bits:
            return "Hra ešte nebola spustená."
        return json.dumps({"Alice_all_bits": self.random_bits})

    def get_results(self):
        data = []
        for i, bit in enumerate(self.random_bits):
            alice_orientation = self.alice_orientation or "N/A"
            bob_orientation = self.measurement_bases[i] if i < len(self.measurement_bases) else "N/A"
            bob_bit = self.results[i] if i < len(self.results) else "N/A"
            alice_bit = self.alice_bits[self.alice_orientation][i] if self.alice_orientation else "N/A"
            measurement_correct = (bob_bit == alice_bit)
            data.append({
                "bit_number": i+1,
                "alice_bit": bit,
                "alice_orientation": alice_orientation,
                "bob_orientation": bob_orientation,
                "bob_bit": bob_bit,
                "measurement_correct": measurement_correct
            })
        return data

    def updateResultsTable(self):
        results = self.get_results()
        self.table.setRowCount(0)
        for i, item in enumerate(results):
            self.table.insertRow(i)

            bit_number_item = QTableWidgetItem(str(item["bit_number"]))
            bit_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, bit_number_item)

            alice_bit_item = QTableWidgetItem(str(item["alice_bit"]))
            alice_bit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, alice_bit_item)

            alice_orientation_item = QTableWidgetItem(item["alice_orientation"])
            alice_orientation_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, alice_orientation_item)

            bob_orientation_item = QTableWidgetItem(item["bob_orientation"])
            bob_orientation_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, bob_orientation_item)

            bob_bit_item = QTableWidgetItem(str(item["bob_bit"]))
            bob_bit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 4, bob_bit_item)

            # Meranie v rovnakej bázi
            same_base = (item["alice_orientation"] == item["bob_orientation"]) and (
                        item["alice_orientation"] in ['rektilineárna', 'diagonálna'])
            sameBaseDisplay = "Áno" if same_base else "Nie"
            sameBaseItem = QTableWidgetItem(sameBaseDisplay)
            sameBaseItem.setForeground(Qt.GlobalColor.green if same_base else Qt.GlobalColor.red)
            sameBaseItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 5, sameBaseItem)
