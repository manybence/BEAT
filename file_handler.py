# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 15:29:03 2024

@author: Bence Many

BEAT - Preprocessing the data files
"""

import pandas as pd
from tkinter import Tk, messagebox
from tkinter.filedialog import askopenfilename
import os
import re

prev_battery = 100  # Battery charge %
fs = 200    # 200 Hz sampling frequency
fs_index = 50   # 50 Hz sampling freq per index (as every 4th sample is recorded only)

def read_raw_data(file_path):
        
    datalines = []
    header = []
    sections = []
    
    # Open the file and read all lines
    with open(file_path, 'r') as file:
        for line in file:
            
            # Extract data lines that start with "Data:"
            if line.startswith("Data:"):
                row = line.replace("Data:", "").split(";")
                
                # New section starts with header ("Data: Index, Raw0, ...")
                # If "Index" is not numerical then it's a header line, which indicates the start of a new section
                if not str.isdigit(row[0]): 
                    
                    # If no header has been read yet, read the header line
                    if not header:
                        header = row
                        
                    # If header is already read, close the current section
                    else:
                        df = pd.DataFrame(datalines, columns=header)
                        df = df.set_index('Index')
                        sections.append(df)
                        datalines = []
                        
                # If "Index" is numerical then append data to current section
                else:
                    datalines.append(row)    
        
        # Close the last section
        if datalines:
            df = pd.DataFrame(datalines, columns=header)
            df = df.set_index('Index')
            sections.append(df)
    
    print("Data read successfully")
    return sections

def read_preproc_data(file_path):
    
    chunksize = 10000
    chunk_list = []
    
    # Read large data in chunks, use first column (Time) as index
    for chunk in pd.read_csv(file_path, index_col=0, compression='infer', chunksize=chunksize, delimiter=";"):
        chunk_list.append(chunk)

    return pd.concat(chunk_list)

def raw_to_mmHg(raw, sensitivity=0.149924):
    '''
    Convert raw AD-value to mmHg.
    '''
    try:
        return sensitivity * raw.astype(float)
    except:
        return 0
    
def s16(value):
    return -(value & 0x8000) | (value & 0x7FFF)

def extract_battery(series):
    '''
    Convert raw AD-value to battery %.
    '''
    global prev_battery
    converted_values = []
    for raw in series:
        ret_val = 0
        if (raw > 3550):
            ret_val = 100
        elif (raw > 2900):
            ret_val = ((((raw - 2900) * 70) / (3550 - 2900)) + 10)
        elif (raw > 2460):
            ret_val = (((raw - 2460) * 10) / (2900 - 2460))
        ret_val = min(ret_val, (prev_battery + 1))
        converted_values.append(ret_val)
        prev_battery = ret_val
    return converted_values

def pulse_bpm(df):
    
    return df.apply(
        lambda row: (60.0*fs) / float(row['BPUpdate']) 
        if (float(row['BPDiff']) >= 1.2 and float(row['BPUpdate']) > 0) 
        else 0.0, axis=1)

def extract_sensitivity(column):
    
    # Extract sensitivity values
    bsn = None
    tsn = None
    for row in column:
        if not bsn: 
            try:
                bsn = float(re.search(r"BSN:[+-]?[\d\.]+", row).group()[4:])  # Regex to match "BSN: <float>"
            except: pass
        if not tsn:
            try:
                tsn = float(re.search(r"TSN:[+-]?[\d\.]+", row).group()[4:])  # Regex to match "TSN: <float>"
            except: pass
        if bsn and tsn:
            break
        
    print(f"BSN: {bsn}, TSN: {tsn}")
    return bsn, tsn
    
def convert_data(df):
        
    # Remove whitespace characters
    df.columns = df.columns.str.strip()
    
    # Extract sensitivity values
    bsn, tsn = extract_sensitivity(df["Comment"])
    
    # Remove unused variables
    df.drop(['Comment', 'TipComp', 'BalloonComp', 'TipJOFR', 'BalloonJOFR', 'Raw0', 'Raw1', 'BattRaw', 'VrefintRaw'], 
            axis=1, inplace=True)
            
    # Convert data to numerical type, discard corrupted data rows
    df = df.apply(pd.to_numeric, errors='coerce')
    df.dropna(inplace=True, axis=0)  
    
    df = df.rename_axis("Time")
    df.index = df.index / fs_index
    
    df["Fast0"] = raw_to_mmHg(df["Fast0"], sensitivity=tsn)
    df["Slow0"] = raw_to_mmHg(df["Slow0"], sensitivity=tsn)
    
    df["Fast1"] = raw_to_mmHg(df["Fast1"], sensitivity=bsn)
    df["Slow1"] = raw_to_mmHg(df["Slow1"], sensitivity=bsn)
    
    df["Systolic"] = df["Systolic"].astype(float) / 10
    df["Diastolic"] = df["Diastolic"].astype(float) / 10
    df["BPDiff"] = df["BPDiff"].astype(float) / 10
    df["SlowBPDiff"] = df["SlowBPDiff"].astype(float) / 10
    
    df["MAP"] = (df["Systolic"] + 2 * df["Diastolic"]) / 3.0
    
    df["Pulse BPM"] = pulse_bpm(df)
    df["BPStable"] = df["BPStable"].astype(float)
    
    df["BalloonHigh"] = df["BalloonHigh"].astype(float) / 10
    df["BalloonLow"] =  df["BalloonLow"].astype(float) / 10
    df["BalloonDiff"] = df["BalloonDiff"].astype(float) / 10
    
    df["AirTemp"] = df["AirTemp"].astype(float) / 10
    df["AirPres"] = df["AirPres"].astype(float) / 10 - 750
    df["SubjTemp"] = df["SubjTemp"].astype(float) / 10
    
    df["BattFast"] = (df["BattFast"].astype(float) * 100) / 4095
    df["BattSlow"] = (df["BattSlow"].astype(float) * 100) / 4095
    
    df["VrefintFast"] = (df["VrefintFast"].astype(float) * 30) / 4095
    df["VrefintSlow"] = (df["VrefintSlow"].astype(float) * 30) / 4095
                                     
    df["MotorPos"] = df["MotorPos"].astype(float) / 1000              
    df["State"] = df["State"].astype(float) * 10
    
    df["Inflate"] = df['Buttons'].apply(lambda x: (int(x) & 0x03) * 10)
    df["Deflate"] = df['Buttons'].apply(lambda x: ((int(x) & 0x0C) >> 2) * 10)
    df["Alarm Ack"] = df['Buttons'].apply(lambda x: ((int(x) & 0x30) >> 4) * 10)
    
    df["TgtSpeed"] = df["TgtSpeed"].astype(float) / 100
    df["CurSpeed"] = df["CurSpeed"].astype(float) / 100
    
    df["BVPoints"] = df["BVDebug"].apply(lambda x: (int(x) >> 24) * 10)
    df["BVState"] = df["BVDebug"].apply(lambda x: ((int(x) >> 16) & 0x0F) * 10)
    df["BVFlags"] = df["BVDebug"].apply(lambda x: (int(x) & 0x0F) * 10 - 150)
    # df["Balloon period"] =   PlotGraphOptional(lambda samples: self.upd_time(samples[14], samples[15], samples[0])
    
    df["PW pos"] = df["PumpWheel"].apply(lambda x: (s16(int(x) >> 16)) / 1000) 
    df["PW State"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 4) & 0x0F) * 10)
    df["PW Illegal"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 8) & 0x00FF) * 10)
    df["PW HallA"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 2) & 0x01) * 10 - 32)
    df["PW HallB"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 3) & 0x01) * 10 - 33)
    df["GPIO HallA"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 0) & 0x01) * 10 - 20)
    df["GPIO HallB"] =  df["PumpWheel"].apply(lambda x: ((int(x) >> 1) & 0x01) * 10 - 21)                         
    

    # Decode variable names
    df.rename(columns={'Fast0': 'Tip, fast',
                       'Slow0': 'Tip, slow',
                       'Fast1': 'Balloon, fast',
                       'Slow1': 'Balloon, slow'
                       }, inplace=True)
    
    
    # Drop unused variables
    df.drop(['PumpWheel', 'Buttons', 'BVDebug'], 
            axis=1, inplace=True)
    #TODO: Comments, alarms
    
    print("Units are converted successfully")
    return df

def find_file():
        
    try:
        root = Tk()
        root.attributes('-topmost', True)  # Display the dialog in the foreground.
        root.iconify()  # Hide the little window.
        file_path = askopenfilename(
            title='Select data file', 
            parent=root, 
            filetypes=[("Text files", "*.txt"),
                      ("Preprocessed files", "*.gz"),
                      ("All files", "*.*")])
        print("File selected: ", file_path)
        root.destroy()  # Destroy the root window when folder selected.
        return file_path
    
    except FileNotFoundError():
        print("File not found")
        return None
    
def open_datafile():
    
    # Prompt user for data file
    file_path = find_file()
    file_dir, file_name = os.path.split(file_path)
    file_base, file_ext = os.path.splitext(file_name)
    
    # The user picked a .txt file
    if file_ext == '.txt':
        
        # Look for a preprocessed file with the same name
        gz_file_path = os.path.join(file_dir, f"{file_base}_PREPROC.gz")
        
        if os.path.exists(gz_file_path):
            print("A preprocessed version is found and will be opened.")
        else:
            print("Preprocessing the selected file...")
            gz_file_path = preprocess_file(file_path, export=True)
            
        return gz_file_path
    
    elif file_ext == '.gz':
        print("Opening the preprocessed file...")
        return file_path
    
    else:
        print("ERROR: Unsupported file type.")
        return None
    
    
def preprocess_file(file_path=None, export=False):
    
    # Import and clean data
    if not file_path: file_path = find_file()
    sections = read_raw_data(file_path)

    print("Number of sections detected: ", len(sections))

    df = pd.concat(sections, ignore_index=True)
    df = convert_data(df)
    
    # Convert all columns to int
    df = df.apply(lambda col: col.astype(int) if col.name != df.index.name else col)
    
    if export:
        # Export preprocessed data file
        base_name, _ = os.path.splitext(file_path)
        file_path_preproc = f"{base_name}_PREPROC.gz"
    
        df.to_csv(
            file_path_preproc,
            index=True,
            header=True,
            sep=";",
            encoding="utf-8",
            compression="gzip"
        )
        
        print("Preprocessed file exported successfully.")
        return file_path_preproc
    
if __name__ == "__main__":
    
    # preprocess_file(export=True)
    df = open_datafile()
    print(df[:2])