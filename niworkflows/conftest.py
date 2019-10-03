"""py.test configuration"""
import os
from pathlib import Path
import numpy as np
import nibabel as nb
import pandas as pd
import pytest
import tempfile
import pkg_resources

from .utils.bids import collect_data

test_data_env = os.getenv('TEST_DATA_HOME',
                          str(Path.home() / '.cache' / 'stanford-crn'))
data_dir = Path(test_data_env) / 'BIDS-examples-1-enh-ds054'


@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace['np'] = np
    doctest_namespace['pd'] = pd
    doctest_namespace['os'] = os
    doctest_namespace['Path'] = Path
    doctest_namespace['datadir'] = data_dir
    doctest_namespace['bids_collect_data'] = collect_data
    doctest_namespace['test_data'] = pkg_resources.resource_filename('niworkflows', 'tests/data')

    tmpdir = tempfile.TemporaryDirectory()
    doctest_namespace['tmpdir'] = tmpdir.name

    nifti_fname = str(Path(tmpdir.name) / 'test.nii.gz')
    nb.Nifti1Image(np.random.random((5, 5)).astype('f4'), np.eye(4)).to_filename(nifti_fname)
    doctest_namespace['nifti_fname'] = nifti_fname
    yield
    tmpdir.cleanup()


@pytest.fixture
def testdata_dir():
    return data_dir
