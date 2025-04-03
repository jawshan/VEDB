import os
from io import BytesIO
import msgpack
import pandas as pd
import warnings

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

def generate_excels(filename_list: list[str]):
    """Generates Excel files from pldata."""
    if not filename_list:
        return

    filename = filename_list[0] #Assuming only one file is passed.
    data = read_pldata(filename)
    if not data:
        return

    df = pd.DataFrame(data)
    if df.empty or 1 not in df.columns:
        print("DataFrame is empty or missing required column.")
        return

    angular_velocity_0_list = []
    angular_velocity_1_list = []
    angular_velocity_2_list = []
    timestamp_list = []

    try:
        first_timestamp = parse_pldata(df[1].iloc[0])['timestamp']
        for i in range(len(df[1])):
            data_frame = parse_pldata(df[1].iloc[i])
            angular_velocity_0_list.append(data_frame.get('angular_velocity_0'))
            angular_velocity_1_list.append(data_frame.get('angular_velocity_1'))
            angular_velocity_2_list.append(data_frame.get('angular_velocity_2'))
            timestamp_list.append(data_frame.get('timestamp') - first_timestamp)

        timelist = [float(i) for i in timestamp_list]
        global df_timestamp, df_ang_vel0, df_ang_vel1
        df_timestamp = pd.DataFrame(timelist)
        df_ang_vel0 = pd.DataFrame(angular_velocity_0_list)
        df_ang_vel1 = pd.DataFrame(angular_velocity_1_list)
    except Exception as e:
        print(f"Error during data processing: {e}")

def main():
    """Main function to process pldata files and generate Excel files."""
    parent_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data"
    result_folder_path = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Headsheak_data"

    session_ids = [item for item in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, item))]

    for session_name in session_ids:
        try:
            loop_through_files(parent_folder_path, session_name)
            filelist = ['odometry.pldata']
            generate_excels(filelist)

            if 'df_timestamp' in globals() and 'df_ang_vel0' in globals() and 'df_ang_vel1' in globals():
                os.chdir(result_folder_path)
                folder_name = session_name

                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                    print(f"Folder '{folder_name}' created successfully.")

                time_xlfilename = os.path.join(folder_name, f'{folder_name}_timestamp.xlsx')
                df_timestamp.to_excel(time_xlfilename, index=False)

                ang0_xlfilename = os.path.join(folder_name, f'{folder_name}_ang_vel_0.xlsx')
                df_ang_vel0.to_excel(ang0_xlfilename, index=False)

                ang1_xlfilename = os.path.join(folder_name, f'{folder_name}_ang_vel_1.xlsx')
                df_ang_vel1.to_excel(ang1_xlfilename, index=False)

        except Exception as e:
            print(f"An unexpected error occurred: {e}. Skipping session: {session_name}")
            continue
if __name__ == "__main__":
    main()