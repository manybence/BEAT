# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 07:54:18 2024

@author: Bence Many

Data extractor function
"""

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

def find_file():
        
    #Open file dialog to pick the desired BoM
    root = Tk()
    root.attributes('-topmost', True)  # Display the dialog in the foreground.
    root.iconify()  # Hide the little window.
    file_path = askopenfilename(title='Select text file', parent=root)
    print("File selected: ", file_path)
    root.destroy()  # Destroy the root window when folder selected.
    return file_path


def main():
    #Find text file
    input_file_path = find_file() 
    
    #Create output file
    directory, filename_extension = os.path.split(input_file_path)
    filename, extension = os.path.splitext(filename_extension)

    # Append "_new" to the filename and reconstruct the new file path
    new_filename = f"{filename}_new{extension}"
    new_file_path = os.path.join(directory, new_filename)

    try:
        with open(input_file_path, 'r') as input_file, open(new_file_path, 'w') as output_file:
            for line in input_file:
                if line.startswith('Data'):
                    output_file.write(line)
        print("Data exported successfully.")
    except FileNotFoundError:
        print(f"File '{input_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return

if __name__ == "__main__":
    main()