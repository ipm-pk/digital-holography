import asyncio
import json

# import copy
import logging
import math
import os
import random
import time
from datetime import datetime

from asyncua import Server, ua, uamethod

from HoloInterfaceTcpClient import InterfaceTcpClient


class holo_opcua_server:
    """
    Class for the OPC UA server. It is used to create the server and link the methods to the holo client.
    """

    def __init__(self, host: str = "0.0.0.0", port: str = "4840"):
        """Constructor for the OPC UA server class. Initializes the server and the holo client."""
        self.measurement_duration = 0.25  # Estimated time for a holographic measurement
        self.opc_ua_server = Server()
        self.opc_ua_endpoint = f"opc.tcp://{host}:{port}/freeopcua/server/"
        self.opc_ua_server_name = "Fraunhofer IPM Holography Sensor"
        # Set to remember the concurrent tasks and prevent early garbage collection
        self.tasks = set()
        # Dict for variables (capability and property nodes are stored here later)
        self.opc_ua_variables = {}
        # Set up holo client
        self.connected_to_simulated_interface = True
        self.holo_client = InterfaceTcpClient()

    async def connect_tcp_client(self, host="localhost", port: str = "1234"):
        port = int(port)
        """Function to connect the holo client to the server."""
        self.holo_client.connectToServer(host, port)

    async def check_measurement_uri_format(self, uris):
        """Passed argument is expected to be a list of strings, representing measurement files."""
        if not isinstance(uris, list):
            return False
        return True

    async def estimate_evaluation_duration(self, uris):
        """Estimate the duration of the evaluation based on the length of measurement files."""
        return 0.5 + math.exp(0.1 * (len(uris) - 1))

    async def get_child_by_name(self, name):
        """Function to get a child node by its name."""
        server_objects = await self.opc_ua_server.get_root_node().get_children()
        for obj in server_objects:
            obj_display_name = await obj.read_display_name()
            if name == obj_display_name.Text:
                return obj
            else:
                print(obj_display_name.Text)

    async def start_opc_ua_server(self):
        """
        Function to start the OPC UA server.
        It initializes the server and links the methods to the holo client.
        """
        print("Starting OPC UA Server")
        # Init server
        await self.opc_ua_server.init()
        # Set endpoint and server name
        # self.server.disable_clock()  # For debugging
        self.opc_ua_server.set_endpoint(self.opc_ua_endpoint)
        self.opc_ua_server.set_server_name(self.opc_ua_server_name)
        # Get objects node. Here we instantiate.
        objects = self.opc_ua_server.get_objects_node()
        # import some nodes from xml
        current_dir = os.path.dirname(__file__)
        swap_nodes_path = os.path.join(current_dir, "swap_common_nodeset_export.xml")
        holo_nodes_path = os.path.join(current_dir, "swap_holography_ipm_export.xml")
        # Import the nodes from the xml files
        swap_nodes = await self.opc_ua_server.import_xml(swap_nodes_path)
        holo_nodes = await self.opc_ua_server.import_xml(holo_nodes_path)

        # Get correct namespace idx
        namespaces = await self.opc_ua_server.get_namespace_array()
        self.namespace_idx_swap = namespaces.index("http://common.swap.fraunhofer.de")
        self.namespace_idx_ipm = namespaces.index(
            "http://holography.swap.ipm.fraunhofer.de"
        )
        self.loaded_type_definitions = (
            await self.opc_ua_server.load_data_type_definitions()
        )
        # Get Holomodule type node and create instance
        # Iterate through the objects in the server and search for the HolographyModule
        opc_ua_server_root = self.opc_ua_server.get_root_node()
        opc_ua_HoloModuleNode = await opc_ua_server_root.get_child(
            [
                f"0:Types",
                f"0:ObjectTypes",
                f"0:BaseObjectType",
                f"{self.namespace_idx_swap}:BaseModuleType",
                f"{self.namespace_idx_ipm}:HolographyModuleType",
            ]
        )
        self.opc_ua_HoloModuleObj = await objects.add_object(
            self.namespace_idx_ipm, "HolographyModule", opc_ua_HoloModuleNode
        )
        await self.link_variables()
        await self.link_services()
        await self.link_events()

        print("OPC UA Server started")

    async def link_variables(self):
        # All variables must be linked here. Otherwise they exist in the opc_ua_server,
        # but are not connected to actual function calls.
        variables = {
            "Calibrated": ["Capabilities", True],
            "ResolutionAxial": ["Capabilities", 1e-3],
            "ResolutionLateral": ["Capabilities", 2 * 3.2e-3],
            "MeasuringFieldHeight": ["Capabilities", 7000 * 5e-3 / 0.5],
            "MeasuringFieldWidth": ["Capabilities", 9344 * 5e-3 / 0.5],
            "SensorWeight": ["Capabilities", 5.1],
            "CameraType": ["Properties", "Ximea"],
            "ImageHeight": ["Properties", 7000],
            "ImageWidth": ["Properties", 9344],
            "Manufacturer": ["Properties", "Fraunhofer IPM"],
            "SensorModel": ["Properties", "HoloTop"],
        }
        # For each element in the dict, create an element self.opc_ua_variables[var] in the server,
        # This element holds the data and is accessed by opc_ua.
        for var, val in variables.items():
            var_path = [
                f"{self.namespace_idx_swap}:{val[0]}",
                f"{self.namespace_idx_ipm}:{var}",
            ]
            try:
                var_node = await self.opc_ua_HoloModuleObj.get_child(var_path)
                self.opc_ua_variables[var] = var_node
                await self.opc_ua_server.write_attribute_value(
                    var_node.nodeid, ua.DataValue(val[1])
                )
                await var_node.set_read_only()  # Read only for client.
            except ua.UaError as e:
                logging.error(f"Could not set {val[0]} {var}: {e}")

    async def link_services(self):
        # All services must be linked here. Otherwise they exist in the opc_ua_server,
        # but are not connected to actual function calls.
        # Link measurement request
        request_measurement_path = [
            f"{self.namespace_idx_swap}:Services",
            f"{self.namespace_idx_ipm}:RequestMeasurement",
        ]
        request_measurement_node = await self.opc_ua_HoloModuleObj.get_child(
            request_measurement_path
        )
        self.opc_ua_server.link_method(
            request_measurement_node, self.request_measurement
        )
        # Link evaluation request
        request_evaluation_path = [
            f"{self.namespace_idx_swap}:Services",
            f"{self.namespace_idx_ipm}:RequestEvaluation",
        ]
        request_eval_node = await self.opc_ua_HoloModuleObj.get_child(
            request_evaluation_path
        )
        self.opc_ua_server.link_method(request_eval_node, self.request_evaluation)

    async def link_events(self):
        # Get the event type
        root = self.opc_ua_server.get_root_node()
        sfet = await root.get_child(
            [
                f"0:Types",
                f"0:EventTypes",
                f"0:BaseEventType",
                f"{self.namespace_idx_swap}:ServiceFinishedEventType",
            ]
        )
        event_type_node = await sfet.get_child(
            [f"{self.namespace_idx_ipm}:RequestMeasurement"]
        )
        # Create a new event of respective type
        self.eventgen_measurement_done = await self.opc_ua_server.get_event_generator(
            event_type_node, self.opc_ua_HoloModuleObj
        )
        # Get the event type
        event_type_node = await sfet.get_child(
            [f"{self.namespace_idx_ipm}:RequestEvaluation"]
        )
        # Create a new event of respective type
        self.eventgen_evaluation_done = await self.opc_ua_server.get_event_generator(
            event_type_node, self.opc_ua_HoloModuleObj
        )

    @uamethod
    async def request_measurement(self, parent, json_cfg):
        # This function starts a threat to run the holo client function and returns immediately
        if isinstance(json_cfg, str):  # TODO: Check the json config more thoroughly
            sync_result_message = "OK"
            sync_result_code = 0
            expected_service_duration = (
                0.25  # TODO: Estimate the measurement duration based on json config
            )

            service_trigger_result = 1  # 1 means ok
            # call measurement in separate task:
            loop = asyncio.get_event_loop()
            if not json_cfg:
                json_cfg = None
            task = loop.create_task(self.holo_interface_measurement(json_cfg))
            self.tasks.add(task)
            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            task.add_done_callback(self.tasks.discard)
        else:
            sync_result_message = "Input needs to be a string"
            expected_service_duration = 0
            sync_result_code = 1
            service_trigger_result = 0  # 0 is wrong parameters
        # Get return type
        type_class = self.loaded_type_definitions["ServiceExecutionAsyncResultDataType"]
        ### Create variable of return type
        service_execution_result = type_class(
            ExpectedServiceExecutionDuration=expected_service_duration,
            ServiceTriggerResult=service_trigger_result,
            ServiceResultMessage=sync_result_message,
            ServiceResultCode=sync_result_code,
        )
        return ua.Variant(service_execution_result, ua.VariantType.ExtensionObject)

    @uamethod
    async def request_evaluation(self, parent, eval_type, measurements_uri):
        # This function starts a threat to run the holo client function and returns immediately
        if not await self.check_measurement_uri_format(measurements_uri):
            service_trigger_result = 0  # 0 is wrong parameters
            expected_service_duration = 0
            sync_result_message = "Measurement URIs needs to be list of files"
            sync_result_code = 1
        else:
            sync_result_message = "OK"
            sync_result_code = 0
            service_trigger_result = 1  # 1 means ok
            # Scale the expected evaluation time
            expected_service_duration = await self.estimate_evaluation_duration(
                measurements_uri
            )
            # call holo software in separate task
            loop = asyncio.get_event_loop()
            task = loop.create_task(
                self.holo_client_evaluation(eval_type, measurements_uri)
            )
            self.tasks.add(task)
            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            task.add_done_callback(self.tasks.discard)
        # Get return type
        type_class = self.loaded_type_definitions["ServiceExecutionAsyncResultDataType"]
        # Create variable of return type
        service_execution_result = type_class(
            ExpectedServiceExecutionDuration=float(expected_service_duration),
            ServiceTriggerResult=service_trigger_result,
            ServiceResultMessage=sync_result_message,
            ServiceResultCode=sync_result_code,
        )
        return ua.Variant(service_execution_result, ua.VariantType.ExtensionObject)

    async def simulate_measurement(self, json_cfg):
        """Function to simulate a measurement with the HoloInterface."""

        # Send JSON to the HoloInterface_
        self.holo_client.sendMessage(json_cfg)

        # Wait for answer and prepare the event to trigger:
        await asyncio.sleep(self.measurement_duration)
        result = self.holo_client.receiveMessage()  # Get answer from HoloInterface
        print(f"Result: {result}")
        start_index = result.find("[")
        end_index = result.find("]")
        error_list = result[start_index + 1 : end_index]  # Cut the "[]" from the string
        error_list = error_list.split(",")  # Split the string into a list

        if len(error_list) < 1:
            event_text = "Simulation finished without errors."

        else:
            event_text = f"Simulation finished with {len(error_list)} errors!"

        return event_text

    async def real_measurement(self, json_cfg):
        """Function to trigger a real measurement with the HoloSoftware."""
        json_cfg = json.loads(json_cfg)
        # Trigger and wait for measurement:
        self.holo_client.slot_request_measurement(additional_json=json_cfg)

        ret = self.holo_client.wait_for_measurement_finish()
        if ret == 110:
            event_text = "Real measurement finished successfully."

        else:
            event_text = "Real measurement failed."

        return event_text

    async def holo_interface_measurement(self, json_cfg):
        """Call the holo TCP client"""
        start_time = time.time()
        # Get and create the output directory for holo client
        try:
            out_path = os.environ["HOLO_OUTPUT"]
        except KeyError:
            release_dir = os.environ["HOLO_RELEASE_DIR"]
            out_path = os.path.join(release_dir, "output")
        # file_tools.safe_mkdir(out_path)
        date_str = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        filename = os.path.join(out_path, f"OPCUA_{date_str}.tiff")
        filename_raw = os.path.join(out_path, f"OPCUA_{date_str}_raw.tiff")
        # Trigger measurement
        try:
            # Check if json_cfg is filled
            if json_cfg:
                pass
            else:
                json_cfg = {}

            # Trigger simulation or real measurement:
            # TODO: This if-else should be in two different functions.
            # In order to do so a new Node should be created in the XML file.
            # Then the client can call the function by the name of the node.
            if json.loads(json_cfg)["use_holointerface"] is True:
                # Trigger simulation and get result:
                if not self.connected_to_simulated_interface:
                    self.holo_client.disconnect()
                    self.holo_client.connectToServer(host="127.0.0.2", port=1234)
                    self.connected_to_simulated_interface = True
                event_text = await self.simulate_measurement(json_cfg)

            else:
                # Trigger real measurement and get result:
                # Because the TCP Client connects automatically to the TCP Server
                # of the HoloInterface, we need to disconnect and reconnect to the
                # TCP server of the HoloSoftware.
                if self.connected_to_simulated_interface:
                    self.holo_client.disconnect()
                    self.holo_client.connectToServer(host="127.0.0.2", port=2025)
                    self.connected_to_simulated_interface = False
                event_text = await self.real_measurement(json_cfg)

        except OSError as err:
            self.eventgen_measurement_done.event.ServiceExecutionResult = 1
            self.eventgen_measurement_done.event.Message = ua.LocalizedText(
                f"Error during measurement: {err}."
            )
        except ValueError as err:
            self.eventgen_measurement_done.event.ServiceExecutionResult = 1
            self.eventgen_measurement_done.event.Message = ua.LocalizedText(
                f"Error during measurement: {err}."
            )
        else:
            self.eventgen_measurement_done.event.ServiceExecutionResult = 0
            self.eventgen_measurement_done.event.Message = ua.LocalizedText(event_text)

        # Trigger event:
        execution_time = time.time() - start_time
        self.eventgen_measurement_done.event.ExecutionTime = float(execution_time)
        self.eventgen_measurement_done.event.URI = filename
        await self.eventgen_measurement_done.trigger()
        print("OPC UA Server: Event triggered")

    async def holo_client_evaluation(self, eval_type, measurements_uri):
        # HACK: created a mockup here, usually the holo client is called like:
        # TODO:  await holo_client.slot_request_measurement()
        ExecutionTime = await self.estimate_evaluation_duration(measurements_uri)
        ExecutionTime = ExecutionTime + random.gauss(0, 0.1)
        await asyncio.sleep(ExecutionTime)
        try:
            for m_uri in measurements_uri:
                if not isinstance(m_uri, str) or not m_uri:
                    raise OSError
                with open(m_uri, mode="a"):
                    pass
            self.eventgen_evaluation_done.URI = "Evaluation simulation successful."
        except OSError:
            self.eventgen_measurement_done.ServiceExecutionResult = 1  # Fail
            self.eventgen_evaluation_done.URI = "Error during evaluation simulation."
        else:
            self.eventgen_measurement_done.ServiceExecutionResult = 0  # Success
        # When measurement is done, trigger event
        print(self.eventgen_evaluation_done.URI)
        await self.eventgen_evaluation_done.trigger()

    async def wait_for_simulation(self):
        """Function to wait for the measurement to finish.
        It then asks the holo client to receive the message.
        """

        await asyncio.sleep(self.measurement_duration)
        print(self.measurement_duration)
        result = self.holo_client.wait_for_measurement_finish()
        return result


async def check_measurement_format(uris):
    """
    Function for checking the format of the measurement URIs
    # TODO: Check the JSON data more thoroughly
    """
    try:
        json_data = json.loads(uris)

        # Check if the JSON data contains the correct function name
        if "simulate_measurement" in json_data and isinstance(
            json_data["simulate_measurement"], dict
        ):
            return "Measurement format for simulation"
        elif isinstance(json_data, dict) and "simulate_measurement" not in json_data:
            return "Measurement format for real measurement"
        else:
            return "Wrong function name in JSON data"
    except json.JSONDecodeError as e:
        return "Wrong format: " + str(e)


async def main(
    ip_opcua: str = "localhost",
    port_opcua: str = "4840",
    ip_holo: str = "localhost",
    port_holo: str = "1234",
):
    opcua_server = holo_opcua_server(ip_opcua, port_opcua)
    await opcua_server.start_opc_ua_server()

    await opcua_server.connect_tcp_client(host=ip_holo, port=port_holo)
    opcua_server.holo_client.receiveMessage()

    async with opcua_server.opc_ua_server:
        while True:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
