#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Credits: Benjamin Dartigues, Emmanuel Bouilhol, Hayssam Soueidan, Macha Nikolski

import pathlib
import warnings
from unittest import TestCase

import numpy as np

import constants
import path
from image3d import Image3dWithSpotsAndMTOC
from repository import H5RepositoryWithCheckpoint

constants.init_config(analysis_config_js_path=path.test_config_path)


class TestImage3dWithSpotsAndMTOC(TestCase):

    def setUp(self) -> None:
        self.h5_sample_path = pathlib.Path(path.global_example_data, "basic.h5")
        self.repo = H5RepositoryWithCheckpoint(repo_path=self.h5_sample_path)
        self.img = Image3dWithSpotsAndMTOC(repository=self.repo, image_path="mrna/arhgdia/2h/1")

    def tearDown(self) -> None:
        self.repo.clear()

    def test_compute_cytoplasmic_density(self):
        result = self.img.compute_cytoplasmic_density()
        self.assertEqual(0.1284945413733293, result)

    def test_compute_density_per_quadrant(self):
        quadrant_mask = self.img.compute_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_density_per_quadrant(mtoc_quad, quadrant_mask)

        self.assertEqual(result.shape, (4, 2))
        self.assertAlmostEqual(result[1, 0], 0.13705567289739, places=3)
        self.assertAlmostEqual(result[:, 0].sum(), 0.5481894332973, places=3)
        self.assertEqual(result[:, 1].sum(), 1.0)

    def test_compute_peripheral_density_per_quadrant(self):
        quadrant_mask = self.img.compute_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_peripheral_density_per_quadrant(mtoc_quad, quadrant_mask)

        self.assertEqual(result.shape, (4, 2))
        self.assertAlmostEqual(result[1, 0], 0.0392974514788, places=3)
        self.assertAlmostEqual(result[:, 0].sum(), 0.3030269392, places=3)
        self.assertEqual(result[:, 1].sum(), 1.0)

    def test_compute_quadrant_densities(self):
        result1 = self.img.compute_quadrant_densities()
        self.assertAlmostEqual(result1[:, 0].sum(), 0.529914777)
        self.assertEqual(result1[3, 1], 1)
        result2 = self.img.compute_quadrant_densities(peripheral_flag=True)
        self.assertAlmostEqual(result2[:, 0].sum(), 0.367422972834)
        self.assertEqual(result2[2, 1], 1) # notice the MTOC quadrant is not the same as before!
        result3 = self.img.compute_quadrant_densities(peripheral_flag=False, stripes=3, stripes_flag=True)
        self.assertAlmostEqual(result3[:, 0].sum(), 1.49816018641)
        self.assertEqual(result3[4, 1], 1)
        result4 = self.img.compute_quadrant_densities(peripheral_flag=True, stripes=3, stripes_flag=True)
        self.assertAlmostEqual(result4[:, 0].sum(), 0.6460654268)
        self.assertEqual(result4[4, 1], 1)

    def test_compute_density_per_quadrant_and_slices(self):
        quadrant_mask = self.img.compute_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_density_per_quadrant_and_slices(mtoc_quad, quadrant_mask, stripes=3, quadrants_num=4)
        self.assertAlmostEqual(result[:,0].sum(), 1.54750719241)
        self.assertAlmostEqual(result[:,1].sum(), 3)
        self.assertAlmostEqual(result[3,0], 0.059481909)

    def test_compute_peripheral_density_per_quadrant_and_slices(self):
        quadrant_mask = self.img.compute_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_peripheral_density_per_quadrant_and_slices(mtoc_quad, quadrant_mask, stripes=3, quadrants_num=4)
        self.assertAlmostEqual(result[:,0].sum(), 0.637391943)
        self.assertAlmostEqual(result[7,0], 0.104579207920)
