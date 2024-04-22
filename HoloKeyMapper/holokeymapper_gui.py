# # -*- coding: utf-8 -*-
#
# author = eschborn
# date created = 23.01.2024

import sys
import os
import json


from PySide6.QtWidgets import QApplication, QMenu, QDialog, QTextEdit, QHBoxLayout, QLabel, QTreeWidget, QListWidget, QFrame
from PySide6.QtWidgets import  QHeaderView, QLineEdit, QTreeWidgetItem, QMainWindow, QWidget, QVBoxLayout, QSplitter, QPushButton, QFileDialog
from PySide6.QtCore import Qt

import holokeymapper_backend

key_object_list = []
key_tree_dict = {}

class ButtonWidget(QWidget):
    '''
    Create a Widget to create a button to search a folder on a local hard drive. 
    This folder is being used to then get all the files that are needed for the data analysis.
    '''
    def __init__(self, text_display, file_list_widget, tree_viewer):
        super().__init__()
        self.text_display = text_display
        self.file_list_widget = file_list_widget
        self.tree_viewer = tree_viewer 
        self.initUI()

    def initUI(self):
        '''
        Initialize the user interface for the main window.

        This method sets up the user interface components for the main window, including
        a button for searching a folder. When the button is clicked, it connects to
        the 'open_file_dialog' method to trigger the file dialog for selecting a folder.
        '''

        layout = QVBoxLayout()

        self.button = QPushButton('Import Source Files')
        self.button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def open_file_dialog(self):
        '''
        Open a file dialog to choose a folder and update the UI components accordingly.

        This method opens a file dialog to allow the user to choose a folder. If a folder
        is selected, it updates the text display with the selected folder's path, updates
        the file list widget with the files in the selected folder, and generates a list
        of file paths within the folder.
        '''

        folder_path = QFileDialog.getExistingDirectory(self, 'Choose Folder')
        global key_object_list

        if folder_path:
            self.text_display.update_text(folder_path)
            self.file_list_widget.update_file_list(folder_path)

            file_paths = []  # Create a file list
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        file_paths.append(file_path)  # Add the file path to the list

            # Create a list with all the key-objects that are found in the files:
            key_object_list = holokeymapper_backend.make_keylist(file_paths)
            self.tree_viewer.update_tree(key_object_list)

class LoadFromCsvButton(QWidget):
    '''
    This widget provides a user interface component for loading data from a CSV file.
    '''
    def __init__(self, text_display, tree_viewer):
        super().__init__()
        self.text_display = text_display
        self.tree_viewer = tree_viewer  
        self.initUI()

    def initUI(self):
        '''
        Initialize the user interface for the main window.

        This method sets up the user interface components for the main window, including
        a button for searching a folder. When the button is clicked, it connects to
        the 'open_file_dialog' method to trigger the file dialog for selecting a folder.
        '''

        layout = QVBoxLayout()

        self.button = QPushButton('Load CSV')
        self.button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def open_file_dialog(self):
        '''
        Open a file dialog to choose a folder and update the UI components accordingly.

        This method opens a file dialog to allow the user to choose a folder. If a folder
        is selected, it updates the text display with the selected folder's path, updates
        the file list widget with the files in the selected folder, and generates a list
        of file paths within the folder.
        '''

        csv_path = QFileDialog.getOpenFileName(self, 'Choose CSV', filter='CSV Files (*.csv)')
        print(csv_path[0])
        global key_object_list

        if csv_path:
            if os.path.exists(csv_path[0]):
                # Create the JSON Object from the CSV file:
                key_object_list = holokeymapper_backend.create_json_objects_from_csv(csv_path[0])

            self.tree_viewer.update_tree(key_object_list)


class TextDisplayWidget(QWidget):
    '''
    Create a Widget to show text. The text is editable with 'object.update_text("YOUR TEXT")'
    
    It is mainly used to show the chosen folder path and the amount of results found during a search
    '''

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        '''
        Initialize the user interface for the TextDisplayWidget.

        This method sets up the user interface components for the TextDisplayWidget,
        including a label for displaying text.
        '''

        layout = QVBoxLayout()
        self.text_label = QLabel('')
        layout.addWidget(self.text_label)
        self.setLayout(layout)

    def update_text(self, new_text):
        '''
        Update the text displayed in the TextDisplayWidget.

        This method takes a new text as input and updates the text displayed in the
        TextDisplayWidget's label with the provided text.

        Parameters:
        - new_text (str): The new text to be displayed in the widget.

        '''

        self.text_label.setText(new_text)

class SplitterWidget(QWidget):
    '''
    This widget provides a user interface component that uses a QSplitter to divide
    content into two frames, allowing for flexible resizing of the frames.

    Methods:
    - initUI: Initialize the user interface for the SplitterWidget.
    - set_default_sizes: Set default sizes for the left and right frames.
    '''

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        '''
        Initialize the user interface for the SplitterWidget.

        This method sets up the user interface components for the SplitterWidget,
        including the QSplitter widget and two frames to hold content.

        '''

        layout = QVBoxLayout(self)
        self.splitter = QSplitter()
        layout.addWidget(self.splitter)

        self.splitter.setHandleWidth(10)  # Adjust handle width for easier grabbing

        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        self.left_layout = QVBoxLayout()  # Define the left_layout
        left_frame.setLayout(self.left_layout)
        self.splitter.addWidget(left_frame)

        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        self.right_layout = QVBoxLayout()  # Define the right_layout
        right_frame.setLayout(self.right_layout)
        self.splitter.addWidget(right_frame)

    def set_default_sizes(self, total_width):
        '''
        Set default sizes for the left and right frames within the SplitterWidget.

        This method calculates and sets default sizes for the left and right frames
        within the SplitterWidget based on the total available width.

        Parameters:
        - total_width (int): The total available width for the SplitterWidget.
        '''

        default_width = total_width // 5  # Set to 1/5 of the total width
        self.splitter.setSizes([default_width, total_width - default_width])


class FileListWidget(QListWidget):
    '''
    This widget extends the functionality of QListWidget to display a list of files
    and provides methods for updating the list and responding to item clicks.

    Methods:
    - __init__: Initialize the FileListWidget.
    - update_file_list: Update the list of files displayed in the widget.
    - itemClicked: Handle item click events and update the text display.

    Attributes:
    - text_display (TextDisplayWidget): The TextDisplayWidget instance for displaying
      selected item text.
    '''

    def __init__(self, text_display):
        super().__init__()
        self.text_display = text_display

    def update_file_list(self, folder_path):
        '''
        Update the list of files displayed in the FileListWidget.

        This method clears the current list and populates it with the files found in
        the specified folder path. It returns a list of file names.

        Parameters:
        - folder_path (str): The path to the folder containing the files to display.

        Returns:
        - file_list (list): A list of file names displayed in the widget.

        '''

        file_list = []
        self.clear()
        if os.path.exists(folder_path):
            dateien = os.listdir(folder_path)
            for datei in dateien:
                self.addItem(datei)
                file_list = file_list + [datei]
        return file_list

    def itemClicked(self, item):
        '''
        This method is called when an item in the FileListWidget is clicked. It
        extracts the selected item's text and updates the TextDisplayWidget with
        the selected text.

        Parameters:
        - item (QListWidgetItem): The selected item in the FileListWidget.
        '''

        selected_text = item.text()
        self.text_display.update_text(selected_text)

class TreeViewer(QMainWindow):
    '''
    This widget provides a user interface component with a tree view for displaying
    hierarchical data. It allows for adding, updating, and interacting with tree items.

    Methods:
    - __init__: Initialize the TreeViewer.
    - update_tree: Update the tree view with a list of objects.
    - show_context_menu: Handle the context menu for tree items.
    - add_file_action: Add a file-related action to the context menu.

    Attributes:
    - code_snippet_viewer: The CodeSnippetViewer instance for displaying code snippets.
    '''

    def __init__(self, code_snippet_viewer):
        '''
        This constructor initializes the TreeViewer, sets up the main window with a
        tree view, and configures its default settings.

        Parameters:
        - code_snippet_viewer (CodeSnippetViewer): The CodeSnippetViewer instance.
        '''

        super().__init__()
        self.setWindowTitle("TreeViewer")
        self.resize(1600, 900)

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.treeWidget = QTreeWidget()  # Define the TreeWidget as attribute
        layout.addWidget(self.treeWidget)

        # Defining the tree widget default settings
        header_labels = ["JSON",
                         "Default Value",
                         "Header Key",
                         "Header Comment",
                         "C++ Name",
                         "Property",
                         "Default Value"]
        self.treeWidget.setHeaderLabels(header_labels)
        self.treeWidget.header().setSectionResizeMode(QHeaderView.Interactive)   # Make headers slideable
        self.setContextMenuPolicy(Qt.CustomContextMenu) #Add context menu
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.code_snippet_viewer = code_snippet_viewer  #Add the CodeSnippetViewer

    def update_tree(self, obj_lst):
        '''
        This method clears the existing tree items and populates the tree view with
        new entries based on the provided list of objects. It also creates a dictionary that
        connects the key_objects to the tree_items

        Parameters:
        - obj_lst (list): A list of objects to display in the tree view.
        '''

        self.treeWidget.clear()     #Clear existing tree items
        global key_tree_dict

        # Adding entries
        for key_object in obj_lst:
            #Create a parent tree item from a JSON1 object.
            parent_item = QTreeWidgetItem(self.treeWidget, [key_object.name,
                                                            str(key_object.default_value),
                                                            key_object.header_key,
                                                            key_object.header_comment,
                                                            key_object.cpp_name])
            key_tree_dict[key_object] = parent_item     #Connect the tree_item to the JSON1 object

            if key_object.ui_list:
                # Create UI-List item:
                for key, value in key_object.ui_list.items():
                    QTreeWidgetItem(parent_item, ['', '', '', '', '', key, value])

            # Check if the key_object has children
            if key_object.children:
                for child in key_object.children:
                    child_item = QTreeWidgetItem(parent_item, [child.name,
                                                               str(child.default_value),
                                                               child.header_key,
                                                               child.header_comment,
                                                               child.cpp_name])
                    key_tree_dict[child] = child_item

                    # Check for children of the child items
                    if child.children:  
                        for grandchild in child.children:
                            grandchild_item = QTreeWidgetItem(child_item, [grandchild.name,
                                                                           str(grandchild.default_value),
                                                                           grandchild.header_key,
                                                                           grandchild.header_comment,
                                                                           grandchild.cpp_name])
                            key_tree_dict[grandchild] = grandchild_item
                    
                    # Check if there is a ui_list in the child items.
                    if child.ui_list:
                        # Create UI-List item:
                        for key, value in child.ui_list.items():
                            QTreeWidgetItem(child_item, ['', '', '', '', '', key, value])


    def show_context_menu(self, pos):
        '''
        This method displays a context menu when a tree item is right-clicked. It
        provides actions for files associated with the selected tree item.

        Parameters:
        - pos (QPoint): The position where the context menu is displayed.
        '''

        item = self.treeWidget.selectedItems()  # Get the TreeItem
        if item:
            menu = QMenu(self)  # Add the menu

            for json_object, tree_item in key_tree_dict.items():
                if tree_item == item[0]:
                    files = json_object.files   # Get the files of the key_object.
                    for file_name in files:
                        self.add_file_action(menu, file_name, json_object)
    
            menu.exec(self.mapToGlobal(pos))

    def add_file_action(self, menu, file_name, json_object):
        '''
        This method adds a file-related action to the context menu and connects it to
        the CodeSnippetViewer for displaying code snippets associated with the file.

        Parameters:
        - menu (QMenu): The context menu to which the action is added.
        - file_name (str): The name of the file associated with the action.
        - json_object: The JSON object associated with the action.
        '''

        action = menu.addAction(file_name)
        # Start the CodeSnippetViewer and show the code of the file.
        action.triggered.connect(lambda checked=False, file=file_name: self.code_snippet_viewer.show_code(file_name, json_object))

class CodeSnippetViewer(QDialog):
    '''
    This widget provides a user interface component for displaying code snippets and
    JSON data. It allows for opening and displaying content from various types of files.

    Methods:
    - __init__: Initialize the CodeSnippetViewer.
    - open_file: Open and read the contents of a file.
    - manage_json: Manage JSON data for display.
    - manage_data: Manage code snippet data for display.
    - show_code: Display code or JSON data in the dialog.
    '''

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Snippet Viewer")
        self.setGeometry(100, 100, 800, 400)  # Set the geometry of the window

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.file_label = QTextEdit()
        layout.addWidget(self.file_label)

    def open_file(self, file_name: str) -> list:
        '''
        This method opens and reads the contents of a specified file. It returns the
        contents as a list of lines.

        Parameters:
        - file_name (str): The name of the file to open.

        Returns:
        - text (list): A list of lines containing the file's contents. Each entry in the list, represents one line of the file.
        '''

        text = []

        if file_name[-4:] == ".jso":    # Json files have to be treated different than the other ones.
            if os.path.exists(file_name):
                with open(file_name, 'r', encoding='iso-8859-1') as json_file:
                    text = json.load(json_file)     # Safe the text.
        
        else:
            if os.path.exists(file_name):   # Each other file
                with open(file_name, "r", encoding='iso-8859-1') as file:
                    for line in file:
                        text.append(line)

        return text
    
    def manage_json(self, json_file, item_to_find):
        '''
        This method takes JSON data and an item to find within the data. It extracts
        relevant portions of the JSON data and returns them as a list of lines.
        This extra function is needed, because the data is being interpretad as a dictionary.

        Parameters:
        - json (dict): The JSON data to be managed.
        - item_to_find (str): The item to search for within the JSON data.

        Returns:
        - text_list (list): A list of lines containing the relevant JSON data.
        '''

        text_list = []
        index_of_element = 0

        for key, item in json_file.items():  # Convert dictionary into List for better handeling
            if isinstance(item, dict):
                text_list = text_list + [f'{key}: {{']  # Make the line of the parent item
                for key, value in item.items(): # then go into the next dictionary
                    text_list = text_list + [f'   {key}: {value}']  # Add the childs
                text_list = text_list + ['   }}']  # Close the brackets

            else:
                text_list = text_list + [f'{key}: {value}'] # if no childs are present

        for line in text_list:    # Find the item in the file.
            if item_to_find in line:
                index_of_element = text_list.index(line)    # Get the index of the line.

        if index_of_element < 5:    # If the item is in the first five lines
            text_list = text_list[:index_of_element + 5]

        else:   # If the item is found in the middle of the document. 
            text_list = text_list[index_of_element - 5: index_of_element + 5]

        return text_list

    def manage_data(self, file, item_to_find):
        '''
        This method takes data from a file and an item to find within the data. It
        extracts relevant portions of the and returns them as a list of lines.

        Parameters:
        - file (list): The code data to be managed.
        - item_to_find (str): The item to search for within the code snippet data.

        Returns:
        - text_list (list): A list of lines containing the relevant code snippet data.
        '''

        text_list = []
        index_of_element = 0

        for line in file:   # Find the given name
            if item_to_find in line:
                index_of_element = file.index(line)
                break

        if index_of_element < 5:    # If the given name is in the beginning of a document
            text_list = file[:index_of_element + 5]

        else:
            text_list = file[index_of_element - 5: index_of_element + 20]

        return text_list
    

    def show_code(self, file_name, json_object):
        '''
        This method displays code in the dialog window based on the
        specified file name and JSON object. It determines the type of data and
        extracts relevant portions for display.

        Parameters:
        - file_name (str): The name of the file containing the data.
        - json_object: The JSON object associated with the data.
        '''

        file_contents = self.open_file(file_name)

        if file_name[-4:] == '.jso':    # handle JSON-Files different since they are returned as Dictionary
            item_to_find = json_object.name     # Define item to find
            #item_to_find = "\t" + item_to_find   # Add quotation marks to the item to find, so that it can be found in the dictionary.
            json_text = self.manage_json(file_contents, item_to_find)
            text = "\n".join(json_text)     # Convert the list to a string, with new lines between the entries.
        
        if file_name[-2:] == '.h':
            item_to_find = json_object.header_key     # Define item to find
            text_list = self.manage_data(file_contents, item_to_find)
            text = "\n".join(text_list)     # Convert the list to a string, with new lines between the entries.

        if file_name[-4:] == '.cpp' or file_name[-3:] == '.ui':
            item_to_find = json_object.cpp_name     # Define item to find
            text_list = self.manage_data(file_contents, item_to_find)
            text = "\n".join(text_list)     # Convert the list to a string, with new lines between the entries.

        self.file_label.setText(text)

        self.exec()    # Open the new Window

class SearchWidget(QWidget):
    '''
    This widget provides a user interface component for searching and navigating through
    search results displayed in a tree viewer. It allows users to enter search queries,
    perform searches, and move between search results.

    Methods:
    - __init__: Initialize the SearchWidget.
    - initUI: Initialize the user interface components.
    - handle_search_next: Handle the search and next result button clicks.
    - keyPressEvent: Handle key presses (e.g., Enter key) for searching and navigating.
    - search: Perform a search based on the user's input.
    - find_items: Find items that match the search query.
    - highlight_current_result: Highlight the current search result in the tree viewer.
    - next_result: Navigate to the next search result.
    '''

    def __init__(self, tree_viewer, result_counter):
        super().__init__()
        self.tree_viewer = tree_viewer
        self.result_counter = result_counter
        self.current_action = None
        self.current_search_term = ""
        self.is_searching = False
        self.search_results = []
        self.current_result_index = 0
        self.initUI()

    def initUI(self):
        '''
        This method sets up the layout, search field, search button, and next button.
        It also connects button actions and initializes variables for storing search data.
        '''
        
        layout = QHBoxLayout()

        # Initialize search field, search button, and next button and add them to the layout 
        self.search_line = QLineEdit()
        self.search_button = QPushButton('Search')
        self.next_button = QPushButton('Next Result')

        self.search_line.setPlaceholderText("Search...")    # Add a text to the searchfield, which disappears, if something new is written in it.

        layout.addWidget(self.search_line, 2)  # Search field takes 2/3 of the given space, buttons the rest
        layout.addWidget(self.search_button)
        layout.addWidget(self.next_button)

        # Connect functions to the buttons
        self.search_button.clicked.connect(self.search)
        self.next_button.clicked.connect(self.handle_search_next)

        # Initialize variables for storing data
        self.search_results = []
        self.current_result_index = 0
        self.current_search_text = ""
        self.is_searching = False

        self.setLayout(layout)

    def handle_search_next(self):
        '''
        This method determines whether to perform a search or move to the next search
        result based on the current input in the search field.
        '''

        if self.search_line.text() == "":
            self.current_action = self.search
        else:
            self.current_action = self.next_result

        # Call the current action
        self.current_action()

    def keyPressEvent(self, event):
        '''
        This method handles Enter key presses, for initiating searches
        and navigating through search results.

        Parameters:
        - event: The key press event.
        '''

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Check if Enter key is pressed
            current_text = self.search_line.text()

            if not self.is_searching or current_text != self.current_search_term:
                self.current_search_term = current_text
                self.search()  # Call the search function
                self.is_searching = True
                event.accept()  # Accept the event
            else:
                self.next_result()  # Call the next result function
                event.accept()

    def search(self):
        '''
        This method performs a search based on the user's input in the search field.
        It updates the list of search results and highlights the first result.
        '''

        search_text = self.search_line.text()   #gets the text in the search field
        if search_text:
            self.search_results = self.find_items(search_text)
            self.current_result_index = 0
            self.highlight_current_result()

    def find_items(self, search_text):
        '''
        This method searches for items that match the provided search query within the
        tree viewer's data.

        Parameters:
        - search_text (str): The search query entered by the user.

        Returns:
        - tree_results (list): A list of matching items in the tree viewer.
        '''
        
        key_results = []
        tree_results = []
        global key_object_list
        global key_tree_dict

        for item in key_object_list:    # Iterate through all the key_objects
            for value in item.__dict__.values():
                if search_text.lower() in str(value).lower():    #search the given text in the JSON-object
                    key_results.append(item)    # Add the object to the list of results

            for child in item.children:     #check the children of each object as well
                for key, value in child.__dict__.items():
                    if key == "parent" or key == "files":   #Leave parent and files out so that there is no error.
                        continue
                    else:
                        if search_text.lower() in str(value).lower():
                            key_results.append(child)

        for item in key_results:    # Handle the results
            if item in key_tree_dict:
                if key_tree_dict[item] not in tree_results:
                    tree_results.append(key_tree_dict[item])    # Add the tree item to the list

        self.result_counter.update_text(f"{len(tree_results)} results are found")   # Provide an overview of how many results are found

        return tree_results
    
    def highlight_current_result(self):
        '''
        This method highlights the current search result in the tree viewer, ensuring
        it is visible and expanded.
        '''

        if self.search_results:
            if 0 <= self.current_result_index < len(self.search_results):
                item = self.search_results[self.current_result_index]   # Get the item
                tree_widget = self.tree_viewer.treeWidget
                tree_widget.clearSelection()
                item.setSelected(True)  # Select the item
                tree_widget.scrollToItem(item)
                tree_widget.expandItem(item)

    def next_result(self):
        '''
        This method navigates to the next search result, highlighting it and expanding
        its parent items. It also collapses the old result.
        '''
        
        if self.search_results:
            if 0 <= self.current_result_index < len(self.search_results):
                # Collapse the old result
                self.search_results[self.current_result_index - 1].setExpanded(False)

                # Get the new result
                self.current_result_index = (self.current_result_index + 1) % len(self.search_results)

                # Highlight the current result
                self.highlight_current_result()

                # Expand the new result
                self.search_results[self.current_result_index].setExpanded(True)

class CSVButton(QWidget):
    '''
    This widget provides a user interface component for creating and saving data to a
    CSV file. It allows users to click a button to initiate the process of saving data
    to a CSV file.

    Methods:
    - __init__: Initialize the CSVButton.
    - initUI: Initialize the user interface components.
    - open_file_dialog: Open a file dialog for specifying the CSV file location.

    '''
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        '''
        This method sets up the layout and creates a button with the text "Export CSV."
        It also connects the button click event to the 'open_file_dialog' method.
        '''
        
        layout = QVBoxLayout()

        # Create a button with the text 'Create CSV'.
        self.button = QPushButton('Export CSV', self)
        self.button.clicked.connect(self.open_file_dialog)  # Connect the Button to the method that it opens a file dialog

        layout.addWidget(self.button)
        self.setLayout(layout)

    def open_file_dialog(self):
        '''
        This method opens a file dialog for the user to specify the location and name of
        the CSV file where data will be saved. It uses the 'holokeymapper_backend.make_csv'
        method to create the CSV file with the specified data.
        '''
        
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV-File as", "", "CSV Dateien (*.csv);;Alle Dateien (*)", options=options)

        if file_path:
            holokeymapper_backend.make_csv(file_path, key_object_list)   # Create CSV
            

class MainWindow(QMainWindow):
    '''
    This window serves as the main user interface for the Key-Mapper application.
    It includes various widgets and components for interacting with and displaying
    data related to the application's functionality.

    Methods:
    - __init__: Initialize the MainWindow and its user interface.
    - initUI: Initialize the user interface components and layout
    '''
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        '''
        This method sets up the layout and creates and configures various widgets
        that make up the user interface of the Key-Mapper application. It establishes
        the layout of the main window, including the left and right sides of a splitter,
        and the widgets within those sides.
        '''

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        splitter = SplitterWidget()
        main_layout.addWidget(splitter)

        #Right side of splitter:
        code_snippet_viewer = CodeSnippetViewer()
        tree_viewer = TreeViewer(code_snippet_viewer)
        result_counter = TextDisplayWidget()
        search_widget = SearchWidget(tree_viewer, result_counter)

        splitter.right_layout.addWidget(tree_viewer)
        splitter.right_layout.addWidget(search_widget)
        splitter.right_layout.addWidget(result_counter)

        #Left side of splitter:
        text_display = TextDisplayWidget()  # Shows the path to the chosen folder.
        list_display = FileListWidget(text_display) # Shows the data prestent in the chosen folder.

        button_widget = ButtonWidget(text_display, list_display, tree_viewer)
        load_from_csv_button = LoadFromCsvButton(text_display, tree_viewer)

        csv_button = CSVButton()  # create the CSV-Button
        button_layout = QVBoxLayout()  # Create layout for buttons

        button_layout.addWidget(button_widget)
        button_layout.addWidget(load_from_csv_button)
        button_layout.addWidget(csv_button)
        splitter.left_layout.addWidget(list_display)
        # Add "Search folder" and "Create CSV" buttons:
        splitter.left_layout.addLayout(button_layout)
        splitter.left_layout.addWidget(text_display)

        self.setGeometry(100, 100, 1600, 900)
        self.setWindowTitle('Key-Mapper')
        self.show()     # Open Window

        splitter.set_default_sizes(self.centralWidget().width())
        list_display.update_file_list(text_display.text_label.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec())
    