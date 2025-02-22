from __future__ import annotations
import typing

from torchvision.transforms import Compose

from ivadomed.loader.bids_dataset import BidsDataset
from ivadomed.loader.mri3d_subvolume_segmentation_dataset import MRI3DSubVolumeSegmentationDataset
from ivadomed.keywords import ModelParamsKW

if typing.TYPE_CHECKING:
    from typing import List, Optional
    from ivadomed.loader.bids_dataframe import BidsDataframe


class Bids3DDataset(MRI3DSubVolumeSegmentationDataset):
    """BIDS specific dataset loader for 3D dataset.

    Args:
        bids_df (BidsDataframe): Object containing dataframe with all BIDS image files and their metadata.
        subject_file_lst (list): Subject filenames list.
        target_suffix (list): List of suffixes for target masks.
        model_params (dict): Dictionary containing model parameters.
        contrast_params (dict): Contains image contrasts related parameters.
        slice_axis (int): Indicates the axis used to extract slices: "axial": 2, "sagittal": 0, "coronal": 1.
        cache (bool): If the data should be cached in memory or not.
        transform (list): Transformation list (length 2) composed of preprocessing transforms (Compose) and transforms
            to apply during training (Compose).
        metadata_choice: Choice between "mri_params", "contrasts", None or False, related to FiLM.
        roi_params (dict): Dictionary containing parameters related to ROI image processing.
        multichannel (bool): If True, the input contrasts are combined as input channels for the model. Otherwise, each
            contrast is processed individually (ie different sample / tensor).
        object_detection_params (dict): Object dection parameters.
        is_input_dropout (bool): Return input with missing modalities.
    """

    def __init__(self,
                 bids_df: BidsDataframe,
                 subject_file_lst: List[str],
                 target_suffix: List[str],
                 model_params: dict,
                 contrast_params: dict,
                 slice_axis: int = 2,
                 cache: bool = True,
                 transform: List[Optional[Compose]] = None,
                 metadata_choice: str | bool = False,
                 roi_params: dict = None,
                 multichannel: bool = False,
                 object_detection_params: dict = None,
                 task: str = "segmentation",
                 soft_gt: bool = False,
                 is_input_dropout: bool = False):

        dataset = BidsDataset(bids_df=bids_df,
                              subject_file_lst=subject_file_lst,
                              target_suffix=target_suffix,
                              roi_params=roi_params,
                              contrast_params=contrast_params,
                              model_params=model_params,
                              metadata_choice=metadata_choice,
                              slice_axis=slice_axis,
                              transform=transform,
                              multichannel=multichannel,
                              object_detection_params=object_detection_params,
                              is_input_dropout=is_input_dropout)

        super().__init__(dataset.filename_pairs,
                         length=model_params[ModelParamsKW.LENGTH_3D],
                         stride=model_params[ModelParamsKW.STRIDE_3D],
                         transform=transform,
                         slice_axis=slice_axis,
                         task=task,
                         soft_gt=soft_gt,
                         is_input_dropout=is_input_dropout)
