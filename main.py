import sys
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import logging
import traceback 


from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QMessageBox,
    QGroupBox,
    QComboBox,
    QLabel,
    QProgressBar,
    QPlainTextEdit,
    QLineEdit,
    QFileDialog,
)

from ffscrapper.ui_options import generate_breadth_search_options
from scrapper import Scrapper

logging.basicConfig(filename="debug.log", level=logging.DEBUG)


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    warningText = pyqtSignal(str)
    enableButton = pyqtSignal(bool)

    def __init__(self, scrapper, message_function, app):
        super().__init__()
        self.scrapper = scrapper
        self.message_function = message_function
        self.app = app

    def run(self):
        try:
            self.scrapper.scrape()
            self.enableButton.emit(True)
        except:
            logging.error("Klaida:" + str(sys.exc_info()))
            traceback.print_exc() 
            self.app.analyse.setEnabled(True)
            self.warningText.emit("Programoje įvyko klaida!")


class Signaller(QObject):
    signal = pyqtSignal(str)


class QTextEditLogger(logging.Handler):
    def __init__(self, parent, slotfunc):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.signaller = Signaller()
        self.signaller.signal.connect(slotfunc)

    def emit(self, record):
        msg = self.format(record)
        # thread safe
        self.signaller.signal.emit(msg)


class App(QWidget):
    def createLayoutForTables(self, outerUpperLayout):
        groupbox = QGroupBox("Lentelės")
        outerUpperLayout.addWidget(groupbox, 0, 0)
        fileSelectLayout = QVBoxLayout()

        groupbox.setLayout(fileSelectLayout)
        # Store ids
        btn = QPushButton("Parduotuvių lentelė")
        btn.clicked.connect(self.getFileForStoreIds)
        fileSelectLayout.addWidget(btn)

        # FF table
        btn = QPushButton("FF produktų lentelė")
        btn.clicked.connect(self.getFileForFFProducts)
        fileSelectLayout.addWidget(btn)

        # Producs
        btn = QPushButton("Produktų lentelė")
        btn.clicked.connect(self.getFileForProducts)
        fileSelectLayout.addWidget(btn)

        # FF Price
        btn = QPushButton("FF kainodaros lentelė")
        btn.clicked.connect(self.getFileForFFPrice)
        fileSelectLayout.addWidget(btn)

        e1 = QLineEdit()
        fileSelectLayout.addWidget(e1)
        self.designer_id = e1

    def createLayoutForAdditionalOptions(self, outerUpperLayout):
        groupbox = QGroupBox("Papildomi nustatymai")
        outerUpperLayout.addWidget(groupbox, 0, 1)

        optionsLayout = QVBoxLayout()
        groupbox.setLayout(optionsLayout)

        for option_id, widget in self.extra_options.items():
            optionsLayout.addWidget(widget)

        boxLayout = QHBoxLayout()
        optionsLayout.addLayout(boxLayout)

        boxLayout.addWidget(QLabel("Regionas"))
        boxLayout.addWidget(self.region_select_combo_box)

    def createOutputTableLayout(self, outerUpperLayout):
        groupbox = QGroupBox("Analizės rezultatai")
        outerUpperLayout.addWidget(groupbox, 0, 2)
        fileSelectLayout = QVBoxLayout()

        groupbox.setLayout(fileSelectLayout)
        btn = QPushButton("Pagrindinė lentelė")
        btn.clicked.connect(self.getFileForSaveMainTable)
        fileSelectLayout.addWidget(btn)

    def createLayoutForCheckboxes(self, outerUpperLayout):
        groupbox = QGroupBox("Analizės apimtis")
        outerUpperLayout.addWidget(groupbox, 1, 0, 1, 3)

        horizontalBox = QHBoxLayout()
        groupbox.setLayout(horizontalBox)

        menOptionsLayout = QVBoxLayout()

        for option_id, widget in self.scrape_breadth_options.items():
            if option_id.startswith("men"):
                menOptionsLayout.addWidget(widget["checkbox"])

        horizontalBox.addLayout(menOptionsLayout)

        womensOptionsLayout = QVBoxLayout()

        for option_id, widget in self.scrape_breadth_options.items():
            if option_id.startswith("women"):
                womensOptionsLayout.addWidget(widget["checkbox"])

        horizontalBox.addLayout(womensOptionsLayout)

        kids = QVBoxLayout()

        for option_id, widget in self.scrape_breadth_options.items():
            if not option_id.startswith("women") and not option_id.startswith("men"):
                kids.addWidget(widget["checkbox"])

        horizontalBox.addLayout(kids)

    def addUpperUIPortion(self):
        outerUpperLayout = QGridLayout()
        self.createLayoutForTables(outerUpperLayout)
        self.createLayoutForAdditionalOptions(outerUpperLayout)
        self.createOutputTableLayout(outerUpperLayout)
        self.createLayoutForCheckboxes(outerUpperLayout)

        # start scrapping button
        self.analyse.clicked.connect(self.scrape)
        outerUpperLayout.addWidget(self.analyse, 2, 0, 2, 3)

        return outerUpperLayout

    def addLowerUIPortion(self):
        outerDownLayout = QGridLayout()
        outerDownLayout.addWidget(self.progress_bar)

        self.logTextBox = QTextEditLogger(self, self.update_status)
        self.logTextBox.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        outerDownLayout.addWidget(self.logTextBox.widget)
        return outerDownLayout

    def __init__(self):
        super().__init__()
        # self.thread = QThread()
        self.title = "FF Produktų analizė"
        self.left = 10
        self.top = 10
        self.width = 2000
        self.height = 480

        self.products_from_ff_table = ""
        self.store_ids_table = ""
        self.products_table = ""
        self.ff_price_table = ""
        self.designer_id = None

        self.main_table_save_path = ""
        self.quantity_table_save_path = ""

        self.scrape_breadth_options = generate_breadth_search_options()

        self.region_select_combo_box = QComboBox()
        self.region_select_combo_box.addItems(
            ["de", "ru", "lt", "pl", "uk", "lv", "ee", "it"]
        )

        self.extra_options = {}
        self.extra_options["add_images"] = QCheckBox("Pridėti paveiksliukus")

        self.analyse = QPushButton("Analizuoti")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        super().__init__()

        outerUpperLayout = self.addUpperUIPortion()
        outerDownLayout = self.addLowerUIPortion()

        outerLayout = QGridLayout()
        outerLayout.addLayout(outerUpperLayout, 0, 0)
        outerLayout.addLayout(outerDownLayout, 1, 0)
        self.setLayout(outerLayout)

        self.show()

    def getFileForStoreIds(self):
        self.store_ids_table = self.getFileName()

    def getFileForFFProducts(self):
        self.products_from_ff_table = self.getFileName()

    def getFileForProducts(self):
        self.products_table = self.getFileName()

    def getFileForFFPrice(self):
        self.ff_price_table = self.getFileName()

    def getFileName(self):
        file_filter = "Excel File (*.xlsx *.xls *.csv)"
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption="Pasirinkite reikiamą lentelę",
            filter=file_filter,
            initialFilter="Excel File (*.xlsx *.xls)",
        )
        return response[0]

    def getFileForSaveMainTable(self):
        self.main_table_save_path = self.saveFileDialog()

    def getFileForSaveQuantityTable(self):
        self.quantity_table_save_path = self.saveFileDialog()

    def saveFileDialog(self):
        # options = QFileDialog.options()
        # options = QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self, "QFileDialog.getSaveFileName()", "", "Excel File (*.xlsx)"
        )
        if fileName:
            return fileName

    def scrape(self):
        if not self.store_ids_table:
            self.displayMessage("Error", "Pasirinkite parduotuvių lentelę")
            return

        if not self.products_from_ff_table:
            self.displayMessage("Error", "Pasirinkite FF produktų lentelę")
            return

        if not self.products_table:
            self.displayMessage("Error", "Pasirinkite produktų lentelę")
            return

        if not self.ff_price_table:
            self.displayMessage("Error", "Pasirinkite FF kainodaros lentelę")
            return

        if not self.main_table_save_path:
            self.displayMessage("Error", "Pasirinkite rezultatų lentelę")
            return

        logging.info("Start")
        logging.info("Store ids table: %s", self.store_ids_table)
        logging.info("Products from ff table: %s", self.products_from_ff_table)
        logging.info("Products table: %s", self.products_table)
        logging.info("Rez table: %s", self.main_table_save_path)
        logging.info("Region: %s", self.region_select_combo_box.currentText())

        category_ids = [
            option["category_id"]
            for option in self.scrape_breadth_options.values()
            if option["checkbox"].isChecked()
        ]

        scrapper = Scrapper(
            store_ids_table=self.store_ids_table,
            products_table=self.products_table,
            products_from_ff_table=self.products_from_ff_table,
            ff_price_table=self.ff_price_table,
            main_table_save_path=self.main_table_save_path,
            quantity_table_save_path=self.quantity_table_save_path,
            categories_to_scrape=category_ids,
            scrape_quantity=True,
            add_images=self.extra_options["add_images"].isChecked(),
            region=self.region_select_combo_box.currentText(),
            progress_bar_update_func=self.updateProgressBar,
            designer_id=self.designer_id.text(),
        )

        self.thread = QThread(parent=self)
        self.worker = Worker(scrapper, self.displayMessage, self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.warningText.connect(self._handleWarningText)
        self.worker.enableButton.connect(self._handleEnableButton)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # Final resets
        self.analyse.setEnabled(False)

        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )

    def _handleWarningText(self, message):
        self.displayMessage("Error", message)

    def _handleEnableButton(self, enabled):
        self.analyse.setEnabled(enabled)

    @pyqtSlot(str)
    def update_status(self, message):
        self.logTextBox.widget.appendPlainText(message)

    def displayMessage(self, status, message):
        QMessageBox.about(self, status, message)

    def updateProgressBar(self, value):
        self.progress_bar.setValue(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
