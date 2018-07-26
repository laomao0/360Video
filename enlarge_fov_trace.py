#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: enlarge_fov_traces.py
# Intro: this program load the Fov tiles of each frame then enlarge the fov tiles of

# The .csv file has the following formats:
# no.frame        |  tile numbers
#    xx           |     4 5 11 12 13 19 20 21
#    xx           |     4 5 11 12 13 19 20 21
#    ...          |     ... ... ...   ...  ..

# the cooked fov trace obtain from the following data set
# "360 video viewing dataset in head-mounted virtual reality"

# author: shenwang@sjtu.edu.cn
# date: 2018/7/26


import os
import csv
TOTAL_VIDEO_CHUNKS = 120

GOP = 15

COOKED_TRACE_FOLDER = './cooked_fov_trace/'

COOKED_ENLARGED_FOV = './cooked_fov_trace/diving_user01_tile_enlarged.csv'


def main(cooked_trace_folder=COOKED_TRACE_FOLDER):
    cooked_files = os.listdir(cooked_trace_folder)
    cooked_file = cooked_files[0]
    file_path = cooked_trace_folder + cooked_file
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
    with open(COOKED_ENLARGED_FOV, 'wb') as fw_obj:
        writer = csv.writer(fw_obj)
        writer.writerow(['no.frame', 'tile_numbers'])
        for chunk_index in range(TOTAL_VIDEO_CHUNKS):
            max_frames_one_chunk = (chunk_index + 1) * GOP
            predicted_fov_pos = range(max_frames_one_chunk - GOP, max_frames_one_chunk)
            enlarged_tiles_set = []
            for frame in predicted_fov_pos:
                tiles_set_fov = all_cooked_tiles[frame]
                for tile in tiles_set_fov:
                    if tile not in enlarged_tiles_set:
                        enlarged_tiles_set.append(tile)
            for frame in predicted_fov_pos:
                write_tiles_set = []
                write_tiles_set.append(int(frame)+1)
                for tile in enlarged_tiles_set:
                    write_tiles_set.append(tile)
                writer.writerow(write_tiles_set)

    print('Task over')






if __name__ == '__main__':
    main()

