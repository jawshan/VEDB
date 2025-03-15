
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import openpyxl


# Sample data (replace with your actual data)
data = np.random.randn(1000)  

# Create the histogram
plt.hist(data, bins=30, color='skyblue', edgecolor='black')

# Customize the plot (optional)
plt.title('Histogram of Data')
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)

# Show the plot
plt.show()