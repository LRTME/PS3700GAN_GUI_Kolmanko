# -*- coding: utf-8 -*-
# splash screen for pyinstaller
import sys
splash_text = "Basic_GUI, Mitja Nemec\n"
if hasattr(sys, 'frozen'):
    import pyi_splash
    pyi_splash.update_text(splash_text + "Importing modules")
import struct
import MAIN_window
import os
from PySide6 import QtWidgets, QtGui, QtCore
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


class MainApp(MAIN_window.AppMainClass):

    def __init__(self, parent=None):
        if hasattr(sys, 'frozen'):
            pyi_splash.update_text(splash_text + "Building GUI")
        if hasattr(sys, '_MEIPASS'):
            self.app_path = sys._MEIPASS
        else:
            self.app_path = os.path.dirname(__file__)

        super().__init__(SERIAL_NUMBER)
        self.setWindowTitle("PS3700GAN_GUI")
        self.about_dialog.lbl_description.setText(self.windowTitle())

        self.ping_count = 0

        self.commonitor.connect_rx_handler(0x0900, self.received_ping)
        self.commonitor.connect_rx_handler(0x0D01, self.measurements_received)
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

        self.sp_sign_leg_1.valueChanged.connect(self.sp_sign_leg_1_changed)
        self.sp_sign_leg_2.valueChanged.connect(self.sp_sign_leg_2_changed)
        self.sp_sign_leg_3.valueChanged.connect(self.sp_sign_leg_3_changed)
        self.sp_sign_leg_4.valueChanged.connect(self.sp_sign_leg_4_changed)
        self.sp_sign_leg_5.valueChanged.connect(self.sp_sign_leg_5_changed)
        self.sp_sign_leg_6.valueChanged.connect(self.sp_sign_leg_6_changed)

        self.spb_shift_leg_2.valueChanged.connect(self.spb_shift_leg_2_changed)
        self.spb_shift_leg_3.valueChanged.connect(self.spb_shift_leg_3_changed)
        self.spb_shift_leg_4.valueChanged.connect(self.spb_shift_leg_4_changed)
        self.spb_shift_leg_5.valueChanged.connect(self.spb_shift_leg_5_changed)
        self.spb_shift_leg_6.valueChanged.connect(self.spb_shift_leg_6_changed)

        # connect max current line edit
        self.le_amp_norm.editingFinished.connect(self.amplitude_norm_set)
        self.norm_max = 15
        self.ref_gen.ref_amp_range(self.norm_max)

        # zahtevam statusne podatke za data logger in generator signalov
        # if com port is open request parameters
        if hasattr(sys, 'frozen'):
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
        self.spb_shift_leg_2.setDisabled(True)
        self.spb_shift_leg_3.setDisabled(True)
        self.spb_shift_leg_4.setDisabled(True)
        self.spb_shift_leg_5.setDisabled(True)
        self.spb_shift_leg_6.setDisabled(True)
        self.sp_sign_leg_1.setDisabled(True)
        self.sp_sign_leg_2.setDisabled(True)
        self.sp_sign_leg_3.setDisabled(True)
        self.sp_sign_leg_4.setDisabled(True)
        self.sp_sign_leg_5.setDisabled(True)
        self.sp_sign_leg_6.setDisabled(True)

    def enable_modifications(self):
        self.le_freq.setEnabled(True)
        self.le_dead_time.setEnabled(True)
        self.cb_leg1.setEnabled(True)
        self.cb_leg2.setEnabled(True)
        self.cb_leg3.setEnabled(True)
        self.cb_leg4.setEnabled(True)
        self.cb_leg5.setEnabled(True)
        self.cb_leg6.setEnabled(True)
        self.spb_shift_leg_2.setEnabled(True)
        self.spb_shift_leg_3.setEnabled(True)
        self.spb_shift_leg_4.setEnabled(True)
        self.spb_shift_leg_5.setEnabled(True)
        self.spb_shift_leg_6.setEnabled(True)
        self.sp_sign_leg_1.setEnabled(True)
        self.sp_sign_leg_2.setEnabled(True)
        self.sp_sign_leg_3.setEnabled(True)
        self.sp_sign_leg_4.setEnabled(True)
        self.sp_sign_leg_5.setEnabled(True)
        self.sp_sign_leg_6.setEnabled(True)

    def sp_sign_leg_1_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_1.value())
        self.commonitor.send_packet(0x0D11, data)

    def sp_sign_leg_2_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_2.value())
        self.commonitor.send_packet(0x0D12, data)

    def sp_sign_leg_3_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_3.value())
        self.commonitor.send_packet(0x0D13, data)

    def sp_sign_leg_4_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_4.value())
        self.commonitor.send_packet(0x0D14, data)

    def sp_sign_leg_5_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_5.value())
        self.commonitor.send_packet(0x0D15, data)

    def sp_sign_leg_6_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.sp_sign_leg_6.value())
        self.commonitor.send_packet(0x0D16, data)

    def spb_shift_leg_2_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.spb_shift_leg_2.value())
        self.commonitor.send_packet(0x0D22, data)

    def spb_shift_leg_3_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.spb_shift_leg_3.value())
        self.commonitor.send_packet(0x0D23, data)

    def spb_shift_leg_4_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.spb_shift_leg_4.value())
        self.commonitor.send_packet(0x0D24, data)

    def spb_shift_leg_5_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.spb_shift_leg_5.value())
        self.commonitor.send_packet(0x0D25, data)

    def spb_shift_leg_6_changed(self):
        # posljem paket po portu
        data = struct.pack('<f', self.spb_shift_leg_6.value())
        self.commonitor.send_packet(0x0D26, data)

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
            print("SENT: Turn on rectifier")
            # zero the reference values
            self.sld_phantom.setValue(0)
            self.sld_amp.setValue(0)
        if (self.lbl_state.text() == "Standby_cold") or (self.lbl_state.text() == "Standby_hot"):
            # send request to turn off the rectifier
            # TODO zero primary secondary, ...
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0001))
            print("SENT: Turn off rectifier")
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
        shift1 = struct.unpack('<f', data[16:20])[0]
        shift2 = struct.unpack('<f', data[20:24])[0]
        shift3 = struct.unpack('<f', data[24:28])[0]
        shift4 = struct.unpack('<f', data[28:32])[0]
        shift5 = struct.unpack('<f', data[32:36])[0]
        shift6 = struct.unpack('<f', data[36:40])[0]

        sign1 = struct.unpack('<f', data[40:44])[0]
        sign2 = struct.unpack('<f', data[44:48])[0]
        sign3 = struct.unpack('<f', data[48:52])[0]
        sign4 = struct.unpack('<f', data[52:56])[0]
        sign5 = struct.unpack('<f', data[56:60])[0]
        sign6 = struct.unpack('<f', data[60:64])[0]

        legs = round(struct.unpack('<h', data[64:68])[0], 2)

        self.le_amp_norm.blockSignals(True)
        self.le_amp_norm.setText("{:.1f}".format(current_norm))
        self.ref_gen.ref_amp_range(current_norm)
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

        self.spb_shift_leg_1.blockSignals(True)
        self.spb_shift_leg_1.setValue(shift1)
        self.spb_shift_leg_1.blockSignals(False)

        self.spb_shift_leg_2.blockSignals(True)
        self.spb_shift_leg_2.setValue(shift2)
        self.spb_shift_leg_2.blockSignals(False)

        self.spb_shift_leg_3.blockSignals(True)
        self.spb_shift_leg_3.setValue(shift3)
        self.spb_shift_leg_3.blockSignals(False)

        self.spb_shift_leg_4.blockSignals(True)
        self.spb_shift_leg_4.setValue(shift4)
        self.spb_shift_leg_4.blockSignals(False)

        self.spb_shift_leg_5.blockSignals(True)
        self.spb_shift_leg_5.setValue(shift5)
        self.spb_shift_leg_5.blockSignals(False)

        self.spb_shift_leg_6.blockSignals(True)
        self.spb_shift_leg_6.setValue(shift6)
        self.spb_shift_leg_6.blockSignals(False)

        self.sp_sign_leg_1.blockSignals(True)
        self.sp_sign_leg_1.setValue(sign1)
        self.sp_sign_leg_1.blockSignals(False)

        self.sp_sign_leg_2.blockSignals(True)
        self.sp_sign_leg_2.setValue(sign2)
        self.sp_sign_leg_2.blockSignals(False)

        self.sp_sign_leg_3.blockSignals(True)
        self.sp_sign_leg_3.setValue(sign3)
        self.sp_sign_leg_3.blockSignals(False)

        self.sp_sign_leg_4.blockSignals(True)
        self.sp_sign_leg_4.setValue(sign4)
        self.sp_sign_leg_4.blockSignals(False)

        self.sp_sign_leg_5.blockSignals(True)
        self.sp_sign_leg_5.setValue(sign5)
        self.sp_sign_leg_5.blockSignals(False)

        self.sp_sign_leg_6.blockSignals(True)
        self.sp_sign_leg_6.setValue(sign6)
        self.sp_sign_leg_6.blockSignals(False)

    def measurements_received(self):
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

        fault_flags = struct.unpack('<h', data[56:58])[0]

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

        # fault flags
        """   bool    overcurrent:1;
              bool    undervoltage:1;
              bool    overvoltage:1;
              bool    cpu_overrun:1;
              bool    fault_registered:1;"""
        if fault_flags & 0x0001:
            self.lbl_flt_overcurrent.setStyleSheet(COLOR_RED)
        else:
            self.lbl_flt_overcurrent.setStyleSheet(COLOR_DEFAULT)
        if fault_flags & 0x0002:
            self.lbl_flt_undervoltage.setStyleSheet(COLOR_RED)
        else:
            self.lbl_flt_undervoltage.setStyleSheet(COLOR_DEFAULT)
        if fault_flags & 0x0004:
            self.lbl_flt_overvoltage.setStyleSheet(COLOR_RED)
        else:
            self.lbl_flt_overvoltage.setStyleSheet(COLOR_DEFAULT)
        if fault_flags & 0x0008:
            self.lbl_flt_cpu_overrun.setStyleSheet(COLOR_RED)
        else:
            self.lbl_flt_cpu_overrun.setStyleSheet(COLOR_DEFAULT)


# glavna funkcija
def main():

    # I need this on Kubuntu otherwise I get an error when creating app (https://stackoverflow.com/a/61691092)
    # error: qt.qpa.plugin: Could not find the Qt platform plugin "xcb" in ""
    # This application failed to start because no Qt platform plugin could be initialized.
    # Reinstalling the application may fix this problem.
    #import PyQt5
    #pyqt = os.path.dirname(PyQt5.__file__)
    #os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt, "Qt/plugins")

    # A new instance of QApplication
    app = QtWidgets.QApplication(sys.argv)
    # We set the form to be our ExampleApp (design)

    try:
        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        if hasattr(sys, 'frozen'):
            pyi_splash.close()
        # tukaj bi lahko pokazal vsaj kaksno okno
        w = QtWidgets.QWidget()
        QtWidgets.QMessageBox.about(w, "Napaka", "Naenkrat se lahko izvaja samo ena instanca programa")
        w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        w.show()
        w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        w.show()
        w.activateWindow()
        sys.exit(0)

    form = MainApp()

    # Show the form
    form.show()

    if hasattr(sys, 'frozen'):
        pyi_splash.close()

    form.activateWindow()
    # and execute the app
    app.exec()


# start of the program
# if we're running file directly and not importing it
if __name__ == '__main__':
    main()

