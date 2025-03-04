import sys
from ast import parse
import numpy as np

import msgpack

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
folder_name = user_input
file_name= "eye0.pldata"
folder_path = Path.cwd() / folder_name

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
#print(file_path)

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


# Generates static graphs for display in the visualizer
def generate_graphs(filename_list: list[str]):
    # assuming either 1. both files exist, 2. neither file exists
    global graph_file_list
    for filename in filename_list:
        data = read_pldata(filename)
        df = pd.DataFrame(data)
        
        angular_velocity_0_list = []
        angular_velocity_1_list = []
        angular_velocity_2_list = []

        timestamp_list = []
        first_timestamp = parse_pldata(df[1].iloc[0])['timestamp']
        last_timestamp = parse_pldata(df[1].iloc[(len(df[1])-1)])['timestamp']
        
        #print(last_timestamp - first_timestamp)
        

        
        for i in range(len(df[1])):
            data_frame = parse_pldata(df[1].iloc[i])
            data_type_4 = 'angular_velocity_0'
            data_type_5 = 'angular_velocity_1'
            data_type_6 = 'angular_velocity_2'
            
            angular_velocity_0_list.append(data_frame[data_type_4])
            angular_velocity_1_list.append(data_frame[data_type_5])
            angular_velocity_2_list.append(data_frame[data_type_6])
            
            # list of time stamp from world camera
            #print(data_frame['timestamp'])
            timestamp_list.append(data_frame['timestamp'] - first_timestamp)
            # list of recording datapoint
            #print(data_frame['timestamp'] - first_timestamp)
        timelist = [float(i) for i in timestamp_list]
        
    
        # # Convert NumPy array to Pandas DataFrame
       
        df_timestamp = pd.DataFrame(timelist)
        df_ang_vel0 = pd.DataFrame(angular_velocity_0_list)
        df_ang_vel1 = pd.DataFrame(angular_velocity_1_list)

        # # Save DataFrame to Excel file
        current_directory = os.getcwd()
        ## change directory
        new_directory = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data"  # Replace with the actual path
        os.chdir(new_directory)
        #timestamp
        time_xlfilename= folder_name + '_'+'timestamp.xlsx'
        filepath = os.path.join(current_directory, time_xlfilename)
        df_timestamp.to_excel(time_xlfilename, index=False)
        #angular velocity0
        ang0_xlfilename=folder_name + '_'+'ang_vel_0.xlsx'
        filepath = os.path.join(current_directory, ang0_xlfilename)
        df_ang_vel0.to_excel(ang0_xlfilename, index=False)
        #angular velocity1
        ang1_xlfilename=folder_name + '_'+'ang_vel_1.xlsx'
        filepath = os.path.join(current_directory, ang1_xlfilename)
        df_ang_vel1.to_excel(ang1_xlfilename, index=False)
        

        #Matplotlib Plots: Static image plots
        # plt.clf()
        # plt.plot(timestamp_list, angular_velocity_0_list, label=data_type_4)
        # plt.plot(timestamp_list, angular_velocity_1_list, label=data_type_5)
        # plt.plot(timestamp_list, angular_velocity_2_list, label=data_type_6)
        # # Set the x-axis range
        # plt.xlim(0, 200)
        # plt.legend()
        # plt.show()

        # #Plotly Plots: Angular velocity, Dynamic interactable plots
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=timelist, y=angular_velocity_0_list, name='Angular Velocity 0'))
        # fig.add_trace(go.Scatter(x=timelist, y=angular_velocity_1_list, name='Angular Velocity 1'))
        # fig.add_trace(go.Scatter(x=timelist, y=angular_velocity_2_list, name='Angular Velocity 2'))
        # fig.update_layout(title='Angular Velocity', xaxis_title='Time', yaxis_title='Angular Velocity',
        #                   legend_title='Lines')
        # fig.update_xaxes(range=[158, 178])
        # #fig.show()

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