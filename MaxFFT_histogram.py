
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import openpyxl

data = pd.read_excel("Max_HeadCal_time_FFTpy.xlsx", usecols=['MaxFFT'])

# Create the histogram
plt.hist(data, bins=35, color='skyblue', edgecolor='black')

# Customize the plot (optional)
#plt.title('Histogram of Data')
plt.xlabel('Max FFT Amplitude')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.5)

# Show the plot
plt.show()