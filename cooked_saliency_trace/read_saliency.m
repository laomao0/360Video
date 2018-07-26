clc
close all

global Width_tile
global Height_tile
global W_frame
global H_frame
global num_w
global num_h

video_name = 'diving_saliency.mp4';
otuput_name = 'diving_saliency'
fov_file_name = 'C:\Users\Wangshen\Desktop\video\src\360Video\cooked_fov_trace\diving_user01_tile_enlarged.csv';
obj = VideoReader(video_name)
num_frames = obj.NumberOfFrames;
disp(['frame number: ', num2str(num_frames)])

% read the fov tile information
divinguser01tile = importfile(fov_file_name, 2, 1801);

% function: get the saliency value of one frame image
Width_tile = 480;
Height_tile = 480;
W_frame = 3840;
H_frame = 1920;
num_w = W_frame / Width_tile;
num_h = H_frame / Height_tile;

% read all frames
% pixel value 0:    - the dark pixel, represent the not interesting pixel
% pixel value 255:  - the white pixel, represent the most interesting pixel
fid = fopen(otuput_name,'wb');

for tile_frame = 1:1:num_frames
    frame = read(obj,tile_frame);
    frame = rgb2gray(frame);
    if tile_frame == 400
        imshow(frame);
    end
    tile_num_set = divinguser01tile(tile_frame,:);
    z = find(~isnan(tile_num_set));
    z_len = length(z);
    tile_num_set = tile_num_set(z(1,2:1:z_len));
    tile_num_set_len = length(tile_num_set);
    all_saliency_frame = [];
    all_tile_num = [];
    for tile = 1:1:tile_num_set_len
        [tile_num, saliency_frame] = compute_one_tile_saliency(tile_num_set(tile), frame);
        all_saliency_frame = [all_saliency_frame, saliency_frame];
        all_tile_num = [all_tile_num, tile_num];
    end
    all_saliency_frame_sum = sum(all_saliency_frame);
    all_saliency_frame = all_saliency_frame ./ all_saliency_frame_sum;
    fprintf(fid, '%d ', tile_frame);
    fprintf(fid, '%0.5f ', all_saliency_frame);
    fprintf(fid, '\n');
    
    
end

fclose(fid);
    



function [tile_num, saliency_frame] = compute_one_tile_saliency(tile_num, frame_array)
    global Width_tile
    global Height_tile
    global W_frame
    global H_frame
    global num_w
    global num_h
    w_t = rem(tile_num -1, num_w) + 1;
    h_t = (tile_num - w_t) / num_w + 1; 
    w_list = (w_t*Width_tile - Width_tile + 1):1:w_t*Width_tile;
    h_list = (h_t*Height_tile - Height_tile +1):1:h_t*Height_tile;   
    tile_array = frame_array(h_list, w_list);
    saliency_frame = sum(sum(tile_array));
end





