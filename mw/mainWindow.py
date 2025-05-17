from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QTextEdit, QTabWidget, QLabel, QPushButton

from QSim_app.qkdProtocol import QKDProtocol #Kvantová distribúcia kľúčov (QKD)
from QSim_app.coinFlipping import CoinFlipping #Kvantový hod mincou (QFC)
from QSim_app.quantumCommitment import QuantumCommitment #Kvantový záväzkový protokol (QC)
from QSim_app.qss import QSSProtocolUI #Kvantové zdieľanie tajomstva (QSS)
from QSim_app.byzantineAgreement import QuantumByzantineAgreement #Kvantová byzantská dohoda (QBA)
from QSim_app.qrng import QRNG #Kvantové generovanie náhodných čísel (QRNG)
from QSim_app.qpv import QuantumPositionVerification #Kvantová verifikácia polohy (QPV)
from QSim_app.qst import QuantumTimeSync #Kvantová synchronizácia času (QST)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mw/main_window.ui", self)

        # Nastavenie ikony aplikácie
        self.setWindowIcon(QIcon("icon/icon.png"))

        # Oblasť popisu pre výstup protokolu
        self.description_area = self.findChild(QTextEdit, "descriptionArea")

        # Karty protokolu
        self.tab_widget = self.findChild(QTabWidget, "tabWidget")

        # Uvítacie prvky
        self.welcome_label = self.findChild(QLabel, "welcomeLabel")
        self.start_button = self.findChild(QPushButton, "startButton")
        self.description_label = self.findChild(QLabel, "descriptionLabel")

        # Pripojenie tlačidla k funkcii
        self.start_button.clicked.connect(self.show_protocol_tabs)

        # Inicializácia protokolov
        self.add_protocol_tabs()

    def add_protocol_tabs(self):
        """Inicializácia a pridanie každej karty protokolu do hlavného okna."""

        # Kvantová distribúcia kľúčov (QKD)
        self.tab_widget.addTab(QKDProtocol(), "Kvantová distribúcia kľúčov - BB84 s polarizačným kódovaním")

        # Kvantový hod mincou (QFC)
        self.tab_widget.addTab(CoinFlipping(self.description_area), "Kvantový hod mincou")

        # Kvantový záväzkový protokol (QC)
        self.tab_widget.addTab(QuantumCommitment(self.description_area), "Kvantový záväzok")

        # Kvantové zdieľanie tajomstva (QSS)
        self.tab_widget.addTab(QSSProtocolUI(), "Kvantové zdieľanie tajomstva")

        # Kvantová byzantská dohoda (QBA)
        self.tab_widget.addTab(QuantumByzantineAgreement(self.description_area), "Kvantová byzantská dohoda")

        # Kvantové generovanie náhodných čísel (QRNG)
        self.tab_widget.addTab(QRNG(), "Kvantové generovanie náhodných čísel")

        # Kvantová verifikácia polohy (QPV)
        self.tab_widget.addTab(QuantumPositionVerification(), "Kvantové overenie polohy")

        # Kvantová synchronizácia času (QST)
        self.tab_widget.addTab(QuantumTimeSync(), "Kvantová synchronizácia času")

    def show_protocol_tabs(self):
        """Zobraziť protokoly a skryť uvítacie prvky."""
        self.welcome_label.hide()
        self.start_button.hide()
        self.description_label.hide()
        self.tab_widget.show()