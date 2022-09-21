# Copyright 2022 The KerasCV Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import tensorflow as tf
from absl.testing import parameterized

from keras_cv import ops


class Boxes3DTestCase(tf.test.TestCase, parameterized.TestCase):
    def test_convert_center_to_corners(self):
        boxes = tf.constant(
            [
                [[1, 2, 3, 4, 3, 6, 0], [1, 2, 3, 4, 3, 6, 0]],
                [[1, 2, 3, 4, 3, 6, np.pi / 2.0], [1, 2, 3, 4, 3, 6, np.pi / 2.0]],
            ]
        )
        corners = ops._center_xyzWHD_to_corner_xyz(boxes)
        self.assertEqual((2, 2, 8, 3), corners.shape)
        for i in [0, 1]:
            self.assertAllClose(-1, np.min(corners[0, i, :, 0]))
            self.assertAllClose(3, np.max(corners[0, i, :, 0]))
            self.assertAllClose(0.5, np.min(corners[0, i, :, 1]))
            self.assertAllClose(3.5, np.max(corners[0, i, :, 1]))
            self.assertAllClose(0, np.min(corners[0, i, :, 2]))
            self.assertAllClose(6, np.max(corners[0, i, :, 2]))

        for i in [0, 1]:
            self.assertAllClose(-0.5, np.min(corners[1, i, :, 0]))
            self.assertAllClose(2.5, np.max(corners[1, i, :, 0]))
            self.assertAllClose(0.0, np.min(corners[1, i, :, 1]))
            self.assertAllClose(4.0, np.max(corners[1, i, :, 1]))
            self.assertAllClose(0, np.min(corners[1, i, :, 2]))
            self.assertAllClose(6, np.max(corners[1, i, :, 2]))

    def test_within_box2d(self):
        boxes = tf.constant(
            [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]], dtype=tf.float32
        )
        points = tf.constant(
            [
                [-0.5, -0.5],
                [0.5, -0.5],
                [1.5, -0.5],
                [1.5, 0.5],
                [1.5, 1.5],
                [0.5, 1.5],
                [-0.5, 1.5],
                [-0.5, 0.5],
                [1.0, 1.0],
                [0.5, 0.5],
            ],
            dtype=tf.float32,
        )
        is_inside = ops.is_within_box2d(points, boxes)
        expected = [[False]] * 8 + [[True]] * 2
        self.assertAllEqual(expected, is_inside)

    def test_within_zero_box2d(self):
        bbox = tf.constant(
            [[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]], dtype=tf.float32
        )
        points = tf.constant(
            [
                [-0.5, -0.5],
                [0.5, -0.5],
                [1.5, -0.5],
                [1.5, 0.5],
                [1.5, 1.5],
                [0.5, 1.5],
                [-0.5, 1.5],
                [-0.5, 0.5],
                [1.0, 1.0],
                [0.5, 0.5],
            ],
            dtype=tf.float32,
        )
        is_inside = ops.is_within_box2d(points, bbox)
        expected = [[False]] * 10
        self.assertAllEqual(expected, is_inside)

    def test_is_on_lefthand_side(self):
        v1 = tf.constant([[0.0, 0.0]], dtype=tf.float32)
        v2 = tf.constant([[1.0, 0.0]], dtype=tf.float32)
        p = tf.constant([[0.5, 0.5], [-1.0, -3], [-1.0, 1.0]], dtype=tf.float32)
        res = ops._is_on_lefthand_side(p, v1, v2)
        self.assertAllEqual([[True, False, True]], res)
        res = ops._is_on_lefthand_side(v1, v1, v2)
        self.assertAllEqual([[True]], res)
        res = ops._is_on_lefthand_side(v2, v1, v2)
        self.assertAllEqual([[True]], res)

    @parameterized.named_parameters(
        ("without_rotation", 0.0),
        ("with_rotation_1_rad", 1.0),
        ("with_rotation_2_rad", 2.0),
        ("with_rotation_3_rad", 3.0),
    )
    def test_box_area(self, angle):
        boxes = tf.constant(
            [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
                [[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [0.0, 1.0]],
                [[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]],
            ],
            dtype=tf.float32,
        )
        expected = [[1.0], [2.0], [4.0]]

        def _rotate(bbox, theta):
            rotation_matrix = tf.reshape(
                [tf.cos(theta), -tf.sin(theta), tf.sin(theta), tf.cos(theta)],
                shape=(2, 2),
            )
            return tf.matmul(bbox, rotation_matrix)

        rotated_bboxes = _rotate(boxes, angle)
        res = ops._box_area(rotated_bboxes)
        self.assertAllClose(expected, res)

    def test_within_box3d(self):
        num_points, num_boxes = 19, 4
        # rotate the first box by pi / 2 so dim_x and dim_y are swapped.
        # The last box is a cube rotated by 45 degrees.
        bboxes = tf.constant(
            [
                [1.0, 2.0, 3.0, 6.0, 0.4, 6.0, np.pi / 2],
                [4.0, 5.0, 6.0, 7.0, 0.8, 7.0, 0.0],
                [0.4, 0.3, 0.2, 0.1, 0.1, 0.2, 0.0],
                [-10.0, -10.0, -10.0, 3.0, 3.0, 3.0, np.pi / 4],
            ],
            dtype=tf.float32,
        )
        points = tf.constant(
            [
                [1.0, 2.0, 3.0],  # box 0 (centroid)
                [0.8, 2.0, 3.0],  # box 0 (below x)
                [1.1, 2.0, 3.0],  # box 0 (above x)
                [1.3, 2.0, 3.0],  # box 0 (too far x)
                [0.7, 2.0, 3.0],  # box 0 (too far x)
                [4.0, 5.0, 6.0],  # box 1 (centroid)
                [4.0, 4.6, 6.0],  # box 1 (below y)
                [4.0, 5.4, 6.0],  # box 1 (above y)
                [4.0, 4.5, 6.0],  # box 1 (too far y)
                [4.0, 5.5, 6.0],  # box 1 (too far y)
                [0.4, 0.3, 0.2],  # box 2 (centroid)
                [0.4, 0.3, 0.1],  # box 2 (below z)
                [0.4, 0.3, 0.3],  # box 2 (above z)
                [0.4, 0.3, 0.0],  # box 2 (too far z)
                [0.4, 0.3, 0.4],  # box 2 (too far z)
                [5.0, 7.0, 8.0],  # none
                [1.0, 5.0, 3.6],  # box0, box1
                [-11.6, -10.0, -10.0],  # box3 (rotated corner point).
                [-11.4, -11.4, -10.0],  # not in box3, would be if not rotated.
            ],
            dtype=tf.float32,
        )
        expected_is_inside = np.array(
            [
                [True, False, False, False],
                [True, False, False, False],
                [True, False, False, False],
                [False, False, False, False],
                [False, False, False, False],
                [False, True, False, False],
                [False, True, False, False],
                [False, True, False, False],
                [False, False, False, False],
                [False, False, False, False],
                [False, False, True, False],
                [False, False, True, False],
                [False, False, True, False],
                [False, False, False, False],
                [False, False, False, False],
                [False, False, False, False],
                [True, True, False, False],
                [False, False, False, True],
                [False, False, False, False],
            ]
        )
        assert points.shape[0] == num_points
        assert bboxes.shape[0] == num_boxes
        assert expected_is_inside.shape[0] == num_points
        assert expected_is_inside.shape[1] == num_boxes
        is_inside = ops.is_within_box3d(points, bboxes)
        self.assertAllEqual([num_points, num_boxes], is_inside.shape)
        self.assertAllEqual(expected_is_inside, is_inside)
        # Add a batch dimension to the data and see that it still works
        # as expected.
        batch_size = 3
        points = tf.tile(points[tf.newaxis, ...], [batch_size, 1, 1])
        bboxes = tf.tile(bboxes[tf.newaxis, ...], [batch_size, 1, 1])
        is_inside = ops.is_within_box3d(points, bboxes)
        self.assertAllEqual([batch_size, num_points, num_boxes], is_inside.shape)
        for batch_idx in range(batch_size):
            self.assertAllEqual(expected_is_inside, is_inside[batch_idx])