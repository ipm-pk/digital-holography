# HoloKeyMapper

**Description:** This project consists of a graphical user interface (GUI) and a program that maps keys from different files together. The program takes a folder as input, which should contain a JSON file and all the files to be searched through. The folder can be selected using the GUI. 

The programme first searches through the .h files to find the `.jso` - `.h` pairs and then searches the `.jso` for the given values for each key. Then the corresponding `.cpp` names, and finally searches for those keys in the `.gui` files. The GUI displays each pair of keys in a collapsible view. It also provides a search function to quickly find specific keys. If the source code files are not available, a CSV file with the corresponding information can also be loaded.

When right-clicking on a key, a menu opens showing the files that correspond to that key. Clicking on a filename opens a separate window that displays 10 lines above and 10 lines below where the key was found.

## Getting Started

These instructions will guide you on how to set up and use the application on your local machine.

### Prerequisites
- [Pyhon](https://www.python.org/) - Version: 3.10.4
- [PySide6](https://doc.qt.io/qtforpython-6/) - Version: 6.6.1

### Installation

1. Clone the repository.
2. Install the required libraries using the following command:

```bash
$ pip install PySide6==6.6.1
```

### Usage

The file `holokeymapper_backend.py` includes the logic of this module. `holokeymapper_gui.py` is only a graphical user interface. `test_holokeymapper.py` runs a unittest for a given examples. 

1. Open the graphical user interface `holokeymapper_gui.py`.
2. Select the folder containing the JSON file and other files by pressing the `Import Source Files` button for loading source code (`.json`, `.cpp`, `.h` files) or `Load CSV`.
3. The program will automatically map the keys and display them in the GUI.
4. Use the search function to find specific keys quickly.

If you have source code, you can

5. Right-click on a key to access the corresponding files.
6. Click on a filename to open a separate window displaying the surrounding lines of the key.
7. If you want to save the keys, press the `Export CSV` button.

From a loaded `.csv` file, the latter options are not available.

## Authors

- Manuel Eschborn - [GitHub Profile](https://github.com/ElManu93)

## License

This project is licensed under the MIT License - see the [LICENSE.md](link_to_license_file) file for details.
