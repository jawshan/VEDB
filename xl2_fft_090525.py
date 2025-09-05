# Author: Jawshan Ara Shatil
# Date: 09.05.2025

import os
import pandas as pd
import numpy as np
import scipy.signal as signal
import openpyxl # Keep for Excel writing, though pandas handles much of it
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, freqz, filtfilt
from pathlib import Path
import warnings

# Ignore all warnings for cleaner output during development
warnings.filterwarnings('ignore')

# Global variable for the timestamp save file - make it a clear configuration
TIMESTAMP_SAVE_FILENAME = 'Max_HeadCal_time_FFTpy.xlsx'

def loop_through_files(directory, session_name):
    """
    Constructs the session path. Does not change the working directory.
    Returns the full path to the session directory.
    """
    session_path = os.path.join(directory, session_name)

    if not os.path.exists(session_path):
        print(f"Error: Directory not found: {session_path}")
        return None
    print(f"Processing session directory: {session_path}")
    return session_path

def butter_bandpass(lowcut, highcut, fs, order=5):
    """
    Designs a Butterworth bandpass filter.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band', analog=False)
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """
    Applies a Butterworth bandpass filter to the data.
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def generate_slidingFFT(session_path, session_id, velocity_id):
    """
    Generates sliding window FFT for angular velocity data for specified velocity IDs.
    Returns a list of paths to the generated FFT excel files.
    """
    generated_fft_files = [] # To store paths of generated FFT files

    # Filter design parameters (can be made configurable if needed, suggested by Pogen)
    lowcut = 0.25
    highcut = 1

    # Plotting setup for individual velocity FFTs
    fig, axes = plt.subplots(1, len(velocity_id), figsize=(15, 5), sharey=True)
    if len(velocity_id) == 1: # Handle single subplot case
        axes = [axes]
#input
    for n, N in enumerate(velocity_id): # Use enumerate to get index and value
        print(f"\nProcessing velocity ID: {N}")
        filename = os.path.join(session_path, f"{session_id}_ang_vel{N}_resampled.xlsx")
        filenameT = os.path.join(session_path, f"{session_id}_timestamp_resampled.xlsx")

        if not os.path.exists(filename) or not os.path.exists(filenameT):
            print(f"Skipping {session_id} velocity {N}: Required files not found.")
            continue

        try:
            timestamp_df = pd.read_excel(filenameT)
            # Assuming the first column after header is the timestamp data
            Time = timestamp_df.iloc[1:, 0].values.flatten().astype(float)

            ang_vel_df = pd.read_excel(filename)
            # Assuming the first column after header is the angular velocity data
            ang_vel = ang_vel_df.iloc[1:, 0].values.flatten().astype(float)

            acceptable_index = min(len(Time), len(ang_vel))
            Time = Time[0:acceptable_index]
            ang_vel = ang_vel[0:acceptable_index]

            if acceptable_index > 1:
                # Calculate Fs more robustly
                Fs = 1.0 / np.mean(np.diff(Time))
                Fs = np.round(Fs).astype(int) # Round to nearest integer for sample rate
                #print(f"Calculated Fs for {session_id} velocity {N}: {Fs} Hz")
            else:
                print(f"Warning: Not enough data points for {session_id} velocity {N} to reliably calculate Fs. Setting Fs to 120.")
                Fs = 120 # Default value

            # FFT parameters
            window_size_sec = 5 # seconds
            sliding_width_sec = 1 # seconds
            window_size_samples = int(window_size_sec * Fs)
            sliding_width_samples = int(sliding_width_sec * Fs)

            # Ensure window_size_samples is not zero if Fs is very low
            if window_size_samples == 0:
                print(f"Warning: Window size in samples is 0 for {session_id} velocity {N}. Skipping FFT.")
                continue

            counter = np.floor((len(ang_vel) - window_size_samples) / sliding_width_samples).astype(int) + 1
            if counter <= 0:
                print(f"Warning: Not enough data for {session_id} velocity {N} to create any windows. Skipping FFT.")
                continue

            dataset_absFFT = []

            for k in range(counter):
                start_index = int(k * sliding_width_samples)
                end_index = int(start_index + window_size_samples)
                if end_index > len(ang_vel):
                    end_index = len(ang_vel) # Adjust end index if it exceeds data length

                segment = ang_vel[start_index:end_index]
                if len(segment) < window_size_samples: # Skip if segment is too short for meaningful FFT
                    continue

                filtered_segment = butter_bandpass_filter(segment, lowcut, highcut, Fs, order=4)

                # Use nperseg = len(filtered_segment) for full segment Welch periodogram
                frequencies, FFT = signal.welch(filtered_segment, fs=Fs, nperseg=len(filtered_segment))
                absFFT = np.abs(FFT)
                dataset_absFFT.append(absFFT)

            if not dataset_absFFT:
                print(f"No valid FFT segments generated for {session_id} velocity {N}. Skipping save and plot.")
                continue

            # Convert list of arrays to a 2D numpy array for consistent DataFrame creation
            dataset_absFFT_np = np.array(dataset_absFFT)

            # Save individual velocity FFT
            df = pd.DataFrame(dataset_absFFT_np)
            FFT_xlfilename = os.path.join(session_path, f'{N}_absFFT.xlsx')
            df.to_excel(FFT_xlfilename, index=False)
            generated_fft_files.append(FFT_xlfilename) # Add to list for later summing

            # Find max on each axis for plotting
            max_absFFT_dataset = np.max(dataset_absFFT_np, axis=1)
            max_All = np.max(max_absFFT_dataset)
            i_col_max = np.where(max_absFFT_dataset == max_All)[0][0] # Get the first index of the max

            # Calculate actual indices for plotting
            maxFFT_index = int(i_col_max * sliding_width_samples)
            maxFFT_end_index = int(maxFFT_index + window_size_samples)

            # Ensure indices are within bounds
            maxFFT_index = max(0, min(maxFFT_index, len(Time) - 1))
            maxFFT_end_index = min(maxFFT_end_index, len(Time) - 1)


            maxFFT_Time = Time[maxFFT_index:maxFFT_end_index]
            maxFFT_angV = ang_vel[maxFFT_index:maxFFT_end_index]

            # Plotting for current velocity
            axes[n].plot(maxFFT_Time, maxFFT_angV)
            axes[n].set_xlabel("Time (s)")
            axes[n].set_title(f"Vel {N} Max FFT Window")
            if n == 0: # Only set ylabel for the first subplot
                axes[n].set_ylabel("Angular Velocity (deg/s)")


        except Exception as e:
            print(f"An error occurred during FFT processing for velocity {N}: {e}")
            continue # Continue to the next velocity if an error occurs

    # Adjust layout and save the figure for individual velocity plots
    fig.tight_layout()
    plot_filename = os.path.join(session_path, f"{session_id}_individual_max_fft_windows.png")
    fig.savefig(plot_filename, dpi=300)
    plt.show(block=False)
    plt.close(fig) # Close the figure to free up memory

    return generated_fft_files, Fs # Return the files and Fs

def sumFFT(session_path, velocity_ids, generated_fft_files):
    """
    Sums the FFT data from individual velocity files.
    """
    print("\nSumming FFT data...")
    dataframes_to_sum = []

    for N in velocity_ids:
        fft_filename = os.path.join(session_path, f'{N}_absFFT.xlsx')
        if os.path.exists(fft_filename):
            dataframes_to_sum.append(pd.read_excel(fft_filename))
        else:
            print(f"Warning: {fft_filename} not found for summing.")

    if not dataframes_to_sum:
        print("No FFT files found to sum.")
        return None

    # Ensure all dataframes have the same number of rows and columns before summing
    # This assumes the FFT output dimensions are consistent
    # If not, you might need to reindex or pad
    min_rows = min(df.shape[0] for df in dataframes_to_sum)
    min_cols = min(df.shape[1] for df in dataframes_to_sum)
    aligned_dfs = [df.iloc[:min_rows, :min_cols] for df in dataframes_to_sum]

    sum_df = pd.DataFrame()
    if aligned_dfs:
        sum_df = sum(aligned_dfs)

    sumFFT_xlfilename = os.path.join(session_path, 'sum_absFFT.xlsx')
    sum_df.to_excel(sumFFT_xlfilename, index=False)
    print(f"Summed FFT data saved to: {sumFFT_xlfilename}")
    return sumFFT_xlfilename # Return the path to the summed file

def find_maxFFT(summed_fft_filename, window_size_sec, Fs, session_name, session_path, timestamp_save_path):
    """
    Finds the maximum FFT value from the summed FFT data and records time information.
    Plots the angular velocity corresponding to the max FFT window.
    """
    if not os.path.exists(summed_fft_filename):
        print(f"Error: Summed FFT file not found at {summed_fft_filename}. Cannot find max FFT.")
        return

    print("\nFinding max FFT from summed data...")
    df_maxFFT = pd.read_excel(summed_fft_filename)

    # Find max on each row (representing each sliding window)
    max_absFFT_per_window = np.max(df_maxFFT.values, axis=1)
    max_overall_FFT = np.max(max_absFFT_per_window)
    # Get the index of the window with the overall maximum FFT
    i_window_max = np.where(max_absFFT_per_window == max_overall_FFT)[0][0]

    # Recalculate segment parameters based on Fs
    window_size_samples = int(window_size_sec * Fs)
    sliding_width_sec = 1 # Consistent with generate_slidingFFT
    sliding_width_samples = int(sliding_width_sec * Fs)

    # Calculate actual start and end indices of the max FFT window in the original data
    #plus/minus 15s to observe activity in all three axes
    maxFFT_start_index = int(i_window_max * sliding_width_samples) - (15*120)
    maxFFT_end_index = (maxFFT_start_index+ (35*120) )

    print(f"Max FFT found at window index: {i_window_max}")
    print(f"Corresponding start index in original data: {maxFFT_start_index}")
    print(f"Corresponding end index in original data: {maxFFT_end_index}")

    # Load original timestamp and angular velocity for plotting
    timestamp_filename = os.path.join(session_path, f"{session_name}_timestamp_resampled.xlsx")
    ang_vel_filename0 = os.path.join(session_path, f"{session_name}_ang_vel0_resampled.xlsx") # Using vel0 as an example
    ang_vel_filename1 = os.path.join(session_path, f"{session_name}_ang_vel1_resampled.xlsx") 
    ang_vel_filename2 = os.path.join(session_path, f"{session_name}_ang_vel2_resampled.xlsx") 

    timestamp_df = pd.read_excel(timestamp_filename)
    Time = timestamp_df.iloc[1:, 0].values.flatten().astype(float)
    ang_vel_df0 = pd.read_excel(ang_vel_filename0)
    ang_vel0 = ang_vel_df0.iloc[1:, 0].values.flatten().astype(float)

    ang_vel_df1 = pd.read_excel(ang_vel_filename1)
    ang_vel1 = ang_vel_df1.iloc[1:, 0].values.flatten().astype(float)
    
    ang_vel_df2 = pd.read_excel(ang_vel_filename2)
    ang_vel2 = ang_vel_df2.iloc[1:, 0].values.flatten().astype(float)
    
    acceptable_index = min(len(Time), len(ang_vel0))
    Time = Time[0:acceptable_index]
    ang_vel0 = ang_vel0[0:acceptable_index]
    ang_vel1 = ang_vel1[0:acceptable_index]
    ang_vel2 = ang_vel2[0:acceptable_index]

    # Ensure indices are within bounds of the original Time and ang_vel arrays
    maxFFT_start_index = max(0, min(maxFFT_start_index, len(Time) - 1))
    maxFFT_end_index = min(maxFFT_end_index, len(Time) - 1)

    if maxFFT_start_index >= maxFFT_end_index:
        print("Warning: Max FFT window start index is not before or equal to end index. Cannot plot.")
        return

    # Extract time and angular velocity for the max FFT window
    maxFFT_Time_segment = Time[maxFFT_start_index:(maxFFT_start_index+ (35*120))]
    maxFFT_angV0_segment = ang_vel0[maxFFT_start_index:(maxFFT_start_index+ (35*120))]
    maxFFT_angV1_segment = ang_vel1[maxFFT_start_index:(maxFFT_start_index+ (35*120))]
    maxFFT_angV2_segment = ang_vel2[maxFFT_start_index:(maxFFT_start_index+ (35*120))]

    # Create a new figure for the combined plot (or just the max FFT window plot)
    plt.figure(figsize=(10, 5))
    plt.plot(maxFFT_Time_segment, maxFFT_angV0_segment, label='Angular Velocity 0')
    plt.plot(maxFFT_Time_segment, maxFFT_angV1_segment, label='Angular Velocity 1')
    plt.plot(maxFFT_Time_segment, maxFFT_angV2_segment, label='Angular Velocity 2')
    plt.xlabel("Time (s)")
    plt.ylabel("Angular Velocity (deg/s)")
    plt.title(f"Max FFT Window for Session {session_name}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plot_filename = os.path.join(session_path, f"{session_name}_max_fft_combined.png")
    plt.savefig(plot_filename, dpi=300)
    plt.close() # Close the figure

    # Prepare data for Excel saving
    # Calculate timestamps from indices
    max_x_start_time = Time[maxFFT_start_index] if maxFFT_start_index < len(Time) else np.nan
    max_x_end_time = Time[maxFFT_end_index] if maxFFT_end_index < len(Time) else np.nan

    HeadCal_Time_title = ['Session_ID', 'MaxFFT start time (s)', 'MaxFFT end time (s)', 'MaxFFT Value']
    results_df = pd.DataFrame(columns=HeadCal_Time_title)
    HeadCal_Time_row = pd.DataFrame([{
        'Session_ID': session_name,
        'MaxFFT start time (s)': max_x_start_time,
        'MaxFFT end time (s)': max_x_end_time,
        'MaxFFT Value': max_overall_FFT
    }])
    results_df = pd.concat([results_df, HeadCal_Time_row], ignore_index=True)

    # Save results to the timestamp save file
    try:
        # Check if the file exists and append the new data
        if os.path.exists(timestamp_save_path):
            with pd.ExcelWriter(timestamp_save_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Load existing sheet to get max row, then append
                existing_df = pd.read_excel(timestamp_save_path)
                start_row = existing_df.shape[0] + 1 # Start writing from the row after the last data row
                results_df.to_excel(writer, sheet_name='Results', header=False, index=False, startrow=start_row)
            print(f"Data appended to '{timestamp_save_path}' successfully.")
        else:
            # If the file doesn't exist, create it and write the header
            results_df.to_excel(timestamp_save_path, sheet_name='Results', index=False)
            print(f"New file '{timestamp_save_path}' created and data written successfully with header.")

    except Exception as e:
        print(f"An error occurred while saving timestamp data: {e}")

    # Return the start time of the max FFT window for potential further use
    return max_x_start_time

def main():
    # Define your parent folder path
    #parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_result_data"
    parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_result_data_y"

    # Define the path where the main timestamp file will be saved
    # This should be a location accessible throughout the script's execution
    results_output_path = os.path.join(parent_folder_path, TIMESTAMP_SAVE_FILENAME)

    # Get list of session directories
    session_ids = [item for item in os.listdir(parent_folder_path)
                   if os.path.isdir(os.path.join(parent_folder_path, item))]
    session_ids.sort() # Process in a consistent order

    velocity_ids = [0, 1, 2] # Define velocity IDs once

    # Ensure the results file has a header if it's new or empty
    if not os.path.exists(results_output_path) or pd.read_excel(results_output_path, sheet_name='Results', header=None).empty:
        # Create an empty DataFrame with headers and save it to create the file structure
        initial_df = pd.DataFrame(columns=['Session_ID', 'MaxFFT start time (s)', 'MaxFFT end time (s)', 'MaxFFT Value'])
        try:
            initial_df.to_excel(results_output_path, sheet_name='Results', index=False)
            print(f"Initialized '{results_output_path}' with headers.")
        except Exception as e:
            print(f"Error initializing results file: {e}")
            return # Exit if we can't even create the results file

    for session_name in session_ids:
        print(f"\n--- Processing Session: {session_name} ---")
        try:
            session_path = loop_through_files(parent_folder_path, session_name)
            if session_path:
                # Generate individual FFTs and get the list of created files and Fs
                generated_fft_files, Fs_calculated = generate_slidingFFT(session_path, session_name, velocity_ids)

                if generated_fft_files: # Only proceed if FFT files were actually generated
                    # Sum the FFTs
                    summed_fft_file = sumFFT(session_path, velocity_ids, generated_fft_files)

                    if summed_fft_file: # Only proceed if summing was successful
                        window_size_sec = 5 # Consistent with generate_slidingFFT
                        # Find max FFT and record timestamps
                        find_maxFFT(summed_fft_file, window_size_sec, Fs_calculated, session_name, session_path, results_output_path)
                else:
                    print(f"No FFT files generated for session {session_name}. Skipping summing and max FFT analysis.")

        except Exception as e:
            print(f"An unexpected error occurred during session processing: {e}. Skipping session: {session_name}")
            continue

    print("\n--- All sessions processed ---")

if __name__ == "__main__":
    main()