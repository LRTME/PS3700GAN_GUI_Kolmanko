# -*- coding: utf-8 -*-
import queue
import serial
from serial.tools import list_ports
import serial.threaded
import threading
import traceback
import time
import cobs
import struct
from PyQt5 import QtCore
import CRC16
import inspect
import sys

class ComMonitor(QtCore.QObject, serial.threaded.Packetizer):

    packets_sent = 0
    packets_received = 0
    non_registered_packets_received = 0
    crc_error_count = 0
    decode_error_count = 0
    bytes_received = 0

    crc_handler_function = False
    crc_print_signal = QtCore.pyqtSignal()

    crc_data = queue.LifoQueue()

    tx_handler_signal = QtCore.pyqtSignal()

    tx_queue = queue.Queue()

    _object_ref = None

    def set_object(self, obj):
        self._object_ref = obj

    def __init__(self):
        # Qt init
        QtCore.QObject.__init__(self)

        # lock for comm port access
        self.com_lock = threading.Lock()

        # com port instance
        self.ser = serial.Serial()
        self.ser.timeout = 0.001

        # win only
        if sys.platform.startswith('win32'):
            self.ser.set_buffer_size()

        # rx handler list
        self.code_list = list()
        self.callback_list = list()

        self.rx_handler_list = list()
        self.rx_code_list = list()
        self.rx_handler_name_list = list()

        # on open callback list
        self.on_open_callbacks = list()

        # receive error counter
        self.crc_error_count = 0

        self.packetizer = None

    def send_packet(self, code, data):
        if data is None:
            packet_out = (struct.pack('<h', code))
        else:
            packet_out = (struct.pack('<h', code)) + data
        # if port is open
        if self.ser.isOpen():
            # prepare for transmission
            crc_of_data = CRC16.CRC16(True).calculate(bytes(packet_out))
            crc_of_data_bytes = struct.pack("<H", crc_of_data)
            packet_array = bytearray(packet_out)
            packet_array.append(crc_of_data_bytes[0])
            packet_array.append(crc_of_data_bytes[1])
            # encode with cobse
            cobs_encoded = cobs.encode(packet_array)
            # terminate packet
            cobs_encoded.append(0)
            # put on the send queue
            self.tx_queue.put(cobs_encoded)
            pass

    @staticmethod
    def get_list_of_ports():
        ports_available = list_ports.comports()
        list_of_ports = list(ports_available)
        list_of_ports_available = list()
        for element in list_of_ports:
            list_of_ports_available.append(element[0])
        tup_list = tuple(list_of_ports_available)
        return tup_list

    @staticmethod
    def get_prefered_port(portname=None):
        ports_available = list_ports.comports()
        list_of_ports = list(ports_available)
        list_of_ports_available = list()
        # if there is no port at all
        if len(list_of_ports) == 0:
            preferred_port = None
        else:
            preferred_port = None
            for element in list_of_ports:
                list_of_ports_available.append(element[0])
                # if no preset serial then try the port description
                if portname is None:
                    if any(s in element.description for s in ['XDS100', 'XDS110', 'USB']):
                        preferred_port = element.device
                        break
                # with preset serial test if serial matches
                else:
                    if portname in element.hwid:
                        preferred_port = element.device
                        break
        return preferred_port

    def statistic_data(self):
        data = (self.packets_sent,
                self.packets_received,
                self.crc_error_count,
                self.decode_error_count,
                self.non_registered_packets_received,
                self.bytes_received)
        return data

    def open_port(self, portname, baudrate):
        self.ser.baudrate = baudrate
        self.ser.port = portname
        self.ser.stopbits = 2
        self.ser.open()

        # reset packet counter
        self.packets_sent = 0
        self.non_registered_packets_received = 0
        self.packets_received = 0
        self.crc_error_count = 0
        self.decode_error_count = 0
        self.bytes_received = 0

        if self.ser.isOpen():
            # empty the tx queue just in case
            while not self.tx_queue.empty():
                try:
                    self.tx_queue.get(False)
                except queue.Empty:
                    continue
                self.tx_queue.task_done()

            # set up the rx thread
            self.packetizer = serial.threaded.ReaderThread(self.ser, ComMonitor)
            self.packetizer.start()
            a, b = self.packetizer.connect()
            b.set_object(self)

            # empty tx queue
            while not self.tx_queue.empty():
                self.tx_queue.get(False)

            # ready the tx thread
            tx_thread = threading.Thread(target=self.send_new_data)
            # and run it (might want to reconsider starting and stopping it on port open)
            tx_thread.daemon = True
            tx_thread.start()

            # execute all the callbacks
            for fnc in self.on_open_callbacks:
                fnc()

        return self.ser.isOpen()

    def register_on_open_callback(self, fnc):
        self.on_open_callbacks.append(fnc)

    def close_port(self):
        self.packetizer.stop()
        return self.ser.isOpen()

    def is_port_open(self):
        return self.ser.isOpen()

    def send_new_data(self):
        while True:
            # get data from tx queue
            try:
                cobs_encoded = self.tx_queue.get(block=True, timeout=0.1)
            except queue.Empty:
                cobs_encoded = None
                pass
            # if port is closed get out
            if not self.ser.isOpen():
                break
            # if there is anything to send, send it
            if cobs_encoded is not None:
                try:
                    self.ser.write(cobs_encoded)
                    self.packets_sent = self.packets_sent + 1
                except serial.SerialException:
                    break
        pass

    def connection_lost(self, exc):
        # close the port as it can not be closed from the rx thread
        self._object_ref.ser.close()
        pass

    def handle_packet(self, data):
        self._object_ref.bytes_received = self._object_ref.bytes_received + len(data) + 1
        try:
            decoded_packet = cobs.decode(data)
        except:
            self._object_ref.decode_error_count = self._object_ref.decode_error_count + 1
        else:
            # ce pa dobim korekten podatek, pogledam po seznamu handlerjev in klicem ustrezen callback
            # parse the packet
            length_of_packet = len(decoded_packet)
            code = decoded_packet[0:2]
            packet_data = decoded_packet[2:length_of_packet - 2]
            code_and_data = decoded_packet[0:length_of_packet - 2]
            crc_received = int.from_bytes(decoded_packet[length_of_packet - 2:length_of_packet], byteorder='little')

            # recalculate packet CRC
            crc_of_data = CRC16.CRC16(True).calculate(bytes(code_and_data))

            # if CRC is fine
            if crc_of_data == crc_received:
                # increase packet counter
                self._object_ref.packets_received = self._object_ref.packets_received + 1
                # and try matching the rx handler and executing it
                try:
                    index = self._object_ref.rx_code_list.index(code)
                    callback = self._object_ref.rx_handler_list[index]
                    # poklicem handler
                    if packet_data is None:
                        callback.rx_handler()
                    else:
                        callback.rx_handler(packet_data)
                except:
                    self._object_ref.non_registered_packets_received = self._object_ref.non_registered_packets_received + 1
                    pass
            else:
                # increase CRC error counter
                self._object_ref.crc_error_count = self._object_ref.crc_error_count + 1
                # and trigger CRC error handler if it is register
                if self._object_ref.crc_handler_function:
                    # put the CRC error count on CRC error count queue
                    self._object_ref.crc_data.put(self._object_ref.crc_error_count)
                    # trigger the CRC handler
                    self._object_ref.crc_print_signal.emit()

    def check_for_new_data(self):
        # we should never get here
        pass
        pass

    def data_to_send(self):
        return self.tx_queue.qsize()

    def connect_rx_handler(self, code, rx_function):
        # if handler with existing code has already been registered, raise an exception
        for existing_code in self.rx_code_list:
            if existing_code == code:
                raise Exception("handler with same code has alredy been registered")

        # create new rx worker
        rx_worker = RxWorker(rx_function)
        # and pass it on rx handler list
        function_name = str(rx_function.__name__)
        self.rx_handler_name_list.append(function_name)
        self.rx_handler_list.append(rx_worker)
        self.rx_code_list.append((struct.pack('<H', code)))

    def get_data(self):
        called_by = inspect.stack()[1][3]
        # find which worker has data
        index = self.rx_handler_name_list.index(called_by)
        # gat data from specific forker
        data = self.rx_handler_list[index].rx_handler_queue.get()
        return data

    # for crc handler registration
    def connect_crc_handler(self, crc_handler_function):
        # connect with the handler function
        self.crc_handler_function = True
        self.crc_print_signal.connect(crc_handler_function)
        pass

    def get_crc(self):
        data = self.crc_data.get()
        return data


class RxWorker(QtCore.QObject):
    # signal to bind RxWorker with rx handler
    rx_handler_signal = QtCore.Signal()

    def __init__(self, rx_function):
        # QT init - for signal
        QtCore.QObject.__init__(self)
        # queue to pass the data
        self.rx_handler_queue = queue.LifoQueue()

        # connect signal with rx handler
        self.rx_handler_signal.connect(rx_function)
        pass

    def rx_handler(self, data):
        # if there is data with the packet put it on the queue
        if data is not None:
            self.rx_handler_queue.put(data)
        # trigger the rx handler
        self.rx_handler_signal.emit()

    def get_data(self):
        return self.rx_handler_queue.get()

