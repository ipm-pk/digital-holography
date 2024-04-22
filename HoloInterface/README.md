# HoloInterface

**Description:** HoloInterface is a software developed to facilitate the evaluation of the [`HoloTop`](https://www.ipm.fraunhofer.de/en/bu/production-control-inline-measurement-techniques/systems/holo-top.html) sensors by Fraunhofer IPM customers. It offers two modes of operation: TCP interface simulation and OPC UA interface control. It can help future customers to test the TCP/OPC UA connection. It can also be used to try different settings in order to make sure the sensor fits the individual needs of your measurement task.

The software features a TCP server that listens for incoming JSON messages containing the desired measurement settings. Upon receiving a JSON message, HoloInterface compares the provided settings with the default values and generates a comprehensive log file, emulating the behavior of the original software.

To ensure data integrity, HoloInterface performs thorough checks on the settings. It verifies if the data types match the expected types, such as validating that a boolean value is provided when a boolean is required. Additionally, for integer and float values, the software examines if the given values fall within the specified range. Any errors encountered during the validation process are compiled into a list appended at the end of the log file.

To use the software, establish connection using either the provided TCP client or through the provided OPC UA server and client. In both cases, the necessary files (example LogFile, CSV containing the keys, HoloInterface, and InterfaceTcpServer) must reside in the same folder. When using OPC UA, ensure the accompanying XML files are in the same folder as the opc_ua_server.py file, while the opc_ua_client can be located in a different folder. It is recommended to maintain the folder structure as provided in the repository for optimal functioning. In order to switch between the HoloInterface and the real HoloSoftware the setting `use_holointerface` can be used. If that setting is `true` a simulation will be triggered, if it is missing or set to `false`, the connection will be established to the real HoloSoftware. 

## Getting Started

These instructions will guide you on how to set up and use the HoloInterface software on your local machine.

### Prerequisites

- [Pyhon](https://www.python.org/) - Version: 3.10.4
- [asyncua](https://github.com/FreeOpcUa/opcua-asyncio) - Version: 0.9.98
- [asyncio](https://docs.python.org/3/library/asyncio.html) - Version: 3.4.3
- [PySide6](https://doc.qt.io/qtforpython-6/) - Version: 6.6.1
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Version: 8.6

### Installation

1. Clone the repository.
2. Install the required libraries using the following command:
3. Set up environmental variable `HOLO_RELEASE_DIR` to e. g. `C:\holo_realease`

```bash
$ pip install -r requirements.txt
```

### Usage
**It is recommended to maintain the folder structure as provided in the repository.**

The program `Control_subprocesses.py` runs a whole simulation cycle. A `.json` must be given as the input for the simulated measurement. It is recommended to start with the provided `TEST_JSON.jso`. If you want to choose the communication inteface individually, please mind the following steps:

1. Ensure that the following files are in one folder:
   - Example_LogFile.txt
   - key_list.csv
   - HoloInterface.py
   - InterfaceTcpServer.py

2. Establish a TCP connection using the provided client to communicate with HoloInterface.
   - You can either use the provided TCP Client, or use your own TCP Client.

3. Alternatively, establish a connection using the provided OPC UA server and client.
   - Place the provided XML files in the same folder as the opc_ua_server.py file.
   - The opc_ua_client can be located in a different folder.

4. Send a JSON input over the established connection to HoloInterface to start a simulation.

## Authors

- Patrick Laux
- Manuel Eschborn - [GitHub Profile](https://github.com/ElManu93)

## License

This project is licensed under the MIT License - see the [LICENSE.md](link_to_license_file) file for details.
