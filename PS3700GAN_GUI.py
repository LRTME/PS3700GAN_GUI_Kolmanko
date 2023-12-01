# -*- coding: utf-8 -*-
# splash screen for pyinstaller
import sys
splash_text = "Basic_GUI, Mitja Nemec\n"
if hasattr(sys, 'frozen'):
    import pyi_splash
    pyi_splash.update_text(splash_text + "Importing modules")

import struct
import Basic_GUI_main_window
import os
from PyQt5 import QtWidgets, QtGui, QtCore
# za samo eno instanco applikacije
import singleton

SERIAL_NUMBER = 'TI0JAY8S'

COLOR_YELLOW = "background-color:#F8D129;"
COLOR_RED = "background-color:#c83531;"
COLOR_GREEN = "background-color:#32cd32;"
COLOR_BRIGHT_RED = "background-color:#FF4646;"
COLOR_DEFAULT = "background-color:rgba(255, 255, 255, 0);"

states = [("Startup", COLOR_YELLOW), ("Standby_cold", COLOR_YELLOW), ("Standby_hot", COLOR_YELLOW),
          ("Work", COLOR_GREEN), ("Fault_sensed", COLOR_RED), ("Fault", COLOR_RED)]

class MainApp(Basic_GUI_main_window.AppMainClass):

    def __init__(self, parent=None):
        if getattr(sys, 'frozen', False):
            pyi_splash.update_text(splash_text + "Building GUI")

        super().__init__(SERIAL_NUMBER)
        self.setWindowTitle("PS3700GAN_GUI")
        self.about_dialog.lbl_description.setText(self.windowTitle())

        self.ping_count = 0

        self.commonitor.connect_rx_handler(0x0900, self.received_ping)
        self.commonitor.connect_rx_handler(0x0D01, self.state_received)
        self.commonitor.connect_rx_handler(0x0D02, self.settings_received)

        # connect buttons
        self.btn_on_off.clicked.connect(self.btn_on_off_clicked)
        self.btn_mode.clicked.connect(self.btn_mode_clicked)

        # phantom slider
        self.sld_phantom.valueChanged[int].connect(self.phantom_changed)
        self.sld_phantom.sliderReleased.connect(self.request_settings)

        # leg checkboxes
        self.cb_leg1.stateChanged.connect(self.legs_changed)
        self.cb_leg2.stateChanged.connect(self.legs_changed)
        self.cb_leg3.stateChanged.connect(self.legs_changed)
        self.cb_leg4.stateChanged.connect(self.legs_changed)
        self.cb_leg5.stateChanged.connect(self.legs_changed)
        self.cb_leg6.stateChanged.connect(self.legs_changed)

        self.le_freq.editingFinished.connect(self.freq_set)
        self.le_dead_time.editingFinished.connect(self.dead_time_set)

        # connect max current line edit
        self.le_amp_norm.editingFinished.connect(self.amplitude_norm_set)
        self.norm_max = 5

        # zahtevam statusne podatke za data logger in generator signalov
        # if com port is open request parameters
        if getattr(sys, 'frozen', False):
            pyi_splash.update_text(splash_text + "Trying to open COM port")
        if self.commonitor.is_port_open():
            self.request_state()
            self.request_settings()
        else:
            self.commonitor.register_on_open_callback(self.request_state)
            self.commonitor.register_on_open_callback(self.request_settings)

    def disable_modifications(self):
        self.le_freq.setDisabled(True)
        self.le_dead_time.setDisabled(True)
        self.cb_leg1.setDisabled(True)
        self.cb_leg2.setDisabled(True)
        self.cb_leg3.setDisabled(True)
        self.cb_leg4.setDisabled(True)
        self.cb_leg5.setDisabled(True)
        self.cb_leg6.setDisabled(True)

    def enable_modifications(self):
        self.le_freq.setEnabled(True)
        self.le_dead_time.setEnabled(True)
        self.cb_leg1.setEnabled(True)
        self.cb_leg2.setEnabled(True)
        self.cb_leg3.setEnabled(True)
        self.cb_leg4.setEnabled(True)
        self.cb_leg5.setEnabled(True)
        self.cb_leg6.setEnabled(True)

    def legs_changed(self):
        num = 0
        if self.cb_leg1.isChecked():
            num = num + 1
        if self.cb_leg2.isChecked():
            num = num + 2
        if self.cb_leg3.isChecked():
            num = num + 4
        if self.cb_leg4.isChecked():
            num = num + 8
        if self.cb_leg5.isChecked():
            num = num + 16
        if self.cb_leg6.isChecked():
            num = num + 32
        data = struct.pack('<h', num)
        self.commonitor.send_packet(0x0D08, data)

    def dead_time_set(self):
        text = self.le_dead_time.text().replace(",", ".")
        try:
            num = float(text)
        except ValueError:
            num = float(self.norm_max)
        if num < 5:
            num = 5
        if num > 500:
            num = 500
        data = struct.pack('<f', num)
        self.commonitor.send_packet(0x0D07, data)

    def freq_set(self):
        text = self.le_freq.text().replace(",", ".")
        try:
            num = float(text)
        except ValueError:
            num = float(self.norm_max)
        if num < 100000:
            num = 100000
        if num > 1000000:
            num = 1000000
        data = struct.pack('<f', num)
        self.commonitor.send_packet(0x0D06, data)

    def phantom_changed(self):
        # osvezim napis pod sliderjem
        a = self.sld_phantom.value()
        self.lbl_phantom.setText(str(round(self.sld_phantom.value() / 100, 2)))
        # posljem paket po portu
        data = struct.pack('<f', self.sld_phantom.value() / 100)
        self.commonitor.send_packet(0x0D05, data)

    def amplitude_norm_set(self):
        text = self.le_amp_norm.text().replace(",", ".")
        try:
            num = float(text)
        except ValueError:
            num = float(self.norm_max)
        if num < 0:
            num = 0
        if num > 30:
            num = 30
        data = struct.pack('<f', num)
        self.commonitor.send_packet(0x0D03, data)
        self.ref_gen.ref_amp_range(num)

    def request_state(self):
        self.commonitor.send_packet(0x0D00, None)

    def request_settings(self):
        self.commonitor.send_packet(0x0D04, None)

    def received_ping(self):
        self.ping_count = self.ping_count + 1

    def btn_mode_clicked(self):
        self.commonitor.send_packet(0x0D02, struct.pack('<h', 0x0000))

    def btn_on_off_clicked(self):
        if self.lbl_state.text() == "Work":
            # send request to turn on the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0000))
            # zero the reference values
            self.sld_phantom.setValue(0)
            self.sld_amp.setValue(0)
        if (self.lbl_state.text() == "Standby_cold") or (self.lbl_state.text() == "Standby_hot"):
            # send request to turn off the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0001))
        if self.lbl_state.text() == "Fault":
            # send request to turn off the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0002))

    def settings_received(self):
        # grab the data
        data = self.commonitor.get_data()
        # decode data
        current_norm = round(struct.unpack('<f', data[0:4])[0], 2)
        phantom = round(struct.unpack('<f', data[4:8])[0], 2)

        sw_freq = round(struct.unpack('<f', data[8:12])[0], 2)
        dead_time = round(struct.unpack('<f', data[12:16])[0], 2)
        legs = round(struct.unpack('<h', data[16:18])[0], 2)

        self.le_amp_norm.blockSignals(True)
        self.le_amp_norm.setText("{:.1f}".format(current_norm))
        self.le_amp_norm.blockSignals(False)

        self.sld_phantom.blockSignals(True)
        self.sld_phantom.setValue(int(phantom*100))
        self.sld_phantom.blockSignals(False)
        self.lbl_phantom.setText(str(self.sld_phantom.value() / 100))

        self.le_freq.blockSignals(True)
        self.le_freq.setText("{:.0f}".format(sw_freq))
        self.le_freq.blockSignals(False)

        self.le_dead_time.blockSignals(True)
        self.le_dead_time.setText("{:.0f}".format(dead_time))
        self.le_dead_time.blockSignals(False)

        self.cb_leg1.blockSignals(True)
        self.cb_leg1.setChecked(legs & 0x01)
        self.cb_leg1.blockSignals(False)

        self.cb_leg2.blockSignals(True)
        self.cb_leg2.setChecked(legs & 0x02)
        self.cb_leg2.blockSignals(False)

        self.cb_leg3.blockSignals(True)
        self.cb_leg3.setChecked(legs & 0x04)
        self.cb_leg3.blockSignals(False)

        self.cb_leg4.blockSignals(True)
        self.cb_leg4.setChecked(legs & 0x08)
        self.cb_leg4.blockSignals(False)

        self.cb_leg5.blockSignals(True)
        self.cb_leg5.setChecked(legs & 0x10)
        self.cb_leg5.blockSignals(False)

        self.cb_leg6.blockSignals(True)
        self.cb_leg6.setChecked(legs & 0x20)
        self.cb_leg6.blockSignals(False)

    def state_received(self):
        # grab the data
        data = self.commonitor.get_data()

        # decode data
        cpu_load = struct.unpack('<f', data[0:4])[0]

        u_dc = struct.unpack('<f', data[4:8])[0]
        u_out = struct.unpack('<f', data[8:12])[0]

        current_1 = struct.unpack('<f', data[12:16])[0]
        current_2 = struct.unpack('<f', data[16:20])[0]
        current_3 = struct.unpack('<f', data[20:24])[0]
        current_4 = struct.unpack('<f', data[24:28])[0]
        current_5 = struct.unpack('<f', data[28:32])[0]
        current_6 = struct.unpack('<f', data[32:36])[0]

        current = struct.unpack('<f', data[36:40])[0]
        current_phantom = struct.unpack('<f', data[40:44])[0]

        temp_pcb = struct.unpack('<f', data[44:48])[0]
        temp_cpu = struct.unpack('<f', data[48:52])[0]

        state = struct.unpack('<h', data[52:54])[0]
        mode = struct.unpack('<h', data[54:56])[0]

        self.lbl_cpu_load.setText("{:.1f}".format(cpu_load))

        self.lbl_u_dc.setText("{:.1f}".format(u_dc))
        self.lbl_u_out.setText("{:.1f}".format(u_out))

        self.lbl_current_1.setText("{:.1f}".format(current_1))
        self.lbl_current_2.setText("{:.1f}".format(current_2))
        self.lbl_current_3.setText("{:.1f}".format(current_3))
        self.lbl_current_4.setText("{:.1f}".format(current_4))
        self.lbl_current_5.setText("{:.1f}".format(current_5))
        self.lbl_current_6.setText("{:.1f}".format(current_6))

        self.lbl_current.setText("{:.1f}".format(current))
        self.lbl_current_phantom.setText("{:.1f}".format(current_phantom))

        self.lbl_temp_pcb.setText("{:.1f}".format(temp_pcb))
        self.lbl_temp_cpu.setText("{:.1f}".format(temp_cpu))

        # enum STATE {SM_startup = 0, SM_standby, SM_work, SM_fault_sensed, SM_fault} state;
        self.lbl_state.setText(states[state][0])
        self.lbl_state.setStyleSheet(states[state][1])

        if self.lbl_state.text() == "Standby_cold" or self.lbl_state.text() == "Standby_hot":
            self.enable_modifications()
        else:
            self.disable_modifications()

        # Open loop, Phantom, Normal
        if mode == 0:
            self.lbl_mode.setStyleSheet(COLOR_YELLOW)
            self.lbl_mode.setText("Open loop")
            self.sld_phantom.setDisabled(True)
            self.lbl_phantom.setDisabled(True)
        if mode == 1:
            self.lbl_mode.setStyleSheet(COLOR_GREEN)
            self.lbl_mode.setText("Phantom")
            self.sld_phantom.setEnabled(True)
            self.lbl_phantom.setEnabled(True)
        if mode == 2:
            self.lbl_mode.setStyleSheet(COLOR_GREEN)
            self.lbl_mode.setText("Normal")
            self.sld_phantom.setDisabled(True)
            self.lbl_phantom.setDisabled(True)


# glavna funkcija
def main():

    # I need this on Kubuntu otherwise I get an error when creating app (https://stackoverflow.com/a/61691092)
    # error: qt.qpa.plugin: Could not find the Qt platform plugin "xcb" in ""
    # This application failed to start because no Qt platform plugin could be initialized.
    # Reinstalling the application may fix this problem.

    import PyQt5
    pyqt = os.path.dirname(PyQt5.__file__)
    os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt, "Qt/plugins")

    # A new instance of QApplication
    app = QtWidgets.QApplication(sys.argv)
    # We set the form to be our ExampleApp (design)

    try:
        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        if getattr(sys, 'frozen', False):
            pyi_splash.close()
        # tukaj bi lahko pokazal vsaj kaksno okno
        w = QtWidgets.QWidget()
        QtWidgets.QMessageBox.about(w, "Napaka", "Naenkrat se lahko izvaja samo ena instanca programa")
        w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        w.show()
        w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        w.show()
        sys.exit(0)

    form = MainApp()
    # Show the form
    form.show()

    if getattr(sys, 'frozen', False):
        pyi_splash.close()

    # and execute the app
    app.exec_()


# start of the program
# if we're running file directly and not importing it
if __name__ == '__main__':
    main()

