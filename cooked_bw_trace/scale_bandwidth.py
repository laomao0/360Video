#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: scale_bandwidth.py
# Intro: this program scale the cooked throughput trace file
# The throughput files has the following format:
# Timestamps(sec) |  Throughput(Mbps)
#    xx           |     xx
#    xx           |     xx
#    ...          |     ...


# author: shenwang@sjtu.edu.cn
# date: 2018/7/21

import numpy as np
import matplotlib.pyplot as plt
import os

FILE_PATH = './'
BITS_IN_BYTE = 8.0
MBITS_IN_BITS = 1000000.0
MILLISECONDS_IN_SECONDS = 1000.0
PACKET_SIZE = 1500.0 # bytes
MEAN_BW = 6  # scaled mean bw 6 Mbps


trace_files = os.listdir(FILE_PATH)
trace_files = [file for file in trace_files if file.startswith('norway')]

for file in trace_files:
    bandwidth_all = []
    time_all = []
    with open(FILE_PATH + file, 'rb') as f_obj:
        for line in f_obj:
            parse = line.split()
            time = float(parse[0])
            throughput = float(parse[1])
            time_all.append(time)
            bandwidth_all.append(throughput)

    bandwidth_all = np.array(bandwidth_all)
    time_all = np.array(time_all)
    mean_bw = np.mean(bandwidth_all)
    scale = MEAN_BW / mean_bw

    scaled_bandwidth_all = bandwidth_all * scale

    # plt.plot(time_all, scaled_bandwidth_all)
    # plt.xlabel('Time (second)')
    # plt.ylabel('Throughput (Mbit/sec) Mean:{}'.format(str(mean_bw)[0:2]))
    # plt.show()
    with open(FILE_PATH + 'scaled_' + file, 'wb') as fw_obj:
        for i in range(scaled_bandwidth_all.size):
            fw_obj.write(str(time_all[i]) + ' ' + str(scaled_bandwidth_all[i]) +'\n')











