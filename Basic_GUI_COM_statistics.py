# -*- coding: utf-8 -*-
import Basic_GUI_COM_statistics_dialog

# Import the PyQt4 module we'll need
from PyQt5 import QtWidgets, QtCore

# com stat dialog
class ComStat(QtWidgets.QDialog, Basic_GUI_COM_statistics_dialog.Ui_Communicationstatistics):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Com statistics")

        #lahko je tudi v ozadju
        self.setModal(False)

        self.app = parent
        # nastavim napise za statistiko
        self.update_values()

        # registriram klik na gumb OK
        self.btn_ok.clicked.connect(self.ok_click)

        # ustvarim casovnik, ki bo vsak 0.25 sekunde osveziv podatke
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_values)
        self.update_timer.start(250)

    # za periodicno osvezevanje
    def update_values(self):
        data = self.app.commonitor.statistic_data();
        self.nr_packets_sent.setText(str(data[0]))
        self.nr_packets_received.setText(str(data[1]))
        self.nr_decode_errors.setText(str(data[2]))
        self.nr_crc_errors.setText(str(data[3]))
        self.nr_non_registered_packets_received.setText(str(data[4]))
        self.nr_bytes_received.setText(str(data[5]))

    # ce pritisnem OK potem zaprem okno
    def ok_click(self):
        self.close()
