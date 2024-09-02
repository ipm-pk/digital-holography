import os
import subprocess
import time

current_path = os.path.dirname(os.path.realpath(__file__))

# Liste zum Speichern der gestarteten Subprozesse
processes = []


def start_interface():
    # Start the Interface:
    interface_path = os.path.join(current_path, "HoloInterface.py")
    process = subprocess.Popen(["python", interface_path])
    processes.append(process)
    print("HoloInterface started")


def start_opc_ua_server():
    # Start the OPC UA Server:
    opc_ua_server_path = os.path.join(current_path, "OpcUaServer.py")
    process = subprocess.Popen(["python", opc_ua_server_path], cwd=current_path)
    processes.append(process)
    print("OPC UA Server started")


def start_opc_ua_client():
    # Start the OPC UA Client:
    opc_ua_client_path = os.path.join(current_path, "OpcUaClient.py")
    process = subprocess.Popen(["python", opc_ua_client_path], cwd=current_path)
    processes.append(process)
    print("OPC UA Client started")


def stop_processes():
    # End all processes:
    for process in processes:
        process.terminate()
    print("Processes terminated")


if __name__ == "__main__":
    # Start the Subprocesses
    start_interface()
    time.sleep(2)
    start_opc_ua_server()
    time.sleep(2)

    use_simulation = True
    if use_simulation:
        start_opc_ua_client()
        # Wait for the processes to finish
        time.sleep(20)
        # Beenden Sie die Subprozesse
        stop_processes()
