''' # -*- coding: utf-8 -*-

 author = eschborn
 date created = 23.01.2024'''

import json
import csv
import os

##############################################CLASSES##############################################

# Main Class:
class JSON():
    """
    Represents a JSON-like object with various attributes.

    Attributes:
        name (str, optional): The name of the JSON object. Defaults to None.
        children (list, optional): A list of child JSON objects. Defaults to an empty list.
        default_value (any, optional): The default value associated with the JSON object.
        header_key (str, optional): The header key for the JSON object. Defaults to None.
        header_comment (str, optional): A comment associated with the header. Defaults to None.
        cpp_name (str, optional): The C++ name for the JSON object. Defaults to None.
        ui_list (dict, optional): A dictionary of UI-related properties.
        files (list, optional): A list of files associated with the JSON object.
    """

    def __init__(self,
                 name=None,
                 parent=None,
                 children=None,
                 default_value='',
                 value_range=None,
                 header_key=None,
                 header_comment='',
                 cpp_name='',
                 ui_list=None,
                 files=None):
        self.name = name
        self.parent = parent
        self.children = children if children is not None else []
        self.default_value = default_value
        self.value_range = value_range if value_range is not None else {}
        self.header_key = header_key
        self.header_comment = header_comment
        self.cpp_name = cpp_name
        self.ui_list = ui_list if ui_list is not None else {}
        self.files = files or []


# File Class:
class File():
    '''
    Represents a file that gets read out. It's used to connect the JSON Object to the files, 
    where the name was found

    Attributes:
        name (str, optional):           Specifies the full path to the file.
        text (list, optional):          This list gives the text of the file. 
                                        Each entrie in the list represents one line of the file.
        file_format (str, optional):    Saves the file format as a string.
    '''

    def __init__(self, name = None, text = None, file_format = None):
        self.name = name
        self.text = text if text is not None else []
        self.file_format = file_format

###########################################WRTITE TO CSV############################################

def write_to_csv(row_data: list, csv_path: str):
    '''
    This function writes a list to a new line in a given CSV-File.
    It must be ensured that Excel interprets the period as the decimal 
    separator so that the data is correctly interpreted.

    Args:
        row_data (list): This list contains the data that has to be written in the CSV-File.
        csv_path (str): Gives the function the information which CSV-File has to be used.
    '''

    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';')
        csv_writer.writerow(row_data)

def print_object_to_csv(json_obj,  csv_path: str):
    '''
    Function to write a JSON or JSON object to a CSV-File.

    Args:
        json_obj (JSON, JSON):  This objects contains the information 
                                which has to be written in the CSV-File.
        csv_path (str):         Gives the function the information which CSV-File has to be used. 
                                This Argument is then also given to the write_to_csv function.
        is_child (Bool):        This information is needed so the function knows how to 
                                build the lines, that are then given to the write_to_csv function.
    '''

    row_data = [json_obj.name,
                json_obj.default_value,
                json_obj.header_key,
                json_obj.header_comment,
                json_obj.cpp_name]
    write_to_csv(row_data, csv_path)
    if json_obj.ui_list:   # If there is a dict containing ui_keys, print them
        # Write the UI-List in the CSV-file:
        for key, value in json_obj.ui_list.items():
            row_data = ['', '', '', '', '', key, value]
            write_to_csv(row_data, csv_path)

def print_object_to_list(json_obj) -> list:
    '''
    Function to create a list containing the information of a 
    JSON-object to show in the GUI without creating a CSV-File.

    Args:
        json_obj (JSON, JSON): The object that has to be processed.
        is_child (Bool): This information is needed so the function knows how to build the list.
    '''

    full_list = []
    # Check if it's a child. They are written in the second coloum:

    row_data = [json_obj.name,
                json_obj.default_value,
                json_obj.header_key,
                json_obj.header_comment,
                json_obj.cpp_name]
    full_list.append(row_data)

    return full_list

###############################################HEADER###############################################

def search_header(header_data: File) -> list:
    '''
    Function to search for the header and json keys in the header file.
    It creates a list of JSON-Objects

    Args:
        header_data (File): The file that has to be looked through.
    '''

    key_list = []

    for line in header_data.text:
        if '"' in line:
            if "const char*" in line:
                # Get the Header Key:
                header_key_start = line.find('*') + 2
                header_key_end = line.find('=', header_key_start) - 1
                header_name = line[header_key_start:header_key_end]

                # Get the JSON Key:
                json_key_start = line.find('"') + 1
                json_key_end = line.find('"', json_key_start)
                json_key = line[json_key_start:json_key_end]

                # Get the Comment:
                comment_start = line.find('/')
                comment = line[comment_start:]

                current_object = JSON(name=json_key, header_key=header_name, header_comment=comment)
                current_object.files.append(header_data.name)
                key_list.append(current_object)

            elif "#define" in line:
                # Get the Header Key:
                header_key_start = line.find('define') + 7
                header_key_end = line.find('"', header_key_start) - 2
                header_name = line[header_key_start:header_key_end]

                # Get the JSON Key:
                json_key_start = line.find('"') + 1
                json_key_end = line.find('"', json_key_start)
                json_key = line[json_key_start:json_key_end]

                # Get the Comment:
                comment_start = line.find('//')
                comment = line[comment_start:]

                current_object = JSON(name=json_key, header_key=header_name, header_comment=comment)
                current_object.files.append(header_data.name)
                key_list.append(current_object)

    return key_list

################################################JSON################################################

def get_default_value(data: list, json_file: File) -> list:
    '''
    Function to find the values that are used in the json file.

    Args:
        data (list): Is the list with the JSON-Objects that have to be processed and changed.
        json_file (File): Is the File that has to be looked through.

    Returns:
        data (list): Returns the list with the JSON-Objects that have been processed and changed.
    '''

    for json_object in data:
        for key, value in json_file.text.items():
            if isinstance(value, dict):

                for key2, value2 in value.items():
                    if isinstance(value2, dict):

                        for key3, value3 in value2.items():
                            if json_object.name == key3:
                                json_object.default_value = value3

                    elif json_object.name == key2:
                        json_object.default_value = value2
            elif json_object.name == key:
                json_object.default_value = value

    return data

################################################C++################################################

def make_cpp_key(line: str) -> str:
    '''
    Function to filter out the needed information from a given line of a C++ file. 
    The comment always shows an example what kind of line is present.

    Args:
        line (str): This string is the line of the C++ file that has to be procesed.
    '''

    if 'register' in line or 'gui_settings' in line:
        # gui_settings_list.append({ ui->rb_phase, KEY_DISPLAY_PHASE });
        start_index = line.find(">") + 1
        end_index = line.find(",")
        key = line[start_index:end_index]

    elif 'mode_jso' in line:    # mode_jso->insert(KEY_DISPLAY_PHASE, display_phase);
        start_index = line.find(">") + 1
        key = line[start_index:]
        if ">" in key:
            start_index = key.find(">") + 1
            key = key[start_index:]
            end_index = key.find("-")
            key = key[:end_index]

        else:
            start_index = key.find(" ") + 1
            end_index = key.find(")")
            key = key[start_index:-3]

    elif "copy" in line:    # copy.insert(KEY_DISPLAY_MODE, (int)disp_mode);
        start_index = line.find(",") + 2
        key = line[start_index:-3]

    elif "ref_json" in line:
        if ">" in line:
            start_index = line.find(">") + 1
            key = line[start_index:]
            end_index = key.find("-")
            key = key[:end_index]

        else:
            start_index = line.find(",") + 1
            key = line[start_index:]
            end_index = key.rfind(")")
            key = key[:end_index]

    else:
        key = ''

    return key

def get_cpp_key(data: list, cpp_data: File) -> list:
    '''
    Function to find the C++ Key, of a given JSON object.

    Args:
        data (list): Is the list with the JSON-Objects that have to be processed and changed.
        cpp_data (File): Is the File that has to be looked through.
    '''

    for cpp_object in data:
        # Check if there is a header_key, if not continue with the next object:
        if cpp_object.header_key is None or cpp_object.cpp_name:
            continue

        else:
            for line in cpp_data.text:
                if str(cpp_object.header_key) in line and not cpp_object.cpp_name:
                    cpp_object.cpp_name = remove_non_printable_characters(make_cpp_key(line))
                    # Check if header key is also in line to avoid doublings:
                    if cpp_data.name not in cpp_object.files and cpp_object.header_key in line:
                        cpp_object.files.append(cpp_data.name)

                else:
                    continue

        if cpp_object.children != []:
            get_cpp_key(cpp_object.children, cpp_data)

    return data


#################################################UI#################################################

def make_block(spaces: int, line_number: int, data: list) -> list:
    '''
    This function creates a block of information, which are linked to the given key word.

    Args: 
        spaces (int): Gives the number of spaces infront of the line with the key word, 
                      so the programm knows on which level the information is.
        line_number (int): Gives the index of the line with the key word.
        data (list): This is the full file, with the key word included

    Returns:
        block (list): The complete block that is connected to the key word.    
    '''

    block = [data[line_number-1]]
    for row in data[line_number:]:      # ui-data from the given line on
        if row[spaces-1] != " ":    # -1 so you get the whole block
            block = block + [row]
            return block
        else:
            block = block + [row]
    return block

def count_spaces(row: str) -> int:
    '''
    Function to count the spaces infront of a line, 
    so that the make_block function knows where to end.

    Args: 
        row (str): Is the line of code with key-word in it.
    '''

    counter = 0
    for i in row:
        if i == " ":
            counter += 1
        else:
            return counter

def find_information(block: list) -> tuple:
    '''
    Function to get the needed information from the ui-file that are then saved to the JSON-Object.
    It might still need some cases for sender and reciever.

    Args:
        block (list): The block is the lines of the ui file that are linked to the given keyword

    Returns: 
        information (tuple): Includes the information of the property and default values.
    '''

    information = {}
    for line in block:
        line_index = block.index(line)  # Get line index so we can later get the right information

        if 'class' in line:     # Get the class of the item
            start_index = line.find("\"")
            key = line[start_index + 1:]
            end_index = key.find("\"")
            key = key[:end_index]
            new_entries = {'class': key}
            information.update(new_entries)

        if 'name' in line and 'class' not in line:  # Get the information of the property
            # First get the name of the property:
            start_index = line.find("\"")
            text = line[start_index + 1:]
            end_index = text.find("\"")
            text = text[:end_index]

            # Then get the default value/text from the next line:
            if text == "minimumSize":
                new_block = block[line_index + 2:]

                # First get the minimum width:
                width = new_block[0]
                start_index = width.find(">")
                width = width[start_index + 1:]
                end_index = width.find("<")
                width = width[:end_index]

                # Then get the minimum height:
                height = new_block[1]
                start_index = height.find(">")
                height = height[start_index + 1:]
                end_index = height.find("<")
                height = height[:end_index]

                # Add data to the dictionary:
                new_entries = {text: '', 'minimumWidth': width, 'minimumHeight': height}
                information.update(new_entries)

            else:
                new_line = block[line_index + 1]
                start_index = new_line.find(">")
                new_line = new_line[start_index + 1:]
                end_index = new_line.find("<")
                new_line = new_line[:end_index]

                # Make dictionary:
                new_entries = {text: new_line}
                information.update(new_entries)

        if 'sender' in line or 'receiver' in line:
            continue

    return information

def get_ui_information(data: list, ui_data: File) -> list:
    '''
    This is the main function to get the information of the UI-file.

    Args:
        - data (list): This is the list of the JSON-Objects, that have to be checked.
        - ui_data (File): This is the UI-file that has to be checked.

    Returns: 
        - data (list): Returns the given list, with the new UI names.
    '''

    for ui_object in data:     # iterate through the given objects
        if ui_object.ui_list:
            continue
        else:
            ui_object.ui_list = {}  # initialize ui_list as an empty dictionary for each object
            if ui_object.cpp_name is not None:
                # The C++ key is always in braclets. This way wrong readings are ruled out:
                search_item = "\"" + ui_object.cpp_name + "\""
            if ui_object.cpp_name != '':
                label_name = 'lb' + ui_object.cpp_name[2:]
            else:
                label_name = ''
            for line in ui_data.text:    # iterate through the ui data
                if ui_object.cpp_name is not None and search_item in line:
                    information_block = make_block(count_spaces(line), ui_data.text.index(line), ui_data.text)
                    ui_object.ui_list.update(find_information(information_block))
                    if ui_data.name not in ui_object.files:
                        ui_object.files.append(ui_data.name)
                    continue

                # Check for the labels:
                if label_name in line and label_name != '':
                    new_entries = {'Label Name': label_name}
                    ui_object.ui_list.update(new_entries)

            get_ui_information(ui_object.children, ui_data)    # Don't forget the children

    return data


#############################################MAKE LISTS#############################################

def sort_files(files = list) -> list:
    '''
    This function sorts the files depending on their file type 
    and creates a lists that contain all the given formats.

    Args:
        - files (list): This is the list of the files in the given folder.

    Returns:
        - file_list (list): Returns the list containing four lists, which carry one file type each.
    '''

    json_files = []
    h_files = []
    cpp_files = []
    ui_files = []
    file_list = [json_files, h_files, cpp_files, ui_files]

    for file in files:  
        if file[-4:] == ".jso":  #check for JSON
            file_list[0].append(file)

        elif file[-2:] == ".h":  #check for Header
            file_list[1].append(file)

        elif file[-4:] == ".cpp":    #check for C++
            file_list[2].append(file)

        elif file[-3:] == ".ui": #check for UI
            file_list[3].append(file)

        else:   #if not one of those types, continue
            continue

    return file_list


def make_keylist(file_list: list) -> list:
    '''
    Function that reads the data from the files,
    and creates a full list containing all JSON-Objects from the given file list. 
    This list can then be printed with the make_csv() funtion.

    Args:
        - file_list (list): This is the list containing all the file paths that have to be checked. 
        It has to be sorted, as in the function "sort_files()".

    Returns:
        - key_list (list): Returns the list containing all JSON-Objects.   
    '''

    file_list = sort_files(file_list)
    header_data = []
    cpp_data = []
    ui_data = []
    key_list = []
    master_file_name = 'IPM_Holo_Globals.h'

    # Open Header-file and load the content:
    for file in file_list[1]:
        if master_file_name in file:
            master_file = File(name= file, file_format=".h")
            if os.path.exists(file):
                file_data = []
                with open(file, "r") as header_file:
                    for line in header_file:
                        file_data.append(line)
                file_data = file_data[15:] # Skip the first 15 lines
                master_file.text = file_data
    key_list = search_header(master_file)

    # Open JSON-file and load the content:
    for file in file_list[0]:
        # Create a File-object with the given file:
        new_json_file = File(name= file, file_format = ".jso")
        if os.path.exists(file):
            with open(file, 'r') as jso_file:
                new_json_file.text = json.load(jso_file)    # Load text, and save it.
                key_list = get_default_value(key_list, new_json_file)     # Add the default values

    # Open CPP-file and load the content:
    for file in file_list[2]:
        # Create a File-object with the given file:
        new_cpp_file = File(name= file, file_format=".cpp")
        if os.path.exists(file):
            file_data = []
            with open(file, 'r') as cpp_file:
                for line in cpp_file:
                    file_data.append(line)  # Add line for line to a new list.
            new_cpp_file.text = file_data   # Add the text to to created File-object.
            cpp_data = cpp_data + [new_cpp_file]    # Add the File to the list.

    # Open CPP-file and load the content:
    for file in file_list[3]:
        # Create a File-object with the given file:
        new_ui_file = File(name= file, file_format=".ui")
        if os.path.exists(file):
            file_data = []
            with open(file, 'r') as ui_file:
                for line in ui_file:
                    file_data.append(line)  # Add line for line to a new list.
            new_ui_file.text = file_data    # Add the text to to created File-object.
            ui_data = ui_data + [new_ui_file]   # Add the File to the list.

    # Handle data, and create the full key_list, containing all the Information found:
    for file in cpp_data:
        key_list = get_cpp_key(key_list, file)
    for file in ui_data:
        key_list = get_ui_information(key_list, file)

    return key_list

def make_csv(path: str, objects: list):
    '''
    This function takes a list, containing the JSON-Objects and saves it to a CSV-File.

    Args: 
        - path (str): Carries the information, where to save the CSV-File.
        - objects (list): The list containg the Objects that have to be written in the CSV-File.
    '''

    # set up csv file with headlines, if not already existing:
    try:
        with open(path, 'r') as csv_file:
            pass
    except FileNotFoundError:
        with open(path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerow(["Json",
                                 "Default Value",
                                 "Header Key",
                                 "Header Comment",
                                 "CPP Name",
                                 "UI-Property",
                                 "UI-Default Value"])

    #print the objects to the CSV-file:
    for key_object in objects:
        print_object_to_csv(key_object, path)

def make_full_list(file_list: list) -> list:
    '''
    Function to create a list containing only lists with strings inside.
    This list is needed for the search function.

    Args:
        - file_list (list): List with the paths to the files that have to be checked.

    Returns:
        - full_list (list): Containg all the information of the JSON-Objects but as a string. 
    '''

    full_list = []
    for key_object in make_keylist(file_list):
        full_list = full_list + [print_object_to_list(key_object)]

    return full_list

def make_file_list(folder_path: str) -> list: 
    '''
    Function that creates a list with all the containg file names in a given folder.

    Args:
        - folder_path (string): Gives the function the folder that has to be handled.

    Returns:
        - file_list (list):  Returns the unsorted list of all files in the given folder.
    '''

    file_list = []
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        for file in files:
            full_path = folder_path + '\\' + file   # Make the full path (folder path + file name)
            file_list = file_list + [full_path]     # Add file path to the file list.

    return file_list

def create_json_objects_from_csv(csv_file_path: str) -> list:
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
                current_json_object= JSON(name=row[0],
                                            default_value=row[1],
                                            header_key=row[2],
                                            header_comment=row[3],
                                            cpp_name=row[4],
                                            ui_list={},
                                            files=[]
                                            )
                # Add the new json object to the list of json objects:
                json_objects.append(current_json_object)

            # Get the value type of the json objects:
            elif row[5] == 'class':
                current_json_object.value_type = type_mapping[row[6]]
                current_json_object.ui_list['class'] = row[6]

            # Set the value range of the json objects:
            elif row[5] == 'minimum':
                current_json_object.value_range['minimum'] = row[6]
                current_json_object.ui_list['minimum'] = row[6]
            elif row[5] == 'maximum':
                current_json_object.value_range['maximum'] = row[6]
                current_json_object.ui_list['maximum'] = row[6]
            elif row[5]:
                current_json_object.ui_list[row[5]] = row[6]

            else:
                continue

    return json_objects

def remove_non_printable_characters(word):
    """
    Removes non-printable characters and spaces from a word.

    Parameters:
    - word (str): The word from which non-printable characters and spaces should be removed.

    Returns:
    - cleaned_word (str): The cleaned word without non-printable characters and spaces.
    """

    cleaned_word = ''.join(char for char in word if char.isprintable() and not char.isspace())
    return cleaned_word
