##!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : Feb 25, 2020
# @Author  : Le Zhang
# @Email   : lezhangisu@gmail.com
# @FileName: filters.py

import numpy as np

class RangeFilter(object):
    """Range Filter for LIDAR sensor data.

    It crops the data array so that all the data below RANGE_MIN
    will be replaced by RANGE_MIN; data value greater than RANGE_MAX
    will be replaced by RANGE_MAX.

    Attributes:
        RANGE_MIN: A number indicating the lower bound of data range.
        RANGE_MAX: A number indicating the upper bound of data range.
    """
    def __init__(self, range_min = 0.03, range_max = 50.0):
        """Inits RangeFilter with min and max range."""
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
        # Return filtered data
        return np.clip(data_input, self.RANGE_MIN, self.RANGE_MAX).tolist()


class TempMedianFilter(object):
    """Temporal Median Filter for LIDAR sensor data.

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
        self.data_array = np.array([])
        print("New Temporal Median Filter created with D = {}".format(self.D))

    def update(self, data_input):
        """Applies temporal median filter to input data"""
        if self.data_array.shape[0] > 0:    # if data pool not empty
            if self.data_array.shape[1] > self.D:   # if exceeds the max pool size
                # delete oldest data (column)
                self.data_array = np.delete(self.data_array, 0, 1)
            # add newest data (column)
            self.data_array = np.column_stack((self.data_array, np.array(data_input)))
        else:       # if data pool empty
            # initialize array with input data
            self.data_array = np.array([[di] for di in data_input])
        # return temporal median list
        return [np.median(self.data_array[i]) for i in range(self.data_array.shape[0])]
