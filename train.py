#!/usr/bin/env python
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import pytest
from functools import reduce
from operator import add
import yaml
import cv2
import tensorflow as tf
import numpy as np
from tqdm import tqdm
from IPython import embed
from data import random_selection, count_files, FeatureScale, Reshape, ReLU, Sigmoid, Weights, Bias, down_sample, to_gray, Regularisation, Softmax
import config


if __name__ == '__main__':
    iterations = 10000
    w, h = 320 // config.sampling, 240 // config.sampling
    n = count_files("images/image%06d.jpg")
    n_train = n * 6 // 10
    n_validation = n * 2 // 10
    batch_size = 256
    n_div = 5
    n_out = n_div * 2 + 1
    regularize = 0.016
    sigma = 1
    alpha = 0.025
    n_hidden1 = 20
    n_hidden2 = 20
    n_hidden3 = 20
    data = np.zeros((n, h, w))
    label = np.zeros((n, 2, n_out))
    drive = np.zeros((n, 2))
    r = np.float32(np.arange(-n_div, n_div + 1) * 100.0 / n_div)
    for i in range(n):
        data[i] = down_sample(to_gray(cv2.imread("images/image%06d.jpg" % i)), config.sampling)
        drive[i] = yaml.load(open("images/image%06d.yml" % i))
        label[i, 0] = np.exp(-((drive[i, 0] - r) / 100.0 * n_div / sigma) ** 2)
        label[i, 1] = np.exp(-((drive[i, 1] - r) / 100.0 * n_div / sigma) ** 2)
    np.random.seed(0)
    data, label, drive = random_selection(n, data, label, drive)
    training = data[:n_train], label[:n_train], drive[:n_train]
    validation = data[n_train:n_train+n_validation], label[n_train:n_train+n_validation], drive[n_train:n_train+n_validation]
    testing = data[n_train+n_validation:], label[n_train+n_validation:], drive[n_train+n_validation:]
    y = tf.placeholder(tf.float32, [None, 2, n_out])

    a0 = ReLU(Reshape([-1, h * w], FeatureScale(data)))
    m1 = Weights(np.random.randn(h * w, n_hidden1) * np.sqrt(2.0 / (h * w)), a0)
    a1 = ReLU(Bias(np.zeros(n_hidden1), m1))
    m2 = Weights(np.random.randn(n_hidden1, n_hidden2) * np.sqrt(2.0 / n_hidden1), a1)
    a2 = ReLU(Bias(np.zeros(n_hidden2), m2))
    m3 = Weights(np.random.randn(n_hidden2, n_hidden3) * np.sqrt(2.0 / n_hidden2), a2)
    a3 = ReLU(Bias(np.zeros(n_hidden3), m3))
    m4 = Weights(np.random.randn(n_hidden3, 2 * n_out) * np.sqrt(1.0 / n_hidden3), a3)
    a4 = Sigmoid(Reshape([-1, 2, n_out], Bias(np.zeros(2 * n_out), m4)))
    x, h = a4.x, a4.operation
    prediction = tf.reduce_sum(r * h, axis=-1) / tf.reduce_sum(h, axis=-1)

    theta = a4.variables()
    m = tf.cast(tf.shape(x)[0], tf.float32)
    safe_log = lambda v: tf.log(tf.clip_by_value(v, 1e-10, 1.0))
    error_term = -tf.reduce_sum(y * safe_log(h) + (1 - y) * safe_log(1 - h)) / m
    cost = error_term + regularize * Regularisation(a4).operation

    optimizer = tf.train.GradientDescentOptimizer(alpha)
    step = optimizer.minimize(cost)

    train = {x: training[0], y: training[1]}
    validate = {x: validation[0], y: validation[1]}
    test = {x: testing[0], y: testing[1]}

    saver = tf.train.Saver()
    session = tf.InteractiveSession()
    session.run(tf.global_variables_initializer())
    c = 0
    progress = tqdm(range(iterations))
    for i in progress:
        selection = random_selection(batch_size, train[x], train[y])
        batch = {x: selection[0], y: selection[1]}
        c = c * (1 - 100.0 / iterations) + 100.0 / iterations * session.run(cost, feed_dict=batch)
        progress.set_description('cost: %8.6f' % c)
        session.run(step, feed_dict=batch)

    print('training error:', np.sqrt(np.average((session.run(prediction, feed_dict=train) - training[2]) ** 2)))
    print('validation error:', np.sqrt(np.average((session.run(prediction, feed_dict=validate) - validation[2]) ** 2)))
    print('test error:', np.sqrt(np.average((session.run(prediction, feed_dict=test) - testing[2]) ** 2)))
    tf.add_to_collection('prediction', prediction)
    saver.save(session, './model')
    embed()
