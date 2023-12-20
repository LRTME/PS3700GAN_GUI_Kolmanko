# -*- coding: utf-8 -*-
import GUI_com_settings_dialog

import os

# Import the PyQt4 module we'll need
from PySide6 import QtWidgets, QtCore

# selected baud rate
BAUDRATE = 1000000
UART_PORT = 'COM1'

# kje je zapisan baudrate - ce je
baudrate_file = "baudrate.ini"
uart_port_file = "uart_port.ini"


# dialog
class ComDialog(QtWidgets.QDialog, GUI_com_settings_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        global BAUDRATE
        global UART_PORT
        self.app = parent
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Connect/disconnect")

        self.app = parent
        # modify the button text accordingly
        if self.app.commonitor.is_port_open():
            self.btn_connect.setText("Disconnect")
        else:
            self.btn_connect.setText("Connect")

        # if config is available, read it
        if os.path.exists(uart_port_file):
            file = open(uart_port_file, "r")
            uart_port = file.read()
            file.close()
            UART_PORT = uart_port
        else:
            uart_port = None

        # populate port combobox
        list_portov = self.app.commonitor.get_list_of_ports()
        self.com_select.clear()
        self.com_select.addItems(list_portov)
        # if there is any port available
        if len(list_portov) != 0:
            # if there is no preferred port, then select the first one
            if self.app.commonitor.get_prefered_port() is None:
                self.com_select.setCurrentIndex(0)
            # otherwise select port from the config
            elif uart_port and UART_PORT in list_portov:
                self.com_select.setCurrentIndex(list_portov.index(UART_PORT))
            # if event that one is not available select the one which seems most likely
            else:
                self.com_select.setCurrentIndex(list_portov.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)

        # read the config
        if os.path.exists(os.path.join(self.app.app_path, baudrate_file)):
            file = open(os.path.join(self.app.app_path, baudrate_file), "r")
            br = file.read()
            file.close()
            BAUDRATE = int(br)

        # set the baudrate
        index = self.baud_select.findText(str(BAUDRATE))
        self.baud_select.setCurrentIndex(index)

        # register connect/disconnect button click
        self.btn_connect.clicked.connect(self.com_click)

        # register Ok button click
        self.btn_ok.clicked.connect(self.ok_click)

        # register Refresh button click
        self.btn_com_refresh.clicked.connect(self.refresh_ports)

        # register change of baud rate
        self.baud_select.activated.connect(self.baud_clicked)

        # register change of port
        self.com_select.activated.connect(self.port_clicked)

        # create a timer instance to send periodic ping
        self.sent_ping_count = 0
        self.received_ping_count = 0
        self.ping_acq = False
        self.quiet_mode = True
        self.app.commonitor.connect_rx_handler(0x0900, self.received_ping)
        self.periodic_timer = QtCore.QTimer()
        self.periodic_timer.timeout.connect(self.send_ping)

    # refresh port list combobox
    def refresh_ports(self):
        global UART_PORT
        # clear the list
        self.com_select.clear()
        # get new list
        port_list = self.app.commonitor.get_list_of_ports()
        # and populate them
        self.com_select.addItems(port_list)

        # read the config
        if os.path.exists(uart_port_file):
            file = open(uart_port_file, "r")
            uart_port = file.read()
            file.close()
            UART_PORT = uart_port
        else:
            uart_port = None

        # select most suitable port
        if len(port_list) != 0:
            if self.app.commonitor.get_prefered_port() is None:
                self.com_select.setCurrentIndex(0)
            elif uart_port and UART_PORT in port_list:
                self.com_select.setCurrentIndex(port_list.index(UART_PORT))
            else:
                self.com_select.setCurrentIndex(port_list.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)

    # on new baud rate selection
    def baud_clicked(self):
        # change the baud rate
        global BAUDRATE
        BAUDRATE = int(self.baud_select.currentText())
        br = str(BAUDRATE)
        # and save the config for next time
        file = open(os.path.join(self.app.app_path, baudrate_file), "w")
        file.write(br)
        file.close()
        pass

    def port_clicked(self):
        # change port
        global UART_PORT
        UART_PORT = self.com_select.currentText()
        # and save the config for next time
        file = open(uart_port_file, "w")
        file.write(UART_PORT)
        file.close()
        pass

    # on Connect/Disconnect button event
    def com_click(self):
        # if port is open, close it
        if self.app.commonitor.is_port_open():
            status = self.app.commonitor.close_port()
            # signal into the GUI
            self.btn_connect.setText("Connect")
            self.app.statusbar.showMessage("Com port je zaprt", 2000)
            # enable port and baud selection
            self.com_select.setDisabled(False)
            self.baud_select.setDisabled(False)
            # stop periodic ping timer
            self.periodic_timer.stop()

        # otherwise open it
        else:
            # get which port to open it
            chosen_port = self.com_select.currentText()
            # then open it
            if chosen_port != "":
                status = self.app.commonitor.open_port(chosen_port, BAUDRATE)
                # if port cannot be opened, let the user know
                if status is False:
                    w = QtWidgets.QWidget()
                    QtWidgets.QMessageBox.about(w, "Error", "Selected COM port could not be opened")
                    w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
                    w.show()
                else:
                    # disable port and baud selection
                    self.com_select.setDisabled(True)
                    self.baud_select.setDisabled(True)

                    # signal int the GUI
                    self.btn_connect.setText("Disconnect")
                    self.app.statusbar.showMessage("Com port je odprt", 2000)

                    # start periodic ping timer
                    self.periodic_timer.start(1000)


            else:
                self.app.statusbar.showMessage("Problem pri odpiranju COM porta", 2000)

    # close the window on Ok
    def ok_click(self):
        self.close()

    # periodic ping thread it stops itself if port is closed
    def send_ping(self):
        if self.app.commonitor.is_port_open():
            if self.ping_acq is False:
                self.quiet_mode = True
            self.ping_acq = False
            self.app.commonitor.send_packet(0x0900, None)
            self.sent_ping_count = self.sent_ping_count + 1
        else:
            self.periodic_timer.stop()

    def received_ping(self):
        self.received_ping_count = self.received_ping_count + 1
        self.ping_acq = True

    def try_connect_at_startup(self, serial_number=None):
        global UART_PORT
        global BAUDRATE
        # check which ports are available
        port_list = self.app.commonitor.get_list_of_ports()
        if len(port_list) != 0:
            # read config
            if os.path.exists(uart_port_file):
                file = open(uart_port_file, "r")
                uart_port = file.read()
                file.close()
                UART_PORT = uart_port
            else:
                uart_port = None
            if uart_port in port_list:
                preferred_port = uart_port
            else:
                preferred_port = self.app.commonitor.get_prefered_port(portname=serial_number)
            # open only if it seems reasonable (port number or description matches
            if preferred_port is not None:
                # read config
                if os.path.exists(os.path.join(self.app.app_path, baudrate_file)):
                    file = open(os.path.join(self.app.app_path, baudrate_file), "r")
                    br = file.read()
                    file.close()
                    BAUDRATE = int(br)
                    uart_port = None
                # open only if currently closed
                if not self.app.commonitor.is_port_open():
                    self.app.commonitor.open_port(preferred_port, BAUDRATE)
                    if self.app.commonitor.is_port_open():
                        self.app.statusbar.showMessage("Com port je odprt", 2000)
                        self.btn_connect.setText("Disconnect")
                        # disable port and baud changes
                        self.com_select.setDisabled(True)
                        self.baud_select.setDisabled(True)
                        self.periodic_timer.start(1000)

    def showEvent(self, show_event):
        # set up gui properly
        if self.app.commonitor.is_port_open():
            self.btn_connect.setText("Disconnect")
            self.com_select.setDisabled(True)
            self.baud_select.setDisabled(True)
        else:
            self.btn_connect.setText("Connect")
            self.com_select.setDisabled(False)
            self.baud_select.setDisabled(False)
            self.periodic_timer.stop()

        # populate port list combobox
        port_list = self.app.commonitor.get_list_of_ports()
        self.com_select.clear()
        self.com_select.addItems(port_list)
        # select the one that seems reasonable
        if len(port_list) != 0:
            if self.app.commonitor.get_prefered_port() is None:
                self.com_select.setCurrentIndex(0)
            else:
                self.com_select.setCurrentIndex(port_list.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)
