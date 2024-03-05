# -*- coding: utf-8 -*-
import GUI_log_dialog
from PySide6 import QtWidgets, QtCore
import datetime

# keep only the last 50 lines
LOG_length = 50


# com stat dialog
class Logger(QtWidgets.QDialog, GUI_log_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Com log")

        # the dialog can be in the background
        self.setModal(False)

        self.app = parent

        self.log = ""

        # register receive handler
        self.app.commonitor.connect_rx_handler(0xFFFF, self.string_log)

        # create a refresh timer
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(250)

        # initial refresh of the text
        self.tex_box.setText(self.log)

        # bind the Clear button
        self.btn_clear_log.clicked.connect(self.clear_log)

    # clear log
    def clear_log(self):
        self.log = ""

    # periodic refresh
    def update_values(self):
        self.tex_box.setText(self.log)

    # string logger
    def string_log(self):
        data = self.app.commonitor.get_data()
        text_log = str(data[:-1], "ascii")
        # add timestamp
        text_time = str(datetime.datetime.now().isoformat())
        log_line = text_time + " " + text_log + "\n"
        # save in the log
        self.log = log_line + self.log
        # if log is to big, shorten it
        nr_lines = self.log.count("\n")
        if nr_lines > LOG_length:
            lines = self.log.split("\n")
            lines_to_keep = lines[0:LOG_length+1]
            self.log = "\n".join(lines_to_keep)
        pass
