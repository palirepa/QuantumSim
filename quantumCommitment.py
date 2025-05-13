from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QRadioButton, QButtonGroup)
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QRectF


class QubitStateWidget(QWidget):
    """Widget pre zobrazenie stavu qubitu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.basis = '-'  # Báza (X alebo Z)
        self.bit = 0  # Bit (0 alebo 1)
        self.active = False  # Či je qubit aktívny

    def setState(self, basis, bit, active=True):
        """Nastaví stav qubitu"""
        self.basis = basis
        self.bit = bit
        self.active = active
        self.update()  # Vyžiada prekresľovanie

    def paintEvent(self, event):
        """Kreslenie stavu qubitu"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Rozmery widgetu
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 5

        # Východiskové kreslenie - šedý kruh
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, 2 * radius, 2 * radius))

        # Ak je qubit aktívny, vykresli podľa bázy a stavu
        if self.active:
            color = QColor(228, 155, 15) if self.basis == 'X' else Qt.GlobalColor.green
            painter.setBrush(QBrush(color))

            # Pre bit 0 vykreslíme hornú polovicu, pre bit 1 dolnú polovicu
            if self.bit == 0:
                painter.drawPie(QRectF(center_x - radius, center_y - radius, 2 * radius, 2 * radius), 0, 180 * 16)
            else:
                painter.drawPie(QRectF(center_x - radius, center_y - radius, 2 * radius, 2 * radius), 180 * 16,
                                180 * 16)


class QuantumCommitment(QWidget):
    """Implementácia jednosmerného kvantového záväzkového protokolu."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Konfigurácia protokolu
        self.num_qubits = 3
        self.resetProtocol()

        # Inicializácia UI
        self.setupUI()

    def resetProtocol(self):
        """Resetuje stav protokolu na začiatok."""
        self.step = 0  # Aktuálny krok protokolu (0-5)
        self.aliceBit = None  # Alicin zvolený bit (0 alebo 1)
        self.randomBits = [0] * self.num_qubits  # Náhodné bity r
        self.bases = []  # Bázy pre qubity
        self.states = []  # Kvantové stavy
        self.verificationSuccess = None  # Výsledok verifikácie

    def setupUI(self):
        """Vytvorenie užívateľského rozhrania."""
        self.setWindowTitle("Kvantový záväzkový protokol")

        # Hlavný layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)

        # Sekcia pre nadpis a informácie
        infoBox = QGroupBox()
        infoLayout = QVBoxLayout(infoBox)

        # Nadpis
        title = QLabel("Kvantový záväzkový protokol")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        infoLayout.addWidget(title)

        # Informačný text
        self.infoLabel = QLabel("<b>Krok 1:</b> <b>Alice si vyberie bit (0 alebo 1).</b>")
        self.infoLabel.setFont(QFont("Arial", 12))
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infoLabel.setWordWrap(True)
        infoLayout.addWidget(self.infoLabel)

        # Kroky protokolu
        stepsLayout = QHBoxLayout()

        self.stepLabels = []
        stepTexts = ["1. Voľba bitu", "2. Náhodné bity", "3. Posielanie", "4. Uloženie", "5. Odhalenie", "6. Verifikácia"]

        for i, text in enumerate(stepTexts):
            stepLabel = QLabel(text)
            stepLabel.setFixedHeight(30)
            stepLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stepLabel.setStyleSheet(
                "background-color: lightgray; border-radius: 5px; margin: 2px; padding: 5px;"
            )
            stepsLayout.addWidget(stepLabel)
            self.stepLabels.append(stepLabel)

        infoLayout.addLayout(stepsLayout)
        mainLayout.addWidget(infoBox)

        # Hlavný obsah - ovládacie prvky a vizualizácia
        contentLayout = QHBoxLayout()

        # Panel ovládania
        controlBox = QGroupBox("Ovládanie")
        controlLayout = QVBoxLayout(controlBox)

        # Výber bitu pre Alicu
        bitGroup = QGroupBox("Alicin bit")
        bitLayout = QHBoxLayout(bitGroup)
        self.bit0Radio = QRadioButton("Bit 0 (XZX)")
        self.bit1Radio = QRadioButton("Bit 1 (ZXZ)")
        self.bitButtonGroup = QButtonGroup()
        self.bitButtonGroup.addButton(self.bit0Radio, 0)
        self.bitButtonGroup.addButton(self.bit1Radio, 1)
        bitLayout.addWidget(self.bit0Radio)
        bitLayout.addWidget(self.bit1Radio)
        bitGroup.setLayout(bitLayout)
        controlLayout.addWidget(bitGroup)

        # Nastavenie náhodných bitov
        randomGroup = QGroupBox("Náhodné bity (r)")
        randomLayout = QVBoxLayout(randomGroup)

        self.randomBitRadios = []
        for i in range(self.num_qubits):
            rowLayout = QHBoxLayout()
            label = QLabel(f"Bit {i + 1}:")
            rowLayout.addWidget(label)

            # Vytvorenie button group pre každý riadok
            bitGroup = QButtonGroup()

            bit0Radio = QRadioButton("0")
            bit1Radio = QRadioButton("1")

            # Pridanie do button group
            bitGroup.addButton(bit0Radio, 0)
            bitGroup.addButton(bit1Radio, 1)

            # Nastavenie predvoleného výberu
            bit0Radio.setChecked(True)

            rowLayout.addWidget(bit0Radio)
            rowLayout.addWidget(bit1Radio)
            randomLayout.addLayout(rowLayout)

            # Uloženie radio buttonov pre neskorší prístup
            self.randomBitRadios.append((bit0Radio, bit1Radio, bitGroup))

        randomGroup.setLayout(randomLayout)
        controlLayout.addWidget(randomGroup)

        # Tlačidlá
        buttonsLayout = QHBoxLayout()

        self.nextStepBtn = QPushButton("Ďalší krok")
        self.nextStepBtn.clicked.connect(self.nextStep)
        buttonsLayout.addWidget(self.nextStepBtn)

        self.resetBtn = QPushButton("Resetovať")
        self.resetBtn.clicked.connect(self.resetUI)
        buttonsLayout.addWidget(self.resetBtn)

        controlLayout.addLayout(buttonsLayout)

        # Pridanie zóny pre verifikačné výsledky
        self.verificationLabel = QLabel("Výsledky verifikácie sa zobrazia v kroku 6.")
        self.verificationLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verificationLabel.setWordWrap(True)
        controlLayout.addWidget(self.verificationLabel)

        contentLayout.addWidget(controlBox)

        # Vizualizácia
        visualizationBox = QGroupBox("Vizualizácia protokolu")
        visualizationLayout = QVBoxLayout(visualizationBox)

        # Nadpis pre účastníkov
        participantsLayout = QHBoxLayout()
        participantsLayout.setContentsMargins(0, 0, 0, 10)  # Pridanie spodného okraja (bottom margin)

        aliceLabel = QLabel("ALICE")
        aliceLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Zarovnanie doľava
        aliceLabel.setStyleSheet(
            "font-weight: bold; color: blue; padding-left: 10px; margin-top: 40px;")  # Posunutie nadol
        participantsLayout.addWidget(aliceLabel)

        for i in range(self.num_qubits):
            qubitLabel = QLabel(f"Qubit {i + 1}")
            qubitLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            participantsLayout.addWidget(qubitLabel)

        bobLabel = QLabel("BOB")
        bobLabel.setAlignment(Qt.AlignmentFlag.AlignRight)  # Zarovnanie doprava
        bobLabel.setStyleSheet(
            "font-weight: bold; color: red; padding-right: 15px; margin-top: 40px;")  # Posunutie nadol
        participantsLayout.addWidget(bobLabel)

        visualizationLayout.addLayout(participantsLayout)

        # Obsah vizualizácie
        visualContent = QHBoxLayout()

        # Ikona Alice
        aliceIcon = QLabel()
        aliceIcon.setFixedSize(60, 100)
        aliceIcon.setStyleSheet("""
            background-color: #AACCFF;
            border: 2px solid blue;
            border-radius: 10px;
        """)
        visualContent.addWidget(aliceIcon)

        # Qubity
        self.qubitWidgets = []
        for i in range(self.num_qubits):
            qubitBox = QGroupBox()
            qubitBox.setFixedWidth(120)
            qubitLayout = QVBoxLayout(qubitBox)

            # Báza a stav
            basisLabel = QLabel("Báza: -")
            basisLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qubitLayout.addWidget(basisLabel)

            stateLabel = QLabel("Stav: |0⟩")
            stateLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qubitLayout.addWidget(stateLabel)

            # Vizualizácia stavu - použijeme vlastnú triedu
            qubitStateWidget = QubitStateWidget()
            qubitLayout.addWidget(qubitStateWidget, alignment=Qt.AlignmentFlag.AlignCenter)

            visualContent.addWidget(qubitBox)
            self.qubitWidgets.append((basisLabel, stateLabel, qubitStateWidget))

        # Ikona Boba
        bobIcon = QLabel()
        bobIcon.setFixedSize(60, 100)
        bobIcon.setStyleSheet("""
            background-color: #FFCCAA;
            border: 2px solid darkred;
            border-radius: 10px;
        """)
        visualContent.addWidget(bobIcon)

        visualizationLayout.addLayout(visualContent)

        # Výsledok protokolu
        self.resultLabel = QLabel()
        self.resultLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resultLabel.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        visualizationLayout.addWidget(self.resultLabel)

        contentLayout.addWidget(visualizationBox)

        mainLayout.addLayout(contentLayout)

        # Inicializácia UI
        self.bit0Radio.setChecked(True)
        self.updateUI()

    def getRandomBits(self):
        """Získa aktuálne nastavené náhodné bity z UI."""
        randomBits = []
        for i, (bit0Radio, bit1Radio, bitGroup) in enumerate(self.randomBitRadios):
            # Explicitne kontrolujeme, ktorý button je vybraný
            checkedButton = bitGroup.checkedButton()
            bit = 0 if checkedButton == bit0Radio else 1
            randomBits.append(bit)
        return randomBits

    def updateUI(self):
        """Aktualizuje UI podľa aktuálneho stavu protokolu."""
        # Aktualizácia indikátorov krokov
        for i, label in enumerate(self.stepLabels):
            if i == self.step:
                label.setStyleSheet(
                    "background-color: #4CAF50; color: white; font-weight: bold; "
                    "border-radius: 5px; margin: 2px; padding: 5px;"
                )
            else:
                label.setStyleSheet(
                    "background-color: lightgray; "
                    "border-radius: 5px; margin: 2px; padding: 5px;"
                )

        # Aktualizácia qubitov
        if self.step >= 2 and self.states:
            for i, (basisLabel, stateLabel, qubitStateWidget) in enumerate(self.qubitWidgets):
                if i < len(self.states):
                    state = self.states[i]
                    stateName = ""

                    if state["basis"] == 'Z':
                        stateName = "|0⟩" if state["bit"] == 0 else "|1⟩"
                    else:  # basis == 'X'
                        stateName = "|+⟩" if state["bit"] == 0 else "|-⟩"

                    basisLabel.setText(f"Báza: {state['basis']}")
                    stateLabel.setText(f"Stav: {stateName}")
                    qubitStateWidget.setState(state["basis"], state["bit"])
        else:
            for basisLabel, stateLabel, qubitStateWidget in self.qubitWidgets:
                basisLabel.setText("Báza: -")
                stateLabel.setText("Stav: -")
                qubitStateWidget.setState('-', 0, False)

    def nextStep(self):
        """Posunie protokol o krok vpred."""
        try:
            if self.step == 0:
                # Alice vyberá bit (už zobrazujeme "Alice si vyberie bit (0 alebo 1)")
                self.aliceBit = 0 if self.bit0Radio.isChecked() else 1
                self.bases = ['X', 'Z', 'X'] if self.aliceBit == 0 else ['Z', 'X', 'Z']

                # Posunieme sa na krok 1
                self.step = 1

                # Aktualizujeme UI, aby sa zvýraznil krok 1
                self.updateUI()

                # Text pre krok 1 (ktorý sa zobrazí so zvýrazneným krokom 1)
                self.infoLabel.setText(f"<b>Krok 2:</b> Alice si vybrala bit <b>{self.aliceBit}</b>. " +
                                       f"Postupnosť báz: <b>{''.join(self.bases)}</b>. " +
                                       "<b>Teraz si zvoľte náhodné bity (r).</b>")

            elif self.step == 1:
                # Alice nastavuje náhodné bity a pripravuje stavy
                self.randomBits = self.getRandomBits()
                self.states = []

                # Vytvorenie kvantových stavov
                for i in range(self.num_qubits):
                    basis = self.bases[i]
                    bit = self.randomBits[i]

                    self.states.append({
                        "basis": basis,
                        "bit": bit
                    })

                # Posunieme sa na krok 2
                self.step = 2

                # Aktualizujeme UI, aby sa zvýraznil krok 2
                self.updateUI()

                # Text pre krok 2 (ktorý sa zobrazí so zvýrazneným krokom 2)
                bitStr = ", ".join([str(bit) for bit in self.randomBits])
                self.infoLabel.setText(f"<b>Krok 3:</b> Alice si zvolila náhodné bity: <b>[{bitStr}]</b>. " +
                                       "Pripravila kvantové stavy a chystá sa ich poslať Bobovi.")

            elif self.step == 2:
                # Posunieme sa na krok 3
                self.step = 3

                # Aktualizujeme UI, aby sa zvýraznil krok 3
                self.updateUI()

                # Text pre krok 3 (ktorý sa zobrazí so zvýrazneným krokom 3)
                self.infoLabel.setText("<b>Krok 4:</b> Alice posiela pripravené kvantové stavy Bobovi. " +
                                       "Bob ukladá qubity do kvantovej pamäte a čaká až nadíde čas na zverejnenie. " +
                                       "<br><br>V tejto chvíli Alice nemôže nič zmeniť a Bob ich nemôže zmerať - " +
                                       "protokol poskytuje binding (záväznosť) aj hiding (utajenie).")

            elif self.step == 3:
                # Posunieme sa na krok 4
                self.step = 4

                # Aktualizujeme UI, aby sa zvýraznil krok 4
                self.updateUI()

                # Text pre krok 4 (ktorý sa zobrazí so zvýrazneným krokom 4)
                bitStr = ", ".join([str(bit) for bit in self.randomBits])
                self.infoLabel.setText(f"<b>Krok 5:</b> Alice odhaľuje svoj záväzok: bit = <b>{self.aliceBit}</b>, " +
                                       f"bázy = <b>{''.join(self.bases)}</b>, náhodné bity = <b>[{bitStr}]</b>. " +
                                       "Bob teraz môže merať qubity a overiť záväzok.")

            elif self.step == 4:
                # Bob verifikuje záväzok
                # Simulácia merania - všetky merania budú korektné,
                # keďže nemáme kvantový šum
                self.verificationSuccess = True

                # Posunieme sa na krok 5
                self.step = 5

                # Aktualizujeme UI, aby sa zvýraznil krok 5
                self.updateUI()

                # Aktualizácia zobrazenia výsledkov
                if self.verificationSuccess:
                    self.resultLabel.setText("ZÁVÄZOK ÚSPEŠNE OVERENÝ ✓")
                    self.resultLabel.setStyleSheet("color: green;")
                else:
                    self.resultLabel.setText("ZÁVÄZOK NEPLATNÝ ✗")
                    self.resultLabel.setStyleSheet("color: red;")

                # Detaily verifikácie
                details_text = "Výsledky verifikácie:\n"
                for i, state in enumerate(self.states):
                    details_text += f"Qubit {i + 1}: Báza {state['basis']}, "
                    details_text += f"Bit {state['bit']} - Overené ✓\n"

                self.verificationLabel.setText(details_text)

                # Text pre krok 5 (ktorý sa zobrazí so zvýrazneným krokom 5)
                bitStr = ", ".join([str(bit) for bit in self.randomBits])
                self.infoLabel.setText(f"<b>Krok 6:</b> Protokol úspešne dokončený. Bob overil Alicin záväzok bit = <b>{self.aliceBit}</b>, " +
                                       f"náhodné bity = <b>[{bitStr}]</b>.")

                # Zablokovanie tlačidla ďalšieho kroku
                self.nextStepBtn.setEnabled(False)

        except Exception as e:
            self.infoLabel.setText(f"Chyba: {str(e)}")

    def resetUI(self):
        """Resetuje protokol a UI do počiatočného stavu."""
        self.resetProtocol()

        self.infoLabel.setText("<b>Krok 1:</b> <b>Alice si vyberie bit (0 alebo 1).</b>")
        self.verificationLabel.setText("Výsledky verifikácie sa zobrazia v kroku 6.")
        self.resultLabel.setText("")

        self.nextStepBtn.setEnabled(True)
        self.updateUI()