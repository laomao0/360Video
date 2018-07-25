#!/usr/bin/python
# -*- coding: UTF-8 -*-

# filename: fixed_env.py
# Intro: this program initialize the simulation environment and simulate the video chunk fetching process
# Note that in 360 video one chunk contains multiple tiles based on the Fov prediction
# when all the tiles of a chunk is downloaded the buffer length will increase

# author: shenwang@sjtu.edu.cn
# date: 2018/7/20

import numpy as np

BITS_IN_BYTE = 8.0
MILLISECONDS_IN_SECOND = 1000.0
B_IN_MB = 1000000.0
TOTAL_VIDEO_CHUNKS = 120.0
RANDOOM_SEED = 42
BITRATE_LEVELS = 5
VIDEO_CHUNK_LEN = 0.5 * MILLISECONDS_IN_SECOND  # millisec, every time add this amount to buffer

IS_ONE_CHUNK_DONE = 0  # indicated all tiles of one chunk is fetched
PACKET_PAYLOAD_PORTION = 0.95
DRAIN_BUFFER_SLEEP_TIME = 500.0  # millisec
LINK_RTT = 10  # millisec
PACKET_SIZE = 1500  # one Package has 1500 bytes
NUM_FRAMES = 1800
TOTAL_TIES = 32
GOP = 15  # gop=15 frames
FPS = 30
TILES_BIT_RATE = [200, 400, 600, 800, 1000]  # Kbps

BUFFER_THRESH = 10.0 * MILLISECONDS_IN_SECOND  # B2
BUFFER_THRESH_FOV = 2.0 * MILLISECONDS_IN_SECOND  # B1


class Environment:
    """
    This simulate the process of fetch one chunk from the dash server and the buffer information
    Notice that in 360 video, one chunk contain multiple tiles we parallel download the whole tiles of one chunk
    similar to HTTP/2
    """

    def __init__(self, all_cooked_time, all_cooked_bw, all_cooked_tiles, all_tile_chunk_video_size,
                 random_seed=RANDOOM_SEED):
        assert len(all_cooked_time) == len(all_cooked_bw)
        assert len(all_cooked_tiles) == NUM_FRAMES

        np.random.seed(random_seed)

        self.all_cooked_time = all_cooked_time
        self.all_cooked_bw = all_cooked_bw
        self.all_cooked_tiles = all_cooked_tiles

        self.video_chunk_counter = 0
        self.buffer_size = 0

        # pick a random throughput trace file
        self.bw_trace_idx = 0
        self.cooked_time = self.all_cooked_time[self.bw_trace_idx]
        self.cooked_bw = self.all_cooked_bw[self.bw_trace_idx]

        self.bw_start_ptr = 1
        # randomize the start point of the trace
        # note: bw trace file starts with time 0
        self.bw_ptr = 1
        self.last_bw_time = self.cooked_time[self.bw_ptr - 1]

        self.all_tile_chunk_video_size = all_tile_chunk_video_size

        self.virtual_bw_ptr = self.bw_ptr
        self.virtual_last_bw_time = self.last_bw_time

    def get_tile_chunk_size(self, tile_num, quality):
        """
            This function get the [index] chunk of [tile_num] tile with quality level [quality]
            quality level [0 1 2 3 4 ] refer to [200k 400k 600k 800k 1000k]
            Total index from [0~TOTAL_VIDEO_CHUNKS-1], TOTAL_VIDEO_CHUNKS chunks
            Total tile from tile_1~tile_32
        """
        all_quality_chunks = self.all_tile_chunk_video_size['tile_' + str(tile_num)]
        all_chunks = all_quality_chunks[quality]
        chunk_size = all_chunks[self.video_chunk_counter]
        return chunk_size

    # def get_video_chunk_size_only_fov(self, quality, predicted_fov_pos=''):
    #     """
    #     Function: get the chunk size (bytes)
    #     the chunk size only include the tiles in FoV, the tiles out of the Fov is not included
    #     :param predicted_fov_pos: list, indicate the predicated tiles per frames in one chunk
    #     :param quality: int, video quality level from 0~BITRATE_LEVELS-1
    #     :return: video chunk size in Bytes
    #     """
    #     # get the predicted FOV tiles of the chunk
    #     max_frames_one_chunk = (self.video_chunk_counter + 1)* GOP
    #     predicted_fov_pos = range(max_frames_one_chunk-GOP, max_frames_one_chunk)
    #     video_chunk_size = 0
    #     for frame in predicted_fov_pos:
    #         tiles_set = self.all_cooked_tiles[frame]
    #         for tile in tiles_set:
    #             tile_chunk_size = self.get_tile_chunk_size(tile, quality)
    #             tile_chunk_size_per_frame = tile_chunk_size / GOP
    #             video_chunk_size = video_chunk_size + tile_chunk_size_per_frame
    #     return video_chunk_size

    def get_video_chunk_size_quality(self, quality_in_fov, quality_out_fov=0, chunk_index=''):
        """
        Function 1: get the chunk size (bytes)
        the chunk size include the tiles in FoV and the tiles out of the Fov
        the tiles within the fov is transmitted in [quality_in_fov]
        the tiles out the fov is transmitted in default quality[0]
        Function 2: the total video quality of one chunk
        Each video chunk has GOP frames, the total chunk quality is related to fov tiles of each frame
        :param quality_in_fov: int, video quality level from 0~BITRATE_LEVELS-1
        :param chunk_index: int, chunk index
        :param quality_out_fov: int, default: lowest quality 0, if you set it with -1, it means do not transmit tiles out of fov
        :return: all_video_chunk_size in Bytes
        :return: all_video_chunk_quality in Kbps
        """
        # get the predicted FOV tiles of the chunk
        if chunk_index == '':
            chunk_index = self.video_chunk_counter
        else:
            pass
        max_frames_one_chunk = (chunk_index + 1) * GOP
        predicted_fov_pos = range(max_frames_one_chunk - GOP, max_frames_one_chunk)
        video_chunk_size_fov = 0
        video_chunk_size_out_fov = 0
        video_chunk_quality_fov_frames = 0
        for frame in predicted_fov_pos:
            tiles_set_fov = self.all_cooked_tiles[frame]
            num_tiles_set_fov = len(tiles_set_fov)
            video_chunk_quality_fov = 0
            video_chunk_quality_out_fov = 0
            for tile in tiles_set_fov:
                tile_chunk_size = self.get_tile_chunk_size(tile, quality_in_fov)
                tile_chunk_size_per_frame = tile_chunk_size / GOP
                video_chunk_size_fov = video_chunk_size_fov + tile_chunk_size_per_frame
                video_chunk_quality_fov += TILES_BIT_RATE[quality_in_fov]


            if quality_out_fov == -1:
                video_chunk_size_out_fov = 0
                video_chunk_quality_out_fov = 0
                num_tiles_set_out_fov = 0
            else:
                tiles_set_out_fov = [i for i in range(1, TOTAL_TIES + 1) if i not in tiles_set_fov]
                num_tiles_set_out_fov = len(tiles_set_out_fov)
                for tile in tiles_set_out_fov:
                    tile_chunk_size = self.get_tile_chunk_size(tile, quality_out_fov)
                    tile_chunk_size_per_frame = tile_chunk_size / GOP
                    video_chunk_size_out_fov = video_chunk_size_out_fov + tile_chunk_size_per_frame
                    video_chunk_quality_out_fov += TILES_BIT_RATE[quality_out_fov]

            video_chunk_quality_fov_frames += (video_chunk_quality_fov + video_chunk_quality_out_fov) / \
                                                (num_tiles_set_fov + num_tiles_set_out_fov)

        all_video_chunk_size = video_chunk_size_out_fov + video_chunk_size_fov
        all_video_chunk_quality = video_chunk_quality_fov_frames/GOP
        return all_video_chunk_size, all_video_chunk_quality

    def fetch_video_chunk(self, quality):
        """
        Download a chunk, which contains multiple tiles per frames
        :param quality: the quality of chunk
        :return:
        """
        assert quality >= 0
        assert quality < BITRATE_LEVELS

        print("fetch video" + str(self.video_chunk_counter))

        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=0, quality_out_fov=-1)
        # print('quality_in_fov=0, quality_out_fov=-1  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=0, quality_out_fov=0)
        # print('quality_in_fov=0, quality_out_fov=0  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=1, quality_out_fov=-1)
        # print('quality_in_fov=1, quality_out_fov=-1  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=1, quality_out_fov=0)
        # print('quality_in_fov=1, quality_out_fov=0  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=2, quality_out_fov=-1)
        # print('quality_in_fov=2, quality_out_fov=-1  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=2, quality_out_fov=0)
        # print('quality_in_fov=2, quality_out_fov=0  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=3, quality_out_fov=-1)
        # print('quality_in_fov=3, quality_out_fov=-1  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=3, quality_out_fov=0)
        # print('quality_in_fov=3, quality_out_fov=0  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=4, quality_out_fov=-1)
        # print('quality_in_fov=4, quality_out_fov=-1  '+str(video_chunk_size_fov_out_fov))
        # video_chunk_size_fov_out_fov = self.get_video_chunk_size_fov_out_fov(quality_in_fov=4, quality_out_fov=0)
        # print('quality_in_fov=4, quality_out_fov=0  '+str(video_chunk_size_fov_out_fov))

        if self.buffer_size <= BUFFER_THRESH_FOV:
            # 1 only fov tiles
            video_chunk_size, video_chunk_quality = self.get_video_chunk_size_quality(quality_in_fov=quality,
                                                                                      quality_out_fov=-1)
            # 2 fov and lowest out fov tiles
            # video_chunk_size, video_chunk_quality = self.get_video_chunk_size_fov_out_fov(quality_in_fov=quality,
            #                                                                               quality_out_fov=0)

            # lowest chunk quality use for log reward
            # 1 only fov tiles
            lowest_video_chunk_size, lowest_video_chunk_quality = self.get_video_chunk_size_quality(quality_in_fov=0,
                                                                                                  quality_out_fov=-1)
            # 2 fov and lowest out fov tiles
            # lowest_video_chunk_size, lowest_video_chunk_quality = self.get_video_chunk_size_fov_out_fov(quality_in_fov=0,
            #                                                                                           quality_out_fov=0)

            # highest chunk quality use for log reward
            # 1 only fov tiles
            highest_video_chunk_size, highest_video_chunk_quality = self.get_video_chunk_size_quality(quality_in_fov=4,
                                                                                                  quality_out_fov=-1)
            # 2 fov and lowest out fov tiles
            # highest_video_chunk_size, highest_video_chunk_quality = self.get_video_chunk_size_fov_out_fov(quality_in_fov=4,
            #                                                                                           quality_out_fov=0)
        else:
            video_chunk_size, video_chunk_quality = self.get_video_chunk_size_quality(quality_in_fov=0,
                                                                                      quality_out_fov=0)
            lowest_video_chunk_quality = video_chunk_quality
            highest_video_chunk_quality = video_chunk_quality


        delay = 0.0  # in ms
        video_chunk_counter_sent = 0  # in bytes

        while True:  # download the whole chunk according to the throughput trace
            throughput = self.cooked_bw[self.bw_ptr] \
                         * B_IN_MB / BITS_IN_BYTE  # in Byte/sec
            duration = self.cooked_time[self.bw_ptr] \
                       - self.last_bw_time

            packet_payload = throughput * duration * PACKET_PAYLOAD_PORTION

            if video_chunk_counter_sent + packet_payload > video_chunk_size:
                fractional_time = (video_chunk_size - video_chunk_counter_sent) / \
                                  throughput / PACKET_PAYLOAD_PORTION

                delay += fractional_time
                self.last_bw_time += fractional_time
                break

            video_chunk_counter_sent += packet_payload
            delay += duration
            self.last_bw_time = self.cooked_time[self.bw_ptr]
            self.bw_ptr += 1

            if self.bw_ptr >= len(self.cooked_bw):
                # loop back in the begining
                # note: trace files starts with time 0
                self.bw_ptr = 1
                self.last_bw_time = 0

        delay *= MILLISECONDS_IN_SECOND
        delay += LINK_RTT

        # rebuffer time
        rebuf = np.maximum(delay - self.buffer_size, 0.0)

        # update the buffer
        self.buffer_size = np.maximum(self.buffer_size - delay, 0.0)

        # add in the new chunk
        self.buffer_size += VIDEO_CHUNK_LEN

        # sleep if buffer gets too large
        sleep_time = 0
        if self.buffer_size > BUFFER_THRESH:
            # exceed the buffer limit
            # we need to skip some network bandwidth here
            # but do not add up the delay
            # Futher version, we use this time to update the FOV tiles
            drain_buffer_time = self.buffer_size - BUFFER_THRESH
            sleep_time = np.ceil(drain_buffer_time / DRAIN_BUFFER_SLEEP_TIME) * DRAIN_BUFFER_SLEEP_TIME
            self.buffer_size -= sleep_time

            while True:
                duration = self.cooked_time[self.bw_ptr] \
                           - self.last_bw_time
                if duration > sleep_time / MILLISECONDS_IN_SECOND:
                    self.last_bw_time += sleep_time / MILLISECONDS_IN_SECOND
                    break
                sleep_time -= duration * MILLISECONDS_IN_SECOND
                self.last_bw_time = self.cooked_time[self.bw_ptr]
                self.bw_ptr += 1

                if self.bw_ptr >= len(self.cooked_bw):
                    # loop back in the begin
                    # note: trace files starts with time 0
                    self.bw_ptr = 1
                    self.last_bw_time = 0

        # the "last buffer size" return to the controller
        # Note: in old version of dash the lowest buffer is 0.
        # In the new version the buffer always have at least
        # one chunk of video
        return_buffer_size = self.buffer_size

        self.video_chunk_counter += 1
        video_chunk_remain = TOTAL_VIDEO_CHUNKS - self.video_chunk_counter

        end_of_video = False

        if self.video_chunk_counter >= TOTAL_VIDEO_CHUNKS:
            end_of_video = True
            self.buffer_size = 0
            self.video_chunk_counter = 0

            self.bw_trace_idx += 1
            if self.bw_trace_idx >= len(self.all_cooked_time):
                self.bw_trace_idx = 0

            self.cooked_time = self.all_cooked_time[self.bw_trace_idx]
            self.cooked_bw = self.all_cooked_bw[self.bw_trace_idx]

            # randomize the start point of the video
            # note: trace file starts with time 0
            self.bw_ptr = self.bw_start_ptr
            self.last_bw_time = self.cooked_time[self.bw_ptr - 1]

        return delay, \
               sleep_time, \
               return_buffer_size / MILLISECONDS_IN_SECOND, \
               rebuf / MILLISECONDS_IN_SECOND, \
               video_chunk_size, \
               end_of_video, \
               video_chunk_remain, \
               video_chunk_quality, \
               lowest_video_chunk_quality, \
               highest_video_chunk_quality

