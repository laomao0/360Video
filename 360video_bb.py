#!/usr/bin/python
# -*- coding: UTF-8 -*-

# file name: 360videompc.py
# Intro:this program simulate the ABR -buffer based method for 360 video


# author: shenwang@sjtu.edu.cn
# date: 2018/7/20

import numpy as np
import load_fov_traces
import load_throughput_trace
import load_tile_chunk_video_size
import fixed_env as env
import matplotlib.pyplot as plt
import itertools

S_INFO = 5  # bitr_ate, buffer_size, rebuffering_time, bandwidth_measurement, chunk_til_video_end
S_LEN = 8  # take how many frames in the past to predict the next chunk
PAST_FRAME = 15  # take how many frames in the past to predict the next chunk fov tiles
TILES_BIT_RATE = [200, 400, 600, 800, 1000]  # Kbps
A_DIM = 5
MPC_FUTURE_CHUNK_COUNT = 4
MILLISECONDS_IN_SECOND = 1000.0
PAST_BW_TO_PREDICT = 5
BUFFER_NORM_FACTOR = 1.0
CHUNK_TIL_VIDEO_END_CAP = 120.0
TOTAL_VIDEO_CHUNKS = 120
M_IN_K = 1000.0

DEFAULT_QUALITY = 1  # default quality
RANDOOM_SEED = 42
RAND_RANGE = 1000000
GOP = 15  # gop=15 frames

VIDEO_CHUNK_LEN = 0.5  # sec
BUFFER_THRESH = 10.0   # B2
BUFFER_THRESH_FOV = 2.0  # B1

REBUF_PENALTY = 20.0
SMOOTH_PENALTY = 1.0

RESEVOIR = 0.2 # sec
CUSHION = BUFFER_THRESH_FOV - 2*RESEVOIR # sec



SUMMARY_DIR = './results'
LOG_FILE = './results/log_sim_bb'

CHUNK_COMBO_OPTIONS = []

# past errors in bandwidth
past_errors = []
past_bandwidth_ests = []


def main():
    np.random.seed(RANDOOM_SEED)

    assert len(TILES_BIT_RATE) == A_DIM
    assert 2 * RESEVOIR + CUSHION == BUFFER_THRESH_FOV

    all_cooked_time, all_cooked_bw, all_file_names = load_throughput_trace.load_throughput_trace()
    all_cooked_tiles = load_fov_traces.load_fov_traces()
    all_tile_chunk_video_size = load_tile_chunk_video_size.load_tile_chunk_video_size()

    net_env = env.Environment(all_cooked_time=all_cooked_time,
                              all_cooked_bw=all_cooked_bw,
                              all_cooked_tiles=all_cooked_tiles,
                              all_tile_chunk_video_size=all_tile_chunk_video_size)

    log_path = LOG_FILE + '_' + all_file_names[net_env.bw_trace_idx]
    log_file = open(log_path, 'wb')

    time_stamp = 0
    last_bit_rate = DEFAULT_QUALITY
    bit_rate = DEFAULT_QUALITY

    r_batch = []

    video_count = 0

    while True:  # serve video forever
        # the action is from the last decision
        if net_env.video_chunk_counter == 0:
            print(all_file_names[net_env.bw_trace_idx])

        delay, sleep_time, buffer_size, rebuf, \
            video_chunk_size, \
            end_of_video, video_chunk_remain, \
            video_chunk_quality, \
            basic_video_chunk_quality, \
            highest_video_chunk_quality = \
            net_env.fetch_video_chunk(bit_rate)

        time_stamp += delay  # ms
        time_stamp += sleep_time  # in ms

        # initialize the last_video chunk quality
        if (net_env.video_chunk_counter == 1):
            last_video_chunk_quality = video_chunk_quality

        # reward is video quality - rebuffer_penalty
        reward = video_chunk_quality / M_IN_K \
                 - REBUF_PENALTY * rebuf \
                 - SMOOTH_PENALTY * np.abs(last_video_chunk_quality -
                                           video_chunk_quality) / M_IN_K

        # log scale reward
        # log_chunk_quality = np.log(video_chunk_quality / float(basic_video_chunk_quality))
        # log_last_chunk_quality = np.log(last_video_chunk_quality / float(basic_video_chunk_quality))
        # reward = log_chunk_quality \
        #             - REBUF_PENALTY * rebuf \
        #             - SMOOTH_PENALTY * np.abs( log_chunk_quality - log_last_chunk_quality)

        r_batch.append(reward)
        last_video_chunk_quality = video_chunk_quality

        # log time_stamp, video_chunk_quality, buffer_size, reward
        log_file.write(str(time_stamp / M_IN_K) + '\t' +  # unit: sec
                       str(video_chunk_quality) + '\t' +  # unit: Kbps
                       str(buffer_size) + '\t' +          # unit: sec
                       str(rebuf) + '\t' +                # unit: sec
                       str(video_chunk_size) + '\t' +     # unit: Bytes
                       str(delay) + '\t' +                # unit: ms
                       str(reward) + '\n')

        log_file.flush()

        #==============================================BB=========================================
        if buffer_size < RESEVOIR:
            bit_rate = 0
        elif (buffer_size >= RESEVOIR + CUSHION) and (buffer_size < BUFFER_THRESH_FOV):
            bit_rate = A_DIM - 1
        elif (buffer_size >= RESEVOIR) and (buffer_size < BUFFER_THRESH_FOV):
            bit_rate = (A_DIM - 1) * (buffer_size - RESEVOIR) / float(CUSHION)
        else:
            bit_rate = 0


        bit_rate = int(np.ceil(bit_rate))





        # ============================================BB end======================================



        if end_of_video:
            log_file.write('\n')
            log_file.close()

            last_bit_rate = DEFAULT_QUALITY
            bit_rate = DEFAULT_QUALITY  # use the default action here

            r_batch = []

            print("trace count"+str(video_count))
            video_count += 1

            if video_count >= len(all_file_names):
                break

            log_path = LOG_FILE + '_' + all_file_names[net_env.bw_trace_idx]
            log_file = open(log_path, 'wb')

















if __name__ == '__main__':
    main()
