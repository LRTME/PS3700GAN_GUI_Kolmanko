# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui
import sys
import com_monitor
import struct
import math
import os

# GUI GUI elements
import LOG_mod
import COM_settings
import COM_statistics
import HELP_about
import GUI_main_window
import SIG_gen
import DLOG_gen
import AUT_measure


class AppMainClass(QtWidgets.QMainWindow, GUI_main_window.Ui_MainWindow):

    # com monitor instance
    commonitor = com_monitor.ComMonitor()

    # log list
    log = ""

    def __init__(self, serial_number=None):
        # Explaining super is out of the scope of this article
        # So please google it if you're not familar with it
        # Simple reason why we use it here is that it allows us to
        # access variables, methods etc in the design.py file
        # super(self.__class__, self).__init__()
        super().__init__()

        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Basic_GUI")
        self.setWindowIcon(QtGui.QIcon(resource_path("Logo_LRTME.png")))

        # register crc error handler
        self.commonitor.connect_crc_handler(self.crc_event_print)

        # connect menu items
        self.actionQuit.triggered.connect(QtWidgets.QApplication.quit)
        self.actionConnect_Disconnect.triggered.connect(self.com_meni_clicked)
        self.actionCom_statistics.triggered.connect(self.com_statistics_clicked)
        self.actionCom_log.triggered.connect(self.com_log_clicked)
        self.actionAutomatic_Measurements.triggered.connect(self.com_auto_measurements_clicked)
        self.actionAbout.triggered.connect(self.com_about_clicked)

        # LOG
        self.com_log_dialog = LOG_mod.Logger(self)

        # set up the dialogs
        self.com_stat_dialog = COM_statistics.ComStat(self)
        self.com_dialog = COM_settings.ComDialog(self)
        self.com_dialog.try_connect_at_startup(serial_number)
        self.about_dialog = HELP_about.About(self)

        # DLOG_GEN
        self.dlog_gen = DLOG_gen.DLOG_viewer(self)

        # refgen init
        self.ref_gen = SIG_gen.SIG_generator(self)

        # automatic measurements
        self.aut_measure = AUT_measure.AUT_measurement(self)

    # make sure to close the port on app close
    def closeEvent(self, event):
        if self.commonitor.is_port_open():
            self.commonitor.close_port()
        # close the app
        super(AppMainClass, self).closeEvent(event)

    """ rx packets handlesr - in GUI thread"""
    def crc_event_print(self):
        crc_num = self.commonitor.get_crc()
        self.statusbar.showMessage("# CRC errors = " + str(crc_num), 2000)

    """ GUI event handlerji """
    # ob pritisku na meni com
    def com_meni_clicked(self):
        self.com_dialog.show()

    def com_statistics_clicked(self):
        self.com_stat_dialog.show()

    def com_log_clicked(self):
        self.com_log_dialog.show()

    def com_auto_measurements_clicked(self):
        self.aut_measure.show()

    def com_about_clicked(self):
        self.about_dialog.show()

    def request_ref_params(self):
        self.commonitor.send_packet(0x0B1A, None)


# pomozne funkcije
def pack_Float_As_U_Long(value):
    """ Pack a float as little endian packed data"""
    return struct.pack('<f', value)


def eng_string(x, format='%s', si=False):
    """
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.

    format: printf-style string used to format the value before the exponent.

    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.

    E.g. with format='%.2f':
        1.23e-08 => 12.30e-9
             123 => 123.00
          1230.0 => 1.23e3
      -1230000.0 => -1.23e6

    and with si=True:
          1230.0 => 1.23k
      -1230000.0 => -1.23M
    """
    sign = ''
    x = float(x)
    if x < 0:
        x = -x
        sign = '-'
    if x == 0.0:
        exp = 0
    else:
        exp = int(math.floor(math.log10(x)))
    exp3 = exp - (exp % 3)
    x3 = x / (10 ** exp3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        index_f = ( exp3 - (-24)) / 3
        index = int(index_f)
        exp3_text = 'yzafpnum kMGTPEZY'[index]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3

    return ('%s'+format+'%s') % (sign, x3, exp3_text)


# za uporabo slike v pyinstaller .exe datoteki
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)







