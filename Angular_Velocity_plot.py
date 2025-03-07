
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import openpyxl


directory = '/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data'
session_id = ["2022_02_09_13_40_13", "2022_06_24_11_41_06", "2022_06_24_11_49_03", "2022_06_24_14_26_28", "2022_09_15_15_25_58", "2022_09_19_11_27_04", "2022_10_06_15_51_11"]

folder_name = session_id[2]
x=0
Ang_file_path = os.path.join(directory, f"{folder_name}_ang_vel_{x}.xlsx")
Time_file_path = os.path.join(directory, f"{folder_name}_timestamp.xlsx")

timestamp = pd.read_excel(Time_file_path)
ang_vel = pd.read_excel(Ang_file_path)

Time = timestamp.values[1:].flatten()
ang_vel = ang_vel.values[1:].flatten()
acceptable_index = min(len(ang_vel), len(Time))


plt.figure(figsize=(10, 6))
plt.plot(Time[1:acceptable_index], ang_vel[1:acceptable_index])  
plt.xlabel('Time (s)')
plt.ylabel('Angular Velocity')
plt.title('Angular Velocity vs. Time')
plt.grid(True)
plt.show()