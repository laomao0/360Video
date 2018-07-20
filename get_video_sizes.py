#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename：get_video_sizes.py
# Intro: this program get the size of each tiles(20x10 tiles), and consider each tiles is the
# same duration of GOP length = 15*1/30=0.5 second
# It save the chunked video size of each tiles into different files

# author: shenwang@sjtu.edu.cn
# date: 2018/7/20

import os

TOTAL_VIDEO_CHUNK = 120
ET_BITRATE_LEVELS = 5
VIDEO_PATH = '../../diving_video/'


def main():
    all_tiles_dirs = os.listdir(VIDEO_PATH)

    # for different tiles
    for tile_dir in all_tiles_dirs:
        tile_dir_path = VIDEO_PATH + tile_dir
        tile_path_bit_levels_dir = os.listdir(tile_dir_path)
        for tile_path_bit_level in tile_path_bit_levels_dir:
            with open('video_size_' + tile_path_bit_level[6:-4], 'w') as f_obj:
                tile_path_bit_level_chunk_path = tile_dir_path + '/' + tile_path_bit_level
                total_chunk_size = os.path.getsize(tile_path_bit_level_chunk_path)
                chunk_size = total_chunk_size / TOTAL_VIDEO_CHUNK
                for chunk_num in range(TOTAL_VIDEO_CHUNK):
                    f_obj.write(str(chunk_size) + '\n')


if __name__ == '__main__':
    main()
