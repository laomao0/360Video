#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: plot.cooked_log_bandwidth.py
# Intro: this program plot the cooked throughput trace file
# The throughput files has the following format:
# Timestamps(sec) |  Throughput(Mbps)
#    xx           |     xx
#    xx           |     xx
#    ...          |     ...


# author: shenwang@sjtu.edu.cn
# date: 2018/7/20

import numpy as np
import os
import matplotlib.pyplot as plt

FILE_PATH = './'
BITS_IN_BYTE = 8.0
MBITS_IN_BITS = 1000000.0
MILLISECONDS_IN_SECONDS = 1000.0
PACKET_SIZE = 1500.0 # bytes
FILE_PFEFIX = 'scaled_norway_'

all_files = os.listdir(FILE_PATH)
files = [file for file in all_files if file.startswith(FILE_PFEFIX)]


for file in files:

    bandwidth_all = []
    time_all = []
    with open(FILE_PATH+file, 'rb') as f_obj:
        for line in f_obj:
            parse = line.split()
            time = float(parse[0])
            throughput = float(parse[1])
            time_all.append(time)
            bandwidth_all.append(throughput)

    bandwidth_all = np.array(bandwidth_all)
    time_all = np.array(time_all)

    plt.plot(time_all, bandwidth_all)
    plt.xlabel('Time (second)')
    plt.ylabel('Throughput (Mbit/sec)')
    plt.title(file)
    plt.show()
