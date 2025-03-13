
#Author: Jawshan Ara Shatil
#Date: 03.07.2025

import os
import pandas as pd
import numpy as np
import scipy.signal as signal
import openpyxl

directory = '/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data'
#session_id = ["2022_02_09_13_40_13", "2022_06_24_11_41_06", "2022_06_24_11_49_03", "2022_06_24_14_26_28", "2022_09_15_15_25_58", "2022_09_19_11_27_04", "2022_10_06_15_51_11"]
velocity_id = [0]# , 1]
session_id = ["2022_06_24_11_41_06","2022_10_06_15_51_11"]
for i in range(len(session_id)):
    folder_name = session_id[i]
    for n in range(len(velocity_id)):
        N = str(n)
        print(N)
        filename = os.path.join(directory, f"{folder_name}_ang_vel_{N}.xlsx")
        filenameT = os.path.join(directory, f"{folder_name}_timestamp.xlsx")
        
        timestamp = pd.read_excel(filenameT)
        Time = timestamp.values[1:].flatten()
        ang_vel = pd.read_excel(filename)
        ang_vel = ang_vel.values[1:].flatten()

        acceptable_index = min(len(Time), len(ang_vel))
        Time = Time[0:acceptable_index]
        ang_vel = ang_vel[0:acceptable_index]

        if acceptable_index > 0 and len(Time) > 1:
            Time = np.array(Time)
            Fs = np.floor(acceptable_index / Time[acceptable_index - 1]).astype(int)
            print(Fs)
        else:
            print(f"Warning: Insufficient data for session {folder_name}, velocity {N}. Skipping.")
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
        #print(max_x_start)
        max_x_end = max_x_start + window_size
        #print(max_x_end)

        i_col_shake = np.where(max_absFFT_dataset > acceptable_absFFT)[0]
        first_shake_FFT_index=int(i_col_shake[0]*Fs)
        first_shake_start = Time[first_shake_FFT_index]
        first_shake_end = first_shake_start + window_size
        
        # Headshake_FFT_index=int(i_col_shake*Fs)
        # Headshake_start = Time[first_shake_FFT_index]
        # print(Headshake_start)
        # Headshake_end = first_shake_start + window_size


        # print(first_shake_start)
        # print(first_shake_end)
        
        HeadCal_Time_title = ['Session_ID', 'Angular Velocity ID', 'MaxFFT start time', 'MaxFFT end time', 'First Shake Start Time', 'First Shake End Time']
        Timestamp_save = 'First_HeadCal_time_FFTpy.xlsx'
        results_df = pd.DataFrame(columns=HeadCal_Time_title)
        HeadCal_Time = pd.DataFrame({'Session_ID': [session_id[i]], 'Angular Velocity ID': [velocity_id[n]], 'MaxFFT start time': [max_x_start], 'MaxFFT end time': [max_x_end], 'First Shake Start Time': [first_shake_start], 'First Shake End Time': [first_shake_end]})
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