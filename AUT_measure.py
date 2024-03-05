# -*- coding: utf-8 -*-
import struct
import sys

from PyQt5 import QtWidgets, QtCore
import threading
import time
import numpy as np
import csv

from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QPushButton

import DS1000Z
import IT9121
import IT6000C
import MSO7034A
import PPA5500

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

        self.itech_watmeter_1_handler = None

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

    # komunikacija ob spremembi vrednosti
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

    def connection_error_message_box(self, device_name):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error during connection establishment with device {0}.".format(device_name))
        msg.setWindowTitle("Connection Error")
        msg.setStandardButtons(QMessageBox.Close | QMessageBox.Ok)

        # Add custom button text
        close_button = msg.button(QMessageBox.Close)
        close_button.setText("Close")

        continue_button = msg.button(QMessageBox.Ok)
        continue_button.setText("Continue")

        result = msg.exec_()

        if msg.clickedButton() == close_button:
            return 1


    # ko uporabnik pritisne na gumb, da bi zagnal meritev
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


        # connect to the measurement equipment
        # if any instruments fail to connect, raise exception
        try:
            self.Rigol_DS1000Z = DS1000Z.DS1000Z(ip_or_name = 'DS1104Z')
        except ValueError:
            is_return = self.connection_error_message_box('Rigol DS1000Z')
            if is_return:
                return

        try:
            self.ITech_IT6000C = IT6000C.IT6000C(ip_or_name = 'IT6010C')
        except ValueError:
            is_return = self.connection_error_message_box('ITech IT6000C')
            if is_return:
                return

        try:
            self.ITech_IT9121_1 = IT9121.IT9121(ip_or_name = '212.235.184.164')
        except ValueError:
            is_return = self.connection_error_message_box('ITech IT9121 (1)')
            if is_return:
                return

        try:
            self.ITech_IT9121_2 = IT9121.IT9121(ip_or_name = '212.235.184.155')
        except ValueError:
            is_return = self.connection_error_message_box('ITech IT9121 (2)')
            if is_return:
                return

        try:
            self.KinetiQ_PPA5530 = PPA5500.PPA5500(ip_or_name='212.235.184.182')
        except ValueError:
            is_return = self.connection_error_message_box('KinetiQ PPA5530')
            if is_return:
                return



        # Block the button until measurements are done
        self.app.btn_start_measure.setEnabled(False)
        # start measurement thread (so that the GUI is not blocked
        self.thread = threading.Thread(target=self.run_measurements)
        self.thread.start()
        pass

    def measure_end(self):
        self.app.btn_start_measure.setEnabled(True)
        self.app.sld_amp.setValue(0)


    # measurement thread
    def run_measurements(self):
        # setup the initial point
        primary_actual = self.primary_start
        secondary_actual = self.secondary_start

        input_voltage_list = [24, 36, 48]

        self.measurement_number = 1

        # iterate over speed
        for input_voltage in input_voltage_list:
            self.input_voltage = input_voltage
            self.ITech_IT6000C.set_system_remote()
            self.ITech_IT6000C.set_output(state=1)
            self.ITech_IT6000C.set_system_local()
            IT6000C_output_voltage = self.ITech_IT6000C.get_output_voltage()
            # checking if output voltage has reached desired voltage
            while IT6000C_output_voltage < (self.input_voltage * 0.95):
                IT6000C_output_voltage = self.ITech_IT6000C.get_output_voltage()
            time.sleep(self.sleep_timer)


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

                    # Set IT6000C voltage [20, 36, 48] and current [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in 2 for loops
                    # when voltage & current are set, wait for a second or two for values to normalize

                    print("measurement: {0} | voltage: {1} | primary: {2} | secondary: {3}".
                          format(self.measurement_number,
                                 self.input_voltage,
                                 primary_actual,
                                 secondary_actual))

                    self.measurement_number = self.measurement_number + 1

                    self.ITech_IT6000C.set_system_remote()
                    #print("IT6000C Error:",self.ITech_IT6000C.read_error())
                    #self.ITech_IT6000C.set_output(state = 0)

                    self.ITech_IT6000C.set_output_current(current = secondary_actual)
                    self.ITech_IT6000C.set_output_voltage(voltage=self.input_voltage)
                    self.ITech_IT6000C.set_system_local()

                    self.sleep_timer = 0.05
                    time.sleep(self.sleep_timer)
                    # self.Rigol_DS1000Z.set_trigger_mode('SING')  # set trigger status to single
                    self.Rigol_DS1000Z.run()  # set oscilloscope to RUN mode
                    self.Rigol_DS1000Z.set_memory_depth()
                    time.sleep(self.sleep_timer)
                    self.Rigol_DS1000Z.autoscale_and_auto_offset(channel=1)

                    self.ITech_IT9121_1.trigger(trigger_mode='OFF')
                    self.ITech_IT9121_2.trigger(trigger_mode='OFF')

                    self.KinetiQ_PPA5530.set_data_hold(hold='OFF')

                    #self.ITech_IT6000C.set_system_remote()
                    #self.ITech_IT6000C.set_output(state = 1)
                    #self.ITech_IT6000C.set_system_local()

                    time.sleep(self.sleep_timer)

                    self.Rigol_DS1000Z.stop()
                    self.ITech_IT9121_1.trigger(trigger_mode='ON')
                    self.ITech_IT9121_2.trigger(trigger_mode='ON')

                    self.KinetiQ_PPA5530.set_data_hold(hold = 'ON')
                    self.KinetiQ_PPA5530.trigger()
                    time.sleep(self.sleep_timer)

                    """ grab measured data """
                    rigol_time, rigol_values = self.Rigol_DS1000Z.capture_waveform(channel = 1,
                                                                                   number_of_points=1200)

                    ITech_1_voltage = self.ITech_IT9121_1.get_base_source_voltage(voltage = 'DC')
                    ITech_1_current = self.ITech_IT9121_1.get_base_source_current(current ='DC')
                    ITech_1_power = self.ITech_IT9121_1.get_active_power()

                    ITech_2_voltage = self.ITech_IT9121_2.get_base_source_voltage(voltage='DC')
                    ITech_2_current = self.ITech_IT9121_2.get_base_source_current(current='DC')
                    ITech_2_power = self.ITech_IT9121_2.get_active_power()

                    KinetiQ_PPA5530_voltage_1 = self.KinetiQ_PPA5530.get_voltage(phase = 3)
                    KinetiQ_PPA5530_voltage_2 = self.KinetiQ_PPA5530.get_voltage(phase=1)

                    KinetiQ_PPA5530_current_1 = self.KinetiQ_PPA5530.get_current(phase=3)
                    KinetiQ_PPA5530_current_2 = self.KinetiQ_PPA5530.get_current(phase=1)

                    KinetiQ_PPA5530_power_1 = self.KinetiQ_PPA5530.get_power(phase = 3)
                    KinetiQ_PPA5530_power_2 = self.KinetiQ_PPA5530.get_power(phase=1)

                    # get the longest array

                    arraylist = [self.app.dlog_gen.ch1_latest, self.app.dlog_gen.ch2_latest, self.app.dlog_gen.ch3_latest,
                                 self.app.dlog_gen.ch4_latest, self.app.dlog_gen.ch5_latest, self.app.dlog_gen.ch6_latest,
                                 self.app.dlog_gen.ch7_latest, self.app.dlog_gen.ch8_latest]

                    scalar_value = float(self.app.lbl_current.text())

                    arraylist_rigol_plot = np.array([rigol_values,rigol_time])
                    arraylist_rigol_plot = arraylist_rigol_plot.T

                    scalar_value_itech_1_voltage = [float(ITech_1_voltage)]
                    scalar_value_itech_1_current = [float(ITech_1_current)]
                    scalar_value_itech_1_power = [float(ITech_1_power)]

                    scalar_value_itech_2_voltage = [float(ITech_2_voltage)]
                    scalar_value_itech_2_current = [float(ITech_2_current)]
                    scalar_value_itech_2_power = [float(ITech_2_power)]

                    scalar_value_kinetiq_1_voltage = [float(KinetiQ_PPA5530_voltage_1)]
                    scalar_value_kinetiq_1_current = [float(KinetiQ_PPA5530_current_1)]
                    scalar_value_kinetiq_1_power = [float(KinetiQ_PPA5530_power_1)]

                    scalar_value_kinetiq_2_voltage = [float(KinetiQ_PPA5530_voltage_2)]
                    scalar_value_kinetiq_2_current = [float(KinetiQ_PPA5530_current_2)]
                    scalar_value_kinetiq_2_power = [float(KinetiQ_PPA5530_power_2)]


                    """
                    STEPS:
                    1.) Set IT6000C voltage [20, 36, 48] and current [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in 2 for loops
                    2.) when voltage & current are set, wait for a second or two for values to normalize
                    3.) set RIGOL autoscale
                    4.) wait for autoscale to complete
                    5.) trigger RIGOL & IT9121s
                    6.) capture RIGOL waveform and IT9121 current, voltage and power
                    7.) save RIGOL waveform to .csv file and IT9121 data to seperate .csv file
                    8.) trigger next loop
                    """

                    # TODO if required zero the secondary and send it to MCU

                    # define empty array
                    """ prepare measured date for saving """
                    # as the user might only select few channels
                    # then the channels which were not refreshed might differ in lenght ot the refreshed ones
                    # get the longest channel and write each channel where shorter chanels have the rest
                    # of data encoded as NaN
                    array_to_write = np.ones((np.max([len(ps) for ps in arraylist]), len(arraylist))) * np.nan
                    for i, c in enumerate(arraylist):  # populate columns
                        array_to_write[:len(c), i] = c

                    """save measured data """
                    itech1_values = (str(scalar_value_itech_1_voltage) + ";" +
                                     str(scalar_value_itech_1_current) + ";" +
                                     str(scalar_value_itech_1_power))

                    itech2_values = (str(scalar_value_itech_2_voltage) + ";" +
                                     str(scalar_value_itech_2_current) + ";" +
                                     str(scalar_value_itech_2_power))

                    kinetiq1_values = (str(scalar_value_kinetiq_1_voltage) + ";" +
                                       str(scalar_value_kinetiq_1_current) + ";" +
                                       str(scalar_value_kinetiq_1_power))

                    kinetiq2_values = (str(scalar_value_kinetiq_2_voltage) + ";" +
                                       str(scalar_value_kinetiq_2_current) + ";" +
                                       str(scalar_value_kinetiq_2_power))

                    filename_actual = (self.filename_base + "_" +
                                       str(self.input_voltage) + "_" +
                                       str(primary_actual) + "_" +
                                       str(secondary_actual) + "." +
                                       self.filename_ext)
                    np.savetxt(filename_actual, array_to_write, delimiter=";")

                    filename_actual_rigol = (self.filename_base + "_rigol_" +
                                             str(self.input_voltage) + "_" +
                                             str(primary_actual) + "_" +
                                             str(secondary_actual) + "." +
                                             self.filename_ext)
                    np.savetxt(filename_actual_rigol, arraylist_rigol_plot, delimiter=";")

                    filename_actual_itech_1_voltage = (self.filename_base + "_itech_1_" +
                                                       str(self.input_voltage) + "_" +
                                                       str(primary_actual) + "_" +
                                                       str(secondary_actual) + "." +
                                                       self.filename_ext)
                    np.savetxt(filename_actual_itech_1_voltage, itech1_values, delimiter=";")

                    filename_actual_itech_2_voltage = (self.filename_base + "_itech_2_"+
                                                       str(self.input_voltage) + "_" +
                                                       str(primary_actual) + "_" + str(secondary_actual) + "." +
                                                       self.filename_ext)
                    np.savetxt(filename_actual_itech_2_voltage, itech2_values, delimiter=";")

                    filename_actual_kinetiq_1_voltage = (self.filename_base + "_kinetiq_1_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    np.savetxt(filename_actual_kinetiq_1_voltage, kinetiq1_values, delimiter=";")

                    filename_actual_kinetiq_2_voltage = (self.filename_base + "_kinetiq_2_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    np.savetxt(filename_actual_kinetiq_2_voltage, kinetiq2_values, delimiter=";")

                    self.Rigol_DS1000Z.run()
                    self.ITech_IT9121_1.trigger(trigger_mode='OFF')
                    self.ITech_IT9121_2.trigger(trigger_mode='OFF')
                    self.KinetiQ_PPA5530.set_data_hold(hold='OFF')
                    self.KinetiQ_PPA5530.start()

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
