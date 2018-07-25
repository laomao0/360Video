#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: load_saliency.py
# Intro: this program load the Fov tiles's saliency of each frame

# The file has the following formats:
# no.frame        |     tiles salience
#    xx           |     0.1 0.2 0.3 0.4 0.5 0.6
#    xx           |     0.1 0.2 0.3 0.4 0.5 0.6
#    ...          |     ... ... ...   ...  ..

# the cooked fov saliency trace obtain from the following data set
# "360 video viewing dataset in head-mounted virtual reality"

# author: shenwang@sjtu.edu.cn
# date: 2018/7/25


import os

COOKED_TRACE_FOLDER = './cooked_saliency_trace/'
FILE_PREFIX = 'diving_'


def load_saliency_trace(cooked_trace_folder=COOKED_TRACE_FOLDER):
    cooked_files = os.listdir(cooked_trace_folder)
    cooked_file = [file for file in cooked_files if file.startswith(FILE_PREFIX)]
    cooked_file = cooked_file[0]
    file_path = cooked_trace_folder + cooked_file
    with open(file_path, 'r') as f_obj:
        all_cooked_tiles = []
        for row in f_obj:
            cooked_frame = []
            cooked_tiles = []
            spare = row.split()
            cooked_frame.append(int(spare[0]))
            #print(int(spare[0]))
            for tile in spare[1:]:
                if tile != '\n':
                    cooked_tiles.append(float(tile))
            all_cooked_tiles.append(cooked_tiles)
    return all_cooked_tiles
