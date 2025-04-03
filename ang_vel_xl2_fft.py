# Author: Jawshan Ara Shatil
# Date: 03.07.2025

import os
import pandas as pd
import numpy as np
import scipy.signal as signal
import openpyxl

import warnings

# Ignore all warnings
warnings.filterwarnings('ignore')

# Timestamp_save = 'HeadShake_time_FFTpy.xlsx'  # Define outside the loop

def loop_through_files(directory, session_name):
    session_id = session_name
    session_path = os.path.join(directory, session_id)

    if not os.path.exists(session_path):
        print(f"Error: Directory not found: {session_path}")
        return None  # Exit if the directory doesn't exist

    try:
        os.chdir(session_path)
        print(f"Current working directory: {os.getcwd()}")
        return os.getcwd() #Return the current directory for next function.
    except Exception as e:
        print(f"An error occurred while changing directory: {e}")
        return None

def generate_slidingFFT(parent_folder_path, session_id, velocity_id):
    for n in range(len(velocity_id)):
        N = str(velocity_id[n])
        print(N)
        filename = os.path.join(parent_folder_path, f"{session_id}_ang_vel_{N}.xlsx")
        filenameT = os.path.join(parent_folder_path, f"{session_id}_timestamp.xlsx")

        if not os.path.exists(filename) or not os.path.exists(filenameT):
            print(f"Warning: File(s) not found for session {session_id}, velocity {N}. Skipping.")
            continue

        try:
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
                absFFT = np.abs(FFT)
                dataset_absFFT.append(absFFT)

            dataset_absFFT = np.array(dataset_absFFT)
            max_absFFT_dataset = np.max(dataset_absFFT, axis=1)
            max_All = np.max(max_absFFT_dataset)
            acceptable_absFFT = (max_All * 2) / 3

            i_col_max = np.where(max_absFFT_dataset == max_All)
            maxFFT_index = int(i_col_max[0][0] * Fs)  # Access the first element of the array
            maxFFT_end_index = int((i_col_max[0][0] * Fs) + (window_size * Fs))
            max_x_start = Time[maxFFT_index]
            max_x_end = Time[maxFFT_end_index]

            # firstshake
            i_col_shake = np.where(max_absFFT_dataset > acceptable_absFFT)[0]
            first_shake_FFT_start_index = int(i_col_shake[0] * Fs)
            first_shake_start = Time[first_shake_FFT_start_index]
            first_shake_FFT_end_index = int((i_col_shake[0] * Fs) + (window_size * Fs))
            first_shake_end = Time[first_shake_FFT_end_index]

            # all headshake
            i_col_shake = np.where(max_absFFT_dataset > acceptable_absFFT)
            head_shake_FFT_start_index = i_col_shake[0] * Fs
            head_shake_FFT_end_index = (i_col_shake[0] * Fs) + (window_size * Fs)

            head_shake_FFT_start_index_np = np.array(head_shake_FFT_start_index)
            num_shake = head_shake_FFT_start_index_np.size
            HeadCal_Time_title = ['Session_ID', 'Angular Velocity ID','MaxFFT', 'MaxFFT start time', 'MaxFFT end time', 'Shake#', 'Head Shake Start Time', 'Head Shake End Time']
            results_df = pd.DataFrame(columns=HeadCal_Time_title)

            Timestamp_save = session_id +'_HeadShake_time_FFTpy.xlsx'  # Define outside the loop

            for j in range(num_shake):
                head_shake_start = Time[int(head_shake_FFT_start_index[j])]
                head_shake_end = Time[int(head_shake_FFT_end_index[j])]
                HeadCal_Time = pd.DataFrame({'Session_ID': [session_id], 'Angular Velocity ID': [velocity_id[n]], 'MaxFFT': [max_All],'MaxFFT start time': [max_x_start], 'MaxFFT end time': [max_x_end], 'Shake#': [j+1], 'Head Shake Start Time': [head_shake_start], 'Head Shake End Time': [head_shake_end]})
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
        except Exception as e:
                print(f"An error occurred during FFT processing: {e}")

def main():
    parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Headsheak_data"
    session_ids = [item for item in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, item))]

    for session_name in session_ids:
        try:
            session_path = loop_through_files(parent_folder_path, session_name)
            if session_path:
                velocity_id = [0, 1]
                generate_slidingFFT(session_path, session_name, velocity_id)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Skipping session: {session_name}")
            continue

if __name__ == "__main__":
    main()