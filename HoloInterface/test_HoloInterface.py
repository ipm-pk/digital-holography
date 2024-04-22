'''
Test the function of the HoloInterface.py file
Author - Manuel Eschborn
Date - 2024-03-19
Coding: utf-8
'''

import unittest
from unittest.mock import MagicMock
import sys
from HoloInterface import HoloInterface
from PySide6.QtWidgets import QApplication

class TestHoloInterface(unittest.TestCase):
    '''Test the function of the HoloInterface.py file'''
    def setUp(self):
        self.app = QApplication(sys.argv)
        self.holo_interface = HoloInterface()
        self.holo_interface.TcpServer = MagicMock()
        self.holo_interface.TcpServer.sendMessage = MagicMock()

        self.test_json = {
                    "use_holointerface": True,
                    "detect_in_focus_settings": {
                       "binning_factor": 63.2,
                       "radius_smooth": True,
                       "threshold_object_mask": 0.3,
                       "use_for_global_reference": False,
                       "use_for_offset_combination": False
                    },
                    "dispersion_settings": {
                       "do_dispersion_correction_xy": False,
                       "do_dispersion_correction_z": False,
                       "thickness_BS_mm": 0,
                       "type_of_glass_BS": 0
                    },
                    "display phase": True,
                    "display_mode": 1,
                    "extended_depth_settings": {
	                    "I_am_a_Bug": True,
                        "extended_depth_active": 3,
                        "extended_depth_auto_tilt_estimation": False,
                        "extended_depth_cad_load_model": False,
                        "extended_depth_center_ROI_to_refpoint": True,
                        "extended_depth_center_x": 5120,
                        "extended_depth_center_y": 3500,
                        "extended_depth_depthrange": 6,
                        "extended_depth_display_diff_with_cad": False,
                        "extended_depth_interpolate_multiplane": False,
                        "extended_depth_method": 0,
                        "extended_depth_multiplane_propagation": False,
                        "extended_depth_num_propagation_distances": 4,
                        "extended_depth_prop_planes_selection_method": 0,
                        "extended_depth_tilt_x_deg": 0,
                        "extended_depth_tilt_y_deg": 0,
                        "filter_radius_SFF": 0,
                        "num_planes_SFF": 2,
                        "radius_close_sff_mask": 0,
                        "radius_open_sff_mask": 0,
                        "smooth_SFF_with_synth": False,
                        "threshold_SFF": 0
                    }
        }

        self.expected_errors = [
            'Value type of JSON object binning_factor is not correct. Expected: int, got: float.',
            'Value type of JSON object radius_smooth is not correct. Expected: float, got: bool.',
            'JSON object I_am_a_Bug is not known in HoloSoftware.',
            'JSON object use_holointerface is not known in HoloSoftware.',
            'Value type of JSON object extended_depth_active is not correct. Expected: bool, got: int.'
        ]

        self.expected_warnings = ['detect_in_focus_settings',
                                  'dispersion_settings',
                                  'extended_depth_settings',
                                  'extended_depth_active',
                                  'extended_depth_cad_load_model',
                                  'extended_depth_center_x',
                                  'extended_depth_center_y',
                                  'extended_depth_depthrange',
                                  'extended_depth_interpolate_multiplane',
                                  'extended_depth_method',
                                  'extended_depth_tilt_x_deg',
                                  'extended_depth_tilt_y_deg',
                                  'filter_radius_SFF',
                                  'num_planes_SFF',
                                  'radius_close_sff_mask',
                                  'radius_open_sff_mask',
                                  'threshold_SFF']

    def test_simulate_measurement(self):
        '''Test the 'simulate_measurement' function'''

        error_list, warnings = self.holo_interface.simulate_measurement(self.test_json)
        print(warnings)

        self.assertEqual(len(error_list), 5)
        self.assertEqual(len(warnings), 17)
        self.assertEqual(warnings, self.expected_warnings)

        for expected_error in self.expected_errors:
            self.assertIn(expected_error, error_list)

if __name__ == '__main__':
    unittest.main()
