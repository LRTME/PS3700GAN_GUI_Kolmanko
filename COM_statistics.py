# -*- coding: utf-8 -*-
import GUI_com_statistics_dialog

from PySide6 import QtWidgets, QtCore


class ComStat(QtWidgets.QDialog, GUI_com_statistics_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Com statistics")

        # The dialog can be in the background
        self.setModal(False)

        self.app = parent
        # refresh label data
        self.update_values()

        # register Ok button click
        self.btn_ok.clicked.connect(self.ok_click)

        # create a timer to trigger periodic refresh
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(250)

    # refresh shown data
    def update_values(self):
        data = self.app.commonitor.statistic_data()
        self.nr_packets_sent.setText(str(data[0]))
        self.nr_packets_received.setText(str(data[1]))
        self.nr_decode_errors.setText(str(data[2]))
        self.nr_crc_errors.setText(str(data[3]))
        self.nr_non_registered_packets_received.setText(str(data[4]))
        self.nr_bytes_received.setText(str(data[5]))

    # close on Ok
    def ok_click(self):
        self.close()
