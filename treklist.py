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
from PyQt6.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt6.QtGui     import QPixmap, QIcon, QAction, QTextCursor, QFont
from PyQt6.QtCore    import Qt, QCoreApplication

import sys
import omdb
import sqlite3
import pandas as pd
import os
import requests
import io
import PIL.Image as Image
import math

# dev vs bundled paths
try:
   wd = sys._MEIPASS
except AttributeError:
   wd = os.path.dirname(os.path.realpath(__file__))
os.chdir(wd)

# window size
init_win_width   = 1400
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

        # initialize info for info label
        self.n_eps  = 0
        self.n_mins = 0

        # set the main vertical box
        mainVBox = QVBoxLayout()
        mainVBox.setSpacing(0)
        mainVBox.setContentsMargins(2, 2, 2, 10) # ltrb
        self.tab_widget = seriesTabWidget(self)
        
        # set the info bar
        days = math.floor(self.n_mins / 1440)
        leftover_minutes = self.n_mins % 1440
        hours = math.floor(leftover_minutes / 60)
        mins = self.n_mins - (days*1440) - (hours*60)
        self.infoBar = QLabel(f"{self.series['num']} series, {self.n_eps} episodes, {days} days {hours} hours {mins} mins runtime")
        
        # add widgets to layout
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
            series_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            series_info.setMaximumWidth(300)
            img_lbl = QLabel()
            parent.tl_curs.execute(f"SELECT * FROM series WHERE imdb_id = '{parent.series['imdb_ids'][i]}'")
            record    = parent.tl_curs.fetchall()
            pix_map   = QPixmap()
            pix_map.loadFromData(record[0][6])
            #pix_map = pix_map.scaled(img_lbl.size().width(), img_lbl.size().height(),
            #    aspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio,
            #    transformMode   = Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix_map)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            series_info_layout.addWidget(img_lbl)#, Qt.AlignmentFlag.AlignLeft)
            series_title_lbl = QLabel(parent.series["titles"][i]+"\n"+parent.series["years"][i])
            series_title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            series_info_layout.addWidget(series_title_lbl)
            series_info.setLayout(series_info_layout)
            this_tab_layout.addWidget(series_info)
            
            # add table
            df = pd.read_sql_query(f"SELECT * FROM {parent.series['abbs'][i]}", parent.tl_conn)
            #df = df.drop(columns=['imdb_id','poster'])
            df = df.filter(['season', 'episode', 'title', 'plot', 'released', 'runtime'], axis=1)
            df = df.astype({"season": str, "episode": str}, errors='raise') 
            data = df.to_dict('list')
            n_cols = len(data.keys())
            n_rows = len(df)
            table_wdgt = seriesTableView(data, n_rows, n_cols)
            this_tab_layout.addWidget(table_wdgt)

            # assign layout
            tab.setLayout(this_tab_layout)

            # calculate num episodes, minutes
            parent.n_eps += len(df)
            for runtime in data['runtime']:
                if runtime != "N/A":
                    this_ep_rt = int(''.join(list(filter(str.isdigit, runtime))))
                    parent.n_mins += this_ep_rt

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
        #self.data = {k : data[k] for k in key_order}
        self.setData()
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()
        self.setAlternatingRowColors(True)
        #self.setDragEnabled(True)

        #self.setDragDropMode()

        # set correct orders and labels
        self.setColumnCount(self.horizontalHeader().count() + 1)
        self.setHorizontalHeaderLabels(['E', 'Plot', 'Released', 'Runtime', 'S', 'Title', 'Screen'])
        self.horizontalHeader().moveSection(4,0)
        self.horizontalHeader().moveSection(5,2)
        self.horizontalHeader().moveSection(4,3)
        self.horizontalHeader().moveSection(6,3)
        #self.resizeColumnsToContents()   
        #self.horizontalHeader().moveSection(7, )
        self.verticalHeader().setDefaultSectionSize(160)  
        self.setColumnWidth(self.horizontalHeader().logicalIndex(0), 30)  # season
        self.setColumnWidth(self.horizontalHeader().logicalIndex(1), 30)  # episode
        self.setColumnWidth(self.horizontalHeader().logicalIndex(2), 130) # title
        self.setColumnWidth(self.horizontalHeader().logicalIndex(3), 200) # screenshot
        self.setColumnWidth(self.horizontalHeader().logicalIndex(4), 90)  # released
        self.setColumnWidth(self.horizontalHeader().logicalIndex(5), 300) # plot
        self.setColumnWidth(self.horizontalHeader().logicalIndex(6), 70)  # runtime
        
        # make headers bold
        font = QFont()
        font.setBold(True)
        self.horizontalHeader().setFont(font)
 
        # make nothing editable
        #self.setEditTriggers(QAbstractItemView.)

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