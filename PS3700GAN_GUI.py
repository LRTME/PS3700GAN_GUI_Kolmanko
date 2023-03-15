# -*- coding: utf-8 -*-
import struct
import Basic_GUI_main_window
import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import threading
import time
# za samo eno instanco applikacije
import singleton
import numpy as np

SERIAL_NUMBER = None

COLOR_YELLOW = "background-color:#F8D129;"
COLOR_RED = "background-color:#c83531;"
COLOR_GREEN = "background-color:#32cd32;"
COLOR_BRIGHT_RED = "background-color:#FF4646;"
COLOR_DEFAULT = "background-color:rgba(255, 255, 255, 0);"


class MainApp(Basic_GUI_main_window.AppMainClass):

    # for measurement automation
    finished = QtCore.pyqtSignal()
    primary_signal = QtCore.pyqtSignal(int)
    secondary_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(SERIAL_NUMBER)
        self.setWindowTitle("PS3700GAN_GUI")
        self.about_dialog.lbl_description.setText(self.windowTitle())

        self.ping_count = 0

        self.commonitor.connect_rx_handler(0x0900, self.received_ping)
        self.commonitor.connect_rx_handler(0x0D01, self.state_received)

        # connect buttons
        self.btn_on_off.clicked.connect(self.btn_on_off_clicked)
        self.btn_mode.clicked.connect(self.btn_mode_clicked)

        # zahtevam statusne podatke za data logger in generator signalov
        # if com port is open request parameters
        if self.commonitor.is_port_open():
            self.request_state()
        else:
            self.commonitor.register_on_open_callback(self.request_state)

        # measurement automation initialization
        self.measurement_init()

    def request_state(self):
        self.commonitor.send_packet(0x0D00, None)

    def received_ping(self):
        self.ping_count = self.ping_count + 1

    def btn_mode_clicked(self):
        self.commonitor.send_packet(0x0D02, struct.pack('<h', 0x0000))

    def btn_on_off_clicked(self):
        if self.lbl_state.text() == "Running":
            # send request to turn on the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0000))
        if self.lbl_state.text() == "Standby":
            # send request to turn off the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0001))
        if self.lbl_state.text() == "Fault":
            # send request to turn off the rectifier
            self.commonitor.send_packet(0x0D01, struct.pack('<h', 0x0002))

    def state_received(self):
        # grab the date
        data = self.commonitor.get_data()

        # decode data
        cpu_load = struct.unpack('<f', data[0:4])[0]
        state = struct.unpack('<h', data[4:6])[0]
        mode = struct.unpack('<h', data[6:8])[0]

        cpu_load = 100 * struct.unpack('<f', data[0:4])[0]
        self.lbl_cpu_load.setText("{:.1f}".format(cpu_load))

        # SM_standby = 0, SM_startup, SM_running, SM_fault
        if state == 0:
            self.lbl_state.setStyleSheet(COLOR_YELLOW)
            self.lbl_state.setText("Standby")
        if state == 1:
            self.lbl_state.setStyleSheet(COLOR_YELLOW)
            self.lbl_state.setText("Startup")
        if state == 2:
            self.lbl_state.setStyleSheet(COLOR_GREEN)
            self.lbl_state.setText("Running")
        if state == 3:
            self.lbl_state.setStyleSheet(COLOR_RED)
            self.lbl_state.setText("Fault")

        # reg_PI = 0, reg_DCC_I, reg_DCC_II
        if mode == 0:
            self.lbl_mode.setStyleSheet(COLOR_YELLOW)
            self.lbl_mode.setText("PI reg.")
        if mode == 1:
            self.lbl_mode.setStyleSheet(COLOR_YELLOW)
            self.lbl_mode.setText("DCC I")
        if mode == 2:
            self.lbl_mode.setStyleSheet(COLOR_GREEN)
            self.lbl_mode.setText("DCC II")

    """
    Measurement automation
    """
    def measurement_init(self):
        self.speed_start = 0
        self.speed_stop = 0
        self.speed_delta = 0

        self.current_start = 0
        self.current_stop = 0
        self.current_delta = 0

        self.filename_base = ""

        # init delay spinboxes
        self.spb_primary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.spb_primary_delay.setMinimum(0.001)
        self.spb_primary_delay.setMaximum(100)
        self.spb_primary_delay.setValue(0.1)

        self.spb_secondary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.spb_secondary_delay.setMinimum(0.001)
        self.spb_secondary_delay.setMaximum(10)
        self.spb_secondary_delay.setValue(0.01)

        self.finished.connect(self.measure_end)
        self.primary_signal.connect(self.primary_updated)
        self.secondary_signal.connect(self.secondary_updated)

        self.sld_primary.valueChanged[int].connect(self.primary_changed)
        self.sld_secondary.valueChanged[int].connect(self.secondary_changed)

        self.btn_start_measure.clicked.connect(self.measure_start)

    def primary_changed(self):
        self.lbl_primary.setText(str(self.sld_primary.value() / 100))
        self.commonitor.send_packet(0x0E01, struct.pack('<f', float(self.sld_primary.value() / 100)))

    def secondary_changed(self):
        self.lbl_secondary.setText(str(self.sld_secondary.value() / 100))
        self.commonitor.send_packet(0x0E02, struct.pack('<f', float(self.sld_secondary.value() / 100)))

    def primary_updated(self, value):
        self.lbl_primary.setText(str(round(value / 100, 2)))
        self.sld_primary.blockSignals(True)
        self.sld_primary.setValue(value)
        self.sld_primary.blockSignals(False)

    def secondary_updated(self, value):
        self.lbl_secondary.setText(str(round(value / 100, 2)))
        self.sld_secondary.blockSignals(True)
        self.sld_secondary.setValue(value)
        self.sld_secondary.blockSignals(True)

    def measure_start(self):
        # parse the test boundary conditions
        self.primary_start = int(self.spb_primary_start.value()*100)
        self.primary_stop = int(self.spb_primary_stop.value()*100)
        self.primary_delta = int(self.spb_primary_delta.value()*100)
        self.primary_delay = self.spb_primary_delay.value()
        self.primary_unroll = self.cb_primary_unroll.isChecked()

        self.secondary_start = int(self.spb_secondary_start.value()*100)
        self.secondary_stop = int(self.spb_secondary_stop.value()*100)
        self.secondary_delta = int(self.spb_secondary_delta.value()*100)
        self.secondary_delay = self.spb_secondary_delay.value()
        self.secondary_unroll = self.cb_secondary_unroll.isChecked()

        # run the measurements only if setup is sane
        if self.primary_stop < self.primary_start:
            self.spb_primary_start.setStyleSheet(COLOR_BRIGHT_RED)
            self.spb_primary_stop.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.spb_primary_start.setStyleSheet(COLOR_DEFAULT)
            self.spb_primary_stop.setStyleSheet(COLOR_DEFAULT)

        if self.primary_delta > (self.primary_stop - self.primary_start):
            self.spb_primary_delta.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.spb_primary_delta.setStyleSheet(COLOR_DEFAULT)

        if self.secondary_stop < self.secondary_start:
            self.spb_secondary_start.setStyleSheet(COLOR_BRIGHT_RED)
            self.spb_secondary_stop.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.spb_secondary_start.setStyleSheet(COLOR_DEFAULT)
            self.spb_secondary_stop.setStyleSheet(COLOR_DEFAULT)

        if self.secondary_delta > (self.secondary_stop - self.secondary_start):
            self.spb_secondary_delta.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.spb_secondary_delta.setStyleSheet(COLOR_DEFAULT)

        # ask user for a filename
        initial_filename = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save File', filter="*.csv")[0]
        self.filename_base = initial_filename.split('.')[0]
        self.filename_ext = initial_filename.split('.')[1]

        # Block the button until measurements are done
        self.btn_start_measure.setEnabled(False)
        # start measurement thread (so that the GUI is not blocked
        self.thread = threading.Thread(target=self.run_measurements)
        self.thread.start()
        pass

    # cleanup after the measurements
    def measure_end(self):
        self.btn_start_measure.setEnabled(True)
        self.sld_amp.setValue(0)

    # measurement thread
    def run_measurements(self):
        # setup the initial point
        primary_actual = self.primary_start
        secondary_actual = self.secondary_start

        # iterate over speed
        while primary_actual <= self.primary_stop:
            # update new value
            data = struct.pack('<f', (primary_actual / 100))
            self.commonitor.send_packet(0x0E01, data)
            self.primary_signal.emit(primary_actual)
            # wait for things to settle down
            time.sleep(self.primary_delay)

            # iterate over current
            while secondary_actual <= self.secondary_stop:
                # update new value
                data = struct.pack('<f', (secondary_actual / 100))
                self.commonitor.send_packet(0x0E02, data)
                self.secondary_signal.emit(secondary_actual)
                # wait for things to settle down
                time.sleep(self.secondary_delay)

                # grab measured data
                # get the longest array
                arraylist = [self.dlog_gen.ch1_latest, self.dlog_gen.ch2_latest, self.dlog_gen.ch3_latest,
                             self.dlog_gen.ch4_latest, self.dlog_gen.ch5_latest, self.dlog_gen.ch6_latest,
                             self.dlog_gen.ch7_latest, self.dlog_gen.ch8_latest]
                # define empty array
                array_to_write = np.ones((np.max([len(ps) for ps in arraylist]), len(arraylist))) * np.nan
                for i, c in enumerate(arraylist):  # populate columns
                    array_to_write[:len(c), i] = c

                # save measured data
                filename_actual = self.filename_base + "_" + str(primary_actual) + "_" + str(secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual, array_to_write, delimiter=";")
                # prep the next value of current
                secondary_actual = secondary_actual + self.secondary_delta

            # at the end of sequence, soft unroll - might be conditional
            secondary_actual = secondary_actual - 2 * self.secondary_delta
            if self.secondary_unroll:
                while secondary_actual > self.secondary_start:
                    # update new value
                    data = struct.pack('<f', (secondary_actual / 100))
                    self.commonitor.send_packet(0x0E02, data)
                    self.secondary_signal.emit(secondary_actual)
                    # wait for things to settle down
                    time.sleep(self.secondary_delay)
                    secondary_actual = secondary_actual - self.secondary_delta

            # prepare for the next iteration
            secondary_actual = self.secondary_start
            self.commonitor.send_packet(0x0E02, data)
            self.secondary_signal.emit(secondary_actual)

            # prep the next value
            primary_actual = primary_actual + self.primary_delta

        # at the end of sequence, soft unroll - might be conditional
        primary_actual = primary_actual - 2 * self.primary_delta
        if self.primary_unroll:
            while primary_actual > self.primary_start:
                # update new value
                data = struct.pack('<f', (primary_actual / 100))
                self.commonitor.send_packet(0x0E01, data)
                self.primary_signal.emit(primary_actual)
                # wait for things to settle down
                time.sleep(self.primary_delay)
                primary_actual = primary_actual - self.primary_delta

        primary_actual = self.primary_start
        self.commonitor.send_packet(0x0E01, data)
        self.primary_signal.emit(primary_actual)
        # trigger cleanup, when finished
        self.finished.emit()


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
        # tukaj bi lahko pokazal vsaj kaksno okno
        w = QtWidgets.QWidget()
        QtWidgets.QMessageBox.about(w, "Napaka", "Naenkrat se lahko izvaja samo ena instanca programa")
        w.show()
        sys.exit(0)

    form = MainApp()
    # Show the form
    form.show()
    # and execute the app
    app.exec_()


# start of the program
# if we're running file directly and not importing it
if __name__ == '__main__':
    main()

