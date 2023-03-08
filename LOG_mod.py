# -*- coding: utf-8 -*-
import Basic_GUI_LOG_mod_dialog

# Import the PyQt4 module we'll need
from PyQt5 import QtWidgets, QtCore
# timestamping received strings
import datetime

LOG_length = 50


# com stat dialog
class Logger(QtWidgets.QDialog, Basic_GUI_LOG_mod_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Com log")

        #lahko je tudi v ozadju
        self.setModal(False)

        self.app = parent

        self.log = ""

        # register all receive handlers
        self.app.commonitor.connect_rx_handler(0xFFFF, self.string_log)

        # ustvarim casovnik, ki bo vsak 0.25 sekunde osveziv podatke
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(250)

        # prvic osvezim tekst
        self.tex_box.setText(self.log)

        # povezem gumb za brisanje log-a
        self.btn_clear_log.clicked.connect(self.clear_log)

    # brisem log
    def clear_log(self):
        self.log = ""

    # za periodicno osvezevanje
    def update_values(self):
        self.tex_box.setText(self.log)

    # string logger
    def string_log(self):
        data = self.app.commonitor.get_data()
        text_log = str(data[:-1], "ascii")
        # dodam uro kdaj sem tole dobil
        text_time = str(datetime.datetime.now().isoformat())
        log_line = text_time + " " + text_log + "\n"
        # shranim v log
        self.log = log_line + self.log
        # ce je log prevelik, ga skrajšam
        nr_lines = self.log.count("\n")
        if nr_lines > LOG_length:
            lines = self.log.split("\n")
            lines_to_keep = lines[0:LOG_length+1]
            self.log = "\n".join(lines_to_keep)
        pass
