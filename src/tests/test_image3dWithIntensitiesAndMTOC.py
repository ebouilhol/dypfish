#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Credits: Benjamin Dartigues, Emmanuel Bouilhol, Hayssam Soueidan, Macha Nikolski


import pathlib
from unittest import TestCase
import numpy as np
import warnings
import constants
import path
from repository import H5RepositoryWithCheckpoint
from image3d import Image3dWithIntensitiesAndMTOC

constants.init_config(analysis_config_js_path=path.test_config_path)


class TestImage3dWithIntensitiesAndMTOC(TestCase):
    def setUp(self) -> None:
        self.h5_sample_path = pathlib.Path(path.global_example_data, "basic.h5")
        self.repo = H5RepositoryWithCheckpoint(repo_path=self.h5_sample_path)
        self.img = Image3dWithIntensitiesAndMTOC(repository=self.repo, image_path="protein/arhgdia/2h/1")

    def tearDown(self) -> None:
        self.repo.clear()

    def test_compute_cytoplasmic_density(self):
        result = self.img.compute_cytoplasmic_density()
        self.assertAlmostEqual(result, 1759171.4466687627)

    def test_compute_density_per_quadrant(self):
        quadrant_mask = self.img.rotate_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_density_per_quadrant(mtoc_quad, quadrant_mask)

        self.assertEqual(result.shape, (4, 2))
        self.assertAlmostEqual(result[1, 0], 2161612.773054066, places=3)
        self.assertEqual(result[:, 1].sum(), 1.0)

    def test_compute_peripheral_density_per_quadrant(self):
        quadrant_mask = self.img.rotate_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_peripheral_density_per_quadrant(mtoc_quad, quadrant_mask)

        self.assertEqual(result.shape, (4, 2))
        self.assertAlmostEqual(result[1, 0], 3519770.290827437, places=3)
        self.assertAlmostEqual(result[:, 0].sum(), 21936379.835062217, places=3)
        self.assertEqual(result[:, 1].sum(), 1.0)

    def test_compute_quadrant_densities(self):
        result = self.img.compute_quadrant_densities()
        self.assertAlmostEqual(result[:, 0].sum(), 9058203.036892714, places=3)
        self.assertEqual(result[2, 1], 1)

    def test_compute_density_per_quadrant_and_slices(self):
        quadrant_mask = self.img.rotate_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_density_per_quadrant_and_slices(mtoc_quad, quadrant_mask, stripes=3, quadrants_num=4)
        self.assertAlmostEqual(result[:,0].sum(), 35743106.157463335, places=3)
        self.assertAlmostEqual(result[3,0], 9870531.478862531)
        self.assertEqual(result[:, 1].sum(), 3)

    def test_compute_peripheral_density_per_quadrant_and_slices(self):
        quadrant_mask = self.img.rotate_quadrant_mask(45, 4)
        mtoc_position = self.img.get_mtoc_position()
        mtoc_quad = quadrant_mask[mtoc_position[1], mtoc_position[0]]
        result = self.img.compute_peripheral_density_per_quadrant_and_slices(mtoc_quad, quadrant_mask, stripes=3, quadrants_num=4)
        self.assertAlmostEqual(result.sum(), 80097725.51824857, places=3)
        self.assertAlmostEqual(result[7,0], 10437447.769777933, places=3)