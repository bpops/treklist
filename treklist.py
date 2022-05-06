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
from PyQt6.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtGui     import QPixmap, QIcon, QAction, QTextCursor
from PyQt6.QtCore    import Qt, QCoreApplication

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

        # set the main vertical box
        mainVBox = QVBoxLayout()
        mainVBox.setSpacing(0)
        mainVBox.setContentsMargins(2, 2, 2, 10) # ltrb
        self.tab_widget = seriesTabWidget(self)
        self.infoBar = QLabel(f"hello")#f"{self.series['num']} series")
        mainVBox.addWidget(self.tab_widget)
        mainVBox.addWidget(self.infoBar, stretch=0, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(mainVBox)

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
    """
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        tab_layout = QHBoxLayout()

        #initialize tab screen
        self.tabs = QTabWidget()
        self.tabList = []
        for i, abb in enumerate(parent.series["abbs"]):
            self.tabList.append(QWidget())
            self.tabs.addTab(self.tabList[i], abb.upper())
        
        # build all series tabs
        for i, tab in enumerate(self.tabList):
            this_tab_layout = QHBoxLayout(self.tabs)

            # series side bar
            series_info = QWidget()
            series_info_layout = QVBoxLayout()
            series_info.setMaximumWidth(300)
            img_lbl = QLabel()
            parent.tl_curs.execute(f"SELECT * FROM series WHERE imdb_id = '{parent.series['imdb_ids'][i]}'")
            record    = parent.tl_curs.fetchall()
            pix_map   = QPixmap()
            pix_map.loadFromData(record[0][5])
            img_lbl.setPixmap(pix_map)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            series_info_layout.addWidget(img_lbl, Qt.AlignmentFlag.AlignLeft)
            series_title_lbl = QLabel(parent.series["titles"][i]+"\n"+parent.series["years"][i])
            series_title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            series_info_layout.addWidget(series_title_lbl)
            series_info.setLayout(series_info_layout)
            this_tab_layout.addWidget(series_info)
            
            # add table
            data =       {'col1': ['1', '2', '3'],
                          'col2': ['4', '5', '6']}
            table_wdgt = seriesTableView(data, 3, 2)
            this_tab_layout.addWidget(table_wdgt)

            # assign layout
            tab.setLayout(this_tab_layout)

        # Add tabs to widget
        tab_layout.addWidget(self.tabs)
        self.setLayout(tab_layout)

class seriesTableView(QTableWidget):
    """
    Series Table View
    """
    def __init__(self, data, *args):
        QTableWidget.__init__(self, *args)
        self.data = data
        self.setData()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
 
    def setData(self): 
        horHeaders = []
        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)
            for m, item in enumerate(self.data[key]):
                newitem = QTableWidgetItem(item)
                self.setItem(m, n, newitem)
        self.setHorizontalHeaderLabels(horHeaders)

def main():
    app = QApplication(sys.argv)
    ex = trekListApp()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()