#!/usr/bin/python
# -*- coding: UTF-8 -*-

# file name: 360videompc.py
# Intro: this program simulate the tiled 360 video streaming using MPC ABR algorithm
# When current buffer occupancy <= B1(fov prediction limitation), we transmit only the tiles within fov,
# WHen current buffer occupancr > B1 and < B2, we transmit the whole lowest quality tiles

# Modification in this version
# use video saliency to save bandwidth

# author: shenwang@sjtu.edu.cn
# date: 2018/7/25

import numpy as np
import load_fov_traces
import load_throughput_trace
import load_tile_chunk_video_size
import load_saliency_trace
import saliency_env as env
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
BW_RATIO = 1

DEFAULT_QUALITY = 1  # default quality
RANDOOM_SEED = 42
RAND_RANGE = 1000000
GOP = 15  # gop=15 frames
VIDEO_CHUNK_LEN = 0.5  # sec
BUFFER_THRESH = 10.0 * MILLISECONDS_IN_SECOND  # B2
BUFFER_THRESH_FOV = 2.0 * MILLISECONDS_IN_SECOND # B1

REBUF_PENALTY = 20.0
SMOOTH_PENALTY = 1.0

SUMMARY_DIR = './results'
LOG_FILE = './results/log_sim_saliency_mpc'

CHUNK_COMBO_OPTIONS = []

# past errors in bandwidth
past_errors = []
past_bandwidth_ests = []


def main():
    np.random.seed(RANDOOM_SEED)

    assert len(TILES_BIT_RATE) == A_DIM

    all_cooked_time, all_cooked_bw, all_file_names = load_throughput_trace.load_throughput_trace()
    all_cooked_tiles = load_fov_traces.load_fov_traces()
    all_cooked_saliency = load_saliency_trace.load_saliency_trace()
    all_tile_chunk_video_size = load_tile_chunk_video_size.load_tile_chunk_video_size()

    net_env = env.Environment(all_cooked_time=all_cooked_time,
                              all_cooked_bw=all_cooked_bw,
                              all_cooked_tiles=all_cooked_tiles,
                              all_tile_chunk_video_size=all_tile_chunk_video_size,
                              all_cooked_saliency=all_cooked_saliency)

    log_path = LOG_FILE + '_' + all_file_names[net_env.bw_trace_idx]
    log_file = open(log_path, 'wb')

    time_stamp = 0
    #last_bit_rate = DEFAULT_QUALITY
    #bit_rate = DEFAULT_QUALITY

    # get the first frame saliency
    # then set the default bitrate set for each tiles
    first_frame_fov_tiles_saliency = all_cooked_saliency[0]
    num_first_frame_fov_tiles_saliency = len(first_frame_fov_tiles_saliency)
    bit_rate_set = np.zeros((1,num_first_frame_fov_tiles_saliency))
    last_bit_rate_set = bit_rate_set


    s_batch = [np.zeros((S_INFO, S_LEN))]

    video_count = 0


    while True:  # serve video forever
        # the action is from the last decision
        if net_env.video_chunk_counter == 0:
            print(all_file_names[net_env.bw_trace_idx])

        if net_env.buffer_size <= BUFFER_THRESH_FOV:
            delay, sleep_time, buffer_size, rebuf, \
            video_chunk_size, \
            end_of_video, video_chunk_remain, \
            video_chunk_quality = \
                net_env.fetch_video_chunk(quality_in_fov=bit_rate_set,
                                          quality_out_fov=0)

            time_stamp += delay  # ms
            time_stamp += sleep_time  # in ms

            # initialize the last_video chunk quality
            if (net_env.video_chunk_counter == 1):
                last_video_chunk_quality = video_chunk_quality



            # reward is video quality - rebuffer_penalty (download reward)
            # then start playback, viewer has the following QoE
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


            last_video_chunk_quality = video_chunk_quality

            # log time_stamp, video_chunk_quality, buffer_size, reward
            log_file.write(str(time_stamp / M_IN_K) + '\t' +  # unit: sec
                           str(video_chunk_quality) + '\t' +  # unit: Kbps
                           str(buffer_size) + '\t' +  # unit: sec
                           str(rebuf) + '\t' +  # unit: sec
                           str(video_chunk_size) + '\t' +  # unit: Bytes
                           str(delay) + '\t' +  # unit: ms
                           str(reward) + '\n')

            log_file.flush()

            len_bit_rate_set = len(net_env.all_cooked_tiles[net_env.video_chunk_counter * GOP])
            bit_rate_set = np.zeros((1,len_bit_rate_set))

        else:
            # buffer size larger than B1, we first update then continue to download
            future_bandwidth_for_update = BW_RATIO * future_bandwidth / abs(BUFFER_THRESH - buffer_size)
            future_bandwidth_for_download = future_bandwidth - future_bandwidth_for_update

            buffer_to_update = net_env.buffer[1:]


            # # future chunks length
            # last_index = int(CHUNK_TIL_VIDEO_END_CAP - video_chunk_remain - 1)
            #
            # future_chunk_length = MPC_FUTURE_CHUNK_COUNT
            #
            # # if future chunk num less than PAST_BW_TO_PREDICT
            # if TOTAL_VIDEO_CHUNKS - 1 - last_index < MPC_FUTURE_CHUNK_COUNT:
            #     future_chunk_length = int(TOTAL_VIDEO_CHUNKS - last_index -1)
            #
            # # all possible combinations of MPC_FUTURE_CHUNK_COUNT chunk video qualitys
            # # iterate over list and for each, compute reward and store max reward combination
            # # make chunk combination options
            # # this combo is used for future optimization
            # # for combo in itertools.product(list(range(MPC_FUTURE_CHUNK_COUNT + 1)), repeat=MPC_FUTURE_CHUNK_COUNT):
            # #    CHUNK_COMBO_OPTIONS.append(combo)
            # #    # print(combo)
            # max_reward = -100000000
            # best_combo = ()
            # start_buffer = buffer_size
            # for full_combo in CHUNK_COMBO_OPTIONS:
            #     combo = full_combo[0:future_chunk_length]
            #     curr_rebuffer_time = 0
            #     curr_buffer = start_buffer
            #     quality_sum = 0
            #     smoothness_diffs = 0
            #     last_quality = video_chunk_quality
            #     for position in range(0, len(combo)):
            #         chunk_quality = combo[position]
            #         index = last_index + position + 1
            #
            #         # decide all LT or only FoV
            #         if curr_buffer <= BUFFER_THRESH_FOV:
            #             curr_video_chunk_size, curr_video_chunk_quality = net_env.get_video_chunk_size_quality(
            #                 quality_in_fov=chunk_quality, quality_out_fov=-1, chunk_index=index)
            #         else:
            #             curr_video_chunk_size, curr_video_chunk_quality = net_env.get_video_chunk_size_quality(
            #                 quality_in_fov=0, quality_out_fov=0, chunk_index=index)
            #
            #         download_time = (curr_video_chunk_size/1000000.0) / future_bandwidth
            #         if curr_buffer < download_time:
            #             curr_rebuffer_time += (download_time - curr_buffer)
            #             curr_buffer = 0
            #         else:
            #             curr_buffer -= download_time
            #
            #         curr_buffer += VIDEO_CHUNK_LEN
            #         quality_sum += curr_video_chunk_quality
            #         smoothness_diffs += abs(curr_video_chunk_quality - last_quality)
            #         last_quality = curr_video_chunk_quality
            #
            #     reward = quality_sum/1000.0 \
            #              - REBUF_PENALTY * curr_rebuffer_time \
            #              - SMOOTH_PENALTY * smoothness_diffs / 1000.0
            #
            #     if reward >= max_reward:
            #         if best_combo != () and best_combo[0] < combo[0]:
            #             best_combo = combo
            #         else:
            #             best_combo = combo
            #         max_reward = reward
            #
            #         send_data = 0
            #         if best_combo != ():
            #             send_data = best_combo[0]




        # retrieve previous state
        if len(s_batch) == 0:
            state = [np.zeros((S_INFO, S_LEN))]
        else:
            state = np.array(s_batch[-1], copy=True)

        # dequeue history record
        state = np.roll(state, -1, axis=1)  # each row left-shift one
        # this should be S_INFO number of terms
        state[0, -1] = video_chunk_quality  # last quality
        state[1, -1] = buffer_size / BUFFER_NORM_FACTOR
        state[2, -1] = rebuf
        state[3, -1] = float(video_chunk_size) / float(delay) / M_IN_K  # Mbyte/s
        state[4, -1] = np.minimum(video_chunk_remain, CHUNK_TIL_VIDEO_END_CAP) / float(CHUNK_TIL_VIDEO_END_CAP)

        # ===================================BW predictin ===================================================
        curr_error = 0  # default assumes that this is the first request so error is 0 since we have never predicted bandwidth
        if (len(past_bandwidth_ests) > 0):
            curr_error = abs(past_bandwidth_ests[-1] - state[3, -1]) / float(state[3, -1])
        past_errors.append(curr_error)

        # pick bitrate according to MPC
        # first get harmonic mean of last n bandwidths
        past_bandwidths = state[3, -PAST_BW_TO_PREDICT:]
        # cut the meaning throughput
        while past_bandwidths[0] == 0.0:
            past_bandwidths = past_bandwidths[1:]

        bandwidth_sum = 0
        for past_val in past_bandwidths:
            bandwidth_sum += (1 / float(past_val))
        harmonic_bandwidth = 1.0 / (bandwidth_sum / len(past_bandwidths))

        # future bandwidth prediction
        # divide by (1+max)  of last PAST_BW_TO_PREDICT
        max_error = 0
        error_pos = -PAST_BW_TO_PREDICT
        if (len(past_errors) < PAST_BW_TO_PREDICT):
            error_pos = -len(past_errors)
        max_error = float(max(past_errors[error_pos:]))
        future_bandwidth = harmonic_bandwidth / (1 + max_error)  # robustMPC here
        past_bandwidth_ests.append(harmonic_bandwidth)

        s_batch.append(state)



        if end_of_video:
            log_file.write('\n')
            log_file.close()

            last_bit_rate = DEFAULT_QUALITY
            bit_rate = DEFAULT_QUALITY  # use the default action here

            del s_batch[:]
            #del a_batch[:]

            action_vec = np.zeros(A_DIM)
            action_vec[bit_rate] = 1

            s_batch.append(np.zeros((S_INFO, S_LEN)))
            #a_batch.append(action_vec)
            entropy_record = []

            print("trace count"+str(video_count))
            video_count += 1

            if video_count >= len(all_file_names):
                break

            log_path = LOG_FILE + '_' + all_file_names[net_env.bw_trace_idx]
            log_file = open(log_path, 'wb')

















if __name__ == '__main__':
    main()
