from __future__ import print_function, division

import os
import tempfile

import h5py
import pytest
import numpy as np

from .. import Model
from ...util.functions import random_filename
from ...dust import IsotropicDust
from .test_helpers import get_test_model_noimaging, get_test_dust


def test_write_noname_nofilename():
    m = Model()
    with pytest.raises(ValueError) as e:
        m.write()
    assert e.value.args[0] == "filename= has not been specified and model has no name"


def test_write_nogrid():
    m = Model()
    with pytest.raises(Exception) as e:
        m.write('test')
    assert e.value.args[0] == 'No coordinate grid has been set up'


def test_write_nophotons():
    m = Model()
    m.set_cartesian_grid([-1., 1.], [-1., 1.], [-1., 1.])
    with pytest.raises(Exception) as e:
        m.write('test')
    assert e.value.args[0] == 'Photon numbers not set'


def test_write_incomplete_photons_1():
    m = Model()
    m.set_cartesian_grid([-1., 1.], [-1., 1.], [-1., 1.])
    with pytest.raises(Exception) as e:
        m.set_n_photons(initial=1)
    assert e.value.args[0] == '[n_photons] imaging should bet set'


def test_write_incomplete_photons_2():
    m = Model()
    m.set_cartesian_grid([-1., 1.], [-1., 1.], [-1., 1.])
    with pytest.raises(Exception) as e:
        m.set_n_photons(imaging=1)
    assert e.value.args[0] == '[n_photons] initial should be set since the initial iterations are being computed'


class TestWriteDustCopy(object):

    def setup_method(self, method):

        self.dust_file = random_filename()
        self.dust = get_test_dust()

        self.density = np.array([[[1.]]])

        self.model = get_test_model_noimaging()

    def test_copy_filename(self):
        self.dust.write(self.dust_file)
        self.model.add_density_grid(self.density, self.dust_file)
        self.model.write(random_filename(), copy=True)
        self.model.run(random_filename())

    def test_copy_object(self):
        self.model.add_density_grid(self.density, self.dust)
        self.model.write(random_filename(), copy=True)
        self.model.run(random_filename())

    def test_link_filename(self):
        self.dust.write(self.dust_file)
        self.model.add_density_grid(self.density, self.dust_file)
        self.model.write(random_filename(), copy=False)
        self.model.run(random_filename())

    def test_link_object(self):
        self.model.add_density_grid(self.density, self.dust)
        with pytest.raises(ValueError) as e:
            self.model.write(random_filename(), copy=False)
        assert e.value.args[0] == 'Dust properties are not located in a file, so cannot link. Use copy=True or write the dust properties to a file first'


@pytest.mark.parametrize(('write_copy'), [True, False])
def test_input_link(write_copy):

    input_file = random_filename()
    output_file = random_filename()

    model = get_test_model_noimaging()
    model.set_copy_input(False)
    model.write(input_file, copy=write_copy)

    # Check that copy parameter is there
    f = h5py.File(input_file, 'r')
    assert f.attrs['copy_input'].decode('utf-8') == 'no'
    f.close()

    # Run the model
    model.run(output_file)

    # Check that attributes from input can still be accessed, then check that
    # 'Input' is a link
    f = h5py.File(output_file, 'r')
    assert f['Input'].attrs['copy_input'].decode('utf-8') == 'no'
    assert f.file != f['Input'].file
    f.close()


@pytest.mark.parametrize(('write_copy'), [True, False])
def test_input_copy(write_copy):

    input_file = random_filename()
    output_file = random_filename()

    model = get_test_model_noimaging()
    model.set_copy_input(True)
    model.write(input_file, copy=write_copy)

    # Check that copy parameter is there
    f = h5py.File(input_file, 'r')
    assert f.attrs['copy_input'].decode('utf-8') == 'yes'
    f.close()

    # Run the model
    model.run(output_file)

    # Check that attributes from input can still be accessed, then check that
    # 'Input' is a not a link
    f = h5py.File(output_file, 'r')
    assert f['Input'].attrs['copy_input'].decode('utf-8') == 'yes'
    assert f.file == f['Input'].file
    f.close()