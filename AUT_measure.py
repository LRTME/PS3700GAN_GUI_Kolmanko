# -*- coding: utf-8 -*-
import struct
from PyQt5 import QtWidgets, QtCore
import threading
import time
import numpy as np

COLOR_YELLOW = "background-color:#F8D129;"
COLOR_RED = "background-color:#c83531;"
COLOR_GREEN = "background-color:#32cd32;"
COLOR_BRIGHT_RED = "background-color:#FF4646;"
COLOR_DEFAULT = "background-color:rgba(255, 255, 255, 0);"


class AUT_measurement(QtCore.QObject):

    # for measurement automation
    finished = QtCore.pyqtSignal()
    primary_signal = QtCore.pyqtSignal(int)
    secondary_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.speed_start = 0
        self.speed_stop = 0
        self.speed_delta = 0

        self.current_start = 0
        self.current_stop = 0
        self.current_delta = 0

        self.filename_base = ""

        # init delay spinboxes
        self.app.spb_primary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.app.spb_primary_delay.setMinimum(0.001)
        self.app.spb_primary_delay.setMaximum(100)
        self.app.spb_primary_delay.setValue(0.1)

        self.app.spb_secondary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.app.spb_secondary_delay.setMinimum(0.001)
        self.app.spb_secondary_delay.setMaximum(10)
        self.app.spb_secondary_delay.setValue(0.01)

        self.finished.connect(self.measure_end)
        self.primary_signal.connect(self.primary_updated)
        self.secondary_signal.connect(self.secondary_updated)

        self.app.sld_primary.valueChanged[int].connect(self.primary_changed)
        self.app.sld_secondary.valueChanged[int].connect(self.secondary_changed)

        self.app.btn_start_measure.clicked.connect(self.measure_start)

    def primary_changed(self):
        self.app.lbl_primary.setText(str(self.app.sld_primary.value() / 100))
        self.app.commonitor.send_packet(0x0E01, struct.pack('<f', float(self.app.sld_primary.value() / 100)))

    def secondary_changed(self):
        self.app.lbl_secondary.setText(str(self.app.sld_secondary.value() / 100))
        self.app.commonitor.send_packet(0x0E02, struct.pack('<f', float(self.app.sld_secondary.value() / 100)))

    def primary_updated(self, value):
        self.app.lbl_primary.setText(str(round(value / 100, 2)))
        self.app.sld_primary.blockSignals(True)
        self.app.sld_primary.setValue(value)
        self.app.sld_primary.blockSignals(False)

    def secondary_updated(self, value):
        self.app.lbl_secondary.setText(str(round(value / 100, 2)))
        self.app.sld_secondary.blockSignals(True)
        self.app.sld_secondary.setValue(value)
        self.app.sld_secondary.blockSignals(True)

    def measure_start(self):
        # parse the test boundary conditions
        self.primary_start = int(self.app.spb_primary_start.value() * 100)
        self.primary_stop = int(self.app.spb_primary_stop.value() * 100)
        self.primary_delta = int(self.app.spb_primary_delta.value() * 100)
        self.primary_delay = self.app.spb_primary_delay.value()
        self.primary_unroll = self.app.cb_primary_unroll.isChecked()

        self.secondary_start = int(self.app.spb_secondary_start.value() * 100)
        self.secondary_stop = int(self.app.spb_secondary_stop.value() * 100)
        self.secondary_delta = int(self.app.spb_secondary_delta.value() * 100)
        self.secondary_delay = self.app.spb_secondary_delay.value()
        self.secondary_unroll = self.app.cb_secondary_unroll.isChecked()

        # run the measurements only if setup is sane
        if self.primary_stop < self.primary_start:
            self.app.spb_primary_start.setStyleSheet(COLOR_BRIGHT_RED)
            self.app.spb_primary_stop.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.app.spb_primary_start.setStyleSheet(COLOR_DEFAULT)
            self.app.spb_primary_stop.setStyleSheet(COLOR_DEFAULT)

        if self.primary_delta > (self.primary_stop - self.primary_start):
            self.app.spb_primary_delta.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.app.spb_primary_delta.setStyleSheet(COLOR_DEFAULT)

        if self.secondary_stop < self.secondary_start:
            self.app.spb_secondary_start.setStyleSheet(COLOR_BRIGHT_RED)
            self.app.spb_secondary_stop.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.app.spb_secondary_start.setStyleSheet(COLOR_DEFAULT)
            self.app.spb_secondary_stop.setStyleSheet(COLOR_DEFAULT)

        if self.secondary_delta > (self.secondary_stop - self.secondary_start):
            self.app.spb_secondary_delta.setStyleSheet(COLOR_BRIGHT_RED)
            return
        else:
            self.app.spb_secondary_delta.setStyleSheet(COLOR_DEFAULT)

        # ask user for a filename
        initial_filename = QtWidgets.QFileDialog.getSaveFileName(self.app, caption='Save File', filter="*.csv")[0]
        # cancel
        if not initial_filename:
            return
        self.filename_base = initial_filename.split('.')[0]
        self.filename_ext = initial_filename.split('.')[1]

        # Block the button until measurements are done
        self.app.btn_start_measure.setEnabled(False)
        # start measurement thread (so that the GUI is not blocked
        self.thread = threading.Thread(target=self.run_measurements)
        self.thread.start()
        pass

        # cleanup after the measurements

    def measure_end(self):
        self.app.btn_start_measure.setEnabled(True)
        self.app.sld_amp.setValue(0)

    # measurement thread
    def run_measurements(self):
        # setup the initial point
        primary_actual = self.primary_start
        secondary_actual = self.secondary_start

        # iterate over speed
        while primary_actual <= self.primary_stop:
            # update new value
            data = struct.pack('<f', (primary_actual / 100))
            self.app.commonitor.send_packet(0x0E01, data)
            self.primary_signal.emit(primary_actual)
            # wait for things to settle down
            time.sleep(self.primary_delay)

            # iterate over current
            while secondary_actual <= self.secondary_stop:
                # update new value
                data = struct.pack('<f', (secondary_actual / 100))
                self.app.commonitor.send_packet(0x0E02, data)
                self.secondary_signal.emit(secondary_actual)
                # wait for things to settle down
                time.sleep(self.secondary_delay)

                # grab measured data
                # get the longest array
                arraylist = [self.app.dlog_gen.ch1_latest, self.app.dlog_gen.ch2_latest, self.app.dlog_gen.ch3_latest,
                             self.app.dlog_gen.ch4_latest, self.app.dlog_gen.ch5_latest, self.app.dlog_gen.ch6_latest,
                             self.app.dlog_gen.ch7_latest, self.app.dlog_gen.ch8_latest]
                # define empty array
                array_to_write = np.ones((np.max([len(ps) for ps in arraylist]), len(arraylist))) * np.nan
                for i, c in enumerate(arraylist):  # populate columns
                    array_to_write[:len(c), i] = c

                # save measured data
                filename_actual = self.filename_base + "_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual, array_to_write, delimiter=";")
                # prep the next value of current
                secondary_actual = secondary_actual + self.secondary_delta

            # at the end of sequence, soft unroll - might be conditional
            secondary_actual = secondary_actual - 2 * self.secondary_delta
            if self.secondary_unroll:
                while secondary_actual > self.secondary_start:
                    # update new value
                    data = struct.pack('<f', (secondary_actual / 100))
                    self.app.commonitor.send_packet(0x0E02, data)
                    self.secondary_signal.emit(secondary_actual)
                    # wait for things to settle down
                    time.sleep(self.secondary_delay)
                    secondary_actual = secondary_actual - self.secondary_delta

            # prepare for the next iteration
            secondary_actual = self.secondary_start
            data = struct.pack('<f', (secondary_actual / 100))
            self.app.commonitor.send_packet(0x0E02, data)
            self.secondary_signal.emit(secondary_actual)

            # prep the next value
            primary_actual = primary_actual + self.primary_delta

        # at the end of sequence, soft unroll - might be conditional
        primary_actual = primary_actual - 2 * self.primary_delta
        if self.primary_unroll:
            while primary_actual > self.primary_start:
                # update new value
                data = struct.pack('<f', (primary_actual / 100))
                self.app.commonitor.send_packet(0x0E01, data)
                self.primary_signal.emit(primary_actual)
                # wait for things to settle down
                time.sleep(self.primary_delay)
                primary_actual = primary_actual - self.primary_delta

        primary_actual = self.primary_start
        data = struct.pack('<f', (primary_actual / 100))
        self.app.commonitor.send_packet(0x0E01, data)
        self.primary_signal.emit(primary_actual)
        # trigger cleanup, when finished
        self.finished.emit()
