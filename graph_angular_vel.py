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

#Flattens the data, makes it readable, output is column sorted
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
        
        # print(last_timestamp)
        # print(first_timestamp)
        
        # print(last_timestamp - first_timestamp)
        
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
        #print(timelist)
        

        #Matplotlib Plots: Static image plots
        plt.clf()
        plt.plot(timestamp_list, angular_velocity_0_list, label=data_type_4)
        plt.plot(timestamp_list, angular_velocity_1_list, label=data_type_5)
        plt.plot(timestamp_list, angular_velocity_2_list, label=data_type_6)
        # Set the x-axis range
        plt.xlim(0, 200)
        plt.legend()
        plt.show()

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

    # print(df0)
    # print("GAP")
    # print(df1)
    # print("GAP")
    # print(dfod)
    # print("GAP")

    filelist.clear()
    arr = df0[1].iloc[2]
    np.set_printoptions(threshold=sys.maxsize)
    print(arr)
    filelist = ['odometry.pldata']
    generate_graphs(filelist)

main()