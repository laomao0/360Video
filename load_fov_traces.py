#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: load_fov_traces.py
# Intro: this program load the Fov tiles of each frame

# The .csv file has the following formats:
# no.frame        |  tile numbers
#    xx           |     4 5 11 12 13 19 20 21
#    xx           |     4 5 11 12 13 19 20 21
#    ...          |     ... ... ...   ...  ..

# the cooked fov trace obtain from the following data set
# "360 video viewing dataset in head-mounted virtual reality"

# author: shenwang@sjtu.edu.cn
# date: 2018/7/20


import os
import csv

COOKED_TRACE_FOLDER = './cooked_fov_trace/'

FILE_END = '_enlarged.csv'


def load_fov_traces(cooked_trace_folder=COOKED_TRACE_FOLDER):
    cooked_files = os.listdir(cooked_trace_folder)
    cooked_file = [file for file in cooked_files if file.endswith(FILE_END)]
    file_path = cooked_trace_folder + cooked_file[0]
    with open(file_path, 'r') as f_obj:
        f_csv = csv.reader(f_obj)
        headers = next(f_csv)
        all_cooked_tiles = []
        for row in f_csv:
            cooked_frame = []
            cooked_tiles = []
            cooked_frame.append(int(row[0]))
            for tile in row[1:]:
                if tile != '':
                    cooked_tiles.append(int(tile))
            all_cooked_tiles.append(cooked_tiles)
    return all_cooked_tiles
