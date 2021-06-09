import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from datetime import date

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
    QMainWindow
)

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, scrapper, message_function):
        super().__init__()
        self.scrapper = scrapper
        self.message_function = message_function

    def run(self):
        try:
            self.scrapper.scrape()
        except:
            with open("log.txt", "a") as file_object:
                # Append 'hello' at the end of file
                file_object.write(str(date.today())+ "Klaida:" + str(sys.exc_info()))
        
class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = "FF Produktų analizė"
        self.left = 10
        self.top = 10
        self.width = 2000
        self.height = 480

        self.products_from_ff_table = ""
        self.store_ids_table = ""
        self.products_table = ""
        self.price_table = ""

        self.main_table_save_path = ""
        self.quantity_table_save_path = ""

        self.scrape_breadth_options = {}
        self.scrape_breadth_options["men_shoes"] = QCheckBox("Vyriski batai")
        self.scrape_breadth_options["women_shoes"] = QCheckBox("Moteriski batai")

        self.region_select_combo_box = QComboBox()
        self.region_select_combo_box.addItems(["de","en"])

        self.extra_options = {}
        self.extra_options["check_quantity"] = QCheckBox("Tikrinti likučius")
        self.extra_options["add_images"] = QCheckBox("Pridėti paveiksliukus")

        self.analise = QPushButton('Analizuoti')

        self.progress_bar = QProgressBar()
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
        outerUpperLayout.addWidget(groupbox,0, 0)
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


        # --------- Create a layout for the checkboxes
        groupbox = QGroupBox("Analizės apimtis")
        outerUpperLayout.addWidget(groupbox,0, 1)
                
        optionsLayout = QVBoxLayout()
        groupbox.setLayout(optionsLayout)

        # Add some checkboxes to the layout
        for option_id, widget in self.scrape_breadth_options.items():
            optionsLayout.addWidget(widget)

        # optionsLayout.addWidget(QCheckBox("Rubai"))

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


        # --------- Create a layout for additional options
        groupbox = QGroupBox("Papildomi nustatymai")
        outerUpperLayout.addWidget(groupbox,1, 0, 1, 3)
                
        optionsLayout = QVBoxLayout()
        groupbox.setLayout(optionsLayout)

        for option_id, widget in self.extra_options.items():
            optionsLayout.addWidget(widget)

        boxLayout = QHBoxLayout()
        optionsLayout.addLayout(boxLayout)

        boxLayout.addWidget(QLabel("Regionas"))
        boxLayout.addWidget(self.region_select_combo_box)

        # start scrapping button
        self.analise.clicked.connect(self.scrape)
        outerUpperLayout.addWidget(self.analise, 2, 0, 2, 3)

        outerDownLayout = QGridLayout()

        outerDownLayout.addWidget(self.progress_bar)

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
    
    def getFileName(self):
        file_filter = 'Excel File (*.xlsx *.xls *.csv)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Pasirinkite reikamą lentelę',
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
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","Excel File (*.xlsx)", options=options)
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

        if not self.price_table:
            self.displayMessage("Error", "Pasirinkite kainodaros lentelę")
            return

        if not self.main_table_save_path:
            self.displayMessage("Error", "Pasirinkite rezultatų lentelę")
            return

        if not self.quantity_table_save_path:
            self.displayMessage("Error", "Pasirinkite likučių rezultatų lentelę")
            return

        print(self.store_ids_table)
        print(self.products_from_ff_table)
        print(self.products_table)
        print(self.price_table)
        print(self.main_table_save_path)
        print(self.quantity_table_save_path)
        print(self.scrape_breadth_options["men_shoes"].isChecked())
        print(self.scrape_breadth_options["women_shoes"].isChecked())
        print(self.extra_options["check_quantity"].isChecked())
        print(self.region_select_combo_box.currentText())

        print(self.progress_bar.value())

        scrapper = Scrapper(self.store_ids_table,
                            self.products_table,
                            self.products_from_ff_table,
                            self.price_table,
                            self.main_table_save_path,
                            self.quantity_table_save_path,
                            self.scrape_breadth_options["men_shoes"].isChecked(),
                            self.scrape_breadth_options["women_shoes"].isChecked(),
                            self.extra_options["check_quantity"].isChecked(),
                            self.extra_options["add_images"].isChecked(),
                            self.region_select_combo_box.currentText(),
                            self.updateProgressBar)        
        
        self.thread = QThread()
        self.worker = Worker(scrapper, self.displayMessage)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # Final resets
        self.analise.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Long-Running Step: 0")
        )

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