#!/usr/bin/env python

import SimpleITK as sitk
import argparse
from ivadomed import utils as imed_utils

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, type=str,
                        help="""Input image path.""",
                        metavar=imed_utils.Metavar.str)
    parser.add_argument("-n", "--n-iterations", dest="n_iterations",
                        type=int, help="Number of iterations to run.",
                        metavar=imed_utils.Metavar.int)
    parser.add_argument("-nf", "--n-fitting_level", dest="n_fitting_level",
                        type=int, help="Number of fitting level.",
                        metavar=imed_utils.Metavar.int)
    parser.add_argument("--shrink_factor", required=False, type=str,
                        help="""shrink factor.""",
                        metavar=imed_utils.Metavar.float)
    parser.add_argument("--mask_image", required=False, type=str,
                        help="""mask image.""",
                        metavar=imed_utils.Metavar.str)
    parser.add_argument("-o", "--output", required=True, type=str,
                        help="Output image path.", metavar=imed_utils.Metavar.str)
    return parser


def main(args=None):
    """

    n4 correction algorithm copied from https://simpleitk.readthedocs.io/en/master/link_N4BiasFieldCorrection_docs.html

    """
    imed_utils.init_ivadomed()
    parser = get_parser()
    args = imed_utils.get_arguments(parser, args)

    input_image = sitk.ReadImage(args.input)

    if args.mask_image:
        mask_image = sitk.ReadImage(args.mask_image, sitk.sitkUint8)
    else:
        mask_image = sitk.OtsuThreshold(input_image, 0, 1, 200)

    if args.shrink_factor:
        input_image = sitk.Shrink(input_image,
                            [args.shrink_factor] * input_image.GetDimension())
        mask_image = sitk.Shrink(mask_image,
                                 [args.shrink_factor] * input_image.GetDimension())

    input_image = sitk.Cast(input_image, sitk.sitkFloat32)

    corrector = sitk.N4BiasFieldCorrectionImageFilter()

    number_fitting_levels = 4

    if args.n_fitting_level:
        number_fitting_levels = args.n_fitting_level

    if args.n_iterations:
        corrector.SetMaximumNumberOfIterations([args.n_iterations]
                                               * number_fitting_levels)

    output = corrector.Execute(input_image, mask_image)

    sitk.WriteImage(output, args.output)


if __name__ == '__main__':
    main()
