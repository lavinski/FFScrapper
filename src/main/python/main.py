import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from datetime import date
import logging

from scrapper import Scrapper

from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QCheckBox,
    QBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QGroupBox,
    QComboBox,
    QLabel,
    QProgressBar,
    QMainWindow,
    QPlainTextEdit
)

logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.DEBUG)


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    warningText = pyqtSignal(str)

    def __init__(self, scrapper, message_function, app):
        super().__init__()
        self.scrapper = scrapper
        self.message_function = message_function
        self.app = app

    def run(self):
        try:
            self.scrapper.scrape()
        except:
            logging.error("Klaida:" + str(sys.exc_info()))
            self.app.analise.setEnabled(True)
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
        self.price_table = ""
        self.ff_price_table = ""

        self.main_table_save_path = ""
        self.quantity_table_save_path = ""

        self.scrape_breadth_options = {}
        self.scrape_breadth_options["men_shoes"] = {"checkbox": QCheckBox("Vyriška avalynė"), "category_id": "135968"}
        self.scrape_breadth_options["men_clothing"] = {"checkbox": QCheckBox("Vyriški drabužiai"),
                                                       "category_id": "136330"}
        self.scrape_breadth_options["men_bags"] = {"checkbox": QCheckBox("Vyriškos rankinės"), "category_id": "135970"}
        self.scrape_breadth_options["men_accesories"] = {"checkbox": QCheckBox("Vyriški aksesuarai"),
                                                         "category_id": "135972"}
        self.scrape_breadth_options["men_watches"] = {"checkbox": QCheckBox("Vyriški laikrodžiai"),
                                                      "category_id": "137177"}

        self.scrape_breadth_options["women_shoes"] = {"checkbox": QCheckBox("Moteriška avalynė"),
                                                      "category_id": "136301"}
        self.scrape_breadth_options["women_clothing"] = {"checkbox": QCheckBox("Moteriški drabužiai"),
                                                         "category_id": "135967"}
        self.scrape_breadth_options["women_bags"] = {"checkbox": QCheckBox("Moteriškos rankinės"),
                                                     "category_id": "135971"}
        self.scrape_breadth_options["women_accesories"] = {"checkbox": QCheckBox("Moteriški aksesuarai"),
                                                           "category_id": "135973"}
        self.scrape_breadth_options["women_watches"] = {"checkbox": QCheckBox("Moteriški papuošalai"),
                                                        "category_id": "135977"}

        self.scrape_breadth_options["baby_girls_shoes"] = {"checkbox": QCheckBox("Baby Girls avalynė"),
                                                           "category_id": "136656"}
        self.scrape_breadth_options["baby_girls_clothing"] = {"checkbox": QCheckBox("Baby Girls rūbai"),
                                                              "category_id": "136657"}
        self.scrape_breadth_options["baby_boys_shoes"] = {"checkbox": QCheckBox("Baby Boys avalynė"),
                                                          "category_id": "136653"}
        self.scrape_breadth_options["baby_boys_clothing"] = {"checkbox": QCheckBox("Baby Boys rūbai"),
                                                             "category_id": "136654"}

        self.scrape_breadth_options["kids_girls_shoes"] = {"checkbox": QCheckBox("Kids Girls avalynė"),
                                                           "category_id": "136651"}
        self.scrape_breadth_options["kids_girls_clothing"] = {"checkbox": QCheckBox("Kids Girls rūbai"),
                                                              "category_id": "136650"}
        self.scrape_breadth_options["kids_boys_shoes"] = {"checkbox": QCheckBox("Kids Boys avalynė"),
                                                          "category_id": "136648"}
        self.scrape_breadth_options["kids_boys_clothing"] = {"checkbox": QCheckBox("Kids Boys rūbai"),
                                                             "category_id": "136647"}

        self.scrape_breadth_options["teens_girls_shoes"] = {"checkbox": QCheckBox("Teens Girls avalynė"),
                                                            "category_id": "136993"}
        self.scrape_breadth_options["teens_girls_clothing"] = {"checkbox": QCheckBox("Teens Girls rūbai"),
                                                               "category_id": "136991"}
        self.scrape_breadth_options["teens_boys_shoes"] = {"checkbox": QCheckBox("Teens Boys avalynė"),
                                                           "category_id": "136990"}
        self.scrape_breadth_options["teens_boys_clothing"] = {"checkbox": QCheckBox("Teens Boys rūbai"),
                                                              "category_id": "136988"}

        self.region_select_combo_box = QComboBox()
        self.region_select_combo_box.addItems(["de", "ru", "lt", "pl", "uk", "lv", "ee"])

        self.extra_options = {}
        self.extra_options["check_quantity"] = QCheckBox("Tikrinti likučius")
        self.extra_options["add_images"] = QCheckBox("Pridėti paveiksliukus")

        self.analise = QPushButton('Analizuoti')

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # self.openFileNameDialog()
        # self.openFileNamesDialog()
        # self.saveFileDialog()

        super().__init__()
        # Create an outer layout
        outerUpperLayout = QGridLayout()

        # --------- Create a layout for tables
        groupbox = QGroupBox("Lentelės")
        outerUpperLayout.addWidget(groupbox, 0, 0)
        fileSelectLayout = QVBoxLayout()

        groupbox.setLayout(fileSelectLayout)
        # Store ids
        btn = QPushButton('Parduotuvių lentelė')
        btn.clicked.connect(self.getFileForStoreIds)
        fileSelectLayout.addWidget(btn)

        # FF table
        btn = QPushButton('FF produktų lentelė')
        btn.clicked.connect(self.getFileForFFProducts)
        fileSelectLayout.addWidget(btn)

        # Producs
        btn = QPushButton('Produktų lentelė')
        btn.clicked.connect(self.getFileForProducts)
        fileSelectLayout.addWidget(btn)

        # Producs
        btn = QPushButton('Kainodaros lentelė')
        btn.clicked.connect(self.getFileForPrice)
        fileSelectLayout.addWidget(btn)

        # FF Price
        btn = QPushButton('FF kainodaros lentelė')
        btn.clicked.connect(self.getFileForFFPrice)
        fileSelectLayout.addWidget(btn)

        # --------- Create a layout for additional options
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

        # --------- Create a output tables
        groupbox = QGroupBox("Analizės rezultatai")
        outerUpperLayout.addWidget(groupbox, 0, 2)
        fileSelectLayout = QVBoxLayout()

        groupbox.setLayout(fileSelectLayout)
        # Store ids
        btn = QPushButton('Pagrindinė lentelė')
        btn.clicked.connect(self.getFileForSaveMainTable)
        fileSelectLayout.addWidget(btn)

        # FF table
        btn = QPushButton('Likučių lentelė')
        btn.clicked.connect(self.getFileForSaveQuantityTable)
        fileSelectLayout.addWidget(btn)

        # --------- Create a layout for the checkboxes
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

        outerDownLayout = QGridLayout()

        outerDownLayout.addWidget(self.progress_bar)

        # logger
        self.logTextBox = QTextEditLogger(self, self.update_status)
        self.logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        outerDownLayout.addWidget(self.logTextBox.widget)

        # start scrapping button
        self.analise.clicked.connect(self.scrape)
        outerUpperLayout.addWidget(self.analise, 2, 0, 2, 3)

        # main layout
        outerLayout = QGridLayout()
        outerLayout.addLayout(outerUpperLayout, 0, 0)
        outerLayout.addLayout(outerDownLayout, 1, 0)

        # Set the window's main layout
        self.setLayout(outerLayout)

        self.show()

    def getFileForStoreIds(self):
        self.store_ids_table = self.getFileName()

    def getFileForFFProducts(self):
        self.products_from_ff_table = self.getFileName()

    def getFileForProducts(self):
        self.products_table = self.getFileName()

    def getFileForPrice(self):
        self.price_table = self.getFileName()

    def getFileForFFPrice(self):
        self.ff_price_table = self.getFileName()

    def getFileName(self):
        file_filter = 'Excel File (*.xlsx *.xls *.csv)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Pasirinkite reikiamą lentelę',
            directory=os.getcwd(),
            filter=file_filter,
            initialFilter='Excel File (*.xlsx *.xls)'
        )
        return response[0]

    def getFileForSaveMainTable(self):
        self.main_table_save_path = self.saveFileDialog()

    def getFileForSaveQuantityTable(self):
        self.quantity_table_save_path = self.saveFileDialog()

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "", "Excel File (*.xlsx)",
                                                  options=options)
        if fileName:
            return fileName

    def scrape(self):
        # if not self.store_ids_table:
        #     self.displayMessage("Error", "Pasirinkite parduotuvių lentelę")
        #     return

        # if not self.products_from_ff_table:
        #     self.displayMessage("Error", "Pasirinkite FF produktų lentelę")
        #     return

        # if not self.products_table:
        #     self.displayMessage("Error", "Pasirinkite produktų lentelę")
        #     return

        # if not self.price_table:
        #     self.displayMessage("Error", "Pasirinkite kainodaros lentelę")
        #     return

        # if not self.ff_price_table:
        #     self.displayMessage("Error", "Pasirinkite FF kainodaros lentelę")
        #     return

        # if not self.main_table_save_path:
        #     self.displayMessage("Error", "Pasirinkite rezultatų lentelę")
        #     return

        # if not self.quantity_table_save_path and self.extra_options["check_quantity"].isChecked():
        #     self.displayMessage("Error", "Pasirinkite likučių rezultatų lentelę")
        #     return

        logging.info("Start")
        logging.info("Store ids table: %s", self.store_ids_table)
        logging.info("Products from ff table: %s", self.products_from_ff_table)
        logging.info("Products table: %s", self.products_table)
        logging.info("Price table: %s", self.price_table)
        logging.info("Rez table: %s", self.main_table_save_path)
        logging.info("Quantity rez table: %s", self.quantity_table_save_path)
        logging.info("Check quantity: %s", self.extra_options["check_quantity"].isChecked())
        logging.info("Region: %s", self.region_select_combo_box.currentText())

        category_ids = [option["category_id"] for option in self.scrape_breadth_options.values() if
                        option["checkbox"].isChecked()]

        scrapper = Scrapper(self.store_ids_table,
                            self.products_table,
                            self.products_from_ff_table,
                            self.price_table,
                            self.ff_price_table,
                            self.main_table_save_path,
                            self.quantity_table_save_path,
                            category_ids,
                            self.extra_options["check_quantity"].isChecked(),
                            self.extra_options["add_images"].isChecked(),
                            self.region_select_combo_box.currentText(),
                            self.updateProgressBar)

        # stop all threads

        self.thread = QThread(parent=self)
        self.worker = Worker(scrapper, self.displayMessage, self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.warningText.connect(self._handleWarningText)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # Final resets
        self.analise.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.analise.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )

    def _handleWarningText(self, message):
        self.displayMessage("Error", message)

    @pyqtSlot(str)
    def update_status(self, message):
        self.logTextBox.widget.appendPlainText(message)

    def displayMessage(self, status, message):
        QMessageBox.about(self, status, message)

    def updateProgressBar(self, value):
        self.progress_bar.setValue(value)

    # def openFileNameDialog(self):
    #     options = QFileDialog.Options()
    #     options |= QFileDialog.DontUseNativeDialog
    #     fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
    #     if fileName:
    #         print(fileName)

    # def openFileNamesDialog(self):
    #     options = QFileDialog.Options()
    #     options |= QFileDialog.DontUseNativeDialog
    #     files, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;Python Files (*.py)", options=options)
    #     if files:
    #         print(files)

    # def saveFileDialog(self):
    #     options = QFileDialog.Options()
    #     options |= QFileDialog.DontUseNativeDialog
    #     fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
    #     if fileName:
    #         print(fileName)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
