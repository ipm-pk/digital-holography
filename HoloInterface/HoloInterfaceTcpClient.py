# # -*- coding: utf-8 -*-
#
# author = eschborn
# date created = 23.01.2024

import json
import os
import socket
import sys
import time
import warnings
from typing import List, Union

from PySide6 import QtWidgets
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWidgets import QApplication, QMainWindow

import globals.cuda_holo_definitions as cuda_holo
import globals.holo_tcp_globals as holo_dll
import globals.IPM_Holo_Globals as holo_globals
from globals.holo_result_buffer import ResultBuffer


def qtMessageHandler(mode, context, message):
    print(message, context)


def byte_keys_to_strings(json_ob: dict):
    """convert a dictionary's keys from bytes to strings, recursively."""
    ret = {}
    if isinstance(json_ob, dict):
        for key, val in json_ob.items():
            if isinstance(key, bytes):
                key = key.decode()
            if isinstance(val, dict):
                val = byte_keys_to_strings(val)
            elif isinstance(val, (tuple, list, set)):
                val = [byte_keys_to_strings(x) for x in val]
            ret[key] = val
        return ret
    elif isinstance(json_ob, (tuple, list, set)):
        val = [byte_keys_to_strings(x) for x in json_ob]  # recurse elements
        return val
    else:
        return json_ob


class InterfaceTcpClient:
    """
    Class to connect to the TCP Server.
    It also has a function to trigger the real HoloSoftware.
    """

    def __init__(self, fullLogging=False):
        self.sock = None
        self.fullLogging = fullLogging
        self.waiting_for = set()

    def connectToServer(self, host=None, port=1234):
        """Function to connect to the server."""
        if self.sock is not None:
            return
        if host is None:
            host = QHostAddress.LocalHost
        print("TCP Client: trying to connect...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
            print("TCP Client: connected")
        except Exception as e:
            print(f"TCP Client: connection failed with error {e}")

    def disconnect(self):
        """Function to disconnect from the server."""
        if self.sock:
            self.sock.close()
            self.sock = None
            print("TCP Client: disconnected")

    def sendMessage(self, message_json=None):
        """Function to send a message to the server."""
        # Check if there is a message and a connection:
        if not message_json:
            warnings.warn("TCP Client: No message to send.")
            return
        if not self.sock:
            warnings.warn("TCP Client: Trying to send message, but no connection...")
            return

        # Send message:
        print("TCP Client: sending message...")
        try:
            self.sock.sendall(message_json.encode())
            print("TCP Client: message sent")
        except Exception as e:
            print(f"TCP Client: failed to send message with error {e}")

    def receiveMessage(self):
        """Function to receive a message from the server."""
        if self.fullLogging:
            print("TCP Client: trying to receive...")
        try:
            while True:
                data = self.sock.recv(4096)
                if data:
                    message = data.decode().strip()
                    print(f"TCP Client got message: {message}")
                    return message
                else:
                    print("TCP Client: No data received. Waiting for more data...")
        except Exception as e:
            print(f"TCP Client: Error receiving data: {e}")
            return None

    def wait_for_measurement_finish(self):
        """Funtion to wait for the HoloSoftware to finish"""

        function_id_to_wait_for = 110  # Indicates that the measurement is finished
        start_time = time.time()
        try:
            while True:
                data = self.sock.recv(4096)
                elapsed_time = time.time() - start_time
                if function_id_to_wait_for in data:
                    return function_id_to_wait_for
                elif elapsed_time > 2:
                    print("TCP Client: Timeout waiting for measurement.")
                    return None
                else:
                    pass
        except Exception as e:
            print(f"TCP Client: Error waiting for measurement: {e}")
            return None

    def slot_request_measurement(
        self,
        filename=None,
        filename_raw=None,
        function_id=holo_globals.FunctionId.grab_single_stack,
        processing_step=cuda_holo.ProcessingStep.STEP_SYN_PHASES_COMBINED,
        additional_json=None,
        buffers_to_return: Union[List[ResultBuffer], None] = None,
    ):
        """Function to send a message to the server to trigger the real HoloSoftware."""

        if buffers_to_return is None:
            buffers_to_return = list()

        json_ob = dict()
        json_ob.update(
            {
                holo_dll.KeysClientToServer().command: holo_dll.ClientToServerCommand.START_ACQUISITION.value
            }
        )
        json_ob.update({holo_dll.KeysStartAcq().function_id: function_id.value})
        json_ob.update(
            {holo_globals.KeysObjectData().KEY_OUTPUT_MODE: processing_step.value}
        )
        if buffers_to_return:
            json_ob.update(
                {
                    holo_dll.KeysStartAcq().buffers_to_return: [
                        b.to_jso() for b in buffers_to_return
                    ]
                }
            )

        if filename is not None:
            json_ob.update(
                {holo_globals.KeysObjectData().KEY_FILE_MASK_RESULT: filename}
            )

        if (
            filename_raw is not None
        ):  # make sure this path exists on the remote machine!
            json_ob.update(
                {holo_globals.KeysObjectData().KEY_FILE_MASK_RAW: filename_raw}
            )

        if additional_json is not None:
            json_ob.update(additional_json)

        json_ob = byte_keys_to_strings(json_ob)
        json_str = json.dumps(json_ob)
        self.sendMessage(json_str)


class ClientTestWindow(QMainWindow):
    def __init__(self, port=1234, app=None):
        super(ClientTestWindow, self).__init__()

        self.client = InterfaceTcpClient()
        self.app = app
        self.init_layout()
        qInstallMessageHandler(qtMessageHandler)

    def init_layout(self):
        self.cw = QtWidgets.QWidget(self)
        self.client = InterfaceTcpClient()

    def connectToServer(self, host=QHostAddress.LocalHost, port=1234):
        self.client.connectToServer(host, port)

    def sendMessage(self, message_json=None):
        self.client.sendMessage(message_json)

    def run(self):
        self.app.exec()


def main():
    # Trigger TCP measurement, directly without OPC-UA
    # Make sure either HoloInterface or HoloSoftware are running

    # Load the JSON file:
    json_file_name = "JSON_Test.jso"  # The JSON file to load
    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(current_path, json_file_name)
    with open(file_path, "r") as json_file:
        json_data = json.load(json_file)

    app = QApplication(sys.argv)

    # Install the custom message handler
    qInstallMessageHandler(qtMessageHandler)

    if json_data["use_holointerface"] is True:
        port_to_use = 1234
        print("TCP Client's port is connecting to HoloInterface!")

        # Create the test window:
        window = ClientTestWindow(port=port_to_use)
        window.connectToServer(host="localhost", port=port_to_use)
        window.client.receiveMessage()

        # Trigger the HoloInterface:
        window.client.sendMessage(json.dumps(json_data))
        time.sleep(0.25)
        window.client.receiveMessage()
        window.close()

    else:
        port_to_use = 2025
        print("TCP Client's port is connecting to real HoloSoftware!")

        # Create the test window:
        window = ClientTestWindow(port=port_to_use)
        window.connectToServer(host="127.0.0.2", port=port_to_use)
        # Trigger the real HoloSoftware:
        window.client.slot_request_measurement(additional_json=json_data)
        ret = window.client.wait_for_measurement_finish()
        if ret == 110:
            print("Interface: Measurement succsesful!")
        else:
            print("Interface: Measurement failed!")
        window.close()

    sys.exit()


if __name__ == "__main__":
    main()
