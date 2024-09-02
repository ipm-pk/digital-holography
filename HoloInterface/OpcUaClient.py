"""
OPC UA Client to connect to the OPC UA Server 
and call the method RequestMeasurement.
author: Manuel Eschborn
date: 19.03.2024
Coding: utf-8
"""

import asyncio
import json
import sys

from asyncua import Client
from PySide6.QtWidgets import QApplication, QFileDialog


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        """
        Function to handle data change events.
        """
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        """
        Function to handle event notifications and print them.
        """
        result = event.Message.Text
        time = event.Time
        excecution_result = getattr(event, "ServiceExecutionResult", None)
        print(
            f"OPC UA CLIENT: Got new event:\n\tResult: {result}\n\tTime: {time} (GMT)\n\tExecution Result: {excecution_result}"
        )


class HoloOpcUaClient:
    """
    Class to connect to the OPC UA Server and call the method RequestMeasurement.
    While running a loop is started to enable the user to select a file
    and call the method RequestMeasurement as long a file is selected.
    """

    def __init__(self):
        self.url = "opc.tcp://localhost:4840/freeopcua/server/"  # Set OPC UA Server URL
        self.client = Client(self.url)
        self.loaded_type_definitions = None
        self.root = None
        self.objects = None
        self.children = None
        self.idx_swap = None
        self.idx_ipm = None
        self.request_measurement_node = None
        self.request_measurement_parent_node = None
        self.event_object_node = None
        self.event_types = None
        self.sub = None
        self.subhandler = None
        self.handle = None

    async def connect(self):
        """Function to connect to the OPC UA Server."""
        try:
            await self.client.connect()
            print("OPC UA Client: 'Connected to Fraunhofer IPM - OPC UA Server'")

            # Load definition of server specific structures/extension objects:
            self.loaded_type_definitions = await self.client.load_type_definitions()

            # Get the root node and the objects node:
            self.root = self.client.get_root_node()
            self.objects = self.client.get_objects_node()
            self.children = await self.objects.get_children()
            namespaces = await self.client.get_namespace_array()

            self.idx_swap = namespaces.index("http://common.swap.fraunhofer.de")
            self.idx_ipm = namespaces.index("http://holography.swap.ipm.fraunhofer.de")

            # Get the node of the method RequestMeasurement and the parent node:
            self.request_measurement_parent_node = await self.root.get_child(
                [
                    "0:Objects",
                    f"{self.idx_ipm}:HolographyModule",
                    f"{self.idx_swap}:Services",
                ]
            )

            self.request_measurement_node = await self.root.get_child(
                [
                    "0:Objects",
                    f"{self.idx_ipm}:HolographyModule",
                    f"{self.idx_swap}:Services",
                    f"{self.idx_ipm}:RequestMeasurement",
                ]
            )

            # Get the event_object_node and the event_types:
            self.event_object_node = await self.root.get_child(
                ["0:Objects", f"{self.idx_ipm}:HolographyModule"]
            )

            self.event_types = await self.client.nodes.base_event_type.get_child(
                f"{self.idx_swap}:ServiceFinishedEventType"
            )

            # Create a subscription and subscribe to events:
            self.subhandler = SubHandler()
            self.sub = await self.client.create_subscription(500, self.subhandler)
            self.handle = await self.sub.subscribe_data_change(
                [
                    self.request_measurement_node,
                    self.event_types,
                    self.event_object_node,
                    self.request_measurement_parent_node,
                ]
            )
            await self.sub.subscribe_events(self.event_object_node, self.event_types)

        except Exception as e:
            print(f"OPC UA Client: Error connecting to server: {e}")

    async def call_request_measurement(self, json_str=None):
        """
        This function try to call the method RequestMeasurement from the server.
        """

        # Get the node of the method RequestMeasurement and the parent node:
        method_id = self.request_measurement_node.nodeid
        parent_id = self.request_measurement_parent_node.nodeid

        method = self.client.get_node(method_id)
        parent = self.client.get_node(parent_id)

        print("OPC UA Client: Calling RequestMeasurement...")

        try:
            # Call the method RequestMeasurement with the input argument:
            await parent.call_method(method, json_str)
            print("OPC UA Client: RequestMeasurement called")

        except Exception as e:
            print(f"Fehler beim Aufrufen von RequestMeasurement: {e}")

    async def disconnect(self):
        """Function to disconnect from the server and delete the subscription."""
        if self.sub is not None:
            try:
                await self.sub.delete()  # Delete the subscription
                self.sub = None  # Set the subscription to None after deleting
                print("OPC UA CLIENT: Subscription deleted")
            except Exception as e:
                print(f"OPC UA CLIENT: Error deleting subscription: {e}")

        if self.client is not None:
            try:
                await self.client.disconnect()  # Disconnect from server
                print("OPC UA Client: Disconnected from server")
            except Exception as e:
                print(f"OPC UA Client: Error disconnecting from server: {e}")
            finally:
                self.client = None  # Set the client to None after disconnecting


class FileSearcher:
    """
    Class to search for a file and return the file path.
    """

    @staticmethod
    def search_file():
        """Open filedialog:"""
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Choose JSON file")
        file_dialog.setFileMode(QFileDialog.ExistingFile)  # Choose a file
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)  # Open a file

        if file_dialog.exec() == QFileDialog.Accepted:
            # Get the selected file path and return it:
            selected_file_path = file_dialog.selectedFiles()[0]
            return selected_file_path


async def loop(opcua_client, file_searcher):
    """
    Loop for the OPC UA CLIENT
    It is always called after a file is selected and the request_measurement method is called.
    In order to stop the loop just close the FileDialog.
    """

    try:
        # Open file dialog to choose a JSON file:
        file_path = file_searcher.search_file()

        if file_path:
            with open(file_path, "r") as json_file:
                json_data = json.load(json_file)
            json_data = json.dumps(
                json_data, indent=2
            )  # Convert the JSON data to a string
            # Call request_measurement method with the JSON data:
            # TODO: Add another Node to the OPC UA Server so that the right node can be triggered.
            await opcua_client.call_request_measurement(json_str=json_data)
            await asyncio.sleep(1)

        else:
            print("OPC UA CLIENT: No file selected. Will disconnect from server...")

    except Exception as e:
        print(f"Error in loop: {e}")

    finally:
        await opcua_client.disconnect()


async def main():
    # Start and connect Client to Server:
    opcua_client = HoloOpcUaClient()
    QApplication(sys.argv)
    file_searcher = FileSearcher()

    try:
        await opcua_client.connect()

    except Exception as e:
        print(f"Error connecting to server: {e}")

    await loop(opcua_client, file_searcher)


if __name__ == "__main__":
    asyncio.run(main())
