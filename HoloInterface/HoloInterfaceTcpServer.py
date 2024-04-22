# # -*- coding: utf-8 -*-
#
# author = eschborn
# date created = 23.01.2024

import sys
import json
import warnings

from PySide6.QtCore import Signal
from PySide6.QtNetwork import QTcpServer, QHostAddress, QTcpSocket
from PySide6.QtWidgets import QApplication, QMainWindow

KEY_FUNCTION_NAME = "simulate_measurement"

def qtMessageHandler(mode, context, message):
    print('TCP Server: ', message, context)

class MySocket(QTcpSocket):
    '''Socket for TCP Server, that can send and receive messages'''
    sig_messageReceived = Signal(str)

    def __init__(self, fullLogging = False):
        super().__init__()
        self.fullLogging = fullLogging
        self.readyRead.connect(self.handleReadyRead)


    def handleReadyRead(self):
        '''Function to handle incoming messages from client'''
        if (self.fullLogging):
            print ("TCP Server: handleReadyRead")
        # Read all available bytes, convert them to a string and emit the signal
        while self.bytesAvailable():
            message = self.readAll().data().decode().strip()
            if (self.fullLogging):
                print("TCP Server received message:", message)
            self.sig_messageReceived.emit(message)
            self.flush()

    def sendMessage(self, message):
        '''Send message, both string and json are possible'''
        if (self.state() != QTcpSocket.ConnectedState): # Check if the socket is connected
            print("TCP Server: Trying to send message, but no connection...")
            return
        message = json.dumps(message)   # Convert message to json
        if (self.fullLogging):
            print (f"TCP Server socket sending message: {message}")
        self.write(message.encode())    # Write the message to the socket
        self.flush()


class HoloInterfaceTcpServer(QTcpServer):
    '''TCP Server for HoloInterface'''
    sigPrintMessage = Signal(str)       # Signal, that message shall be returned

    def __init__(self, parent, port = 1234, fullLogging = False):
        super().__init__()
        self.parent = parent
        self.fullLogging = fullLogging
        self.socket = None
        self.sigPrintMessage.connect(print)
        if self.fullLogging:
            self.sigPrintMessage.emit("starting TCP Server")

        ret = self.listen(QHostAddress.LocalHost, port)  # Start listening on port 1234
        if ret:
            self.sigPrintMessage.emit(f"TCP Server listening on port {port}")
        else:
            error_message = self.errorString()
            self.sigPrintMessage.emit("Failed to start TCP Server: " + error_message)

    def incomingConnection(self, socketDescriptor):
        self.sigPrintMessage.emit ("TCP Server: incoming connection")
        print("TCP Server: incoming connection")
        self.socket = MySocket(fullLogging=self.fullLogging)
        self.socket.sig_messageReceived.connect(self.slotMessageReceived)
        self.socket.setSocketDescriptor(socketDescriptor)
        self.sendMessage({"Welcome to the Fraunhofer TCP Server": 0})

    def slotMessageReceived(self, msg: str):
        if self.fullLogging:
            print(f"TCP Server got message in container: {msg}")

        # make sure that msg is in json format
        msg =msg.replace("'", '"').replace("True", "true").replace("False", "false")
        # msg needs to be in json format
        try:
            msg_as_json = json.loads(msg)
            print("TCP Server: Message in valid json format")
        except:
            print("message not in valid json format; no function called")
            self.sendMessage({"message_not_in_valid_json_format": -1})
            return

        # check
        if self.fullLogging:
            msg_to_print = "receieved following json data"
            for key in msg_as_json.keys():
                msg_to_print+=f"  key: {key}, value: {msg_as_json[key]}\n"
            self.sigPrintMessage.emit(msg_to_print)

        # special case: list all functions
        if (KEY_FUNCTION_NAME in msg_as_json.keys()):
            if (msg_as_json[KEY_FUNCTION_NAME] in ["listAvailableFunctions", "help"]):
                self.listAvailableFunctions()
                return
        # all other cases: try to execute the function:
        self.try_execute_function(msg_as_json)

    def _listAvailableFunctions(self):
        # internal function: get list of function(-pointers)
        child_obj = self.parent
        # List only the functions that are not inherited from QMainWindow
        functions = [func for func in dir(child_obj)
                     if callable(getattr(child_obj, func))
                     and func not in dir(QMainWindow)
                     and not (func.startswith("__") and func.endswith("__"))]
        return functions

    def listAvailableFunctions(self):
        # get list of all parent-function and send via TCP
        functions = self._listAvailableFunctions()
        # build a reasonable json_object, i.e. dict in Python
        dict_of_functions = my_dict = {str(index): value for index, value in enumerate(functions)}
        json_to_send = {"help": dict_of_functions}
        self.sendMessage(json_to_send)
        if self.fullLogging:
            print('TCP Server: ', json_to_send)

    def try_execute_function(self, jso_msg):
        self.err_dict = {"invalid_function": -2000}     # Define Error dictionary

        function_name = KEY_FUNCTION_NAME

        #to do: check if function is available
        if hasattr(self.parent, function_name):
            function = getattr(self.parent, function_name)

            returned_value = function(jso_msg)
            print('TCP Server: Simulate Measurement')
            jso_to_return = {function_name: returned_value}
        else:
            jso_to_return = {function_name: self.err_dict["invalid_function"]}

    def sendMessage(self, message):
        '''Send Message to client'''
        self.socket.sendMessage(message)
        print("TCP Server: Sent message: ", message)

    def __del__(self):
        if self.fullLogging:
            print("TCP Server: Destructor called")
        super().close()
        super().__del__()

class container_for_server(QMainWindow):
    '''
    Container for TCP server
    '''
    def __init__(self, port = 1234):
        super(container_for_server, self).__init__()
        self.setWindowTitle("Window for TCP server")
        self.server = HoloInterfaceTcpServer(self, port=port)

    def function_to_be_called_for_test(self):
        '''Function to be called for test purposes, that sends a message to the client'''
        print ("container of TCP: function_to_be_called_for_test is executed...")
        self.server.sendMessage({"function_to_be_called_for_test": 0})

    def __del__(self):
        print ("destructor of container called")
        super().__del__()


if __name__ =="__main__":
    warnings.warn("This is only for debugging, make sure you run HoloInterface instead for real operation")

    port_to_use = 1234
    app = QApplication(sys.argv)

    cfs = container_for_server(port=port_to_use)
    cfs.show()
    # IPM_TCP_server
    sys.exit(app.exec())
