#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: load_throughput_trace.py
# Intro: this program load the throughput trace file
# The throughput files has the following format:
# Timestamps(sec) |  Throughput(Mbps)
#    xx           |     xx
#    xx           |     xx
#    ...          |     ...

# the cooked throughput trace is from Fcc and Hsdpa


# author: shenwang@sjtu.edu.cn
# date: 2018/7/20

import os

COOKED_TRACE_FOLDER = './cooked_bw_trace/'
FILE_PFEFIX = 'scaled_'


def load_throughput_trace(cooked_trace_folder=COOKED_TRACE_FOLDER):
    cooked_files = os.listdir(cooked_trace_folder)
    cooked_files = [file for file in cooked_files if file.startswith(FILE_PFEFIX)]
    all_cooked_time = []
    all_cooked_bw = []
    all_file_names = []
    for cooked_file in cooked_files:
        file_path = cooked_trace_folder + cooked_file
        cooked_time = []
        cooked_bw = []

        # print file_path
        with open(file_path, 'r') as f_obj:
            for line in f_obj:
                parse = line.split()
                cooked_time.append(float(parse[0]))
                cooked_bw.append(float(parse[1]))

        all_cooked_time.append(cooked_time)
        all_cooked_bw.append(cooked_bw)
        all_file_names.append(cooked_file)

    return all_cooked_time, all_cooked_bw, all_file_names