'''
Test the function of the key_list_full.py file
Author - Manuel Eschborn
Date - 2024-03-12
Coding: utf-8
'''

import unittest
import holokeymapper_backend as kl

class TestKeyList(unittest.TestCase):
    '''Test the function of the key_list_full.py file'''
    def setUp(self):
        # Create a json file
        json_text = {"detect_in_focus_settings": {
                        "binning_factor": 63,
                        "radius_smooth": True,
                        "threshold_object_mask": 0.3,
                        "use_for_global_reference": False,
                        "use_for_offset_combination": False}
        }
        self.json_file = kl.File(name = "test.json", text=json_text, file_format='.jso')

        # Create a header file:
        header_text = ['#define KEY_DETECT_IN_FOCUS_SETTINGS "detect_in_focus_settings"',
                       '	const char* BINNING_FACTOR = "binning_factor";',
                       '	const char* USE_FOR_GLOBAL_REFERENCE = "use_for_global_reference";',
                       '	const char* USE_FOR_OFFSET_COMBINATION = "use_for_offset_combination";',
                       '	const char* RADIUS_SMOOTH = "radius_smooth";',
                       '    const char* THRESHOLD_OBJECT_MASK = "threshold_object_mask";']
        self.header_file = kl.File(name = "test.h", text=header_text, file_format='.h')

        # Create a CPP file:
        cpp_text = ['void detect_in_focus_widget::register_widgets() {',
                    '	register_widget(ui->sb_binning_factor, KeysDetectInFocusSettings.BINNING_FACTOR);',
                    '	register_widget(ui->cb_use_for_global_reference, KeysDetectInFocusSettings.USE_FOR_GLOBAL_REFERENCE);',
                    '	register_widget(ui->cb_use_for_offset_combination, KeysDetectInFocusSettings.USE_FOR_OFFSET_COMBINATION);',
                    '	register_widget(ui->sb_threshold_object_mask, KeysDetectInFocusSettings.THRESHOLD_OBJECT_MASK);',
                    '	register_widget(ui->sb_radius_smooth, KeysDetectInFocusSettings.RADIUS_SMOOTH);',
                    '}']
        self.cpp_file = kl.File(name = "test.cpp", text=cpp_text, file_format='.cpp')

        # Create a UI file:
        ui_text = ['   <item row="4" column="1">',
                   '    <widget class="QSpinBox" name="sb_binning_factor">',
                   '     <property name="minimum">',
                   '      <number>8</number>',
                   '     </property>',
                   '     <property name="maximum">',
                   '      <number>256</number>',
                   '     </property>',
                   '     <property name="singleStep">',
                   '      <number>8</number>',
                   '     </property>',
                   '    </widget>',
                   '   </item>']
        self.ui_file = kl.File(name = "test.ui", text=ui_text, file_format='.ui')

    def test_search_header(self):
        '''Test the 'search_header' function'''

        json_objects = kl.search_header(self.header_file)
        # Check the Parent object
        self.assertEqual(len(json_objects), 6)
        self.assertEqual(json_objects[0].name, "detect_in_focus_settings")
        self.assertEqual(json_objects[1].name, "binning_factor")
        self.assertEqual(json_objects[2].header_key, "USE_FOR_GLOBAL_REFERENCE")
        self.assertEqual(json_objects[3].header_key, "USE_FOR_OFFSET_COMBINATION")
        self.assertEqual(json_objects[5].name, "threshold_object_mask")
        self.assertEqual(json_objects[0].files[0], "test.h")

    def test_get_default_value(self):
        '''Test the 'get_default_value' function'''

        json_objects = kl.search_header(self.header_file)
        json_objects = kl.get_default_value(json_objects, self.json_file)

        self.assertEqual(json_objects[0].default_value, '')
        self.assertEqual(json_objects[1].default_value, 63)
        self.assertEqual(json_objects[3].default_value, False)
        self.assertEqual(json_objects[5].default_value, 0.3)

    def test_get_cpp_key(self):
        '''Test if the C++ Keys work fine'''
        json_objects = kl.search_header(self.header_file)
        json_objects = kl.get_default_value(json_objects, self.json_file)
        json_objects = kl.get_cpp_key(json_objects, self.cpp_file)

        self.assertEqual(json_objects[0].cpp_name, '')
        self.assertEqual(json_objects[1].cpp_name, 'sb_binning_factor')
        self.assertEqual(json_objects[5].cpp_name, 'sb_threshold_object_mask')
        self.assertEqual(json_objects[3].files[1], "test.cpp")

    def test_get_ui_information(self):
        '''Test if the UI information is correct'''
        json_objects = kl.search_header(self.header_file)
        json_objects = kl.get_default_value(json_objects, self.json_file)
        json_objects = kl.get_cpp_key(json_objects, self.cpp_file)
        json_objects = kl.get_ui_information(json_objects, self.ui_file)

        self.assertEqual(json_objects[0].ui_list, {})
        self.assertEqual(json_objects[1].ui_list['minimum'], '8')
        self.assertEqual(json_objects[1].ui_list['maximum'], '256')
        self.assertEqual(json_objects[1].ui_list['singleStep'], '8')
        self.assertEqual(json_objects[1].files[-1], 'test.ui')

if __name__ == '__main__':
    unittest.main()
