# -*- coding: utf-8 -*-
import struct
from PyQt5 import QtWidgets, QtCore
import threading
import time
import numpy as np
import csv
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

        # Block the button until measurements are done
        self.app.btn_start_measure.setEnabled(False)
        # start measurement thread (so that the GUI is not blocked
        self.thread = threading.Thread(target=self.run_measurements)
        self.thread.start()
        pass

    def measure_end(self):
        self.app.btn_start_measure.setEnabled(True)
        self.app.sld_amp.setValue(0)

    """
    $

    def named_parameters(self, name=None, ip=None, serial=None):
        if name:
            # zrihtaj listo resourcev in poglej če je ta na listi
            pass
        if ip:
            # poglej če je IP veljaven in če je se poveži nanj
            pass
        if serial:
            # zrihaj listo resourcev in se poveži na vsakega
            # pri vsakem poglje če je serial v IDN?
            # če je serial ta prav, potem štima če ne se pa odvežeš
            pass

    def test_named_parameters(self):
        self.named_parameters(name="ime")
        self.named_parameters(ip='212')
    
    """

    # measurement thread
    def run_measurements(self):
        # setup the initial point
        primary_actual = self.primary_start
        secondary_actual = self.secondary_start

        # connect to instruments
        Rigol_DS1000Z = DS1000Z.DS1000Z(ip_or_name = 'DS1104Z') # DS1000Z Can accept ip or name
        ITech_IT6000C = IT6000C.IT6000C(ip_or_name = 'IT6010C') # IT6000C Can accept ip or name

        # IT9121 can accept only ip. It has a preset port of '30000' and it only works on it. socket specifies
        # to pyvisa to use .SOCKET instead of .INSTR. .SOCKET accepts ip & port while .INSTR only accepts ip
        ITech_IT9121_1 = IT9121.IT9121(ip_or_name = '212.212.235.211')
        ITech_IT9121_2 = IT9121.IT9121(ip_or_name = '212.212.235.125')

        KinetiQ_PPA5530 = PPA5500.PPA5500(ip_or_name='212.235.184.182')


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

                # Set IT6000C voltage [20, 36, 48] and current [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in 2 for loops
                # when voltage & current are set, wait for a second or two for values to normalize
                if primary_actual == 0:
                    ITech_IT6000C.set_output_voltage(voltage = 20)
                if primary_actual == 0.5:
                    ITech_IT6000C.set_output_voltage(voltage=36)
                if primary_actual == 1:
                    ITech_IT6000C.set_output_voltage(voltage=48)

                ITech_IT6000C.set_output_current(current = secondary_actual*60)
                time.sleep(1)

                # set RIGOL autoscale
                # set all measuring instruments to 'RUN'
                # wait for autoscale to complete
                Rigol_DS1000Z.set_trigger_mode('SINGLE') # set trigger status to single
                Rigol_DS1000Z.run() # set oscilloscope to RUN mode
                Rigol_DS1000Z.autoscale_and_auto_offset(channel=1)

                ITech_IT9121_1.trigger(trigger_mode='OFF')
                ITech_IT9121_2.trigger(trigger_mode = 'OFF')

                KinetiQ_PPA5530.set_data_hold(hold = 'OFF')

                time.sleep(1)

                Rigol_DS1000Z.trigger()
                ITech_IT9121_1.trigger(trigger_mode='ON')
                ITech_IT9121_2.trigger(trigger_mode='ON')

                KinetiQ_PPA5530.set_data_hold(hold = 'ON')
                time.sleep(1)

                """ grab measured data """
                rigol_values = []
                rigol_time = []

                rigol_values, rigol_time = Rigol_DS1000Z.capture_waveform(channel = 1)

                ITech_1_voltage = ITech_IT9121_1.get_base_source_voltage(voltage = 'DC')
                ITech_1_current = ITech_IT9121_1.get_base_source_current(current ='DC')
                ITech_2_voltage = ITech_IT9121_2.get_base_source_voltage(voltage='DC')
                ITech_2_current = ITech_IT9121_2.get_base_source_current(current='DC')

                KinetiQ_PPA5530_voltage_1 = KinetiQ_PPA5530.get_voltage(phase = 1)
                KinetiQ_PPA5530_voltage_2 = KinetiQ_PPA5530.get_voltage(phase=2)
                KinetiQ_PPA5530_current_1 = KinetiQ_PPA5530.get_current(phase=1)
                KinetiQ_PPA5530_current_2 = KinetiQ_PPA5530.get_current(phase=2)

                # get the longest array

                arraylist = [self.app.dlog_gen.ch1_latest, self.app.dlog_gen.ch2_latest, self.app.dlog_gen.ch3_latest,
                             self.app.dlog_gen.ch4_latest, self.app.dlog_gen.ch5_latest, self.app.dlog_gen.ch6_latest,
                             self.app.dlog_gen.ch7_latest, self.app.dlog_gen.ch8_latest]

                scalar_value = float(self.app.lbl_current.text())

                arraylist_rigol_plot = [[rigol_values], [rigol_time]]

                scalar_value_itech_1_voltage = float(ITech_1_voltage)
                scalar_value_itech_1_current = float(ITech_1_current)

                scalar_value_itech_2_voltage = float(ITech_2_voltage)
                scalar_value_itech_2_current = float(ITech_2_current)

                scalar_value_kinetiq_1_voltage = float(KinetiQ_PPA5530_voltage_1)
                scalar_value_kinetiq_1_current = float(KinetiQ_PPA5530_current_1)

                scalar_value_kinetiq_2_voltage = float(KinetiQ_PPA5530_voltage_2)
                scalar_value_kinetiq_2_current = float(KinetiQ_PPA5530_current_2)


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
                array_to_write = np.ones((np.max([len(ps) for ps in arraylist]), len(arraylist))) * np.nan
                for i, c in enumerate(arraylist):  # populate columns
                    array_to_write[:len(c), i] = c

                array_to_write_rigol = np.ones((np.max([len(ps) for ps in arraylist_rigol_plot]), len(arraylist_rigol_plot))) * np.nan
                for i, c in enumerate(arraylist_rigol_plot):  # populate columns
                    array_to_write_rigol[:len(c), i] = c

                """ save measured data """

                filename_actual = self.filename_base + "_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual, array_to_write, delimiter=";")

                filename_actual_rigol = self.filename_base + "_rigol_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_rigol, array_to_write_rigol, delimiter=";")

                filename_actual_itech_1_voltage = self.filename_base + "_itech_1_voltage_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_itech_1_voltage, scalar_value_itech_1_voltage, delimiter=";")

                filename_actual_itech_1_current = self.filename_base + "_itech_1_current_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_itech_1_current, scalar_value_itech_1_current, delimiter=";")

                filename_actual_itech_2_voltage = self.filename_base + "_itech_2_voltage_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_itech_2_voltage, scalar_value_itech_2_voltage, delimiter=";")

                filename_actual_itech_2_current = self.filename_base + "_itech_2_current_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_itech_2_current, scalar_value_itech_2_current, delimiter=";")

                filename_actual_kinetiq_1_voltage = self.filename_base + "_kinetiq_1_voltage_" + str(primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_kinetiq_1_voltage, scalar_value_kinetiq_1_voltage, delimiter=";")

                filename_actual_kinetiq_1_current = self.filename_base + "_kinetiq_1_current_" + str(
                    primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_kinetiq_1_current, scalar_value_kinetiq_1_current, delimiter=";")

                filename_actual_kinetiq_2_voltage = self.filename_base + "_kinetiq_2_voltage_" + str(
                    primary_actual) + "_" + str(
                    secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_kinetiq_2_voltage, scalar_value_kinetiq_2_voltage, delimiter=";")

                filename_actual_kinetiq_2_current = self.filename_base + "_kinetiq_2_current_" + str(
                primary_actual) + "_" + str(
                secondary_actual) + "." + self.filename_ext
                np.savetxt(filename_actual_kinetiq_2_current, scalar_value_kinetiq_2_current, delimiter=";")

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
