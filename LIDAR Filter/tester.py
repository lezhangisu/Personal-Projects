##!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : Feb 26, 2020
# @Author  : Le Zhang
# @Email   : lezhangisu@gmail.com
# @FileName: tester.py

import unittest
import random
import sys
from filters import RangeFilter, TempMedianFilter

TEST_ROUNDS = 500
UP_BOUND = 60.0
LOW_BOUND = -5.0

class RangeFilterTester(object):
    """Range Filter for LIDAR sensor data

    This is an implementation without Numpy library for testing purposes.

    It crops the data array so that all the data below RANGE_MIN
    will be replaced by RANGE_MIN; data value greater than RANGE_MAX
    will be replaced by RANGE_MAX.

    Attributes:
        data: A list for data storage
        RANGE_MIN: A number indicating the lower bound of data range.
        RANGE_MAX: A number indicating the upper bound of data range.
    """

    def __init__(self, range_min = 0.03, range_max = 50.0):
        """Inits RangeFilter with min and max range."""
        self.data = []
        if range_min < range_max:
            self.RANGE_MIN = float(range_min)
            self.RANGE_MAX = float(range_max)
        else:
            self.RANGE_MIN = 0.03
            self.RANGE_MAX = 50.0
            print("Invalid input range [{}, {}], default range applied.".format(range_min, range_max))
        print("New Range Filter created with range [{}, {}]".format(self.RANGE_MIN, self.RANGE_MAX))

    def update(self, data_input):
        """Performs range filter with input data"""
        self.data = map(float, data_input)
        for i in range(len(self.data)):
            # for each data element, adjust if value out of bound
            if self.data[i] < self.RANGE_MIN:
                self.data[i] = self.RANGE_MIN
            elif self.data[i] > self.RANGE_MAX:
                self.data[i] = self.RANGE_MAX
        # return filtered data
        return self.data


def median(input_list):
    """Computes median for a given input array."""
    n = len(input_list)
    # map numbers to float and sort list
    sorted_list = map(float, sorted(input_list))

    if n % 2 == 0:  # if list length is an even number
        med = (sorted_list[n // 2] + sorted_list[n // 2 - 1]) / 2
    else:  # if list length is an odd number
        med = sorted_list[n // 2]
    return med


class TempMedianFilterTester(object):
    """Temporal Median Filter for LIDAR sensor data.

    This is an implementation without Numpy library for testing purposes.

    It computes median for current data inputs and D previous data.
    update() method returns an array with all the median numbers.

    Attributes:
        D: An integer indicating the maximum temporal size of data array.
        data_array: A numpy array with the data of current and previous D scans.
    """
    def __init__(self, d):
        """Inits TempMedianFilter with pool size D."""
        if d < 0:
            print("Invalid input D = {}, default value applied.".format(d))
            d = 0
        self.D = int(d)
        self.data_array = []
        print("New Temporal Median Filter created with D = {}".format(self.D))

    def update(self, data_input):
        """Applies temporal median filter to input data"""
        if len(self.data_array) > 0:    # if data array not empty
            # add newest data (column)
            self.data_array = [ (self.data_array[i] + [data_input[i]])[-self.D - 1:] for i in range(len(data_input))]
        else:       # if empty data array
            # initialize array with input data
            self.data_array = [[di] for di in data_input]
        # return the temporal median list
        return [median(di) for di in self.data_array]


def float_array_gen(length, min, max):
    return [random.uniform(min, max) for _ in range(length)]


class TestRF(unittest.TestCase):
    """Unit test class for Range Filter."""
    def test_init(self):
        """Tests initialization of Range Filter."""
        print("**** Range Filter initialization test begins ****")
        for _ in range(TEST_ROUNDS):
            # generates random ranges with value low and high
            low = random.uniform(0.0, 20.0)
            high = random.uniform(40.0, 80.0)
            # initialize range filter
            rf_init = RangeFilter(low, high)
            # test if range_min equals the value of low
            self.assertEquals(rf_init.RANGE_MIN, low)
            # test if range_max equals the value of high
            self.assertEquals(rf_init.RANGE_MAX, high)
            # test if instance equals the target instance
            self.assertTrue(isinstance(rf_init, RangeFilter))

    def test_filter(self):
        """Tests update() method of Range Filter."""
        """Each test contains TEST_ROUNDS (500 by default) rounds"""
        print("**** Range Filter update() test begins ****")
        # initialize range filter and test filter
        rf = RangeFilter()
        rft = RangeFilterTester()
        # initialize data dimension
        dim = random.randint(200, 1000)
        for _ in range(TEST_ROUNDS):
            # generates array with random float within certain range
            # typically the testing range should be larger than default range
            arr = float_array_gen(dim, LOW_BOUND, UP_BOUND)
            # test if results from filter and tester filter are equal
            self.assertEquals(rf.update(arr), rft.update(arr))
        print("**** {} rounds of tests done ****".format(TEST_ROUNDS))


class TestTMF(unittest.TestCase):
    """Unit test class for Temporal Median Filter."""
    def test_init(self):
        """Tests initialization of Temporal Median Filter."""
        print("**** Temporal Median Filter initialization test begins ****")
        for _ in range(TEST_ROUNDS):
            # generates random int as pool size
            rnd = random.randint(0, 900)
            # initialize temporal median filter
            tf_init = TempMedianFilter(rnd)
            # test if pool size set as expected
            self.assertEquals(tf_init.D, rnd)
            # test if instance equals the target instance
            self.assertTrue(isinstance(tf_init, TempMedianFilter))

    def test_filter(self):
        """Tests update() method of Temporal Median Filter."""
        """Each test contains TEST_ROUNDS (500 by default) rounds"""
        print("**** Temporal Median Filter update() test begins ****")
        # create new filter and test filter with same pool size
        tmf = TempMedianFilter(5)
        tmft = TempMedianFilterTester(5)
        # initialize data dimension
        dim = random.randint(200, 1000)
        for _ in range(TEST_ROUNDS):
            # generates array with random float within certain range
            # default data range used
            arr = float_array_gen(dim, 0.03, 50.0)
            # test if results from filter and tester filter are equal
            self.assertEquals(tmf.update(arr), tmft.update(arr))
        print("**** {} rounds of tests done ****".format(TEST_ROUNDS))


if __name__ == '__main__':
    unittest.main()
