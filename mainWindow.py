from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QTextEdit, QTabWidget, QLabel, QPushButton
from coinFlipping import CoinFlipping
from qkdProtocol import QKDProtocol
from qrng import QRNG
from quantumCommitment import QuantumCommitment
from byzantineAgreement import QuantumByzantineAgreement
from qssProtocol import QSSProtocol
from qst import QuantumTimeSync
from qpv import QuantumPositionVerification


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)

        # Set application icon (use your icon path)
        self.setWindowIcon(QIcon("icons/icon.png"))  # Adjust path as needed

        # Description area for protocol output
        self.description_area = self.findChild(QTextEdit, "descriptionArea")
        # Optional: Skryť descriptionArea, ak nie je potrebné
        # self.description_area.hide()

        # Protocol tabs
        self.tab_widget = self.findChild(QTabWidget, "tabWidget")

        # Uvítacie prvky
        self.welcome_label = self.findChild(QLabel, "welcomeLabel")
        self.start_button = self.findChild(QPushButton, "startButton")
        self.description_label = self.findChild(QLabel, "descriptionLabel")  # Nový label

        # Pripojenie tlačidla k funkcii
        self.start_button.clicked.connect(self.show_protocol_tabs)

        # Inicializácia protokolov
        self.add_protocol_tabs()

    def add_protocol_tabs(self):
        """Initialize and add each protocol tab to the main window."""

        #  Kvantová distribúcia kľúčov (QKD)
        self.tab_widget.addTab(QKDProtocol(), "Kvantová distribúcia kľúčov - BB84 s polarizačným kódovaním")

        #  Kvantový hod mincou (QFC)
        self.tab_widget.addTab(CoinFlipping(self.description_area), "Kvantový hod mincou")

        # Kvantový záväzkový protokol (QC)
        self.tab_widget.addTab(QuantumCommitment(self.description_area), "Kvantový záväzok")

        # Kvantové zdieľanie tajomstva (QSS)
        self.tab_widget.addTab(QSSProtocolUI(), "Kvantové zdieľanie tajomstva")

        # Kvantová byzantská dohoda (QBA)
        self.tab_widget.addTab(QuantumByzantineAgreement(self.description_area), "Kvantová byzantská dohoda")

        #  Kvantové generovanie náhodných čísel (QRNG)
        # self.tab_widget.addTab(QRNG(), "QRNG")
        self.tab_widget.addTab(QRNG(), "Kvantové generovanie náhodných čísel")

        # Kvantová verifikácia polohy (QPV)
        self.tab_widget.addTab(QuantumPositionVerification(), "Kvantové overenie polohy")

        # Kvantová synchronizácia času (QST)
        # self.tab_widget.addTab(QuantumTimeSync(), "QST")
        self.tab_widget.addTab(QuantumTimeSync(), "Kvantová synchronizácia času")



    def show_protocol_tabs(self):
        """Zobraziť protokoly a skryť uvítacie prvky."""
        self.welcome_label.hide()
        self.start_button.hide()
        self.description_label.hide()  # Skryť popisný label
        self.tab_widget.show()