#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
from distutils.version import LooseVersion
import logging

import nibabel as nib
import numpy as np

if LooseVersion(nib.__version__) < LooseVersion('2.1.0'):
    raise ImportError("Unable to import the Nibabel streamline API. "
                      "Nibabel >= v2.1.0 is required")

from scilpy.io.utils import (
    add_overwrite_arg, assert_inputs_exist, assert_outputs_exists)
from scilpy.tractometry.distance_to_centroid import min_dist_to_centroid

logging.basicConfig()
logger = logging.getLogger(__file__)


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description='Compute assignment map from bundle and centroid '
                    'streamline. This script can be very memory hungry on '
                    'large fiber bundle.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bundle', help='Fiber bundle file')
    parser.add_argument(
        'centroid_streamline',
        help='Centroid streamline associated to input fiber bundle')
    parser.add_argument(
        'output_label',
        help='Output (.npz) file containing the label of the nearest point '
             'on the centroid streamline for each point of the bundle')
    parser.add_argument(
        'output_distance',
        help='Output (.npz) file containing the distance (in mm) to the '
             'nearest centroid streamline for each point of the bundle')
    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.bundle, args.centroid_streamline])
    assert_outputs_exists(
        parser, args, [args.output_label, args.output_distance])

    bundle_tractogram = nib.streamlines.load(args.bundle)
    bundle_streamlines = bundle_tractogram.streamlines

    centroid_tractogram = nib.streamlines.load(args.centroid_streamline)
    centroid_streamline = centroid_tractogram.streamlines

    nb_bundle_points = bundle_streamlines.total_nb_rows
    if nb_bundle_points == 0:
        logger.warning('Empty bundle file {}. Skipping'.format(args.bundle))
        return

    nb_centroid_points = centroid_streamline.total_nb_rows
    if nb_centroid_points == 0:
        logger.warning('Empty centroid streamline file {}. Skipping'
                       .format(args.centroid_streamline))
        return

    min_dist_label, min_dist = min_dist_to_centroid(bundle_streamlines.data,
                                                    centroid_streamline.data)
    min_dist_label += 1

    # Save assignment in a compressed numpy file
    # You can load this file and access its data using
    # f = np.load('someFile.npz')
    # assignment = f['arr_0']
    np.savez_compressed(args.output_label, min_dist_label)

    # Save distance in a compressed numpy file
    # You can load this file and access its data using
    # f = np.load('someFile.npz')
    # distance = f['arr_0']
    np.savez_compressed(args.output_distance, min_dist)


if __name__ == '__main__':
    main()
