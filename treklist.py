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
from PyQt6.QtWidgets import QTabWidget
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

class trekListApp(QMainWindow):

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

        # generate tabs
        self.tab_widget = tabWidget(self)
        self.setCentralWidget(self.tab_widget)


    def centerWindow(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)


class tabWidget(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # pull in series info
        parent.tl_df = pd.read_sql_query("SELECT * FROM series", parent.tl_conn)
        titles = parent.tl_df['title'].tolist()
        abbs   = parent.tl_df['abb'].tolist()
        years  = parent.tl_df['year'].tolist()
        n_series = len(abbs)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabList = []
        for i, series in enumerate(abbs):
            self.tabList.append(QWidget())
            self.tabs.addTab(self.tabList[i], abbs[i].upper())
        
        for i, tab in enumerate(self.tabList):
            tab.layout = QVBoxLayout(self)
            tab.layout.addWidget(QLabel(titles[i]))
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