# -*- coding: utf-8 -*-
"""
Created on 04.09.2020

@author: beckmann
"""

import unittest
import warnings
from typing import Union

import numpy

import globals.cuda_holo_definitions as cuda_holo
import globals.holo_tcp_globals as holo_dll

class CvImageBuffer:
    """
    Class for opencv result images
    """
    def __init__(self, data, name, im_id, stack_size):
        self.data = data
        self.name = name
        self.im_id = im_id
        self.stack_size = stack_size


class ResultBuffer:
    """
    Resultbuffer (or its description, if data is None)
    """

    def __init__(self, step: cuda_holo.ProcessingStep=None,
                 laser_nr=0,
                 img_nr=0,
                 is_amp=False,
                 data: Union[None, numpy.array] = None,
                 measurement_id=0):
        self.processing_step = step
        self.laser_nr = laser_nr
        self.img_nr = img_nr
        self.is_amp = is_amp
        self.data = data
        self.measurement_id = measurement_id

    def __repr__(self):
        rep = f"<ResultBuffer: {self.processing_step.name}"
        if self.data is not None:
            rep += f", {self.data.shape[1]}×{self.data.shape[0]}, {self.data.dtype}"
        if self.laser_nr is not None:
            rep += f", Laser {self.laser_nr}"
        if self.img_nr is not None:
            rep += f", Image {self.img_nr}"
        if self.is_amp:
            rep += ", amplitude"
        if self.measurement_id is not None:
            rep += f", measurement_id {self.measurement_id}"
        return rep + ">"

    def __eq__(self, other):
        # TBe: if kind of __eq__ and __hash__ are ever needed for another class, pull them into superclass and inherit.
        same_type = isinstance(other, self.__class__)
        same_members = self.__dict__ == other.__dict__
        return same_type and same_members

    def __hash__(self):
        # for set membership test, see
        # https://stackoverflow.com/questions/15326985/how-to-implement-eq-for-set-inclusion-test
        # https://stackoverflow.com/questions/390250/elegant-ways-to-support-equivalence-equality-in-python-classes
        return hash(tuple(sorted(self.__dict__.items())))

    def from_jso(self, jso):
        keys = holo_dll.KeysBufferDesc()

        if keys.processing_step in jso:
            proc_step_code = jso[keys.processing_step]
            self.processing_step = cuda_holo.ProcessingStep(proc_step_code)
        else:
            warnings.warn("No ProcessingStep found trying to parse ResultBuffer")
            self.processing_step = None

        self.laser_nr = int(jso[keys.laser_nr]) if keys.laser_nr in jso else None
        self.img_nr = int(jso[keys.img_nr]) if keys.img_nr in jso else None
        self.is_amp = bool(jso[keys.is_amp]) if keys.is_amp in jso else None
        self.measurement_id = int(jso[keys.meas_id]) if keys.meas_id in jso else None

    def to_jso(self):
        """return a json-dict, e.g. for sending to holo_software"""
        keys = holo_dll.KeysBufferDesc()
        jso = {keys.processing_step: self.processing_step.value,
               keys.laser_nr: self.laser_nr,
               keys.img_nr: self.img_nr,
               keys.is_amp: self.is_amp,
               keys.meas_id: self.measurement_id}

        return jso


class TestBufferComparison(unittest.TestCase):
    buffer_syn_phs = ResultBuffer(cuda_holo.ProcessingStep.STEP_SYN_PHASES_COMBINED)
    buffer_syn_amp = ResultBuffer(cuda_holo.ProcessingStep.STEP_SYN_PHASES_COMBINED, is_amp=True)
    buffer_syn_phs_2 = ResultBuffer(cuda_holo.ProcessingStep.STEP_SYN_PHASES_COMBINED)

    def test_different(self):
        self.assertTrue(self.buffer_syn_phs != self.buffer_syn_amp)

    def test_identical_equal(self):
        self.assertTrue(self.buffer_syn_phs == self.buffer_syn_phs)

    def test_same_but_separate_instances_are_equal(self):
        # The tricky one: are two different instances with the same properties equal?
        self.assertTrue(self.buffer_syn_phs == self.buffer_syn_phs_2)

    def test_set_membership_detectable(self):
        sample_set = {self.buffer_syn_phs, self.buffer_syn_amp}  # syn_phs_2 is not explicitly in this set.
        # ...but should be "in" set by comparison (__hash__ and __eq__):
        self.assertTrue(self.buffer_syn_phs_2 in sample_set)


if __name__ == "__main__":
    unittest.main()
