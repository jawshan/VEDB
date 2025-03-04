import os
from pathlib import Path
## folder path setting
folder_name = "2022_02_09_13_40_13"
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


## change directory
        #current_directory = os.getcwd()
        #new_directory = "/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/VEDB/angular_vel_data"  # Replace with the actual path
        #os.chdir(new_directory)
            