# -*- coding: utf-8 -*-
import struct
from PySide6 import QtWidgets, QtCore
import threading
import time
import numpy as np
import csv
import logging
import datetime

import GUI_automatic_measurements_dialog
import GUI_main_window

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

class AUT_measurement(QtWidgets.QDialog, GUI_automatic_measurements_dialog.Ui_Dialog):

    # for measurement automation
    finished = QtCore.Signal()
    primary_signal = QtCore.Signal(int)
    secondary_signal = QtCore.Signal(int)

    def __init__(self, parent: GUI_main_window.Ui_MainWindow):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setModal(False)
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
        self.spb_primary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.spb_primary_delay.setMinimum(0.001)
        self.spb_primary_delay.setMaximum(100)
        self.spb_primary_delay.setValue(0.1)

        self.spb_secondary_delay.setOpts(value=1, dec=True, step=1, minStep=0.01, int=False)
        self.spb_secondary_delay.setMinimum(0.001)
        self.spb_secondary_delay.setMaximum(10)
        self.spb_secondary_delay.setValue(0.1)

        self.finished.connect(self.measure_end)
        self.primary_signal.connect(self.primary_updated)
        self.secondary_signal.connect(self.secondary_updated)

        self.sld_primary.valueChanged[int].connect(self.primary_changed)
        self.sld_secondary.valueChanged[int].connect(self.secondary_changed)

        self.btn_start_measure.clicked.connect(self.measure_start)
        self.btn_stop_measure.clicked.connect(self.measure_stop)

    # komunikacija ob spremembi vrednosti
    def primary_changed(self):
        self.lbl_primary.setText(str(self.sld_primary.value() / 100))
        self.app.commonitor.send_packet(0x0E01, struct.pack('<f', float(self.sld_primary.value() / 100)))

    def secondary_changed(self):
        self.lbl_secondary.setText(str(self.sld_secondary.value() / 100))
        self.app.commonitor.send_packet(0x0E02, struct.pack('<f', float(self.sld_secondary.value() / 100)))

    def primary_updated(self, value):
        self.lbl_primary.setText(str(round(value / 100, 2)))
        self.sld_primary.blockSignals(True)
        self.sld_primary.setValue(value)
        self.sld_primary.blockSignals(False)

    def secondary_updated(self, value):
        self.lbl_secondary.setText(str(round(value / 100, 2)))
        self.sld_secondary.blockSignals(True)
        self.sld_secondary.setValue(value)
        self.sld_secondary.blockSignals(False)

    def connection_error_message_box(self, device_name):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error during connection establishment with device {0}.".format(device_name))
        msg.setWindowTitle("Connection Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Ok)

        # Add custom button text
        close_button = msg.button(QtWidgets.QMessageBox.Close)
        close_button.setText("Close")

        continue_button = msg.button(QtWidgets.QMessageBox.Ok)
        continue_button.setText("Continue")

        result = msg.exec_()

        if msg.clickedButton() == close_button:
            return 1


    # ko uporabnik pritisne na gumb, da bi zagnal meritev
    def measure_start(self):
        # parse the test boundary conditions
        self.primary_start = int(self.spb_primary_start.value() * 100)
        self.primary_stop = int(self.spb_primary_stop.value() * 100)
        self.primary_delta = int(self.spb_primary_delta.value() * 100)
        self.primary_delay = self.spb_primary_delay.value()
        self.primary_unroll = self.cb_primary_unroll.isChecked()

        self.secondary_start = int(self.spb_secondary_start.value() * 100)
        self.secondary_stop = int(self.spb_secondary_stop.value() * 100)
        self.secondary_delta = int(self.spb_secondary_delta.value() * 100)
        self.secondary_delay = self.spb_secondary_delay.value()
        self.secondary_unroll = self.cb_secondary_unroll.isChecked()
        self.secondary_zero = self.cb_secondary_zero.isChecked()

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
        initial_filename = QtWidgets.QFileDialog.getSaveFileName(self.app, caption='Save File', filter="*.csv")[0]
        # cancel
        if not initial_filename:
            return
        self.filename_base = initial_filename.split('.')[0]
        self.filename_ext = initial_filename.split('.')[1]

        # configure logging
        # file name consists of YYYY:MM:DD:HH:MM:SS_USER-FILE-NAME_LOG
        now = datetime.datetime.now()
        log_filename = str(now.strftime("%Y-%m-%d_%H-%M-%S")) + "logfile" + ".log"

        logging.basicConfig(filename=log_filename,
                            encoding='utf-8',
                            filemode = "w",
                            level=logging.DEBUG)

        # TODO grab MCU commit number and store it
        mcu_commit_number = self.app.about_dialog.lbl_git_sha.text()
        logging.info("{0}: MCU commit number: {1}".format(datetime.datetime.now(), mcu_commit_number))

        # connect to the measurement equipment
        # if any instruments fail to connect, raise exception
        logging.info("{0}: Starting connection attempts to instruments".format(datetime.datetime.now()))
        logging.info("{0}: Attempting to connect to Rigol DS1000Z".format(datetime.datetime.now()))
        try:
            self.Rigol_DS1000Z = DS1000Z.DS1000Z(ip_or_name = 'DS1104Z')
        except ValueError:
            logging.error("{0}: Could not connect to Rigol DS1000Z".format(datetime.datetime.now()))
            is_return = self.connection_error_message_box('Rigol DS1000Z')
            if is_return:
                return

        logging.info("{0}: Connection to Rigol DS1000Z successful".format(datetime.datetime.now()))
        logging.info("{0}: Attempting to connect to ITech IT6000C".format(datetime.datetime.now()))

        try:
            self.ITech_IT6000C = IT6000C.IT6000C(ip_or_name = 'IT6010C')
        except ValueError:
            logging.error("{0}: Could not connect to ITech IT6000C".format(datetime.datetime.now()))
            is_return = self.connection_error_message_box('ITech IT6000C')
            if is_return:
                return

        logging.info("{0}: Connection to ITech IT6000C successful".format(datetime.datetime.now()))
        logging.info("{0}: Attempting to connect to ITech IT9121 (1)".format(datetime.datetime.now()))

        try:
            self.ITech_IT9121_1 = IT9121.IT9121(ip_or_name = '212.235.184.148')
        except ValueError:
            logging.error("{0}: Could not connect to ITech IT9121 (1)".format(datetime.datetime.now()))
            is_return = self.connection_error_message_box('ITech IT9121 (1)')
            if is_return:
                return

        logging.info("{0}: Connection to ITech IT9121 (1) successful".format(datetime.datetime.now()))
        logging.info("{0}: Attempting to connect to ITech IT9121 (2)".format(datetime.datetime.now()))

        try:
            self.ITech_IT9121_2 = IT9121.IT9121(ip_or_name = '212.235.184.150')
        except ValueError:
            logging.error("{0}: Could not connect to ITech IT9121 (2)".format(datetime.datetime.now()))
            is_return = self.connection_error_message_box('ITech IT9121 (2)')
            if is_return:
                return

        logging.info("{0}: Connection to ITech IT9121 (2) successful".format(datetime.datetime.now()))
        logging.info("{0}: Attempting to connect to KinetiQ PPA5530".format(datetime.datetime.now()))

        try:
            self.KinetiQ_PPA5530 = PPA5500.PPA5500(ip_or_name='212.235.184.182')
        except ValueError:
            logging.error("{0}: Could not connect to KinetiQ PPA5530".format(datetime.datetime.now()))
            is_return = self.connection_error_message_box('KinetiQ PPA5530')
            if is_return:
                return

        logging.info("{0}: Connection to KinetiQ PPA5530 successful".format(datetime.datetime.now()))


        # Block the button until measurements are done
        self.btn_start_measure.setEnabled(False)
        # start measurement thread (so that the GUI is not blocked
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run_measurements, args=(self.stop_event,))
        self.thread.start()

        # enable the stop button
        self.btn_stop_measure.setEnabled(True)
        pass

    def measure_stop(self):
        logging.info("{0}: Measurement stopped".format(datetime.datetime.now()))
        self.stop_event.set()
        self.btn_stop_measure.setEnabled(False)

    def measure_end(self):
        logging.info("{0}: Measurement ended".format(datetime.datetime.now()))
        self.btn_start_measure.setEnabled(True)
        self.btn_stop_measure.setEnabled(False)
        self.sld_primary.setValue(0)
        self.sld_secondary.setValue(0)

    # measurement thread
    def run_measurements(self, stop_event: threading.Event):
        # setup the initial point
        logging.info("{0}: Setting up initial points".format(datetime.datetime.now()))

        primary_actual = self.primary_start
        secondary_actual = self.secondary_start

        logging.info("{0}: Initial points set; Primary: {1}, Secondary: {2}".format(datetime.datetime.now(),
                                                                                    primary_actual,
                                                                                    secondary_actual))

        self.measurement_start_time = time.time()

        #input_voltage_list = [24, 36, 48]
        input_voltage_list = [10, 20, 30]
        logging.info("{0}: Input voltages list set to: {1}".format(datetime.datetime.now(), input_voltage_list))


        self.measurement_number = 1

        for input_voltage in input_voltage_list:

            self.input_voltage = input_voltage

            logging.info("{0}: Currently set input voltage: {1}".format(datetime.datetime.now(), input_voltage))
            logging.info("{0}: Setting DC/DC to standby".format(datetime.datetime.now()))

            # preden spremenim napetost ugasnem
            self.lbl_state_previous = self.app.lbl_state.text()
            if self.app.lbl_state.text() == "Work":
                self.app.btn_on_off.click()
                logging.info("{0}: DC/DC set from {1} to {2}".format(datetime.datetime.now(),
                                                                     self.lbl_state_previous,
                                                                     self.app.lbl_state.text()))
                time.sleep(1.0)
            else:
                logging.error("{0}: Could not set DC/DC to standby".format(datetime.datetime.now()))
                raise Exception

            print("DC/DC state set from {0} -> {1}".format(self.lbl_state_previous, self.app.lbl_state.text()))

            logging.info("{0}: Setting ITech IT6000C to remote".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_system_remote()

            logging.info("{0}: Setting ITech IT6000C positive voltage slew to 1".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_positive_voltage_slew(1)
            logging.info("{0}: Setting ITech IT6000C current limits to 20, -20".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_current_limits(20, -20)
            logging.info("{0}: Setting ITech IT6000C negative voltage slew to 1".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_negative_voltage_slew(1)
            logging.info("{0}: Setting ITech IT6000C output voltage to {1}".format(datetime.datetime.now(),
                                                                                   input_voltage))
            self.ITech_IT6000C.set_output_voltage(input_voltage)
            logging.info("{0}: Setting ITech IT6000C output to ON".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_output(state=1)

            logging.info("{0}: Setting ITech IT6000C to local".format(datetime.datetime.now()))
            self.ITech_IT6000C.set_system_local()

            logging.info("{0}: Setting ITech IT9121 (1) to remote".format(datetime.datetime.now()))
            self.ITech_IT9121_1.set_system_remote()
            logging.info("{0}: Setting ITech IT9121 (2) to remote".format(datetime.datetime.now()))
            self.ITech_IT9121_2.set_system_remote()

            logging.info("{0}: Setting ITech IT9121 (1) capture mode to not continuous".format(datetime.datetime.now()))
            self.ITech_IT9121_1.set_capture_mode(continuous = "OFF")
            logging.info("{0}: Setting ITech IT9121 (2) capture mode to not continuous".format(datetime.datetime.now()))
            self.ITech_IT9121_2.set_capture_mode(continuous="OFF")

            logging.info("{0}: Setting ITech IT9121 (1) to local".format(datetime.datetime.now()))
            self.ITech_IT9121_1.set_system_local()
            logging.info("{0}: Setting ITech IT9121 (3) to local".format(datetime.datetime.now()))
            self.ITech_IT9121_2.set_system_local()

            # checking for errors...
            print("IT6000C error: ",self.ITech_IT6000C.read_error())

            print("Waiting for power meter to reach desired value ({0}V)...".format(input_voltage))
            logging.info(
                "{0}: Waiting for ITech IT6000C to reach desired voltage value ({1}V)"
                .format(datetime.datetime.now(),input_voltage))

            IT6000C_output_voltage = float(self.ITech_IT6000C.get_output_voltage())
            # checking if output voltage has reached desired voltage
            while float(IT6000C_output_voltage) < (float(self.input_voltage) * 0.99):
                logging.info("{0}: Current ITech IT6000C output voltage: {1}V".format(datetime.datetime.now(),
                                                                                      IT6000C_output_voltage))
                IT6000C_output_voltage = self.ITech_IT6000C.get_output_voltage()

            logging.info(
                "{0}: ITech IT6000C has reached the desired voltage value ({1}V)".format(datetime.datetime.now(),
                                                                                              input_voltage))

            self.lbl_state_previous = self.app.lbl_state.text()
            logging.info("{0}: Setting DC/DC to work".format(datetime.datetime.now()))
            if self.app.lbl_state.text() == "Standby_cold":
                self.app.btn_on_off.click()
                time.sleep(1.0)

            logging.info("{0}: DC/DC set from {1} to {2}".format(datetime.datetime.now(),
                                                                 self.lbl_state_previous,
                                                                 self.app.lbl_state.text()))
            print("DC/DC state set from {0} -> {1}".format(self.lbl_state_previous, self.app.lbl_state.text()))

            self.lbl_state_previous = self.app.lbl_state.text()
            if self.app.lbl_state.text() == "Standby_hot":
                self.app.btn_on_off.click()
                time.sleep(1.0)

            logging.info("{0}: DC/DC set from {1} to {2}".format(datetime.datetime.now(),
                                                                 self.lbl_state_previous,
                                                                 self.app.lbl_state.text()))
            print("DC/DC state set from {0} -> {1}".format(self.lbl_state_previous, self.app.lbl_state.text()))

            # Set IT6000C voltage [20, 36, 48] and current [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in 2 for loops
            # when voltage & current are set, wait for a second or two for values to normalize

            logging.info(
                "{0}: Waiting for ITech IT6000C to reach desired voltage value ({1}V)"
                .format(datetime.datetime.now(),input_voltage))
            print("Rechecking if power meter is at desired value ({0}V)...".format(input_voltage))

            IT6000C_output_voltage = float(self.ITech_IT6000C.get_output_voltage())
            # re-checking if output voltage has reached desired voltage
            while float(IT6000C_output_voltage) < (float(self.input_voltage) * 0.99):
                IT6000C_output_voltage = self.ITech_IT6000C.get_output_voltage()

            logging.info(
                "{0}: ITech IT6000C has reached the desired voltage value ({1}V)".format(datetime.datetime.now(),
                                                                                              input_voltage))
            print("Desired value reached.")

            run_once = True

            #while primary_actual <= self.primary_stop:
            while run_once:

                run_once = False
                # exit if required
                if stop_event.is_set():
                    break
                # update new value
                data = struct.pack('<f', (primary_actual / 100))
                self.app.commonitor.send_packet(0x0E01, data)
                self.primary_signal.emit(primary_actual)

                # wait for things to settle down
                time.sleep(self.primary_delay)

                # iterate over current
                while secondary_actual <= self.secondary_stop:
                    # exit if required
                    if stop_event.is_set():
                        break
                    # update new value
                    data = struct.pack('<f', (secondary_actual / 100))
                    self.app.commonitor.send_packet(0x0E02, data)
                    self.secondary_signal.emit(secondary_actual)
                    # wait for things to settle down
                    time.sleep(self.secondary_delay)

                    logging.info(
                        "{0}: ---------------------------------------------------------------"
                        .format(datetime.datetime.now()))
                    logging.info(
                        "{0}: measurement: {1} | voltage: {2} | primary: {3} | secondary: {4}"
                        .format(datetime.datetime.now(),
                                self.measurement_number,
                                self.input_voltage,
                                primary_actual,
                                secondary_actual))

                    print("---------------------------------------------------------------")
                    print("measurement: {0} | voltage: {1} | primary: {2} | secondary: {3}".
                          format(self.measurement_number,
                                 self.input_voltage,
                                 primary_actual,
                                 secondary_actual))

                    self.measurement_number = self.measurement_number + 1

                    self.sleep_timer = 0.1
                    # self.Rigol_DS1000Z.set_trigger_mode('SING')  # set trigger status to single

                    logging.info(
                        "{0}: Setting Rigol DS1000Z to run mode (Trigger = OFF)".format(datetime.datetime.now()))
                    self.Rigol_DS1000Z.run()  # set oscilloscope to RUN mode

                    logging.info("{0}: Setting Rigol DS1000Z memory depth".format(datetime.datetime.now()))
                    self.Rigol_DS1000Z.set_memory_depth()
                    time.sleep(self.sleep_timer)
                    #self.Rigol_DS1000Z.autoscale_and_auto_offset(channel=1)
                    #self.Rigol_DS1000Z.autoscale_and_auto_offset(channel=2)
                    #time.sleep(1)

                    logging.info("{0}: Setting ITech IT9121 (1) to remote".format(datetime.datetime.now()))
                    self.ITech_IT9121_1.set_system_remote()

                    logging.info("{0}: Setting ITech IT9121 (2) to remote".format(datetime.datetime.now()))
                    self.ITech_IT9121_2.set_system_remote()

                    logging.info(
                        "{0}: Setting ITech IT9121 (1) to run mode (trigger = OFF)".format(datetime.datetime.now()))
                    self.ITech_IT9121_1.trigger()

                    logging.info(
                        "{0}: Setting ITech IT9121 (2) to run mode (trigger = OFF)".format(datetime.datetime.now()))
                    self.ITech_IT9121_2.trigger()

                    logging.info(
                        "{0}: Setting KinetiQ PPA5530 to run mode (hold = OFF)".format(datetime.datetime.now()))
                    self.KinetiQ_PPA5530.set_data_hold(hold='OFF')

                    #self.ITech_IT6000C.set_system_remote()
                    #self.ITech_IT6000C.set_output(state = 1)
                    #self.ITech_IT6000C.set_system_local()

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Setting Rigol DS1000Z to SINGLE trigger".format(datetime.datetime.now()))
                    self.Rigol_DS1000Z.trigger_single()


                    logging.info(
                        "{0}: Setting ITech IT9121 (1) to stop mode (Trigger = ON)".format(datetime.datetime.now()))
                    self.ITech_IT9121_1.trigger()

                    logging.info(
                        "{0}: Setting ITech IT9121 (2) to stop mode (Trigger = ON)".format(datetime.datetime.now()))
                    self.ITech_IT9121_2.trigger()

                    logging.info(
                        "{0}: Setting KinetiQ PPA5530 to run mode (hold = OFF)".format(datetime.datetime.now()))
                    self.KinetiQ_PPA5530.set_data_hold(hold = 'ON')

                    time.sleep(self.sleep_timer)

                    """ grab measured data """
                    logging.info(
                        "{0}: Grabbing measured data".format(datetime.datetime.now()))

                    # check if rigol trigger is done
                    while True:
                        trigger_status = self.Rigol_DS1000Z.get_trigger_status()
                        if trigger_status == "STOP":
                            break

                    logging.info(
                        "{0}: Grabbing Rigol DS1000Z captured waveform on channel 1".format(datetime.datetime.now()))
                    rigol_time_ch1, rigol_values_ch1 = self.Rigol_DS1000Z.capture_waveform(channel = 1)

                    logging.info(
                        "{0}: Grabbing Rigol DS1000Z captured waveform on channel 2".format(datetime.datetime.now()))
                    rigol_time_ch2, rigol_values_ch2 = self.Rigol_DS1000Z.capture_waveform(channel=2)

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured voltage".format(datetime.datetime.now()))
                    ITech_1_voltage = self.ITech_IT9121_1.get_base_source_voltage(voltage = 'DC')

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured voltage".format(datetime.datetime.now()))
                    ITech_2_voltage = self.ITech_IT9121_2.get_base_source_voltage(voltage='DC')

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured current".format(datetime.datetime.now()))
                    ITech_1_current = self.ITech_IT9121_1.get_base_source_current(current ='DC')

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured current".format(datetime.datetime.now()))
                    ITech_2_current = self.ITech_IT9121_2.get_base_source_current(current='DC')

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured active power".format(datetime.datetime.now()))
                    ITech_1_power = self.ITech_IT9121_1.get_active_power()

                    logging.info(
                        "{0}: Grabbing ITech IT9121 (1) captured active power".format(datetime.datetime.now()))
                    ITech_2_power = self.ITech_IT9121_2.get_active_power()

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Setting ITech IT9121 (1) to local".format(datetime.datetime.now()))
                    self.ITech_IT9121_1.set_system_local()

                    logging.info(
                        "{0}: Setting ITech IT9121 (1) to local".format(datetime.datetime.now()))
                    self.ITech_IT9121_2.set_system_local()

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 voltage on phase 3".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_voltage_1 = self.KinetiQ_PPA5530.get_voltage(phase = 3)

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 voltage on phase 1".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_voltage_2 = self.KinetiQ_PPA5530.get_voltage(phase=1)

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 current on phase 3".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_current_1 = self.KinetiQ_PPA5530.get_current(phase=3)

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 current on phase 1".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_current_2 = self.KinetiQ_PPA5530.get_current(phase=1)

                    time.sleep(self.sleep_timer)

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 power on phase 3".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_power_1 = self.KinetiQ_PPA5530.get_power(phase = 3)

                    logging.info(
                        "{0}: Grabbing KinetiQ PPA5530 power on phase 1".format(datetime.datetime.now()))
                    KinetiQ_PPA5530_power_2 = self.KinetiQ_PPA5530.get_power(phase=1)

                    logging.info(
                        "{0}: Grabbing measured data: DONE".format(datetime.datetime.now()))

                    # get the longest array

                    arraylist = [self.app.dlog_gen.ch1_latest, self.app.dlog_gen.ch2_latest, self.app.dlog_gen.ch3_latest,
                                 self.app.dlog_gen.ch4_latest, self.app.dlog_gen.ch5_latest, self.app.dlog_gen.ch6_latest,
                                 self.app.dlog_gen.ch7_latest, self.app.dlog_gen.ch8_latest]

                    scalar_value = [float(self.app.lbl_current.text())]

                    # Zero secondary between measurements if grabbing data takes a long time
                    if self.secondary_zero:
                        logging.info(
                            "{0}: Zeroing secondary".format(datetime.datetime.now()))
                        data = struct.pack('<f', (0 / 100))
                        self.app.commonitor.send_packet(0x0E02, data)
                        self.secondary_signal.emit(secondary_actual)

                    # TODO save to file
                    logging.info(
                        "{0}: Formatting measured data for saving".format(datetime.datetime.now()))
                    pcb_temp = [float(self.app.lbl_temp_pcb.text())]

                    arraylist_rigol_ch1_plot = np.array([rigol_values_ch1,rigol_time_ch1])
                    arraylist_rigol_ch1_plot = arraylist_rigol_ch1_plot.T

                    arraylist_rigol_ch2_plot = np.array([rigol_values_ch2,rigol_time_ch2])
                    arraylist_rigol_ch2_plot = arraylist_rigol_ch2_plot.T

                    scalar_value_itech_1_voltage = float(ITech_1_voltage)
                    scalar_value_itech_1_current = float(ITech_1_current)
                    scalar_value_itech_1_power = float(ITech_1_power)
                    #itech1_values = [[scalar_value_itech_1_voltage],[scalar_value_itech_1_current],[scalar_value_itech_1_power]]

                    scalar_value_itech_2_voltage = float(ITech_2_voltage)
                    scalar_value_itech_2_current = float(ITech_2_current)
                    scalar_value_itech_2_power = float(ITech_2_power)
                    #itech2_values = [scalar_value_itech_2_voltage,scalar_value_itech_2_current,scalar_value_itech_2_power]

                    scalar_value_kinetiq_1_voltage = float(KinetiQ_PPA5530_voltage_1)
                    scalar_value_kinetiq_1_current = float(KinetiQ_PPA5530_current_1)
                    scalar_value_kinetiq_1_power = float(KinetiQ_PPA5530_power_1)
                    #kinetiq1_values = [scalar_value_kinetiq_1_voltage,scalar_value_kinetiq_1_current,scalar_value_kinetiq_1_power]

                    scalar_value_kinetiq_2_voltage = float(KinetiQ_PPA5530_voltage_2)
                    scalar_value_kinetiq_2_current = float(KinetiQ_PPA5530_current_2)
                    scalar_value_kinetiq_2_power = float(KinetiQ_PPA5530_power_2)
                    #kinetiq2_values = [scalar_value_kinetiq_2_voltage,scalar_value_kinetiq_2_current,scalar_value_kinetiq_2_power]


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

                    logging.info(
                        "{0}: Saving measured data".format(datetime.datetime.now()))

                    array_to_write = np.ones((np.max([len(ps) for ps in arraylist]), len(arraylist))) * np.nan
                    for i, c in enumerate(arraylist):  # populate columns
                        array_to_write[:len(c), i] = c

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


                    logging.info(
                        "{0}: Saving  channel 1 measured data of Rigol DS1000Z".format(datetime.datetime.now()))
                    filename_actual_rigol_ch1 = (self.filename_base + "_rigol_ch1_" +
                                             str(self.input_voltage) + "_" +
                                             str(primary_actual) + "_" +
                                             str(secondary_actual) + "." +
                                             self.filename_ext)
                    np.savetxt(filename_actual_rigol_ch1, arraylist_rigol_ch1_plot, delimiter=";")
                    logging.info(
                        "{0}: Rigol DS1000Z channel 1 measured data saved".format(datetime.datetime.now()))

                    logging.info(
                        "{0}: Saving  channel 2 measured data of Rigol DS1000Z".format(datetime.datetime.now()))
                    filename_actual_rigol_ch2 = (self.filename_base + "_rigol_ch2_" +
                                             str(self.input_voltage) + "_" +
                                             str(primary_actual) + "_" +
                                             str(secondary_actual) + "." +
                                             self.filename_ext)
                    np.savetxt(filename_actual_rigol_ch2, arraylist_rigol_ch2_plot, delimiter=";")
                    logging.info(
                        "{0}: Rigol DS1000Z channel 2 measured data saved".format(datetime.datetime.now()))

                    logging.info(
                        "{0}: Saving measured data of Itech IT9121 (1)".format(datetime.datetime.now()))
                    filename_actual_itech_1_voltage = (self.filename_base + "_itech_1_" +
                                                       str(self.input_voltage) + "_" +
                                                       str(primary_actual) + "_" +
                                                       str(secondary_actual) + "." +
                                                       self.filename_ext)
                    #np.savetxt(filename_actual_itech_1_voltage, itech1_values, delimiter=";")
                    with open(filename_actual_itech_1_voltage, "w", newline="") as file:
                        writer = csv.writer(file, delimiter=' ')
                        writer.writerow([itech1_values])
                    logging.info(
                        "{0}: Itech IT9121 (1) measured data saved".format(datetime.datetime.now()))


                    logging.info(
                        "{0}: Saving measured data of Itech IT9121 (2)".format(datetime.datetime.now()))
                    filename_actual_itech_2_voltage = (self.filename_base + "_itech_2_"+
                                                       str(self.input_voltage) + "_" +
                                                       str(primary_actual) + "_" + str(secondary_actual) + "." +
                                                       self.filename_ext)
                    #np.savetxt(filename_actual_itech_2_voltage, itech2_values, delimiter=";")
                    with open(filename_actual_itech_2_voltage, "w", newline="") as file:
                        writer = csv.writer(file, delimiter=' ')
                        writer.writerow([itech2_values])
                    logging.info(
                        "{0}: Itech IT9121 (2) measured data saved".format(datetime.datetime.now()))

                    logging.info(
                        "{0}: Saving phase 1 measured data of KinetiQ PPA5530".format(datetime.datetime.now()))
                    filename_actual_kinetiq_1_voltage = (self.filename_base + "_kinetiq_1_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    #np.savetxt(filename_actual_kinetiq_1_voltage, kinetiq1_values, delimiter=";")
                    with open(filename_actual_kinetiq_1_voltage, "w", newline="") as file:
                        writer = csv.writer(file, delimiter=' ')
                        writer.writerow([kinetiq1_values])
                    logging.info(
                        "{0}: KinetiQ PPA5530 phase 1 measured data saved".format(datetime.datetime.now()))

                    logging.info(
                        "{0}: Saving phase 3 measured data of KinetiQ PPA5530".format(datetime.datetime.now()))
                    filename_actual_kinetiq_2_voltage = (self.filename_base + "_kinetiq_2_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    #np.savetxt(filename_actual_kinetiq_2_voltage, kinetiq2_values, delimiter=";")
                    with open(filename_actual_kinetiq_2_voltage, "w", newline="") as file:
                        writer = csv.writer(file, delimiter=' ')
                        writer.writerow([kinetiq2_values])
                    logging.info(
                        "{0}: KinetiQ PPA5530 phase 3 measured data saved".format(datetime.datetime.now()))

                    filename_pcb_temp = (self.filename_base + "_pcb_temp_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    logging.info(
                        "{0}: Saving measured temperature (PCB) of DC/DC".format(datetime.datetime.now()))
                    np.savetxt(filename_pcb_temp, pcb_temp, delimiter=";")
                    logging.info(
                        "{0}: Measured temperature (PCB) of DC/DC saved".format(datetime.datetime.now()))

                    filename_scalar_value = (self.filename_base + "_scalar_value_"+
                                                         str(self.input_voltage) + "_" +
                                                         str(primary_actual) + "_" +
                                                         str(secondary_actual) + "." +
                                                         self.filename_ext)
                    logging.info(
                        "{0}: Saving scalar value of DC/DC".format(datetime.datetime.now()))
                    np.savetxt(filename_scalar_value, scalar_value , delimiter=";")
                    logging.info(
                        "{0}: Scalar value of DC/DC saved".format(datetime.datetime.now()))

                    logging.info(
                        "{0}: Setting Rigol DS1000Z to run mode (Trigger = OFF)".format(datetime.datetime.now()))
                    self.Rigol_DS1000Z.run()

                    # TODO RE-ENABLE
                    logging.info(
                        "{0}: Setting ITech IT9121 (1) to run mode (Trigger = OFF)".format(datetime.datetime.now()))
                    self.ITech_IT9121_1.trigger()

                    logging.info(
                        "{0}: Setting ITech IT9121 (2) to run mode (Trigger = OFF)".format(datetime.datetime.now()))
                    self.ITech_IT9121_2.trigger()

                    logging.info(
                        "{0}: Setting KinetiQ PPA5530 to run mode (Hold = OFF)".format(datetime.datetime.now()))
                    self.KinetiQ_PPA5530.set_data_hold(hold='OFF')

                    # display time elapsed
                    self.time_elapsed_seconds = round(time.time() - self.measurement_start_time,2)
                    self.time_elapsed_minutes = round(self.time_elapsed_seconds/60, 2)
                    self.time_elapsed_hours = round(self.time_elapsed_minutes/60, 2)
                    print("Elapsed time: ", self.time_elapsed_seconds,"s/ ",
                          self.time_elapsed_minutes,"m/ ",
                          self.time_elapsed_hours,"h")

                    # prep the next value of current
                    secondary_actual = secondary_actual + self.secondary_delta

                # at the end of sequence, soft unroll - might be conditional
                secondary_actual = secondary_actual - 2 * self.secondary_delta
                if self.secondary_unroll:
                    while secondary_actual > self.secondary_start:
                        # exit if required
                        if stop_event.is_set():
                            break
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
                    # exit if required
                    if stop_event.is_set():
                        break
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
            # trigger cleanup, when finished TODO a je to prav
            self.finished.emit()

        self.ITech_IT6000C.set_system_remote()
        self.ITech_IT6000C.set_output("OFF")
        self.ITech_IT6000C.set_system_local()
        logging.info(
            "{0}: Measurements DONE. Elapsed time: {1} | Measurements done: {2}".format(datetime.datetime.now(),
                                                                                        self.time_elapsed_minutes,
                                                                                        self.measurement_number))
        print("Measurements: DONE")