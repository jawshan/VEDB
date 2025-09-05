# Author: Jawshan Ara Shatil
# Date: 09.05.2025
#resampled to 120Hz

import os
from io import BytesIO
import msgpack
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import numpy as np
import math
from scipy import signal
from scipy.signal import resample
import numpy.linalg as la

# Ignore all warnings
warnings.filterwarnings('ignore')

def loop_through_files(directory, session_name):
    """Changes the current working directory to the session directory."""
    session_path = os.path.join(directory, session_name)
    try:
        os.chdir(session_path)
        print(f"Current working directory: {os.getcwd()}")
    except FileNotFoundError:
        print(f"Error: Directory not found: {session_path}")

def read_pldata(file_path):
    """Reads msgpack data from a file."""
    try:
        with open(file_path, 'rb') as file:
            unpacker = msgpack.Unpacker(file, raw=False)
            data = list(unpacker)  # Read all packets into a list
        return data
    except OSError:
        print(f'File path: "{file_path}" not found.')
        return []

def parse_pldata(data):
    """Parses msgpack data into a flattened dictionary."""
    try:
        unpacker = msgpack.Unpacker(BytesIO(data), raw=False)
        parsed_data = next(unpacker)

        flattened = {}
        for key, value in parsed_data.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    flattened[f"{key}_{i}"] = item
            else:
                flattened[key] = value
        return flattened
    except Exception as e:
        print(f"Error parsing pldata: {e}")
        return {}

def generate_dataframe(filename_list: list[str]):
    """Generates DataFrames for timestamp and normalized resampled angular velocities."""
    if not filename_list:
        return None, None

    filename = filename_list[0] #Assuming only one file is passed.
    data = read_pldata(filename)
    if not data:
        return None, None

    df = pd.DataFrame(data)
    if df.empty or 1 not in df.columns:
        print("DataFrame is empty or missing required column.")
        return None, None

    angular_velocity_0_list = []
    angular_velocity_1_list = []
    angular_velocity_2_list = []
    timestamp_list = []

    try:
        first_timestamp = None
        for i in range(len(df[1])):
            parsed_data = parse_pldata(df[1].iloc[i])
            timestamp = parsed_data.get('timestamp')
            angular_velocity_0_list.append(parsed_data.get('angular_velocity_0'))
            angular_velocity_1_list.append(parsed_data.get('angular_velocity_1'))
            angular_velocity_2_list.append(parsed_data.get('angular_velocity_2'))
            if first_timestamp is None and timestamp is not None:
                first_timestamp = timestamp

            timestamp_list.append(timestamp - first_timestamp if first_timestamp is not None and timestamp is not None else None)

        # Create a temporary DataFrame for initial interpolation
        temp_df = pd.DataFrame({'timestamp_diff': timestamp_list, 'ang_vel0': angular_velocity_0_list,
                                'ang_vel1': angular_velocity_1_list, 'ang_vel2': angular_velocity_2_list})

        # Perform linear interpolation on all angular velocity components
        temp_df['ang_vel0_interpolated'] = temp_df['ang_vel0'].interpolate(method='linear')
        temp_df['ang_vel1_interpolated'] = temp_df['ang_vel1'].interpolate(method='linear')
        temp_df['ang_vel2_interpolated'] = temp_df['ang_vel2'].interpolate(method='linear')

        Time_interp = temp_df['timestamp_diff'].dropna().to_numpy()
        ang_vel0_interpolated = temp_df['ang_vel0_interpolated'].dropna().to_numpy()
        ang_vel1_interpolated = temp_df['ang_vel1_interpolated'].dropna().to_numpy()
        ang_vel2_interpolated = temp_df['ang_vel2_interpolated'].dropna().to_numpy()

        min_len = min(len(Time_interp), len(ang_vel0_interpolated), len(ang_vel1_interpolated), len(ang_vel2_interpolated))
        print(f"Minimum length for session: {os.path.basename(os.getcwd())}: {min_len}")

        if not Time_interp.size > 1 or min_len <= 1:
            print(f"Not enough valid data for resampling in session: {os.path.basename(os.getcwd())}.")
            return None, None

        #resampled to 120Hz
        Time_resampled = np.linspace(Time_interp.min(), Time_interp.max(), int((Time_interp.max() - Time_interp.min()) * 120), endpoint=True)
        #print(len(Time_resampled))
        df_timestamp = pd.DataFrame(Time_resampled, columns=['timestamp'])

        # Resample using the interpolated angular velocities
        ang_vel0_resampled = np.interp(Time_resampled, Time_interp[:min_len], ang_vel0_interpolated[:min_len])
        ang_vel1_resampled = np.interp(Time_resampled, Time_interp[:min_len], ang_vel1_interpolated[:min_len])
        ang_vel2_resampled = np.interp(Time_resampled, Time_interp[:min_len], ang_vel2_interpolated[:min_len])

        #saving three axis
        #axis0
        #ang_vel0_resampled = np.array([ang_vel0_resampled]).T
        df_ang_vel0_resampled = pd.DataFrame(ang_vel0_resampled, columns=['angular_velocity_x'])
        #axis1
        #ang_vel1_resampled = np.array([ang_vel1_resampled]).T
        df_ang_vel1_resampled = pd.DataFrame(ang_vel1_resampled, columns=['angular_velocity_y'])
        #axis2
        #ang_vel2_resampled = np.array([ang_vel2_resampled]).T
        df_ang_vel2_resampled = pd.DataFrame(ang_vel2_resampled, columns=['angular_velocity_z'])

        #combined three axis togather
        ang_vel_resampled = np.array([ang_vel0_resampled, ang_vel1_resampled, ang_vel2_resampled]).T
        df_ang_vel_resampled = pd.DataFrame(ang_vel_resampled, columns=['angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z'])
        #euc norm
        ang_vel_magnitude_resampled = np.sqrt(ang_vel0_resampled**2 + ang_vel1_resampled**2 + ang_vel2_resampled**2)
        print(len(ang_vel_magnitude_resampled))
        df_ang_vel_magnitude_resampled = pd.DataFrame(ang_vel_magnitude_resampled, columns=['angular_velocity_magnitude'])


        return df_timestamp,df_ang_vel_resampled, df_ang_vel_magnitude_resampled, df_ang_vel0_resampled, df_ang_vel1_resampled, df_ang_vel2_resampled

    except Exception as e:
        print(f"Error during data processing for session {os.path.basename(os.getcwd())}: {e}")
        return None, None


def main():
    """Main function to process pldata files and generate Excel files."""
    parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_good_data_y"
    result_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_result_data_y"
    
    #parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_good_data"
    #result_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/test_result_data"

    session_ids = [item for item in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, item))]

    for session_name in session_ids:
        try:
            loop_through_files(parent_folder_path, session_name)
            filelist = ['odometry.pldata']
            df_timestamp,df_ang_vel_resampled, df_ang_vel_magnitude_resampled, df_ang_vel0_resampled, df_ang_vel1_resampled, df_ang_vel2_resampled = generate_dataframe(filelist)

            if df_timestamp is not None and df_ang_vel_magnitude_resampled is not None:
                os.chdir(result_folder_path)
                folder_name = session_name

                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                    print(f"Folder '{folder_name}' created successfully.")

                time_xlfilename = os.path.join(folder_name, f'{folder_name}_timestamp_resampled.xlsx')
                df_timestamp.to_excel(time_xlfilename, index=False)
                
                # ang_xlfilename = os.path.join(folder_name, f'{folder_name}_normalized_ang_vel_resampled.xlsx')
                # df_ang_vel_resampled.to_excel(ang_xlfilename, index=False)

                # ang_mag_xlfilename = os.path.join(folder_name, f'{folder_name}_normalized_ang_vel_resampled_mag.xlsx')
                # df_ang_vel_magnitude_resampled.to_excel(ang_mag_xlfilename, index=False)
                
                ##
                
                ang0_xlfilename = os.path.join(folder_name, f'{folder_name}_ang_vel0_resampled.xlsx')
                df_ang_vel0_resampled.to_excel(ang0_xlfilename, index=False)
                ang1_xlfilename = os.path.join(folder_name, f'{folder_name}_ang_vel1_resampled.xlsx')
                df_ang_vel1_resampled.to_excel(ang1_xlfilename, index=False)
                ang2_xlfilename = os.path.join(folder_name, f'{folder_name}_ang_vel2_resampled.xlsx')
                df_ang_vel2_resampled.to_excel(ang2_xlfilename, index=False)
                
            else:
                print(f"No valid DataFrames returned for session: {session_name}. Skipping Excel creation.")

        except Exception as e:
            print(f"An unexpected error occurred during processing session {session_name}: {e}")
            continue

if __name__ == "__main__":
    main()