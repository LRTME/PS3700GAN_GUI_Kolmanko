# -*- coding: utf-8 -*-
import Basic_GUI_COM_settings_dialog

import os

# Import the PyQt4 module we'll need
from PyQt5 import QtWidgets, QtCore

# selected baud rate
BAUDRATE = 1000000

# kje je zapisan baudrate - ce je
baudrate_file = "baudrate.ini"


# dialog
class ComDialog(QtWidgets.QDialog, Basic_GUI_COM_settings_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("Connect/disconnect")

        self.app = parent
        # ustrezno nastavim napis na gumbu
        if self.app.commonitor.is_port_open() == True:
            self.btn_connect.setText("Disconnect")
        else:
            self.btn_connect.setText("Connect")

        # populiram combbox za izbiro porta
        list_portov = self.app.commonitor.get_list_of_ports()
        self.com_select.clear()
        self.com_select.addItems(list_portov)
        # ce je kaksen port na voljo
        if len(list_portov) != 0:
            # ce ni primernega potem izberi prvega
            if self.app.commonitor.get_prefered_port() == None:
                self.com_select.setCurrentIndex(0)
            else:
                self.com_select.setCurrentIndex(list_portov.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)

        # ce imam ini datoteko preberem iz nje
        if os.path.exists(baudrate_file):
            file = open(baudrate_file, "r")
            br = file.read()
            file.close()
            global BAUDRATE
            BAUDRATE = int(br)

        # privzeto nastavim baudrate
        index = self.baud_select.findText(str(BAUDRATE))
        self.baud_select.setCurrentIndex(index)

        # regirstriam klik na gum connect/disconnect
        self.btn_connect.clicked.connect(self.com_click)

        # registriram klik na gumb OK
        self.btn_ok.clicked.connect(self.ok_click)

        # registriam gumb refresh
        self.btn_com_refresh.clicked.connect(self.refresh_ports)

        # registrisam spremebo baud_rate-a
        self.baud_select.activated.connect(self.baud_clicked)

        # ustvarim timer za periodicno povprasevanje
        self.periodic_timer = QtCore.QTimer()
        self.periodic_timer.timeout.connect(self.periodic_query)

    # osvezim seznam com portov
    def refresh_ports(self):
        # najprej odstranim vse treutne porte
        self.com_select.clear()
        # pogledam kateri so na voljo
        list_portov = self.app.commonitor.get_list_of_ports()
        # in jih dodam
        self.com_select.addItems(list_portov)
        # privzeto izberem najprimernejsi port
        if len(list_portov) != 0:
            if self.app.commonitor.get_prefered_port() == None:
                self.com_select.setCurrentIndex(0)
            else:
                self.com_select.setCurrentIndex(list_portov.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)

    # ob izbiri baudrate-a
    def baud_clicked(self):
        # popravim baudrate
        global BAUDRATE
        BAUDRATE = int(self.baud_select.currentText())
        br = str(BAUDRATE)
        # odprem datoteko in zapisem nastavitve
        file = open(baudrate_file, "w")
        file.write(br)
        file.close()
        pass

    # ob pritisku na gum connect/disconnect
    def com_click(self):
        # ce je port odport, ga zaprem
        if self.app.commonitor.is_port_open() == True:
            # sprostim nadzor po potrebi
            self.app.commonitor.close_port()
            self.btn_connect.setText("Connect")
            # sporocim v GUI, da je port zaprt
            self.app.statusbar.showMessage("Com port je zaprt", 2000)
            # omogocim nastavljanje porta
            self.com_select.setDisabled(False)
            self.baud_select.setDisabled(False)
            # ustavim timer
            self.periodic_timer.stop()

        # sicer ga pa odprem
        else:
            # najprej pogledam kateri port je izbran
            chosen_port = self.com_select.currentText()
            # potem odprem port, samo ce je port izbran
            if chosen_port != "":
                self.app.commonitor.open_port(chosen_port, BAUDRATE)
                if self.app.commonitor.is_port_open() == True:
                    # onemogocim spremebe porta in hitrosti
                    self.com_select.setDisabled(True)
                    self.baud_select.setDisabled(True)

                    # prevzamem nadzor
                    self.btn_connect.setText("Disconnect")
                    self.app.statusbar.showMessage("Com port je odprt", 2000)

                    # poženem timer thread
                    self.periodic_timer.start(1000)

                else:
                    self.app.commonitor.close_port()
                    self.btn_connect.setText("Connect")
                    self.periodic_timer.stop()
            else:
                self.app.statusbar.showMessage("Problem pri odpiranju COM porta", 2000)

    # ce pritisnem OK potem zaprem okno
    def ok_click(self):
        self.close()

    # nov thread, ki periodično pošlje zahtevo po svežih podatkih
    # ce je port odprt. Sicer ustavi sam sebe
    def periodic_query(self):
        if self.app.commonitor.is_port_open():
            self.app.commonitor.send_packet(0x0900, None)
        else:
            self.periodic_timer.stop()

    # ob zagonu skušam odpreti port
    def try_connect_at_startup(self, serial_number=None):
        # pogledam kateri porti so sploh na voljo
        list_portov = self.app.commonitor.get_list_of_ports()
        # ce je kaksen port na voljo
        if len(list_portov) != 0:
            preffered_port = self.app.commonitor.get_prefered_port(serial=serial_number)
            # in ce je naprava priklopljena
            global BAUDRATE
            if preffered_port != None:
                # in ce imam ini datoteko preberem iz nje
                if os.path.exists(baudrate_file):
                    file = open(baudrate_file, "r")
                    br = file.read()
                    file.close()
                    BAUDRATE = int(br)
                # in ce je trenutno port zaprt
                if self.app.commonitor.is_port_open() == False:
                    self.app.commonitor.open_port(preffered_port, BAUDRATE)
                    if self.app.commonitor.is_port_open() == True:
                        self.app.statusbar.showMessage("Com port je odprt", 2000)
                        self.btn_connect.setText("Disconnect")
                        # onemogocim spremebe porta in hitrosti
                        self.com_select.setDisabled(True)
                        self.baud_select.setDisabled(True)
                        self.periodic_timer.start(1000)

    def showEvent(self, show_event):
        # ustrezno nastavim napis na gumbu
        if self.app.commonitor.is_port_open() == True:
            self.btn_connect.setText("Disconnect")
            self.com_select.setDisabled(True)
            self.baud_select.setDisabled(True)
        else:
            self.btn_connect.setText("Connect")
            self.com_select.setDisabled(False)
            self.baud_select.setDisabled(False)
            self.periodic_timer.stop()

        # populiram combbox za izbiro porta
        list_portov = self.app.commonitor.get_list_of_ports()
        self.com_select.clear()
        self.com_select.addItems(list_portov)
        # ce je kaksen port na voljo
        if len(list_portov) != 0:
            # ce ni primernega potem izberi prvega
            if self.app.commonitor.get_prefered_port() == None:
                self.com_select.setCurrentIndex(0)
            else:
                self.com_select.setCurrentIndex(list_portov.index(self.app.commonitor.get_prefered_port()))
        self.com_select.setEditable(False)
