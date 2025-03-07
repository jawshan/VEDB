#Author: Jawshan Ara Shatil
#Date: 03.06.2025

import pandas as pd
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import os
import openpyxl


directory = '/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data'
session_id = ["2022_02_09_13_40_13", "2022_06_24_11_41_06", "2022_06_24_11_49_03", "2022_06_24_14_26_28", "2022_09_15_15_25_58", "2022_09_19_11_27_04", "2022_10_06_15_51_11"]
velocity_id = [0 , 1]

for session_index in range(len(session_id)):
    folder_name = session_id[session_index]
    for velocity_index in range(len(velocity_id)):
        x = str(velocity_index)
        Ang_file_path = os.path.join(directory, f"{folder_name}_ang_vel_{x}.xlsx")
        Time_file_path = os.path.join(directory, f"{folder_name}_timestamp.xlsx")

        try:
            timestamp = pd.read_excel(Time_file_path)
            ang_vel = pd.read_excel(Ang_file_path)

            # Create a Pandas DataFrame to store the results for the current session
            results_df = pd.DataFrame({
                'Session_id': [session_id[session_index]],
                'Angular_velocity_id': [velocity_id[velocity_index]],
                'First Start Time': [first_start_time],
                'First End Time': [first_end_time]
            })
        except FileNotFoundError:
            print(f"Error: One or both files not found for session {folder_name}, velocity {x}")
        except Exception as e:
            print(f"An error occurred during processing for session {folder_name}, velocity {x}: {e}")

        Time = timestamp.values[1:].flatten()
        len_ang_vel = len(ang_vel)
        len_Time = len(Time)
        acceptable_index = min(len_ang_vel, len_Time)
        #sampling frequency
        Fs = np.floor(acceptable_index / Time[acceptable_index - 1]).astype(int)


        # FFT for angular velocity
        z = np.zeros(6 * Fs)  # 6s window
        window_size = 6  # in seconds
        sliding_width = 1  # in seconds
        counter = np.floor((len(ang_vel) - (window_size * Fs)) / (sliding_width * Fs)).astype(int) + 1
        dataset_absFFT = []
        max_fft_value = -1
        max_fft_index = -1

        for i in range(counter):
            start_index = int(i * sliding_width * Fs)
            end_index = int(start_index + window_size * Fs)
            segment = ang_vel.values[start_index:end_index,0]
            frequencies, FFT = signal.welch(segment, fs=Fs, nperseg=len(segment))
            absFFT=np.abs(FFT)
            dataset_absFFT.append(absFFT)

            # Find the maximum FFT value within the current window
            current_max_fft = np.max(absFFT)
            if current_max_fft > max_fft_value:
                max_fft_value = current_max_fft
                max_fft_index = i


        acceptable_absFFT = (max_fft_value * 2) / 3
        print(f"\nMaximum absolute FFT value: {max_fft_value}")
        print(f"Threshold of absolute FFT value: {acceptable_absFFT}")

        print(f"Index of the time window with maximum FFT: {max_fft_index}")
        print(f"Start time of the window with maximum FFT: {max_fft_index * sliding_width} seconds")



        # Find the first time window where absFFT is above the threshold
        for i in range(counter):
            if np.max(dataset_absFFT[i]) > acceptable_absFFT:
                first_index_above_threshold = i
                break  # Exit the loop after finding the first occurrence

        if first_index_above_threshold != -1:
            first_start_time = first_index_above_threshold * sliding_width
            first_end_time=first_start_time+window_size
            print(f"\nFirst time window where absFFT exceeds the threshold:")
            print(f"Index: {first_index_above_threshold}")
            print(f"Start time: {first_start_time} seconds")
        else:
            print("\nNo time window found where absFFT exceeds the threshold.")

        # Create a Pandas DataFrame to store the results
        results_df = pd.DataFrame(columns=['Session_id', 'Angular_velocity_id','First Start Time', 'First End Time'])
        # Append the new data to the DataFrame
        new_data = pd.DataFrame({'Session_id': [session_id[session_index]], 'Angular_velocity_id': [velocity_id[velocity_index]],'First Start Time': [first_start_time], 'First End Time': [first_end_time]})
        results_df = pd.concat([results_df, new_data], ignore_index=True)
        # Define the output Excel file path
        output_file = 'First_HeadCal_time.xlsx'

        try:
            # Check if the file exists and append the new data
            with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                results_df.to_excel(writer, sheet_name='Results', header=False, index=False, startrow=writer.sheets['Results'].max_row)
                print(f"Data appended to '{output_file}' successfully.")

        except FileNotFoundError:
            # If the file doesn't exist, create it and write the header
            results_df.to_excel(output_file, sheet_name='Results', index=False)
            print(f"New file '{output_file}' created and data written successfully.")