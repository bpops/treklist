#
#                __________  ________ __ __    _______________
#               /_  __/ __ \/ ____/ //_// /   /  _/ ___/_  __/
#                / / / /_/ / __/ / ,<  / /    / / \__ \ / /
#               / / / _, _/ /___/ /| |/ /____/ / ___/ // /
#              /_/ /_/ |_/_____/_/ |_/_____/___//____//_/
#
#                      a Star Trek episode tracker
#
#                   https://github.com/bpops/treklist

# pyqt6 requirements
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QGroupBox, QPushButton, QHBoxLayout, QLineEdit
from PyQt6.QtWidgets import QCheckBox, QComboBox, QSlider, QFileDialog
from PyQt6.QtWidgets import QSizePolicy, QMenuBar, QMainWindow, QMenu, QTextBrowser
from PyQt6.QtWidgets import QTabWidget, QTableWidget
from PyQt6.QtGui     import QPixmap, QIcon, QAction, QTextCursor
from PyQt6.QtCore    import Qt, QCoreApplication#, pyqtSignal

import sys
import omdb
import sqlite3
import pandas as pd
import os
import requests
import io
import PIL.Image as Image

# dev vs bundled paths
try:
   wd = sys._MEIPASS
except AttributeError:
   wd = os.path.dirname(os.path.realpath(__file__))
os.chdir(wd)

# window size
init_win_width   = 1200
init_win_height  = 600

class trekListApp(QWidget):

    def __init__(self):
        super().__init__()

        # init UI
        self.resize(init_win_width, init_win_height)
        self.setWindowTitle('TrekList v0.1')
        self.show();
        self.centerWindow()

        # initialize databases
        tl_filename = "treklist.db"
        self.tl_conn = sqlite3.connect(tl_filename)
        self.tl_curs = self.tl_conn.cursor()

        # query databases
        self.querySeriesDB()


        # generate series Tab Widget
        self.tab_widget = seriesTabWidget(self)
        #self.setCentralWidget(self.tab_widget)

        # set the main vertical box
        self.mainVBox = QVBoxLayout()
        self.mainVBox.setSpacing(0)
        self.mainVBox.setContentsMargins(2, 2, 2, 10) # ltrb
        self.statusBar = QLabel(f"{self.series['num']} series")
        self.mainVBox.addWidget(self.tab_widget)
        self.mainVBox.addWidget(self.statusBar, stretch=0, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(self.mainVBox)        

    def centerWindow(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)

    def querySeriesDB(self):
        """
        Query the Series Database

        This function will build a series dictionary with relevant information
        """

        # pull in series info
        self.series = dict()
        self.series["df"]       = pd.read_sql_query("SELECT * FROM series", self.tl_conn)
        self.series["titles"]   = self.series["df"]['title'].tolist()
        self.series["abbs"]     = self.series["df"]['abb'].tolist()
        self.series["years"]    = self.series["df"]['year'].tolist()
        self.series["imdb_ids"] = self.series["df"]['imdb_id'].tolist()
        self.series["num"]      = len(self.series["abbs"])

class seriesTabWidget(QWidget):
    """
    Series Tab Widget

    This widget is the primary series tab widget
    """
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # initialize tab screen
        self.tabs = QTabWidget()
        self.tabList = []
        for i, abb in enumerate(parent.series["abbs"]):
            self.tabList.append(QWidget())
            self.tabs.addTab(self.tabList[i], abb.upper())
        
        # build all series tabs
        for i, tab in enumerate(self.tabList):
            tab.layout = QHBoxLayout(self)
            series_info = QWidget()
            series_info.layout = QVBoxLayout(tab)
            img_lbl = QLabel()
            series_info.layout.addWidget(img_lbl)
            series_info.layout.addWidget(QLabel(parent.series["titles"][i]+"\n"+parent.series["years"][i]))

            # pull in poster
            parent.tl_curs.execute(f"SELECT * FROM series WHERE imdb_id = '{parent.series['imdb_ids'][i]}'")
            record    = parent.tl_curs.fetchall()
            pix_map   = QPixmap()
            pix_map.loadFromData(record[0][5])
            img_lbl.setPixmap(pix_map)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            # add table
            #table_wdgt = QTableWidget()
            #table_data = {'col1': ['1', '2', '3'],
            #              'col2': ['4', '5', '6']}
            #self.data = table_data
            #table_wdgt.setData()
            #table_wdgt.resizeColumnsToContents()
            #table_wdgt.resizeRowsToContents()
            #tab.layout.addWidget(table_wdgt)

            #tab.layout.addWidget()
            tab.setLayout(tab.layout)

        # Create first tab
        #self.tab1.layout = QVBoxLayout(self)
        #self.pushButton1 = QPushButton("PyQt5 button")
        #self.tab1.layout.addWidget(self.pushButton1)
        #self.tab1.setLayout(self.tab1.layout)
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    ex = trekListApp()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()