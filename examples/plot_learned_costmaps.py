#!/usr/bin/env python

# Copyright (c) 2018, University of Stuttgart
# All rights reserved.
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without   fee is hereby granted, provided   that the above  copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS  SOFTWARE INCLUDING ALL  IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR  BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR  ANY DAMAGES WHATSOEVER RESULTING  FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION,   ARISING OUT OF OR IN    CONNECTION WITH THE USE   OR
# PERFORMANCE OF THIS SOFTWARE.
#
#                                        Jim Mainprice on Sunday June 13 2018

import demos_common_imports
import tensorflow as tf
import tensorflow.contrib.layers as lays
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import sys
from pyrieef.learning.dataset import *
from skimage import transform

# works with tensotflow 1.1.0.

tf.set_random_seed(1)

# Hyper Parameters
BATCHES = 8000
BATCH_SIZE = 64
PIXELS = 28        # Used to be 100.
LR = 0.002         # learning rate
NUM_TEST_IMG = 5
DRAW = False


def lrelu(x, alpha=0.3):
    return tf.maximum(x, tf.multiply(x, alpha))


def autoencoder_cnn(X_in):

    print("---------------------------------------------")
    print("Define layers of AutoEncoder !!!")
    print("---------------------------------------------")

    dec_in_channels = 1
    n_latent = 8

    reshaped_dim = [-1, 7, 7, dec_in_channels]
    inputs_decoder = 49 * dec_in_channels / 2
    activation = lrelu
    nb_filters = 64

    # Encoder.
    X = tf.reshape(X_in, shape=[-1, 28, 28, 1])
    x = tf.layers.conv2d(
        X, filters=nb_filters, kernel_size=4, strides=2,
        padding='same', activation=activation)
    print(x.get_shape())
    x = tf.layers.conv2d(
        x, filters=nb_filters, kernel_size=4, strides=2,
        padding='same', activation=activation)
    print(x.get_shape())
    x = tf.layers.conv2d(
        x, filters=nb_filters, kernel_size=4, strides=1,
        padding='same', activation=activation)
    print(x.get_shape())
    x = tf.contrib.layers.flatten(x)
    print(x.get_shape())
    x = tf.layers.dense(x, units=n_latent)
    print(x.get_shape())

    # Decoder.
    x = tf.layers.dense(x, units=inputs_decoder * 2 + 1,
                        activation=lrelu)
    print(x.get_shape())
    x = tf.reshape(x, reshaped_dim)
    print(x.get_shape())
    x = tf.layers.conv2d_transpose(
        x, filters=nb_filters, kernel_size=4, strides=2,
        padding='same', activation=tf.nn.relu)
    print(x.get_shape())
    x = tf.layers.conv2d_transpose(
        x, filters=nb_filters, kernel_size=4, strides=1,
        padding='same', activation=tf.nn.relu)
    print(x.get_shape())
    x = tf.layers.conv2d_transpose(
        x, filters=nb_filters, kernel_size=4, strides=1,
        padding='same', activation=tf.nn.relu)
    print(x.get_shape())

    x = tf.contrib.layers.flatten(x)
    print(x.get_shape())
    x = tf.layers.dense(x, units=28 * 28, activation=tf.nn.sigmoid)
    print(x.get_shape())
    img = tf.reshape(x, shape=[-1, 28, 28])
    return img


# Costmaps
costmaps = CostmapDataset(filename='costdata2d_55k.hdf5')
costmaps.normalize_maps()
costmaps.reshape_data_to_tensors()

# plot one example
print(costmaps.train_inputs.shape)    # (55000, PIXELS * PIXELS)
print(costmaps.test_inputs.shape)     # (55000, 10)
# plt.imshow(costmaps.test_targets[0].reshape((PIXELS, PIXELS)), cmap='gray')
# plt.title('%i' % np.argmax('cost'))
# plt.show()

# sys.exit(0)

tf_x = tf.placeholder(tf.float32, (None, 28, 28))
tf_y = tf.placeholder(tf.float32, (None, 28, 28))
decoded = autoencoder_cnn(tf_x)
# loss = tf.losses.mean_squared_error(
#     labels=tf_y,
#     predictions=decoded)
loss = tf.reduce_mean(tf.square(tf_y - decoded))
train = tf.train.AdamOptimizer(LR).minimize(loss)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

# initialize figure
fig = plt.figure(figsize=(8, 4))
grid = plt.GridSpec(3, NUM_TEST_IMG, wspace=0.4, hspace=0.3)

a = [None] * 3
for i in range(3):
    a[i] = [None] * NUM_TEST_IMG
    for j in range(NUM_TEST_IMG):
        a[i][j] = fig.add_subplot(grid[i, j])
plt.ion()   # continuously plot

# original data (first row) for viewing
test_view_data_inputs = costmaps.test_inputs[:NUM_TEST_IMG]
test_view_data_targets = costmaps.test_targets[:NUM_TEST_IMG]
for i in range(NUM_TEST_IMG):
    a[0][i].imshow(test_view_data_inputs[i].reshape(28, 28))
    a[0][i].set_xticks(())
    a[0][i].set_yticks(())

    # original data (first row) for viewing
    a[1][i].imshow(test_view_data_targets[i].reshape(28, 28))
    a[1][i].set_xticks(())
    a[1][i].set_yticks(())

i = 0

train_loss_ = 0.
test_loss_ = 0.
# loss = []
for step in range(BATCHES):
    b_x, b_y = costmaps.next_batch(BATCH_SIZE)
    _, decoded_, train_loss_ = sess.run(
        [train, decoded, loss],
        feed_dict={tf_x: b_x.reshape((-1, 28, 28)),
                   tf_y: b_y.reshape((-1, 28, 28))})
    if step % 2 == 0:  # plotting
        test_loss_ = sess.run(
            loss,
            {tf_x: costmaps.test_inputs[:50].reshape((-1, 28, 28)),
             tf_y: costmaps.test_targets[:50].reshape((-1, 28, 28))})
        epoch = costmaps.epochs_completed
        infostr = str()
        infostr += 'step: {:8}, epoch: {:3}, '.format(step, epoch)
        infostr += 'train loss: {:.4f}, test loss: {:.4f}'.format(
            train_loss_, test_loss_)
        print(infostr)
        # loss.append([train_loss_, test_loss_])
        # plotting decoded image (second row)
        decoded_data = sess.run(
            decoded, {tf_x: test_view_data_inputs.reshape((-1, 28, 28))})
        # trained data
        for i in range(NUM_TEST_IMG):
            a[2][i].clear()
            a[2][i].imshow(decoded_data[i])
            a[2][i].set_xticks(())
            a[2][i].set_yticks(())
        i += 1
        plt.draw()
        plt.pause(0.01)

plt.ioff()
