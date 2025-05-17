from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, \
    QGraphicsScene, QGraphicsView, QHeaderView, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsLineItem, \
    QGraphicsPolygonItem, QGraphicsPathItem, QGraphicsItemGroup, QLineEdit, QCheckBox, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF
from PyQt6.QtGui import QPixmap, QColor, QFont, QPen, QBrush, QPainterPath, QPolygonF, QTransform
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6 import uic
import random
import sys
import math


class QKDProtocol(QWidget):
    def __init__(self):
        super().__init__()

        # Načítanie UI
        uic.loadUi('mw/qkd_protocol.ui', self)

        # Nastavenie vlastností okna
        self.setStyleSheet("background-color: white")
        self.setWindowTitle("QKD - Simulácia")

        # Pridanie titulného textu
        title_label = QLabel("Kvantová distribúcia kľúčov - BB84 s polarizačným kódovaním")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #333; margin: 10px 0;")

        # Vloženie titulku do hlavného layoutu
        main_layout = self.layout()
        main_layout.insertWidget(0, title_label)

        # Nájdenie prvkov UI
        self.output_label = self.findChild(QLabel, "output_label")
        self.view = self.findChild(QGraphicsView, "graphics_view")
        self.table = self.findChild(QTableWidget, "result_table")
        self.use_custom_bits = self.findChild(QCheckBox, "use_custom_bits")
        self.custom_bits_input = self.findChild(QLineEdit, "custom_bits_input")
        self.start_button = self.findChild(QPushButton, "start_button")

        # Pripojenie signálov
        self.start_button.clicked.connect(self.start_simulation)
        self.use_custom_bits.stateChanged.connect(self.toggle_custom_bits_input)

        # Inicializácia scény
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Počet simulovaných fotónov (bitov)
        self.num_bits = 8

        # Timer pre posielanie fotónov
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_next_photon)

        # Timer pre animáciu fotónu
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_photon_step)

        # Parametre animácie
        self.animation_total_steps = 100
        self.current_step = 0
        self.animation_phase = None
        self.photon_in_flight = False

        # Alice vygeneruje náhodnú sekvenciu bitov
        self.alice_bits = []

        # Výsledný kľúč po "preosievaní"
        self.shared_key = []

        # Aktuálny fotón a jeho atribúty
        self.photon = None
        self.alice_bit = None
        self.alice_basis = None
        self.bob_basis = None

        # Základné pozície
        self.scene_width = 800
        self.scene_height = 400

        # Oblasti pre Alice a Bob
        self.alice_area = QRectF(50, 50, 200, 300)
        self.bob_area = QRectF(430, 50, 320, 300)

        # Stredová os-kvantový kanál
        self.channel_y = 250

        # Zdroj fotónov
        self.photon_source_pos = QPointF(150, self.channel_y)

        # Komponenty na Bobovej strane
        self.beam_splitter_pos = QPointF(525, 250)  # Delič 50:50
        self.rotator_pos = QPointF(525, 200)  # Rotátor 45°
        self.diagonal_polarizer_pos = QPointF(525, 150)  # Polarizačný delič pre diagonálnu bázu
        self.rect_polarizer_pos = QPointF(625, 250)  # Polarizačný delič pre rektilineárnu bázu

        # Detektory
        self.diagonal_detector_0_pos = QPointF(525, 100)  # Horný detektor (0) pre diagonálnu bázu
        self.diagonal_detector_1_pos = QPointF(600, 150)  # Pravý detektor (1) pre diagonálnu bázu
        self.rect_detector_1_pos = QPointF(700, 250)  # Pravý detektor (1) pre rektilineárnu bázu
        self.rect_detector_0_pos = QPointF(625, 320)  # Dolný detektor (0) pre rektilineárnu bázu

        # Popisy detektorov
        self.diagonal_label_pos = QPointF(650, 100)  # Popis pre diagonálne detektory
        self.rect_label_pos = QPointF(650, 300)  # Popis pre rektilineárne detektory

        # Mapovanie bází a stavov
        self.bases = {
            "⨁": {0: "→", 1: "↑"},  # Rectilinear basis
            "⨂": {0: "↘", 1: "↗"}  # Diagonal basis
        }

        # Mapovanie polarizácií na farby a smery
        self.polarization_colors = {
            "→": (QColor(255, 0, 0), 0),  # Červená, horizontálna
            "↑": (QColor(0, 128, 0), 270),  # Zelená, vertikálna
            "↘": (QColor(255, 165, 0), 45),  # Oranžová, 45°
            "↗": (QColor(0, 0, 255), 315)  # Modrá, 135°
        }

        # Základné nastavenie
        self.setup_table()
        self.draw_static_elements()

    def toggle_custom_bits_input(self, state):
        """Prepína režim vlastných a náhodných bitov"""
        if state:
            self.custom_bits_input.setEnabled(True)
            self.custom_bits_input.setStyleSheet("background-color: white; color: black; font-size: 14px;")
            self.custom_bits_input.setFocus()
        else:
            self.custom_bits_input.setEnabled(False)
            self.custom_bits_input.setStyleSheet("background-color: lightgray; color: gray; font-size: 14px;")

    def setup_table(self):
        """Nastavenie tabuľky pre výsledky"""
        self.table.setRowCount(self.num_bits)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Aliciný bit", "Alicin fotón", "Bob vyberá bázu",
                                              "Bobov výsledok", "Bobov bit", "Bob oznámi bázu",
                                              "Zhoda s Alicou", "Hrubý kľúč"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Nastavenie farby hlavičky na čiernu
        for col in range(8):
            item = self.table.horizontalHeaderItem(col)
            item.setForeground(QColor("black"))

    def draw_static_elements(self):
        """Vykreslenie všetkých statických prvkov scény"""
        self.scene.clear()

        # Vykreslenie hlavných komponentov
        self.draw_alice_area()
        self.draw_bob_area()
        self.draw_quantum_channel()
        self.draw_polarizers_and_detectors()

    def draw_alice_area(self):
        """Vykreslenie oblasti Alice s červeným rámčekom"""
        # Červený rámček pre Alicu
        alice_rect = QGraphicsRectItem(self.alice_area)
        alice_rect.setPen(QPen(QColor("red"), 3))
        self.scene.addItem(alice_rect)

        # Text "Alice" - veľký, červený
        alice_text = self.scene.addSimpleText("Alice")
        alice_text.setBrush(QColor("red"))
        alice_text.setPos(
            self.alice_area.x() + 80,
            self.alice_area.y() + 20
        )
        alice_text.setScale(2.0)

        # Text "Zdroj fotónov"
        source_text = self.scene.addSimpleText("Zdroj fotónov")
        source_text.setPos(
            self.alice_area.x() + 60,
            self.alice_area.y() + 125
        )
        source_text.setScale(1.2)

        # Tabuľka fotónov
        self.draw_photon_source()

    def draw_photon_source(self):
        """Vykreslenie tabuľky so zdrojom fotónov a rôznymi polarizáciami"""
        table_width = 80
        table_height = 100
        cell_height = table_height / 4
        scale_factor = 1.5  # Škálovací faktor pre text

        # Pozícia tabuľky-zarovnanie stredu tabuľky s kvantovým kanálom
        table_x = self.alice_area.x() + (self.alice_area.width() - table_width) / 2
        table_y = self.channel_y - table_height / 2  # Centrum tabuľky na úrovni kvantového kanála

        # Hlavná tabuľka-vycentrovaná
        table_rect = QGraphicsRectItem(
            table_x,
            table_y,
            table_width,
            table_height
        )
        table_rect.setPen(QPen(QColor("black"), 2))  # Ponechaná pôvodná hrúbka
        self.scene.addItem(table_rect)

        # Horizontálne čiary-vycentrované
        for i in range(1, 4):
            y_pos = table_y + i * cell_height
            line = QGraphicsLineItem(
                table_x,
                y_pos,
                table_x + table_width,
                y_pos
            )
            line.setPen(QPen(QColor("black"), 1))  # Ponechaná pôvodná hrúbka
            self.scene.addItem(line)

        # Obsah buniek-bity a šípky
        table_entries = [
            (1, "↑", QColor(0, 128, 0)),  # 1, vertikálna, zelená
            (0, "→", QColor(255, 0, 0)),  # 0, horizontálna, červená
            (1, "↗", QColor(0, 0, 255)),  # 1, diagonálna 135°, modrá
            (0, "↘", QColor(255, 165, 0))  # 0, diagonálna 45°, oranžová
        ]

        # Stredové pozície buniek
        for i, (bit, symbol, color) in enumerate(table_entries):
            # Vertikálna pozícia pre stred bunky
            center_y = table_y + i * cell_height + cell_height / 2
            left_center_x = table_x + table_width / 4
            right_center_x = table_x + 3 * table_width / 4

            bit_text = self.scene.addSimpleText(str(bit))
            bit_text.setScale(scale_factor)

            bit_width = bit_text.boundingRect().width() * scale_factor
            bit_height = bit_text.boundingRect().height() * scale_factor
            bit_x = left_center_x - bit_width / 2
            bit_y = center_y - bit_height / 2

            bit_text.setPos(bit_x, bit_y)

            # Symbol šípky
            arrow_text = self.scene.addSimpleText(symbol)
            arrow_text.setBrush(color)
            arrow_text.setScale(scale_factor)

            arrow_width = arrow_text.boundingRect().width() * scale_factor
            arrow_height = arrow_text.boundingRect().height() * scale_factor
            arrow_x = right_center_x - arrow_width / 2
            arrow_y = center_y - arrow_height / 2

            arrow_text.setPos(arrow_x, arrow_y)

    def draw_bob_area(self):
        """Vykreslenie oblasti Boba so zeleným rámčekom"""
        # Zelený rámček pre Boba
        bob_rect = QGraphicsRectItem(self.bob_area)
        bob_rect.setPen(QPen(QColor("green"), 3))
        self.scene.addItem(bob_rect)

        # Text "Bob" - veľký, zelený
        bob_text = self.scene.addSimpleText("Bob")
        bob_text.setBrush(QColor("green"))
        bob_text.setPos(
            self.bob_area.x() + self.bob_area.width() - 70,
            self.bob_area.y() + 20
        )
        bob_text.setScale(2.0)

    def draw_quantum_channel(self):
        """Vykreslenie kvantového kanála medzi Alice a Bobom"""
        table_width = 80
        table_right_edge = self.alice_area.x() + (self.alice_area.width() + table_width) / 2

        # Kvantový kanál-prerušovaná čiara začínajúca od pravého okraja tabuľky
        channel = QGraphicsLineItem(
            table_right_edge,  # Začiatok na pravom okraji tabuľky
            self.channel_y,
            self.bob_area.left(),
            self.channel_y
        )
        channel.setPen(QPen(QColor("black"), 1, Qt.PenStyle.DashLine))
        self.scene.addItem(channel)

        channel_text = self.scene.addSimpleText("Kvantový kanál")
        channel_text.setPos(
            (self.alice_area.right() + self.bob_area.left()) / 2 - channel_text.boundingRect().width() / 2,
            self.channel_y + 15
        )
        channel_text.setScale(1.2)

    def draw_polarizers_and_detectors(self):
        """Vykreslenie polarizačných deličov a detektorov v Bobovej oblasti"""
        # Delič 50:50
        self.draw_polarizer(self.beam_splitter_pos.x(), self.beam_splitter_pos.y(),
                            "Delič 50:50", rotate_diagonal=True, label_position="bottom")

        # Rotátor 45°
        self.draw_rotator()

        # Polarizačný delič pre diagonálnu bázu
        self.draw_polarizer(self.diagonal_polarizer_pos.x(), self.diagonal_polarizer_pos.y(),
                            "Polarizačný\ndelič zväzkov", rotate_diagonal=True, label_position="left")

        # Polarizačný delič pre rektilineárnu bázu
        self.draw_polarizer(self.rect_polarizer_pos.x(), self.rect_polarizer_pos.y(),
                            "Polarizačný\ndelič zväzkov", rotate_diagonal=False, label_position="top")

        # Detektory pre diagonálnu bázu
        self.draw_detector(self.diagonal_detector_0_pos, "0", "↘", QColor(255, 165, 0), offset_x=0,
                           offset_y=+15)  # 0 - oranžová diagonála
        self.draw_detector(self.diagonal_detector_1_pos, "1", "↗", QColor(0, 0, 255), rotation=90, offset_x=-15,
                           offset_y=0)  # 1 - modrá diagonála

        # Detektory pre rektilineárnu bázu
        self.draw_detector(self.rect_detector_1_pos, "1", "↑", QColor(0, 128, 0), rotation=90, offset_x=-15,
                           offset_y=0)  # 1 - zelená vertikála
        self.draw_detector(self.rect_detector_0_pos, "0", "→", QColor(255, 0, 0), rotation=180, offset_x=0,
                           offset_y=-15)  # 0 - červená horizontála

        # Popisy detektorov ako modré boxy
        self.draw_detector_label(self.diagonal_label_pos.x(), self.diagonal_label_pos.y(),
                                 "Detektory pre\ndiagonálnu bázu")
        # Posunutie popisu pre základnú bázu (20px hore)
        self.draw_detector_label(self.rect_label_pos.x(), self.rect_label_pos.y() - 25,
                                 "Detektory pre\nzákladnú bázu")

        # Prepojenia medzi komponentmi
        # Vertikálne prepojenie od deliča 50:50 k rotátoru
        connector1 = QGraphicsLineItem(
            self.beam_splitter_pos.x(),
            self.beam_splitter_pos.y() - 15,
            self.beam_splitter_pos.x(),
            self.rotator_pos.y() + 10
        )
        connector1.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector1)

        # Vertikálne prepojenie od rotátora k hornému polarizačnému deliču
        connector2 = QGraphicsLineItem(
            self.rotator_pos.x(),
            self.rotator_pos.y() - 10,
            self.rotator_pos.x(),
            self.diagonal_polarizer_pos.y() + 15
        )
        connector2.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector2)

        # Horizontálne prepojenie od deliča 50:50 k pravému polarizačnému deliču
        connector3 = QGraphicsLineItem(
            self.beam_splitter_pos.x() + 15,
            self.beam_splitter_pos.y(),
            self.rect_polarizer_pos.x() - 15,
            self.rect_polarizer_pos.y()
        )
        connector3.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector3)

        # Horizontálne prepojenie od hranice Boba k deliču 50:50
        connector4 = QGraphicsLineItem(
            self.bob_area.left(),
            self.channel_y,
            self.beam_splitter_pos.x() - 15,
            self.beam_splitter_pos.y()
        )
        connector4.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector4)

        # Prepojenia k detektorom diagonálnej bázy
        # K hornému detektoru - vertikálna čiara nahor
        connector5 = QGraphicsLineItem(
            self.diagonal_polarizer_pos.x(),
            self.diagonal_polarizer_pos.y() - 15,
            self.diagonal_polarizer_pos.x(),
            self.diagonal_detector_0_pos.y() + 15
        )
        connector5.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector5)

        # K pravému detektoru - horizontálna čiara doprava
        connector6 = QGraphicsLineItem(
            self.diagonal_polarizer_pos.x() + 15,
            self.diagonal_polarizer_pos.y(),
            self.diagonal_detector_1_pos.x() - 15,
            self.diagonal_detector_1_pos.y()
        )
        connector6.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector6)

        # Prepojenia k detektorom rektilineárnej bázy
        connector7 = QGraphicsLineItem(
            self.rect_polarizer_pos.x() + 15,
            self.rect_polarizer_pos.y(),
            self.rect_detector_1_pos.x() - 15,
            self.rect_detector_1_pos.y()
        )
        connector7.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector7)

        connector8 = QGraphicsLineItem(
            self.rect_polarizer_pos.x(),
            self.rect_polarizer_pos.y() + 15,
            self.rect_polarizer_pos.x(),
            self.rect_detector_0_pos.y() - 15
        )
        connector8.setPen(QPen(QColor("black"), 1))
        self.scene.addItem(connector8)

    def draw_polarizer(self, x, y, label_text=None, rotate_diagonal=False, label_position="top"):
        """Vykreslenie polarizačného deliča ako štvorec s diagonálnou čiarou"""
        # Veľkosť polarizačného deliča
        size = 30

        # Štvorec
        polarizer = QGraphicsRectItem(
            x - size / 2,
            y - size / 2,
            size,
            size
        )
        polarizer.setPen(QPen(QColor("black"), 2))
        polarizer.setBrush(QBrush(QColor(255, 255, 255)))
        self.scene.addItem(polarizer)

        if rotate_diagonal:
            diagonal = QGraphicsLineItem(
                x + size / 2,
                y - size / 2,
                x - size / 2,
                y + size / 2
            )
        else:
            diagonal = QGraphicsLineItem(
                x - size / 2,
                y - size / 2,
                x + size / 2,
                y + size / 2
            )
        diagonal.setPen(QPen(QColor("black"), 2))
        self.scene.addItem(diagonal)

        if label_text:
            label = self.scene.addSimpleText(label_text)

            if label_position == "bottom":
                # Popis pod komponentom
                label.setPos(
                    x - label.boundingRect().width() / 2,
                    y + size / 2 + 5
                )
            elif label_position == "top":
                # Popis nad komponentom
                label.setPos(
                    x - label.boundingRect().width() / 2,
                    y - size / 2 - label.boundingRect().height() - 5
                )
            elif label_position == "left":
                # Popis naľavo od komponentu
                label.setPos(
                    x - size / 2 - label.boundingRect().width() - 5,
                    y - label.boundingRect().height() / 2
                )
            elif label_position == "right":
                # Popis napravo od komponentu
                label.setPos(
                    x + size / 2 + 5,
                    y - label.boundingRect().height() / 2
                )

            label.setScale(0.9)  # Zmenšenie textu

    def draw_rotator(self):
        """Vykreslenie rotátora 45° ako žltého obdĺžnika"""
        # Rozmery rotátora
        width = 30
        height = 15

        # Žltý obdĺžnik
        rotator = QGraphicsRectItem(
            self.rotator_pos.x() - width / 2,
            self.rotator_pos.y() - height / 2,
            width,
            height
        )
        rotator.setPen(QPen(QColor("black"), 1))
        rotator.setBrush(QBrush(QColor(255, 215, 0)))  # Žltá farba
        self.scene.addItem(rotator)

        # Popis naľavo od rotátora
        label_text = "Rotátor 45°"
        label = self.scene.addSimpleText(label_text)

        # Umiestnenie popisu naľavo
        label.setPos(
            self.rotator_pos.x() - width / 2 - label.boundingRect().width() - 5,
            self.rotator_pos.y() - label.boundingRect().height() / 2
        )
        label.setScale(0.9)  # Zmenšenie textu

    def draw_detector(self, pos, bit_value, polarization_symbol, color, rotation=0, offset_x=0, offset_y=0,
                      vertical_spacing=0):
        """Vykreslenie detektora ako polkruhu s príslušnými textami"""
        pos = QPointF(pos.x() + offset_x, pos.y() + offset_y)

        # Veľkosť detektora
        radius = 20

        # Vytvorenie základného polkruhu
        path = QPainterPath()
        path.moveTo(0, 0)
        path.arcTo(-radius, -radius, radius * 2, radius * 2, 0, 180)
        path.closeSubpath()

        # Vytvorenie detektora ako objektu
        detector = QGraphicsPathItem(path)
        detector.setPen(QPen(QColor("black"), 2))
        detector.setBrush(QBrush(QColor(200, 220, 255)))

        # Použitie transformácie na otočenie a posun detektora
        transform = QTransform()
        transform.translate(pos.x(), pos.y())
        transform.rotate(rotation)
        detector.setTransform(transform)

        self.scene.addItem(detector)

        # Vytvorenie bitového textu (0 alebo 1)
        bit_text = self.scene.addSimpleText(bit_value)
        bit_text.setScale(1.3)

        # Vytvorenie polarizačného symbolu (↘, ↗, ↑, →)
        polarization_text = self.scene.addSimpleText(polarization_symbol)
        polarization_text.setBrush(color)
        polarization_text.setScale(1.3)

        if bit_value == "0":
            spacing = 5
            bit_x = pos.x() - (bit_text.boundingRect().width() + polarization_text.boundingRect().width() + spacing) / 2
            bit_y = pos.y() - radius / 2 - bit_text.boundingRect().height() / 2

            polarization_x = bit_x + bit_text.boundingRect().width() + spacing
            polarization_y = bit_y

            if polarization_symbol == "↘":
                bit_y -= 2.5
                polarization_y -= 2.5

            if polarization_symbol == "→":
                bit_y += 15
                polarization_y += 15


        else:


            bit_x = pos.x() - bit_text.boundingRect().width() / 2
            bit_y = pos.y() - radius / 2 - bit_text.boundingRect().height() / 2

            polarization_x = pos.x() - polarization_text.boundingRect().width() / 2
            polarization_y = bit_y + bit_text.boundingRect().height() + vertical_spacing


            if polarization_symbol == "↗":
                bit_x += 5
                polarization_x += 5

            if polarization_symbol == "↑":
                bit_x += 5
                polarization_x += 5

        # Nastavenie pozícií textov
        bit_text.setPos(bit_x, bit_y)
        polarization_text.setPos(polarization_x, polarization_y)

        self.scene.addItem(bit_text)
        self.scene.addItem(polarization_text)

    def draw_detector_label(self, x, y, text):
        """Vykreslenie popisku detektorov ako modrý box s textom"""
        if "základnou bázou" in text:
            y -= 0
        elif "diagonálnu bázu" in text:
            x -= 100
            y -= 17.5

        # Vytvorenie textového popisu
        label = self.scene.addSimpleText(text)
        label.setScale(1)
        label.setBrush(QBrush(QColor("black")))

        # Získanie veľkosti textu na správne nastavenie rámčeka
        text_width = label.boundingRect().width()
        text_height = label.boundingRect().height()

        # Vytvorenie modrého rámčeka s paddingom okolo textu
        padding = 10
        label_bg = QGraphicsRectItem(
            x, y,
            text_width + padding,
            text_height + padding
        )
        label_bg.setBrush(QBrush(QColor(200, 220, 255)))
        label_bg.setPen(QPen(QColor("black"), 2))

        # Umiestnenie textu do stredu modrého rámčeka
        label.setPos(
            x + padding / 2,
            y + padding / 2
        )

        self.scene.addItem(label_bg)
        self.scene.addItem(label)

        # **Zvýšenie vrstvy textu, aby bol nad rámčekom**
        label.setZValue(1)  # Vyššia hodnota znamená vyššiu prioritu

    def create_photon(self, state):
        """Vytvorenie fotónu s daným stavom (polarizáciou)"""
        # Získať farbu a uhol podľa polarizácie
        color, angle = self.polarization_colors[state]

        # Vytvorenie šípky
        arrow_length = 15
        arrow_head_size = 5

        # Qt používa systém, kde 0° je doprava, 90° je dole, 180° je doľava, 270° je hore
        rad_angle = math.radians(angle)
        end_x = arrow_length * math.cos(rad_angle)
        end_y = arrow_length * math.sin(rad_angle)

        # Vytvorenie cesty pre šípku
        line = QGraphicsLineItem(0, 0, end_x, end_y)
        line.setPen(QPen(color, 2))

        # Hlavička šípky (trojuholník)
        head_x1 = end_x - arrow_head_size * math.cos(rad_angle - math.pi / 6)
        head_y1 = end_y - arrow_head_size * math.sin(rad_angle - math.pi / 6)
        head_x2 = end_x - arrow_head_size * math.cos(rad_angle + math.pi / 6)
        head_y2 = end_y - arrow_head_size * math.sin(rad_angle + math.pi / 6)

        polygon = QPolygonF()
        polygon.append(QPointF(end_x, end_y))
        polygon.append(QPointF(head_x1, head_y1))
        polygon.append(QPointF(head_x2, head_y2))

        head = QGraphicsPolygonItem(polygon)
        head.setPen(QPen(color, 1))
        head.setBrush(QBrush(color))

        return line, head

    def animate_photon_step(self):
        """Animácia jedného kroku pohybu fotónu v kvantovom kanáli"""
        try:
            if self.current_step >= self.animation_total_steps:
                self.animation_timer.stop()

                # Pridané overenie existencie animačnej fázy
                if not hasattr(self, 'animation_phase') or self.animation_phase is None:
                    print("No animation phase defined!")
                    return

                if self.animation_phase == "to_beam_splitter":
                    # Prechod do ďalšej fázy: podľa Bobovej bázy
                    if self.bob_basis == "⨂":  # Diagonálna báza-pohyb k hornému deliču
                        self.animation_phase = "to_diagonal_polarizer"
                    else:  # Rektilineárna báza-pohyb k pravému deliču
                        self.animation_phase = "to_rect_polarizer"
                    self.current_step = 0
                    self.animation_timer.start(10)

                elif self.animation_phase == "to_diagonal_polarizer":
                    # Prechod k jednému z detektorov pre diagonálnu bázu
                    if self.alice_basis == self.bob_basis and self.alice_bit == 0:
                        self.animation_phase = "to_diagonal_detector_0"
                    elif self.alice_basis == self.bob_basis and self.alice_bit == 1:
                        self.animation_phase = "to_diagonal_detector_1"
                    else:
                        # Ak sa bázy nezhodujú, náhodný výber detektora
                        self.animation_phase = random.choice(["to_diagonal_detector_0", "to_diagonal_detector_1"])
                    self.current_step = 0
                    self.animation_timer.start(10)

                elif self.animation_phase == "to_rect_polarizer":
                    # Prechod k jednému z detektorov pre rektilineárnu bázu
                    if self.alice_basis == self.bob_basis and self.alice_bit == 0:
                        self.animation_phase = "to_rect_detector_0"
                    elif self.alice_basis == self.bob_basis and self.alice_bit == 1:
                        self.animation_phase = "to_rect_detector_1"
                    else:
                        # Ak sa bázy nezhodujú, náhodný výber detektora
                        self.animation_phase = random.choice(["to_rect_detector_0", "to_rect_detector_1"])
                    self.current_step = 0
                    self.animation_timer.start(10)

                elif self.animation_phase in ["to_diagonal_detector_0", "to_diagonal_detector_1",
                                              "to_rect_detector_0", "to_rect_detector_1"]:
                    # Fotón dorazil k detektoru
                    self.scene.removeItem(self.photon_line)
                    self.scene.removeItem(self.photon_head)
                    self.photon_in_flight = False

                    # Vyhodnotenie merania: ak sa bázy zhodujú, Bob dostane rovnaký bit ako Alice
                    if self.alice_basis == self.bob_basis:
                        measured_bit = self.alice_bit
                        self.shared_key.append(measured_bit)
                    else:
                        # Ak sa bázy nezhodujú, bit je náhodný
                        if self.animation_phase == "to_diagonal_detector_0" or self.animation_phase == "to_rect_detector_0":
                            measured_bit = 0
                        else:
                            measured_bit = 1

                    # Aktualizácia tabuľky
                    self.update_table(self.current_bit, self.alice_bit, self.alice_basis, self.bob_basis, measured_bit)

                    self.current_bit += 1
                return

            # Určenie počiatočnej a cieľovej pozície podľa fázy animácie
            if self.animation_phase == "to_beam_splitter":
                # Pohyb z hranice Alice k deliču 50:50
                start_pos = QPointF(self.alice_area.right(), self.channel_y)
                end_pos = QPointF(self.beam_splitter_pos.x() - 15, self.beam_splitter_pos.y())

            elif self.animation_phase == "to_diagonal_polarizer":
                # Pohyb od deliča 50:50 k rotátoru a potom k hornému polarizačnému deliču
                if self.current_step < self.animation_total_steps / 2:
                    # Prvá polovica - pohyb k rotátoru
                    start_pos = QPointF(self.beam_splitter_pos.x(), self.beam_splitter_pos.y() - 15)
                    end_pos = QPointF(self.rotator_pos.x(), self.rotator_pos.y() + 10)
                    t = 2 * self.current_step / self.animation_total_steps
                else:
                    # Druhá polovica - pohyb od rotátora k hornému polarizačnému deliču
                    start_pos = QPointF(self.rotator_pos.x(), self.rotator_pos.y() - 10)
                    end_pos = QPointF(self.diagonal_polarizer_pos.x(), self.diagonal_polarizer_pos.y() + 15)
                    t = 2 * (self.current_step - self.animation_total_steps / 2) / self.animation_total_steps

                # Lineárna interpolácia
                new_x = (1 - t) * start_pos.x() + t * end_pos.x()
                new_y = (1 - t) * start_pos.y() + t * end_pos.y()
                self.photon_line.setPos(new_x, new_y)
                self.photon_head.setPos(new_x, new_y)
                self.current_step += 1
                return

            elif self.animation_phase == "to_rect_polarizer":
                # Pohyb od deliča 50:50 k pravému polarizačnému deliču
                start_pos = QPointF(self.beam_splitter_pos.x() + 15, self.beam_splitter_pos.y())
                end_pos = QPointF(self.rect_polarizer_pos.x() - 15, self.rect_polarizer_pos.y())

            elif self.animation_phase == "to_diagonal_detector_0":
                # Pohyb od horného polarizačného deliča k hornému detektoru (0)
                start_pos = QPointF(self.diagonal_polarizer_pos.x(), self.diagonal_polarizer_pos.y() - 15)
                end_pos = QPointF(self.diagonal_detector_0_pos.x(), self.diagonal_detector_0_pos.y() + 15)

            elif self.animation_phase == "to_diagonal_detector_1":
                # Pohyb od horného polarizačného deliča k pravému detektoru (1)
                start_pos = QPointF(self.diagonal_polarizer_pos.x() + 15, self.diagonal_polarizer_pos.y())
                end_pos = QPointF(self.diagonal_detector_1_pos.x() - 15, self.diagonal_detector_1_pos.y())

            elif self.animation_phase == "to_rect_detector_0":
                # Pohyb od pravého polarizačného deliča k dolnému detektoru (0)
                start_pos = QPointF(self.rect_polarizer_pos.x(), self.rect_polarizer_pos.y() + 15)
                end_pos = QPointF(self.rect_polarizer_pos.x(), self.rect_detector_0_pos.y() - 15)

            elif self.animation_phase == "to_rect_detector_1":
                # Pohyb od pravého polarizačného deliča k pravému detektoru (1)
                start_pos = QPointF(self.rect_polarizer_pos.x() + 15, self.rect_polarizer_pos.y())
                end_pos = QPointF(self.rect_detector_1_pos.x() - 15, self.rect_detector_1_pos.y())

            else:
                self.animation_timer.stop()
                return

            # Lineárna interpolácia pozície fotónu
            t = self.current_step / self.animation_total_steps
            new_x = (1 - t) * start_pos.x() + t * end_pos.x()
            new_y = (1 - t) * start_pos.y() + t * end_pos.y()

            self.photon_line.setPos(new_x, new_y)
            self.photon_head.setPos(new_x, new_y)

            self.current_step += 1

            # Pridané globálne zachytávanie výnimiek
            if not hasattr(self, 'photon_line') or not hasattr(self, 'photon_head'):
                print("Photon line or head not initialized!")
                return

            # Zvyšok pôvodného kódu s pridaným ladením
        except Exception as e:
            print(f"Unexpected error in animate_photon_step: {e}")
            import traceback
            traceback.print_exc()
            self.animation_timer.stop()
            self.start_button.setEnabled(True)

    def send_next_photon(self):
        """Odoslanie ďalšieho fotónu z Alicinej sekvencie"""
        try:
            if self.current_bit < self.num_bits and not self.photon_in_flight:
                # Overenie, že máme dostatok bitov v sekvencii
                if len(self.alice_bits) <= self.current_bit:
                    print(
                        f"Error: Not enough bits. Current bit: {self.current_bit}, Total bits: {len(self.alice_bits)}")
                    self.timer.stop()
                    self.start_button.setEnabled(True)
                    return

                # Získame bit z Alicinej sekvencie
                self.alice_bit = self.alice_bits[self.current_bit]

                # Pre Alicu a Boba vyberieme bázu náhodne (rektilineárna '⨁' alebo diagonálna '⨂')
                self.alice_basis = random.choice(["⨁", "⨂"])
                self.bob_basis = random.choice(["⨁", "⨂"])

                # Overenie, že máme platný stav pre daný bit a bázu
                try:
                    photon_state = self.bases[self.alice_basis][self.alice_bit]
                except KeyError as e:
                    print(f"Error creating photon state: {e}")
                    print(f"Alice basis: {self.alice_basis}, Alice bit: {self.alice_bit}")
                    self.timer.stop()
                    self.start_button.setEnabled(True)
                    return

                # Vytvorenie šípky fotónu
                try:
                    self.photon_line, self.photon_head = self.create_photon(photon_state)
                    self.scene.addItem(self.photon_line)
                    self.scene.addItem(self.photon_head)
                except Exception as e:
                    print(f"Error creating photon: {e}")
                    self.timer.stop()
                    self.start_button.setEnabled(True)
                    return

                # Výpočet pozície pravého okraja tabuľky zdroja fotónov
                table_width = 80
                table_x = self.alice_area.x() + (self.alice_area.width() - table_width) / 2
                table_right_edge = table_x + table_width

                # Nastavenie pozície fotónu na pravý okraj tabuľky
                self.photon_line.setPos(table_right_edge, self.channel_y)
                self.photon_head.setPos(table_right_edge, self.channel_y)

                self.photon_in_flight = True
                self.animation_phase = "to_beam_splitter"
                self.current_step = 0

                # Pridané bezpečnostné overenie
                if not self.animation_timer.isActive():
                    self.animation_timer.start(10)
                else:
                    print("Animation timer already active!")

            elif self.current_bit >= self.num_bits:
                # Keď už sme odoslali všetky bity, zastavíme timer a povolíme tlačidlo
                self.timer.stop()
                self.start_button.setEnabled(True)

                # Vypíšeme výsledný preosiaty kľúč
                final_key = ''.join(map(str, self.shared_key))
                current_text = self.output_label.text()
                self.output_label.setText(
                    current_text + f"\n\nPreosiaty kľúč (po zahodení nezhodných báz): {final_key}"
                )
        except Exception as e:
            print(f"Unexpected error in send_next_photon: {e}")
            import traceback
            traceback.print_exc()
            self.timer.stop()
            self.start_button.setEnabled(True)

    def update_table(self, bit_index, alice_bit, alice_basis, bob_basis, bob_bit):
        """Aktualizácia tabuľky s výsledkami meraní"""
        def create_table_item(text, color, is_bold=False, size=14):
            item = QTableWidgetItem(str(text))
            font = QFont()
            font.setPointSize(size)
            if is_bold:
                font.setBold(True)
            item.setFont(font)
            item.setForeground(QColor(color))
            return item

        # Aliciný bit
        self.table.setItem(bit_index, 0, create_table_item(alice_bit, "black", True))

        # Mapovanie fotónov na farby
        photon_colors = {
            "↑": QColor(0, 128, 0),  # zelená
            "→": QColor(255, 0, 0),  # červená
            "↗": QColor(0, 0, 255),  # modrá
            "↘": QColor(255, 165, 0)  # oranžová
        }

        # Alicin fotón
        alice_photon_state = self.bases[alice_basis][alice_bit]
        # Farba bázy - rektilineárna (⨁) modrá, diagonálna (⨂) čierna
        basis_color = QColor("blue") if alice_basis == "⨁" else QColor("black")
        self.table.setItem(bit_index, 1, create_table_item(alice_photon_state, photon_colors[alice_photon_state], True))

        # Bobom vybraná báza
        basis_color = QColor("blue") if bob_basis == "⨁" else QColor("black")
        self.table.setItem(bit_index, 2, create_table_item(bob_basis, basis_color, True))

        # Bobov výsledok
        bob_photon_state = self.bases[bob_basis][bob_bit]
        self.table.setItem(bit_index, 3, create_table_item(bob_photon_state, photon_colors[bob_photon_state], True))

        # Bobov bit
        self.table.setItem(bit_index, 4, create_table_item(bob_bit, "black", True))

        # Bob oznamí bázu
        basis_color = QColor("blue") if bob_basis == "⨁" else QColor("black")
        self.table.setItem(bit_index, 5, create_table_item(bob_basis, basis_color, True))

        # Alice oznamí shodu
        if alice_basis == bob_basis:
            self.table.setItem(bit_index, 6, create_table_item("✓", "green", True))
            # Hrubý kľúč
            self.table.setItem(bit_index, 7, create_table_item(bob_bit, "black", True))
        else:
            self.table.setItem(bit_index, 6, create_table_item("✗", "red", True))
            # Prázdna bunka pre hrubý kľúč
            self.table.setItem(bit_index, 7, create_table_item("", "black", True))

    def start_simulation(self):
        """Spustenie simulácie protokolu BB84"""
        try:
            # Determine whether to use custom or random bits
            if self.use_custom_bits.isChecked():
                # Get custom bits from input field
                custom_sequence = self.custom_bits_input.text().strip()

                # Validate input (only 0s and 1s)
                if not all(bit in '01' for bit in custom_sequence):
                    self.output_label.setText("Chyba: Vlastná sekvencia môže obsahovať iba 0 a 1.")
                    return

                # Make sure we have enough bits
                if len(custom_sequence) < self.num_bits:
                    self.output_label.setText(f"Chyba: Očakáva sa aspoň {self.num_bits}-bitový vstup.")
                    return

                # Convert string to list of integers and use only first num_bits
                self.alice_bits = [int(bit) for bit in custom_sequence[:self.num_bits]]
                source_text = "manuálne vygenerovanú sekvenciu bitov"
            else:
                # Use original random generation
                self.alice_bits = [random.choice([0, 1]) for _ in range(self.num_bits)]
                source_text = "náhodne vygenerovanú sekvenciu bitov"

            self.output_label.setText(f"Výstup: \nAlice použila {source_text}: "
                                      f"{''.join(map(str, self.alice_bits))}")

            # Reset všetkých kľúčových premenných
            self.current_bit = 0
            self.shared_key = []
            self.photon_in_flight = False

            # Reset animačných premenných
            self.current_step = 0
            self.animation_phase = None

            # Zastavenie všetkých timerov pred reštartom
            self.timer.stop()
            self.animation_timer.stop()

            self.start_button.setEnabled(False)

            # Reset tabuľky
            self.table.clearContents()

            # Prekresliť statické prvky
            self.draw_static_elements()

            # Spustí timer pre odosielanie fotónov (každých 1000 ms)
            self.timer.start(1000)
        except Exception as e:
            print(f"Error in start_simulation: {e}")
            import traceback
            traceback.print_exc()
            self.start_button.setEnabled(True)
            self.output_label.setText(f"Chyba pri spúšťaní simulácie: {e}")