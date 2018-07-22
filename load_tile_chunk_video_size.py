#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: load_tile_chunk_video_size.py
# Intro: this program load each video tiles' chunk size
# return data structure is as following:
# dict{ tile_number_1 : [[quality_1 chunk size list],...,[quality_n chunk size list]],
#       tile_number_2 : [[quality_1 chunk size list],...,[quality_n chunk size list]],
#       ...
#       tile_number_m : [[quality_1 chunk size list],...,[quality_n chunk size list]]
#     }

# author: shenwang@sjtu.edu.cn
# date: 2018/7/22

import os

COOKED_TRACE_FOLDER = '.././video_size/'
FILE_PFEFIX = 'video_size_'
QUALITY = ['200k', '400k', '600k', '800k', '1000k']
QUALITY_LEVEL = 5
TILE_WIDTH = 8
TILE_HEIGTH = 4


def load_tile_chunk_video_size(cooked_trace_folder=COOKED_TRACE_FOLDER):
    all_cooked_files = os.listdir(cooked_trace_folder)
    all_tile_chunk_video_size = {}  # initialize a dict

    for num in range(QUALITY_LEVEL):
        cooked_files = [file for file in all_cooked_files if
                        file.startswith(FILE_PFEFIX) and file.endswith(QUALITY[num])]
        for cooked_file in cooked_files:
            file_path = cooked_trace_folder + cooked_file
            tile_width = int(cooked_file[12])
            tile_height = int(cooked_file[14])
            tile_num = (tile_height - 1) * TILE_WIDTH + tile_width  # relative position
            chunk_video_size = []
            # print file_path
            with open(file_path, 'r') as f_obj:
                for line in f_obj:
                    chunk_video_size.append(int(line))
            if all_tile_chunk_video_size.has_key('tile_' + str(tile_num)):
                tmp_list = all_tile_chunk_video_size['tile_' + str(tile_num)]
                tmp_list.append(chunk_video_size)
                all_tile_chunk_video_size['tile_' + str(tile_num)] = tmp_list
            else:
                all_tile_chunk_video_size['tile_' + str(tile_num)] = [chunk_video_size]

    return all_tile_chunk_video_size
