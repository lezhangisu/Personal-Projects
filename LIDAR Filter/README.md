
<!-- Documentation for LIDAR filters -->
## LIDAR Filters

### 1. Backgrounds

The python library of LIDAR filters consists of two filters:

#### 1.1 Range Filter  

It crops all the values that are below range_min (resp. above range_max), and replaces them with the range_min value (resp. range_max).

#### 1.2 Temporal Median Filter

It returns the median of the current and the previous D scans.

If we have a temporal median filter with D = 3 and data dimension N = 5, the inputs and outputs should be:

| T(time) | X(input scan)              | Y(return of the update)   |
|---------|----------------------------|---------------------------|
| 0       | [0.0, 1.0, 2.0, 1.0, 3.0]  | [0.0, 1.0, 2.0, 1.0, 3.0] |
| 1       | [1.0, 5.0, 7.0, 1.0, 3.0]  | [0.5, 3.0, 4.5, 1.0, 3.0] |
| 2       | [2.0, 3.0, 4.0, 1.0, 0.0]  | [1.0, 3.0, 4.0, 1.0, 3.0] |
| 3       | [3.0, 3.0, 3.0, 1.0, 3.0]  | [1.5, 3.0, 3.5, 1.0, 3.0] |
| 4       | [10.0, 2.0, 4.0, 0.0, 0.0] | [2.5, 3.0, 4.0, 1.0, 1.5] |
| 5       | [5.0, 9.0, 6.0, 1.0, 7.0]  | [4.0, 3.0, 4.0, 1.0, 1.5] |


### 2. How to Use

First, to use filters, filter classes need to be imported:

```python
from filters import RangeFilter, TemporalMedianFilter
...
```

Upon initialization, if no parameters are given, a Range Filter will be created with default range of [0.03, 50.0].

```python
range_filter = RangeFilter()
```

A Range Filter can also be initiated with specific range:

```python
# range filter with range [3.0, 100.5]
range_filter = RangeFilter(3.0, 100.5)
```

A parameter D is required once a Temporal Median Filter is created:

```python
# a temporal median filter with D = 4
temp_med_filter = TemporalMedianFilter(4)
```

update() method in each filter class takes in a fixed length array of float numbers and returns a same-length array of float numbers as result:

```python
range_filter = RangeFilter(3.0, 10.0)
print(range_filter.update([0.0, 2.0, 4.0, 16.0, 8.0]))
"""expected output:
$ [3.0, 3.0, 4.0, 10.0, 8.0]
"""

temp_med_filter = TemporalMedianFilter(3)
temp_med_filter.update([0.0, 1.0, 2.0, 1.0, 3.0])
temp_med_filter.update([1.0, 5.0, 7.0, 1.0, 3.0])
temp_med_filter.update([2.0, 3.0, 4.0, 1.0, 0.0])
temp_med_filter.update([3.0, 3.0, 3.0, 1.0, 3.0])
print(temp_med_filter.update([10.0, 2.0, 4.0, 0.0, 0.0]))
"""expected output:
$ [2.5, 3.0, 4.0, 1.0, 1.5]
"""
```

### 3. Test

#### 3.1 Overview

Test cases are written in **tester.py**. Two test cases are created for each filter class: test_init() and test_filter().

test_init() tests the initializations of the filter instances.
test_filter() tests the results correctness of the filter.

Numpy library was used in RangeFilter and TemporalMedianFilter classes, two xxFilterTester classes are implemented without using Numpy and serving as control group data generators.

First, the test_filter() initializes instances for both Filter class and FilterTester classes. Then, it generates 500 fixed-length float arrays with randomly generated data. Finally, it feed those data into Filter and FilterTester classes to make sure they return exactly same outputs for each same input.

#### 3.2 How to use

A simple way of using tester:

```
$ python tester.py
```

Number of tests for each test case is set to 500 by default. Lower and upper bound for range filter tests are set to [-5.0, 60.0].

A successful test result looks like:

```
...
New Temporal Median Filter created with D = 821
New Temporal Median Filter created with D = 666
New Temporal Median Filter created with D = 764
.
-------------------------------------------------
Ran 4 tests in 2.569s
OK
```
