#!/usr/bin/env python
# -*- coding: utf-8
# pytest unit tests for ivadomed.postprocessing


import pytest
import scipy
import numpy as np
import nibabel as nib

import ivadomed.postprocessing as postproc


def nii_dummy_seg(size_arr=(15, 15, 9), pixdim=(1, 1, 1), dtype=np.float64, orientation='LPI', shape='rectangle',
            radius_RL=3.0, radius_AP=2.0, zeroslice=[], softseg=False):
    """Create a dummy nibabel object with a ellipse or rectangle of ones running from top to bottom in the 3rd
    dimension.
    :param size_arr: tuple: (nx, ny, nz)
    :param pixdim: tuple: (px, py, pz)
    :param dtype: Numpy dtype.
    :param orientation: Orientation of the image. Default: LPI
    :param shape: {'rectangle', 'ellipse'}
    :param radius_RL: float: 1st radius. With a, b = 50.0, 30.0 (in mm), theoretical CSA of ellipse is 4712.4
    :param radius_AP: float: 2nd radius
    :param zeroslice: list int: zero all slices listed in this param
    :param softseg: Bool: Generate soft segmentation by applying blurring filter.
    :return: nibabel: Image object
    """
    # Create a 3d array, with dimensions corresponding to x: RL, y: AP, z: IS
    nx, ny, nz = [int(size_arr[i] * pixdim[i]) for i in range(3)]
    data = np.zeros((nx, ny, nz), dtype)
    xx, yy = np.mgrid[:nx, :ny]
    # loop across slices and add object
    for iz in range(nz):
        if shape == 'rectangle':  # theoretical CSA: (a*2+1)(b*2+1)
            data[:, :, iz] = ((abs(xx - nx / 2) <= radius_RL) & (abs(yy - ny / 2) <= radius_AP)) * 1
        if shape == 'ellipse':
            data[:, :, iz] = (((xx - nx / 2) / radius_RL) ** 2 + ((yy - ny / 2) / radius_AP) ** 2 <= 1) * 1
    # Zero specified slices
    if zeroslice is not []:
        data[:, :, zeroslice] = 0
    # Apply Gaussian filter (to get soft seg)
    if softseg:
        kernel = np.ones((3, 3, 3)) / 27
        data = scipy.ndimage.convolve(data, kernel)
    # Create nibabel object
    affine = np.eye(4)
    nii = nib.nifti1.Nifti1Image(data, affine)
    # Change orientation
    # TODO
    return nii


@pytest.mark.parametrize('nii_seg', [nii_dummy_seg(softseg=True)])
def test_threshold(nii_seg):
    # input array
    arr_seg_proc = postproc.threshold_predictions(np.copy(np.asanyarray(nii_seg.dataobj)))
    assert isinstance(arr_seg_proc, np.ndarray)
    # Before thresholding: [0.33333333, 0.66666667, 1.        ] --> after thresholding: [0, 1, 1]
    assert np.array_equal(arr_seg_proc[4:7, 8, 4], np.array([0, 1, 1]))
    # input nibabel
    nii_seg_proc = postproc.threshold_predictions(nii_seg)
    assert isinstance(nii_seg_proc, nib.nifti1.Nifti1Image)
    assert np.array_equal(nii_seg_proc.get_fdata()[4:7, 8, 4], np.array([0, 1, 1]))


@pytest.mark.parametrize('nii_seg', [nii_dummy_seg(), nii_dummy_seg(softseg=True)])
def test_keep_largest_object(nii_seg):
    nii_seg_copy = np.copy(nii_seg)
    # Set a voxel to 1 at the corner to make sure it is set to 0 by the function
    coord = (1, 1, 1)
    nii_seg.dataobj[coord] = 1
    # Test function with array input
    arr_seg_proc = postproc.keep_largest_object(np.copy(np.asanyarray(nii_seg.dataobj)))
    assert isinstance(arr_seg_proc, np.ndarray)
    assert arr_seg_proc[coord] == 0
    # Make sure it equals the input data, in particular: still binary / soft if the input was binary / soft
    assert np.array_equal(nii_seg.dataobj, arr_seg_proc)
    # Make sure it works with nibabel input
    nii_seg_proc = postproc.keep_largest_object(nii_seg)
    assert isinstance(nii_seg_proc, nib.nifti1.Nifti1Image)
    assert nii_seg_proc.dataobj[coord] == 0


@pytest.mark.parametrize('nii_seg', [nii_dummy_seg()])
def test_keep_largest_object_per_slice(nii_seg):
    # Set a voxel to 1 at the corner to make sure it is set to 0 by the function
    coord = (1, 1, 1)
    nii_seg.dataobj[coord] = 1
    # Test function with array input
    arr_seg_proc = postproc.keep_largest_object_per_slice(np.copy(np.asanyarray(nii_seg.dataobj)), axis=2)
    assert isinstance(arr_seg_proc, np.ndarray)
    assert arr_seg_proc[coord] == 0
    # Make sure it works with nibabel input
    nii_seg_proc = postproc.keep_largest_object_per_slice(nii_seg)
    assert isinstance(nii_seg_proc, nib.nifti1.Nifti1Image)
    assert nii_seg_proc.dataobj[coord] == 0


@pytest.mark.parametrize('nii_seg', [nii_dummy_seg()])
def test_fill_holes(nii_seg):
    # Set a voxel to 0 in the middle of the segmentation to make sure it is set to 1 by the function
    coord = (7, 7, 4)
    nii_seg.dataobj[coord] = 0
    # Test function with array input
    arr_seg_proc = postproc.fill_holes(np.copy(np.asanyarray(nii_seg.dataobj)))
    assert isinstance(arr_seg_proc, np.ndarray)
    assert arr_seg_proc[coord] == 1
    # Make sure it works with nibabel input
    nii_seg_proc = postproc.fill_holes(nii_seg)
    assert isinstance(nii_seg_proc, nib.nifti1.Nifti1Image)
    assert nii_seg_proc.dataobj[coord] == 1


@pytest.mark.parametrize('nii_seg', [nii_dummy_seg()])
def test_mask_predictions(nii_seg):
    # create nii object with a voxel of 0 somewhere in the middle
    nii_seg_mask = nib.nifti1.Nifti1Image(np.copy(np.asanyarray(nii_seg.dataobj)), nii_seg.affine)
    coord = (7, 7, 4)
    nii_seg_mask.dataobj[coord] = 0
    # Test function with array input
    arr_seg_proc = postproc.mask_predictions(
        np.copy(np.asanyarray(nii_seg.dataobj)), np.asanyarray(nii_seg_mask.dataobj))
    assert isinstance(arr_seg_proc, np.ndarray)
    assert arr_seg_proc[coord] == 0
    # Make sure it works with nibabel input
    nii_seg_proc = postproc.mask_predictions(nii_seg, nii_seg_mask.dataobj)
    assert isinstance(nii_seg_proc, nib.nifti1.Nifti1Image)
    assert nii_seg_proc.dataobj[coord] == 0
