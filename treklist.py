#
#                __________  ________ __ __    _______________
#               /_  __/ __ \/ ____/ //_// /   /  _/ ___/_  __/
#                / / / /_/ / __/ / ,<  / /    / / \__ \ / /
#               / / / _, _/ /___/ /| |/ /____/ / ___/ // /
#              /_/ /_/ |_/_____/_/ |_/_____/___//____//_/
#
#                      a Star Trek episode tracker
#                   https://github.com/bpops/treklist
#

from   appdirs         import user_data_dir
from   datetime        import datetime
from   http.client     import PRECONDITION_REQUIRED
import math
import os
import pandas          as     pd
import platform
from   PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from   PyQt6.QtWidgets import QMainWindow, QGridLayout, QDialog
from   PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QTableWidgetItem
from   PyQt6.QtWidgets import QTabWidget, QTableWidget
from   PyQt6.QtWidgets import QCheckBox, QPushButton, QDateEdit
from   PyQt6.QtWidgets import QMenuBar, QTextBrowser, QFileDialog
from   PyQt6.QtGui     import QPixmap, QFont, QAction
from   PyQt6.QtCore    import Qt, QDate
import shutil
import sqlite3
import sys
import yaml
from   yaml.loader     import SafeLoader

# defaults
main_win_width       = 1430
main_win_height      = 800
series_sidebar_width = 300
series_tbl_hdrs      = ('season', 'episode', 'title', 'poster', 'released', 'plot', 'runtime')
series_tbl_hdr_names = ('S',      'E',       'Title', 'Screen', 'Released', 'Plot', 'Runtime')
series_tbl_widths    = (30,       30,        120,     200,      90,         280,    80)
series_tbl_row_hgt   = 150
usr_tbl_hdrs         = ('watched', 'last_watched')#, 'rating')
usr_tbl_names        = ('✓',       'Watched')#,      'Rate')
usr_tbl_widths       = (30,        125)#,            50)
movies_tbl_hdrs      = ('title',  'poster',  'released', 'plot', 'director', 'runtime')
movies_tbl_hdr_names = ('Title',  'Poster',  'Released', 'Plot', 'Director', 'Runtime')
movies_tbl_widths    = (180,      300,        100,       350,     100,       80)
movies_tbl_row_hgt   = 400

# change working directory
try:                    # bundled path
   wd = sys._MEIPASS
except AttributeError:  # python script
   wd = os.path.dirname(os.path.realpath(__file__))
wd = f"{wd}/"
os.chdir(wd)

# determine operating system
on_macos = platform.uname().system.startswith('Darw')

# determine data directory - this is where the
# user sql database will be stored
data_dir = user_data_dir("TrekList") + "/"
log_file = data_dir + "user.db"
set_file = data_dir + "settings.yaml"

# make data directory and copy fresh user log
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
if not os.path.exists(log_file):
    shutil.copyfile(f"{wd}/user.db", log_file)
if not os.path.exists(set_file):
    shutil.copyfile(f"{wd}/settings.yaml", set_file)

def getMain(widget):
    """
    Get the main window
    """
    widget = widget or QApplication.activeWindow()
    if widget is None:
        return
    parent = widget.parent()
    if parent is None:
        return widget
    return getMain(parent) 

class trekListApp(QMainWindow):
    """
    Main TrekList App Window
    """
    
    def __init__(self):
        super().__init__()
    
        # init UI
        self.resize(main_win_width, main_win_height)
        self.setWindowTitle('TrekList')

        # initialize treklist database
        self.tl_filename = f"{wd}treklist.db"
        self.tl_conn = sqlite3.connect(self.tl_filename)
        self.tl_curs = self.tl_conn.cursor()

        # initialize user database
        self.usr_filename = log_file
        self.usr_conn = sqlite3.connect(self.usr_filename)
        self.usr_curs = self.usr_conn.cursor()

        # query databases
        self.dfs = dict()    # holds all dataframes
        self.querySeries()
        self.queryEpisodes()
        self.queryMovies()
        self.queryUserLog()

        # read settings
        self.readSettings()
    
        # set up main vertical layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(2, 2, 2, 10) # ltrb
        wdw = QWidget()
        wdw.setLayout(self.layout)
        self.setCentralWidget(wdw)

        # tab widget
        self.tab_widget = seriesTabsWidget(self)
        self.layout.addWidget(self.tab_widget)

        # info bar
        self.info_bar = QLabel()
        self.layout.addWidget(self.info_bar, stretch=0,
            alignment=Qt.AlignmentFlag.AlignHCenter)
        self.updateInfoBar()

        # menu bar contents
        save_act  = QAction("Save User Log...", self)
        save_act.triggered.connect(self.saveLog)
        load_act  = QAction("Load User Log...", self)
        load_act.triggered.connect(self.loadLog)
        gpl_act   = QAction("License: GPL-3.0", self)
        gpl_act.triggered.connect(self.showGPL)
        cc_act    = QAction("License: CC BY-NC 4.0", self)
        cc_act.triggered.connect(self.showCC)
        abt_act   = QAction("More Info", self)
        abt_act.triggered.connect(self.showAbout)

        # generate menu bar
        if on_macos:
            self.menu_bar = QMenuBar()
            self.menu_bar.setNativeMenuBar(True)
        else:
            self.menu_bar = self.menuBar()

        # file menu
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction(save_act)
        file_menu.addAction(load_act)

        # help menu
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction(gpl_act)
        help_menu.addAction(cc_act)
        help_menu.addAction(abt_act)
    
        self.show();

    def centerWindow(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)

    def restart(self):
        """
        Restarts the application
        """

        # setup modal dialog
        dlg_wgt = QDialog()
        ok_btn  = QPushButton("Okay")
        ok_btn.clicked.connect(dlg_wgt.close)
        dlg_txt = QLabel()
        dlg_txt.setText("TrekList will now restart.")
        layout  = QVBoxLayout()
        layout.addWidget(dlg_txt)
        layout.addWidget(ok_btn)
        dlg_wgt.setLayout(layout)

        # execute the dialog widget
        dlg_wgt.exec()

        # peform restart
        python = sys.executable
        os.execl(python, python, * sys.argv)

    def saveLog(self):
        """
        Save the User Log to file
        """
        save_pth = QFileDialog.getSaveFileName(self, 'Save User Log')
        if save_pth[0]:
            shutil.copyfile(self.usr_filename, save_pth[0])

    def loadLog(self):
        """
        Load the User Log from file
        """
        load_pth = QFileDialog.getOpenFileName(self, 'Load User Log')
        if load_pth[0]:
            shutil.copyfile(load_pth[0], self.usr_filename)
            self.restart()

    def showGPL(self):
        """
        Show the GPL License
        """
        self.gpl_win = gplWindow()
    
    def showCC(self):
        """
        Show the CC License
        """
        self.cc_win = ccWindow()

    def showAbout(self):
        """
        Show the About Window
        """
        self.abt_win = aboutWindow()

    def readSettings(self):
        """
        Read the settings file
        """
        with open("settings.yaml") as f:
            self.settings = yaml.load(f, Loader=SafeLoader)    

    def querySeries(self):
        """
        Query the Series SQL Database
        """
        self.series             = dict()
        self.dfs["series"]      = pd.read_sql_query("SELECT * FROM series", self.tl_conn)
        self.series["titles"]   = self.dfs["series"]['title'].tolist()
        self.series["abbs"]     = self.dfs["series"]['abb'].tolist()
        self.series["years"]    = self.dfs["series"]['year'].tolist()
        self.series["imdb_ids"] = self.dfs["series"]['imdb_id'].tolist()
        self.n_series           = len(self.dfs["series"])

    def queryEpisodes(self):
        """
        Query the Episodes SQL Database
        """

        # initialize vars for info label
        self.n_eps  = 0
        self.n_mins = 0

        # query all
        for abb in self.dfs["series"]["abb"].tolist():

            # query and determine num eps
            self.dfs[abb] = pd.read_sql_query(f"SELECT * FROM {abb}",
                self.tl_conn)
            self.n_eps += len(self.dfs[abb])
        
            # determine num mins total
            for i, row in self.dfs[abb].iterrows():
                runtime = row['runtime']
                if runtime != "N/A":
                    self.n_mins += int(''.join(list(filter(str.isdigit,
                        runtime))))

            # sort by season, episode
            self.dfs[abb].sort_values(by=['season', 'episode'], inplace=True)

    def queryMovies(self):
        """
        Query the Movies SQL Database
        """

        # query
        self.dfs["mov"] = pd.read_sql_query(f"SELECT * FROM mov", self.tl_conn)
        self.n_movies   = len(self.dfs["mov"])
        for i, row in self.dfs["mov"].iterrows():
            runtime = row['runtime']
            if runtime != "N/A":
                self.n_mins += int(''.join(list(filter(str.isdigit,
                        runtime))))

    def queryUserLog(self):
        """
        Query the User SQL Database
        """
        self.dfs["usr"] = pd.read_sql_query(f"SELECT * FROM log", self.usr_conn)

    def getUserItem(self, imdb_id, hdr):
        """
        Get User Log Item
        """

        def_values = {"watched": False,
                      "last_watched": None,
                     }
        def_value  = def_values[hdr]
        res = self.dfs["usr"][self.dfs["usr"]["imdb_id"] == imdb_id][hdr]
        if len(res) > 0:
            value = res.values[0]
        else:
            value = def_value
        if value != value: # correct for possible nans
            value = False

        return value

    def setUserItem(self, imdb_id, **kwargs):
        """
        Set User Log Item in SQL database
        """

        # get info
        df = pd.read_sql_query(f"SELECT * FROM log WHERE imdb_id == '{imdb_id}'", self.usr_conn)
        key = list(kwargs.keys())[0]
        val = kwargs[key]

        # update the record
        if len(df) > 0: # record exists
            if isinstance(val, int):
                cmd = f"UPDATE log SET {key} = {int(val)} WHERE imdb_id = '{imdb_id}'"
            elif val == "NULL":
                cmd = f"UPDATE log SET {key} = NULL WHERE imdb_id = '{imdb_id}'"
            else:
                cmd = f"UPDATE log SET {key} = '{val}' WHERE imdb_id = '{imdb_id}'"
        else:           # record does not exist
            if isinstance(val, int):
                cmd = f"INSERT INTO log (imdb_id, {key}) VALUES('{imdb_id}', {int(val)})"
            elif val == "NULL":
                cmd = f"INSERT INTO log (imdb_id, {key}) VALUES('{imdb_id}', NULL)"   
            else:
                cmd = f"INSERT INTO log (imdb_id, {key}) VALUES('{imdb_id}', '{val}')"   
        self.usr_conn.execute(cmd)
        self.usr_conn.commit()

    def getPoster(self, abb, imdb_id):
        """
        Retreive poster from database

        Returns
        -------
        pix_map : QPixMap
        """
        df = self.dfs[abb]
        img_data = df[df['imdb_id'] == imdb_id]['poster'].values[0]
        pix_map  = QPixmap()
        pix_map.loadFromData(img_data)
        return pix_map

    def updateInfoBar(self):
        """
        Updates the info bar with series, eps, mins, etc.
        """
        days     = math.floor(self.n_mins / 1440)
        rem_mins = self.n_mins % 1440
        hours    = math.floor(rem_mins / 60)
        mins     = self.n_mins - (days*1440) - (hours*60)
        info_txt = f"{self.n_series} series, {self.n_eps} episodes, " + \
                   f"{self.n_movies} movies, " + \
                   f"{days} days {hours} hours {mins} mins runtime"
        self.info_bar.setText(info_txt)

    def resizeEvent(self, event):
        return super().resizeEvent(event)

class seriesTabsWidget(QWidget):
    """
    Series Tabs Widget
    """
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout   = QHBoxLayout()

        #initialize tab screen
        self.tabs     = QTabWidget()
        self.tab_list = []
        for i, abb in enumerate(parent.dfs["series"]["abb"]):
            self.tab_list.append(QWidget())
            self.tabs.addTab(self.tab_list[i], abb.upper())

        # add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # build each series tabs
        for i, tab in enumerate(self.tab_list):

            # setup layout
            tab_layout  = QHBoxLayout()
            tab.setLayout(tab_layout)

            # set imdb_id for this tab
            tab.imdb_id = parent.dfs["series"]["imdb_id"][i]
            tab.abb = parent.dfs["series"]["abb"][i]

            # series side bar
            series_widg = seriesSideBarWidget(tab.abb, tab.imdb_id)
            tab_layout.addWidget(series_widg)
            series_widg.populate()

            # series table
            series_tbl = seriesTableWidget(tab.abb)
            tab_layout.addWidget(series_tbl, stretch=1)
            series_tbl.populate()

        # initialize movies tab
        movies_tab = QWidget()
        self.tab_list.append(movies_tab)
        self.tabs.addTab(movies_tab, "MOV")
        tab_layout = QHBoxLayout()
        movies_tab.setLayout(tab_layout)

        # build movies tab
        movies_tbl = moviesTableWidget()
        tab_layout.addWidget(movies_tbl)
        movies_tbl.populate()

class seriesSideBarWidget(QWidget):
    """
    Series Side Bar Widget
    """
    def __init__(self, abb, imdb_id):
        super(QWidget, self).__init__()

        # initialize layout
        self.abb     = abb
        self.imdb_id = imdb_id
        self.setFixedWidth(series_sidebar_width)
        self.layout  = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setContentsMargins(0, 0, 11, 11)
        self.setLayout(self.layout)

    def populate(self):

        # add series title
        df = getMain(self).dfs["series"]
        df = df[df['imdb_id'] == self.imdb_id]
        title = df['title'].values[0]
        title_label = QLabel(title)
        font = QFont()
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(title_label)

        # add years
        year = df['year'].values[0]
        year_label = QLabel(year)
        year_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(year_label)

        # add seasons
        seas = df['total_seasons'].values[0]
        seas_label = QLabel(f"{seas} seasons")
        seas_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(seas_label)

        # add series poster
        self.poster = resizingImageWidget()
        self.layout.addWidget(self.poster)
        self.poster.setPoster("series", self.imdb_id)

class seriesTableWidget(QTableWidget):
    """
    Series Table Widget
    """
    def __init__(self, abb):
        super(QTableWidget, self).__init__()
        self.abb = abb
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def populate(self):

        # get dataframe
        self.df      = getMain(self).dfs[self.abb]
        self.df_hdrs = self.df.keys().values
        
        # set up columns/headers
        self.setColumnCount(len(series_tbl_hdrs) + len(usr_tbl_hdrs))
        self.setHorizontalHeaderLabels(series_tbl_hdr_names + usr_tbl_names)
        for c, hdr_width in enumerate(series_tbl_widths + usr_tbl_widths):
            self.setColumnWidth(c, hdr_width)
        font = QFont()
        font.setBold(True)
        self.horizontalHeader().setFont(font)
        
        # append each row from series dataframes
        for r, row in enumerate(self.df.iterrows()):
            self.insertRow(r)

            # insert series info
            for c, hdr in enumerate(series_tbl_hdrs):
                if hdr == "poster":
                    self.setImage(r, c)
                elif hdr in ("season", "episode"):
                    item = QTableWidgetItem()
                    item.setData(0, int(self.df[hdr][r]))
                    self.setItem(r, c, item)
                else:
                    self.setItem(r, c, QTableWidgetItem(f"{self.df[hdr][r]}"))
                    
            # query user info
            imdb_id = self.df["imdb_id"][r]

            # insert user info
            for c, hdr in enumerate(usr_tbl_hdrs):
                c += len(series_tbl_hdrs)

                # watched checckbox
                if hdr == "watched":
                    checkbox = watchedCheckboxWidget(imdb_id)
                    self.setCellWidget(r, c, checkbox)
                    checkbox.setCheckedState()
                elif hdr == "last_watched":
                    date_widg  = watchedDateWidget(imdb_id)
                    self.setCellWidget(r, c, date_widg)
                    date_widg.loadWatchedDate()

        self.verticalHeader().setDefaultSectionSize(series_tbl_row_hgt)

        # sort
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def setImage(self, row, col):
        img_wdgt = resizingImageWidget()
        self.setCellWidget(row, col, img_wdgt)
        img_wdgt.setPoster(self.abb, self.df["imdb_id"][row])

class watchedCheckboxWidget(QCheckBox):
    """
    Checkbox table widget
    """

    def __init__(self, imdb_id):
        super(QCheckBox, self).__init__()
        self.imdb_id = imdb_id

        # tie action
        self.clicked.connect(self.setTo)

    def setCheckedState(self):
        checked = getMain(self).getUserItem(self.imdb_id, 'watched')
        self.setChecked(checked)

    def setTo(self):
        getMain(self).setUserItem(self.imdb_id, watched=self.isChecked())

class watchedDateWidget(QWidget):
    """
    Watched Date Widget
    """
    def __init__(self, imdb_id):
        super(QWidget, self).__init__()
        self.imdb_id = imdb_id
        layout = QGridLayout()
        layout.setHorizontalSpacing(1)
        self.setLayout(layout)

        # settings
        #self.setCalendarPopup(True)
        self.date_wgt = QDateEdit()
        self.date_wgt.setDisplayFormat("yyyy-MM-dd")
        self.date_wgt.dateChanged.connect(self.setTo)
        self.layout().addWidget(self.date_wgt, 0, 0, 1, 2)

        # today button
        tdy_btn = QPushButton()
        tdy_btn.setText("Today")
        self.layout().addWidget(tdy_btn, 1, 0, 1, 1)
        tdy_btn.clicked.connect(self.setToToday)

        # clear button
        clr_btn = QPushButton()
        clr_btn.setText("Clear")
        self.layout().addWidget(clr_btn, 1, 1, 1, 1)
        clr_btn.clicked.connect(self.setToNull)

    #def calendarPopup(self) -> bool:
    #    self.calendarWidget().setSelectedDate(QDate.currentDate())
    #    return super().calendarPopup()

    #def mousePressEvent(self, event: QMouseEvent) -> None:
    #    self.calendarWidget().setSelectedDate(QDate.currentDate())
    #    return super().mousePressEvent(event)

    # load watched date
    def loadWatchedDate(self):
        self.date_wgt.blockSignals(True)
        watched_date = getMain(self).getUserItem(self.imdb_id, 'last_watched')
        if watched_date is None:
            self.loadNull()
        else:
            self.date_wgt.setDate(QDate.fromString(watched_date, "yyyy-MM-dd"))
        self.date_wgt.blockSignals(False)

    def loadNull(self):
        self.date_wgt.setSpecialValueText(" ")
        self.date_wgt.setDate(QDate.fromString("01/01/0001", "dd/MM/yyyy"))

    # set to Null
    def setToNull(self):
        """
        Clear date value
        """
        self.loadNull()
        getMain(self).setUserItem(self.imdb_id, last_watched="NULL")

    def setToToday(self):
        """
        Set date value to today
        """
        self.date_wgt.setDate(QDate.currentDate())

    def setTo(self):
        date_str = self.date_wgt.date().toString("yyyy-MM-dd")
        getMain(self).setUserItem(self.imdb_id, last_watched=date_str)

class moviesTableWidget(QTableWidget):
    """
    Movies Table Widget
    """
    def __init__(self):
        super(QTableWidget, self).__init__()
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def populate(self):

        # get dataframe
        self.df      = getMain(self).dfs["mov"]
        self.df_hdrs = self.df.keys().values
        
        # set up columns/headers
        self.setColumnCount(len(movies_tbl_hdrs)+len(usr_tbl_hdrs))
        self.setHorizontalHeaderLabels(movies_tbl_hdr_names + usr_tbl_names)
        for c, hdr_width in enumerate(movies_tbl_widths + usr_tbl_widths):
            self.setColumnWidth(c, hdr_width)
        font = QFont()
        font.setBold(True)
        self.horizontalHeader().setFont(font)
        
        # append each row from series dataframes
        for r, row in enumerate(self.df.iterrows()):
            self.insertRow(r)
            for c, hdr in enumerate(movies_tbl_hdrs):
                # datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
                if hdr != "poster":
                    if hdr == "released":
                        dt_obj = datetime.strptime(self.df[hdr][r], "%d %b %Y")
                        self.setItem(r, c, QTableWidgetItem(dt_obj.strftime("%Y-%m-%d")))
                    else:
                        self.setItem(r, c, QTableWidgetItem(f"{self.df[hdr][r]}"))
                else:
                    self.setImage(r, c)

                        # query user info
            imdb_id = self.df["imdb_id"][r]

            # insert user info
            for c, hdr in enumerate(usr_tbl_hdrs):
                c += len(movies_tbl_hdrs)

                # watched checckbox
                if hdr == "watched":
                    checkbox = watchedCheckboxWidget(imdb_id)
                    self.setCellWidget(r, c, checkbox)
                    checkbox.setCheckedState()
                elif hdr == "last_watched":
                    date_widg  = watchedDateWidget(imdb_id)
                    self.setCellWidget(r, c, date_widg)
                    date_widg.loadWatchedDate()

        self.verticalHeader().setDefaultSectionSize(movies_tbl_row_hgt)

    def setImage(self, row, col):
        img_wdgt = resizingImageWidget()
        self.setCellWidget(row, col, img_wdgt)
        img_wdgt.setPoster("mov", self.df["imdb_id"][row])

class resizingImageWidget(QLabel):
    """
    Resizing Image Widget
    """
    def __init__(self):
        super(QLabel, self).__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        
    def setPoster(self, abb, imdb_id):
        self.pix_map = getMain(self).getPoster(abb,imdb_id)

    def resizeEvent(self, event):
        pix_map = self.pix_map.scaled(self.size().width(), self.size().height(),
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(pix_map)
        self.adjustSize()
        return super().resizeEvent(event)

class gplWindow(QTextBrowser):
    """
    GPL License Window
    """
    def __init__(self):
        super().__init__()

        # read license text and add
        f = open("LICENSE")
        licText = f.read()
        f.close()
        self.insertPlainText(licText)
        self.setWindowTitle("GNU General Public License v3")
        self.resize(580,500)
        self.show()

        # scroll to top
        self.verticalScrollBar().setValue(0)

class ccWindow(QTextBrowser):
    """
    CC License Window
    """
    def __init__(self):
        super().__init__()

        # read license text and add
        f = open("lic/cc_by-nc_4.0")
        licText = f.read()
        f.close()
        self.insertPlainText(licText)
        self.setWindowTitle("Creative Commons License")
        self.resize(600,500)
        self.show()

        # scroll to top
        self.verticalScrollBar().setValue(0)

class aboutWindow(QTextBrowser):
    """
    About Window
    """
    def __init__(self):
        super().__init__()

        # read license text and add
        self.append("\n")
        self.append("                            TrekList v1.0.1")
        self.append("                    created for fun by bpops")
        self.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"https://github.com/bpops/treklist\">https://github.com/bpops/treklist</a>")
        self.setWindowTitle("More Info")
        self.resize(290,120)
        self.setOpenExternalLinks(True)
        self.show()

        # scroll to top
        self.verticalScrollBar().setValue(0)

def main():
    app = QApplication(sys.argv)
    ex = trekListApp()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()