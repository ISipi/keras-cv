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
import tensorflow as tf
from keras_cv.layers.preprocessing.cut_mix import CutMix


NUM_CLASSES = 10


class CutMixTest(tf.test.TestCase):
    def test_return_shapes(self):
        xs = tf.ones((2, 512, 512, 3))
        # randomly sample labels
        ys = tf.random.categorical(tf.math.log([[0.5, 0.5]]), 2)
        ys = tf.squeeze(ys)
        ys = tf.one_hot(ys, NUM_CLASSES)

        layer = CutMix(1.0, seed=1)
        xs, ys = layer(xs, ys)

        self.assertEqual(xs.shape, [2, 512, 512, 3])
        # one hot smoothed labels
        self.assertEqual(ys.shape, [2, 10])
        self.assertEqual(len(ys != 0.0), 2)

    def test_label_smoothing(self):
        xs = tf.ones((2, 512, 512, 3))
        # randomly sample labels
        ys = tf.random.categorical(tf.math.log([[0.5, 0.5]]), 2)
        ys = tf.squeeze(ys)
        ys = tf.one_hot(ys, NUM_CLASSES)

        layer = CutMix(1.0, label_smoothing=0.2, seed=1)
        xs, ys = layer(xs, ys)
        self.assertNotAllClose(ys, 0.0)

    def test_cut_mix_call_results(self):
        xs = tf.cast(
            tf.stack(
                [2 * tf.ones((4, 4, 3)), tf.ones((4, 4, 3))],
                axis=0,
            ),
            tf.float32,
        )
        ys = tf.one_hot(tf.constant([0, 1]), 2)

        layer = CutMix(1.0, label_smoothing=0.0, seed=1)
        xs, ys = layer(xs, ys)

        # At least some pixels should be replaced in the CutMix operation
        self.assertTrue(tf.math.reduce_any(xs[0] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[0] == 2.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 2.0))
        # No labels should still be close to their original values
        self.assertNotAllClose(ys, 1.0)
        self.assertNotAllClose(ys, 0.0)

    def test_cut_mix_call_results_one_channel(self):
        xs = tf.cast(
            tf.stack(
                [2 * tf.ones((4, 4, 1)), tf.ones((4, 4, 1))],
                axis=0,
            ),
            tf.float32,
        )
        ys = tf.one_hot(tf.constant([0, 1]), 2)

        layer = CutMix(1.0, label_smoothing=0.0, seed=1)
        xs, ys = layer(xs, ys)

        # At least some pixels should be replaced in the CutMix operation
        self.assertTrue(tf.math.reduce_any(xs[0] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[0] == 2.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 2.0))
        # No labels should still be close to their original values
        self.assertNotAllClose(ys, 1.0)
        self.assertNotAllClose(ys, 0.0)

    def test_in_tf_function(self):
        xs = tf.cast(
            tf.stack([2 * tf.ones((100, 100, 1)), tf.ones((100, 100, 1))], axis=0),
            tf.float32,
        )
        ys = tf.one_hot(tf.constant([0, 1]), 2)

        layer = CutMix(1.0, label_smoothing=0.0, seed=1)

        @tf.function
        def augment(x, y):
            return layer(x, y)

        xs, ys = augment(xs, ys)

        # At least some pixels should be replaced in the CutMix operation
        self.assertTrue(tf.math.reduce_any(xs[0] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[0] == 2.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 1.0))
        self.assertTrue(tf.math.reduce_any(xs[1] == 2.0))
        # No labels should still be close to their original values
        self.assertNotAllClose(ys, 1.0)
        self.assertNotAllClose(ys, 0.0)