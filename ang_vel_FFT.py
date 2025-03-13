#Author: Jawshan Ara Shatil
#Date: 03.07.2025

import sys
from ast import parse
import numpy as np
import msgpack
import scipy.signal as signal
from scipy.fft import fft
from scipy.signal.windows import hann
from scipy.signal import resample
import openpyxl

#The two graphing packages
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import os
from io import BytesIO
from pathlib import Path

## folder path setting
current_directory = os.getcwd()
## change directory
new_directory = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data"  # Replace with the actual path
os.chdir(new_directory)
user_input = input("Enter Folder name: ")       
session_id = user_input
file_name= "eye0.pldata"
folder_path = Path.cwd() / session_id

new_directory = folder_path
try:
    os.chdir(new_directory)
    print(f"Current working directory after change: {os.getcwd()}")
except FileNotFoundError:
    print(f"Error: Directory not found: {new_directory}")
except NotADirectoryError:
    print(f"Error: Not a directory: {new_directory}")
except PermissionError:
    print(f"Error: Permission denied: {new_directory}")
except Exception as e:
    print(f"An error occurred: {e}")

## file path setting    
file_path=folder_path/file_name

#Opens the file, extracts the data
def read_pldata(file_path):
    try:
        with open(file_path, 'rb') as file:
            unpacker = msgpack.Unpacker(file, raw=False)
            data = []
            for packet in unpacker:
                data.append(packet)
    except OSError:
        print(f'File path: "{file_path}" not found.')
        print(f"Current working directory: {os.getcwd()}")
        raise OSError
    return data

## Flattens the data, makes it readable, output is column sorted
def parse_pldata(data):
    unpacker = msgpack.Unpacker(BytesIO(data), raw=False)
    parsed_data = next(unpacker)

    # flatten nested structures
    flattened = {}
    for key, value in parsed_data.items():
        if isinstance(value, list):
            for i, item in enumerate(value):
                flattened[f"{key}_{i}"] = item
        else:
            flattened[key] = value

    return flattened

def FFT_function(data, x_start, x_end, Fs):
    segment = data[x_start:x_end]
    x = np.arange(len(segment))
    L = len(x)
    samp_rate = Fs

    window_fft = np.fft.fft(segment)
    # Single-sided FFT, amplitude of the real value
    P2 = np.abs(window_fft / L)
    P1 = P2[:L // 2 + 1]
    P1[1:-1] = 2 * P1[1:-1]

    absFFT = P1
    return absFFT

# Generates static graphs for display in the visualizer
def generate_graphs(filename_list: list[str]):
    # assuming either 1. both files exist, 2. neither file exists
    global graph_file_list
    for filename in filename_list:
        print(filename)
        data = read_pldata(filename)
        df = pd.DataFrame(data)
        
        angular_velocity_0_list = []
        angular_velocity_1_list = []
        angular_velocity_2_list = []

        timestamp_list = []
        first_timestamp = parse_pldata(df[1].iloc[0])['timestamp']
        last_timestamp = parse_pldata(df[1].iloc[(len(df[1])-1)])['timestamp']
        
        
        for i in range(len(df[1])):
            data_frame = parse_pldata(df[1].iloc[i])
            data_type_4 = 'angular_velocity_0'
            data_type_5 = 'angular_velocity_1'
            data_type_6 = 'angular_velocity_2'
            
            angular_velocity_0_list.append(data_frame[data_type_4])
            angular_velocity_1_list.append(data_frame[data_type_5])
            angular_velocity_2_list.append(data_frame[data_type_6])
            
            # list of time stamp from world camera
            timestamp_list.append(data_frame['timestamp'] - first_timestamp)
            # list of recording datapoint
            
        timelist = [float(i) for i in timestamp_list]
        Time = timelist[1:]
        #print(len(Time))
        ang_vel0 = angular_velocity_0_list[1:]
        #print(len(ang_vel0))
        ang_vel1 = angular_velocity_1_list[1:]
        #print(len(ang_vel1))
        
        velocity_id=[0,1]
        #session_id = ["2022_10_06_15_51_11"]
        for n in range(len(velocity_id)):
            N = str(n)
            ang_filename = f"{session_id}_ang_vel_{N}"
            print(ang_filename)
            if n==0:
                ang_vel = ang_vel0
                print(len(ang_vel))
            else:
                ang_vel = ang_vel1
                print(len(ang_vel))
            

            acceptable_index = min(len(Time), len(ang_vel))
            #print(acceptable_index)
            Time = Time[0:acceptable_index]
            ang_vel = ang_vel[0:acceptable_index]

            if acceptable_index > 0 and len(Time) > 1:
                Time = np.array(Time)
                Fs = np.floor(acceptable_index / Time[acceptable_index - 1]).astype(int)
                print(Fs)
            else:
                print(f"Warning: Insufficient data for session {session_id}, velocity {N}. Skipping.")
                continue

            # FFT for angular velocity
            window_size = 5
            sliding_width = 1
            counter = np.floor((len(ang_vel) - (window_size * Fs)) / (sliding_width * Fs)).astype(int) + 1
            dataset_absFFT = []

            for k in range(counter):
                start_index = int(k * sliding_width * Fs)
                end_index = int(start_index + window_size * Fs)
                if end_index > len(ang_vel):
                    end_index = len(ang_vel)
                segment = ang_vel[start_index:end_index]
                frequencies, FFT = signal.welch(segment, fs=Fs, nperseg=len(segment))
                absFFT=np.abs(FFT)
                dataset_absFFT.append(absFFT)

            dataset_absFFT = np.array(dataset_absFFT)
            max_absFFT_dataset = np.max(dataset_absFFT, axis=1)
            max_All = np.max(max_absFFT_dataset)
            print(max_All)
            acceptable_absFFT = (max_All * 2) / 3
            print(acceptable_absFFT)

            i_col_max = np.where(max_absFFT_dataset == max_All)
            maxFFT_index=int(i_col_max[0]*Fs)
            #print(maxFFT_index)
            max_x_start = Time[maxFFT_index]
            print(max_x_start)
            max_x_end = max_x_start + window_size

            i_col_shake = np.where(max_absFFT_dataset > acceptable_absFFT)[0]
            first_shake_FFT_index=int(i_col_shake[0]*Fs)
            first_shake_start = Time[first_shake_FFT_index]
            print(first_shake_start)
            first_shake_end = first_shake_start + window_size
            
            # Headshake_FFT_index=int(i_col_shake*Fs)
            # Headshake_start = Time[first_shake_FFT_index]
            # print(Headshake_start)
            # Headshake_end = first_shake_start + window_size

            
            
            new_directory = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/VEDB"  # Replace with the actual path
            os.chdir(new_directory)
            #user_input = input("Enter Folder name: ")       
            #session_id = user_input
            #file_name= "eye0.pldata"
            folder_path = Path.cwd()

            new_directory = folder_path

            
            
            Timestamp_save = 'Max_HeadCal_time_FFTpy.xlsx'
            #HeadCal_Time_title = ['Session_ID', 'Angular Velocity ID', 'MaxFFT start time', 'MaxFFT end time', 'First Shake Start Time', 'First Shake End Time']
            HeadCal_Time_title = ['Session_ID', 'Angular Velocity ID', 'MaxFFT start time','MaxFFT']#, 'MaxFFT end time', 'First Shake Start Time', 'First Shake End Time']
            
            results_df = pd.DataFrame(columns=HeadCal_Time_title)
            #HeadCal_Time = pd.DataFrame({'Session_ID': [session_id], 'Angular Velocity ID': [velocity_id[n]], 'MaxFFT start time': [max_x_start], 'MaxFFT end time': [max_x_end], 'First Shake Start Time': [first_shake_start], 'First Shake End Time': [first_shake_end]})
            HeadCal_Time = pd.DataFrame({'Session_ID': [session_id], 'Angular Velocity ID': [velocity_id[n]], 'MaxFFT start time': [max_x_start], 'MaxFFT': [max_All]})#, 'MaxFFT end time': [max_x_end], 'First Shake Start Time': [first_shake_start], 'First Shake End Time': [first_shake_end]})
            
            results_df = pd.concat([results_df, HeadCal_Time], ignore_index=True)

        
            try:
                    # Check if the file exists and append the new data
                    with pd.ExcelWriter(Timestamp_save, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                        results_df.to_excel(writer, sheet_name='Results', header=False, index=False, startrow=writer.sheets['Results'].max_row)
                        print(f"Data appended to '{Timestamp_save}' successfully.")

            except FileNotFoundError:
                # If the file doesn't exist, create it and write the header
                results_df.to_excel(Timestamp_save, sheet_name='Results', index=False)
                print(f"New file '{Timestamp_save}' created and data written successfully.")
            
        
        
        
        
def main():
    filelist = ['eye0.pldata', 'eye1.pldata', 'odometry.pldata']
    for file in filelist:
        if not os.path.exists(file):
            filelist.remove(file)

    data0 = read_pldata('eye0.pldata')
    data1 = read_pldata('eye1.pldata')
    dataod = read_pldata('odometry.pldata')

    df0 = pd.DataFrame(data0)
    df1= pd.DataFrame(data1)
    dfod = pd.DataFrame(dataod)


    filelist.clear()
    arr = df0[1].iloc[2]
    np.set_printoptions(threshold=sys.maxsize)
    #print(arr)
    filelist = ['odometry.pldata']
    generate_graphs(filelist)
    

main()