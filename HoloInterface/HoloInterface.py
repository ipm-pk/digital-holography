'''
This is the main file of the HoloInterface. It contains the main class HoloInterface, 
which is the main window of the HoloInterface. It can be used to simulate a measurement.
Author - Manuel Eschborn
Date - 2024-03-19
Coding: utf-8
'''
import csv
import os
import re
import sys
from datetime import datetime, timedelta

from PySide6.QtWidgets import QApplication, QMainWindow

from HoloInterfaceTcpServer import HoloInterfaceTcpServer


class JsonObject:
    """
    Represents a JSON-like object with various attributes.

    Attributes:
        name (str, optional): The name of the JSON object. Defaults to None.
        children (list, optional): A list of child JSON objects. Defaults to an empty list.
        parent (JsonObject, optional): The parent JSON object. Defaults to None.
        value_type (str, optional): The type of the value. Defaults to None.
        value_range (dict, optional): The range of the value. Defaults to an empty dictionary.
        set_value (str, optional): The value that is set in the JSON File that is being tested.
        error_flag (bool, optional): Indicates if an error has been found. Defaults to False.
        warning_trigger (bool, optional): Indicates if a warning has to be triggered. 
                                          This occurs, when the GUI Element is not found.
    """

    def __init__(self, name=None,
                 children=None,
                 parent=None,
                 value_type=None,
                 value_range=None,
                 set_value=None,
                 default_value=None,
                 error_flag=False,
                 warning_trigger=False):

        self.name = name
        self.children = children if children is not None else []
        self.parent = parent
        self.value_type = value_type
        self.value_range = value_range if value_range is not None else {}
        self.set_value = set_value
        self.default_value = default_value
        self.error_flag = error_flag
        self.warning_trigger = warning_trigger

class HoloInterface(QMainWindow):
    '''
    This class represents the main window of the HoloInterface.
    It can be used to simulate a measurement and also to test
    the functionality of the TCP Interface.
    '''

    def __init__(self, error_list=[], warning_list=[], recieved_data=None, port=1234):
        super(HoloInterface, self).__init__()
        self.setWindowTitle("Window for HoloInterface with TCP Server")
        self.error_list = error_list
        self.warning_list = warning_list
        self.recieved_data = recieved_data

        # Define TCP Server and start it:
        self.TcpServer = HoloInterfaceTcpServer(self, port=port)

    def create_json_objects(self, csv_file_path: str) -> list:
        ''' This function creates json objects from the csv file containing the key-value pairs.
            Those Objects build the base of the HoloSoftware simulation

        Attributes:
            csv_file (str): The path to the csv file containing the 
            key-value pairs and the information about the GUI elements.

        Returns:
            list: A list of json objects.
        '''

        json_objects = []               # List of json objects
        current_json_object = None      # Saves the current json parent object

        # Create a dictionary that maps the class of the gui element to the type of the value:
        type_mapping = {
            "QSpinBox": "int",
            "QDoubleSpinBox": "float",
            "QCheckBox": "bool",
            "QRadioButton": "bool",
            "QComboBox": "int",
            "QLineEdit": "str",
        }

        # Read out the given csv file:
        with open(csv_file_path, mode='r', encoding='utf-8') as master_csv_file:
            csv_reader = csv.reader(master_csv_file, delimiter=';')
            next(csv_reader)    # Skip the first row of the csv file (header)
            next(csv_reader)    # Skip the second row of the csv file (header)

            # Iterate through the csv file row by row:
            for row in csv_reader:
                if row[0]:    # Names are always in the first column
                    current_json_object= JsonObject(name=row[0],
                                                default_value=row[1])
                    # Add the new json object to the list of json objects:
                    json_objects.append(current_json_object)

                # Get the value type of the json objects:
                elif row[5] == 'class':
                    current_json_object.value_type = type_mapping[row[6]] 

                # Set the value range of the json objects:
                elif row[5] == 'minimum':
                    current_json_object.value_range['minimum'] = row[6]
                elif row[5] == 'maximum':
                    current_json_object.value_range['maximum'] = row[6]

                else:
                    continue

        return json_objects

    def guess_value_type(self, object_list: list) -> list:
        ''' This function guesses the value type of the json object 
            by looking at the default value of the object. 
            This is necessary, because the value type is not always clear in the csv file.

        Attributes:
            object_list (list): A list of json objects.

        Returns:
            object_list: A list of json objects with the value type set.
        '''

        for obj in object_list:
            # Objects with children don't have a value type:
            if obj.parent is None and obj.children != []:
                obj.value_type = 'NoneType'

            elif obj.value_type is None:
                # Check if the default value is a boolean:
                if obj.default_value == 'True' or obj.default_value == 'False':
                    obj.value_type = 'bool'
                # Check if the default value is a float:
                elif '.' in obj.default_value:
                    obj.value_type = 'float'
                # Check if the default value is None:
                elif obj.default_value is None or obj.default_value == '':
                    obj.value_type = 'NoneType'
                # If none of the above is true, the default value should be an integer:S
                else:
                    obj.value_type = 'int'

                # Set the warning trigger to true, because the GUI element is not connected:
                obj.warning_trigger = True

            else:
                continue

        return object_list


    def create_json_objects_from_json(self, json_dict: dict, parent=None) -> list:
        ''' This function creates json objects from a given json dictionary.

        Attributes:
            json_dict (dict): A dictionary containing the json objects.
            parent (json_object, optional): The parent json object. Defaults to None.

        Returns:
            list: A list of json objects.    
        '''

        json_objects = []

        for key, item in json_dict.items():
            current_json_object = JsonObject(name=key,
                                             parent=parent,
                                             value_type=type(item).__name__,
                                             set_value=item)
            # If the value is a dictionary, create a new json object for each key in the dictionary:
            if current_json_object.value_type == 'dict':
                current_json_object.value_type = 'NoneType'
            json_objects.append(current_json_object)

        for current_json_object in json_objects:
            if isinstance(current_json_object.set_value, dict):
                current_json_object.children = self.create_json_objects_from_json(current_json_object.set_value, current_json_object)
                current_json_object.set_value = None

            else:
                current_json_object.children = []

        return json_objects


    def compare_json_objects(self, json_objects: list, csv_objects: list, error_list=[], warning_list=[]) -> list:
        ''' This function compares the json objects from 
            the json file with the json objects from the csv file.

        Attributes:
            json_objects (list): A list of json objects handed from the user.
            csv_objects (list): A list of csv objects.
            error_list (list, optional): A list of errors that have been found. 
                                         Defaults to an empty list.
            warning_list (list, optional): A list of warnings that have been found. 
                                           It indicates missing GUI elements in the CSV. 

        Returns:
            error_list, warning_list: List of errors and warnings that have been found.

        '''

        # Create a list of the names of the csv objects:
        csv_names = [obj.name for obj in csv_objects]

        # Check if the name of the JSON object is in the CSV file:
        for json_obj in json_objects:

            # Check if the name of the JSON object is in the CSV file:
            if json_obj.name not in csv_names:
                if json_obj.name != "use_holointerface":
                    self.error_list.append(f'JSON object {json_obj.name} is not known in HoloSoftware.')

            else:
                element_index = csv_names.index(json_obj.name)

                # Check the value type:
                if json_obj.value_type != csv_objects[element_index].value_type:
                    # When a float is excepted an int is allowed as well:
                    if json_obj.value_type == 'int' and csv_objects[element_index].value_type == 'float':
                        continue 
                    else:
                        self.error_list.append('Value type of JSON object ' +
                                               json_obj.name +
                                               ' is not correct. Expected: ' + 
                                               csv_objects[element_index].value_type +
                                               ', got: ' + json_obj.value_type + '.' )

                        # Set the error flag of the CSV object to true:
                        csv_objects[element_index].error_flag = True

                # Check the value range:
                elif 'minimum' in csv_objects[element_index].value_range:
                    if json_obj.set_value < float(csv_objects[element_index].value_range['minimum']):
                        self.error_list.append('Value of JSON object ' +
                                               json_obj.name + 
                                               ' is too low. Minimum value is: ' +
                                               csv_objects[element_index].value_range['minimum'] +
                                               ', got: ' + str(json_obj.set_value) + '.')

                        # Set the error flag of the CSV object to true
                        csv_objects[element_index].error_flag = True

                elif 'maximum' in csv_objects[element_index].value_range:
                    if json_obj.set_value > float(csv_objects[element_index].value_range['maximum']):
                        self.error_list.append('Value of JSON object ' +
                                                json_obj.name +
                                                ' is too high. Maximum value is: ' + 
                                                csv_objects[element_index].value_range['maximum'] + 
                                                ', got: ' + str(json_obj.set_value )+ '.')

                        # Set the error flag of the CSV object to true:
                        csv_objects[element_index].error_flag = True

                # When no error has been raised, the set value of the
                # CSV object is set to the set value of the JSON object:
                if csv_objects[element_index].error_flag is False:
                    csv_objects[element_index].set_value = json_obj.set_value

                # Check if the GUI element is connected and if not give a warning:
                if csv_objects[element_index].warning_trigger is True:
                    self.warning_list.append(json_obj.name)

            # Check for the children and grandchildren as well:
            if json_obj.children:
                self.compare_json_objects(json_obj.children, csv_objects, self.error_list)

        # Vielleicht braucht es den return gar nicht
        return self.error_list, self.warning_list

    def create_value_dict(self, json_objects: list) -> dict:
        ''' This function creates a dictionary with the names of the 
            json objects as keys and the set/default values as values
            This way the log file can be created. It always checks if a 
            correct value has been entered by the user. If not, the default value is used.

        Attributes:
            json_objects (list): A list of json objects.

        Returns:
            value_dict (dict): A dictionary with the names of 
                               the json objects as keys and the values.
        '''

        value_dict = {}

        for json_obj in json_objects:
            # Create the full key for the dictionary so that the placeholders can be replaced:
            key = '{' + json_obj.name + '}'
            if json_obj.set_value is not None:
                value_dict[key] = json_obj.set_value

            else:
                value_dict[key] = json_obj.default_value

        return value_dict

    def make_raw_file(self, log_file_name: str, json_objects: list):
        ''' This function creates a raw file from a given log file. 
            The log files get provided by Fraunhofer.

        Attributes:
            log_file_name (str): The name of the log file that has to be altered.
            json_objects (list): A list of json objects, 
                                 so their values can be replaced by placeholder.

        Returns:
            log_file_data (str): The raw data of the log file.
        '''

        # Read the given log file:
        log_file_path = os.path.join(os.path.dirname(__file__), log_file_name)
        with open(log_file_path, "r", encoding='utf-8') as log_file:
            log_file_data = log_file.read()

        # Replace the time stamps with placeholder '{time}':
        time_stamp_pattern = re.compile(r'\d{2}/\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?')
        # Replace the time stamps with the placeholder:
        log_file_data = time_stamp_pattern.sub('{time}', log_file_data)

        # Replace the values of the given keys with placeholders:
        names = [obj.name for obj in json_objects]

        for name in names:
            # Create a pattern for the key, value pairs and replace values:
            pattern = re.compile(r'"' + re.escape(name) + r'":(.*?)(?=,)')
            log_file_data = pattern.sub('"' + name + '":{' + name + '}', log_file_data)

        # Safe the raw log file:    (can be uncommented if needed)
        '''raw_file_name = log_file_name.replace("log", "raw")  # Create the name of the raw file
        with open(raw_file_name, "w") as raw_file:
            raw_file.write(log_file_data)'''

        return log_file_data


    def create_log_file(self, raw_file_data: str, value_dict: dict, errors: list, warnings: list):
        '''
        This function creates a log file as the HoloSoftware would create it.
        The errors found are added to the end of the file.


        Attributes:
            raw_file_data (str): The raw data of the log file.
            value_dict (dict): Containing names of the json objects as keys and the values.
            errors (list): A list of errors that have been found.
            warnings (list): A list of warnings that have to be triggered.
        '''

        current_time = datetime.now()  # Get the current time
        time_format = "%m/%d %H:%M:%S.%f"  # Define the time format
        #TODO: time_steps should be calculated from the starting time and depending on the settings
        time_steps = [0.0, 0.0, 0.321, 69.912, 69.912, 69.914, 69.915, 69.915,
                      69.915, 93.924, 93.927, 93.927, 93.927, 93.933, 93.933,
                      93.941, 93.941, 93.942, 94.152, 94.153, 94.154, 94.154,
                      94.154, 94.154, 95.033, 95.039, 95.075, 95.075, 95.085,
                      95.106, 95.106, 95.113, 95.113, 95.113, 95.114, 95.114,
                      95.114, 95.115, 95.115, 95.115]

        # Replace the placeholders with the values from the value dictionary:
        modified_data = raw_file_data
        for key, value in value_dict.items():
            modified_data = modified_data.replace(key, str(value), -1)

        # Add time stamps to the data:
        time_stamp_list = [current_time + timedelta(seconds=timestep) for timestep in time_steps]
        # Replace one time stamp at a time:
        for time_stamp in time_stamp_list:
            modified_data = modified_data.replace('{time}', str(time_stamp.strftime(time_format)), 1)

        # Add the errors to the data:
        modified_data += '\n' + 120*'+' + '\n' + '\n' + str(len(errors)) + ' errors have been found:\n'  # Header
        for error in errors:
            modified_data += error + '\n'       # Add the errors to the log file

        # Add the warnings to the data:
        modified_data += 'Be aware that the value type of the following objects might be wrong: ' + ', '.join(warnings)

        # Open/create and save the new log file:
        log_file_name = str(current_time).replace(":", "_")[:19] + "_log.txt"  # Log file name
        log_file_path = os.path.join(os.path.dirname(__file__), log_file_name)  # Log file path
        with open(log_file_path, "w", encoding='utf-8') as log_file:
            log_file.write(modified_data)  # Write log file


    def simulate_measurement(self, json_str: dict):
        '''
        This is the main function of the dummy.
        It simulates a measurement by comparing the JSON objects
        from the JSON file with the JSON objects from the CSV file.

        Attributes:
            json_str (str): The JSON string from the JSON file, which gets recieved from the server.
            json_objects (list): The list containing the JSON objects from the CSV file.
        '''

        print('Interface: Simulating measurement...')
        self.error_list = []

        # Make JSON objects from the input JSON:
        json_input_objects = self.create_json_objects_from_json(json_str)

        # Make JSON objects from the CSV file:
        csv_file_path = os.path.join(os.path.dirname(__file__), 'Keylist.csv')
        json_objects = self.create_json_objects(csv_file_path)
        json_objects = self.guess_value_type(json_objects)   # Add missing value types

        # Compare the JSON objects:
        self.error_list, self.warnings = self.compare_json_objects(json_input_objects,
                                                                   json_objects,
                                                                   error_list=[],
                                                                   warning_list=[])

        # Create a dictionary with the names of the json objects and the values:
        value_dict = self.create_value_dict(json_objects)

        # Create a log file (Name of log file can be changed to choose different log file):
        raw_log_file_data = self.make_raw_file('ExampleLogFile.txt', json_objects)
        self.create_log_file(raw_log_file_data, value_dict, self.error_list, self.warnings)

        # Finish the simulation and send the error list to the client:
        print('Interface: Simulation finished')

        if not self.error_list:
            ret = 'Interface: Simulation finished! No Errors found.'
        else:
            ret = 'Interface: Simulation finished! Errors found: ' + str(self.error_list)

        self.TcpServer.sendMessage(ret)

        return self.error_list, self.warnings

if __name__ == "__main__":
    # Start the Interface:
    app = QApplication(sys.argv)
    Interface = HoloInterface(port=1234)
    sys.exit(app.exec())
