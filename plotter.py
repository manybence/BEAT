# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 16:53:29 2024

@author: Bence Many

BEAT visualization app
"""

import plotly.graph_objects as go
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import webbrowser
import dash_bootstrap_components as dbc

prev_battery = 100  # Battery charge %
fs = 200    # 200 Hz sampling frequency

def highlight_area(figure, X0, X1, color="darkred", label="", shape_id="highlighted_area", visibility=True):
    
    # Add shaded region for specific X range
    figure.add_shape(
        type="rect",
        x0=X0,  # Start of the shaded region
        x1=X1,  # End of the shaded region
        y0=0,   # Bottom of the plot
        y1=1,   # Top of the plot (use 'yref' to set as relative or absolute)
        xref="x",  # Use X-axis data for bounds
        yref="paper",  # Use relative 0-1 for Y-axis
        fillcolor=color,  # Background color
        opacity=0.2,  # Transparency
        layer="below",  # Place below the data
        name="highlighted_area",  # Add a name for identification
        visible=visibility
    )
    
    if label and visibility:
        figure.add_annotation(
            x=(X0 + X1) / 2,  # Place the text in the middle of the rectangle
            y=(figure.layout.yaxis.range[1] if figure.layout.yaxis.range else 1) * 0.9,  # Slightly below the top of the plot
            text=label,  # Text to display
            showarrow=False,
            font=dict(size=14, color="white"),  # Style for the text
            align="center",
            bgcolor=color,  # Background color for the text
            opacity=0.8,  # Slightly transparent text background
        )
    
    return figure
    
def display_figure(dataframe):
    
    default_items = ["Systolic", "Battery", "Inflate", "Inline comments", "Catheter", "Balloon, raw", "State"]
    fig = go.Figure()
    
    for column in df.columns:
        if column in default_items: visibility = True
        else: visibility = False
        fig.add_trace(
            go.Scatter(
                x=df.index, 
                y=df[column], 
                name=column, 
                mode="lines", 
                visible=visibility if visibility else "legendonly"
        ))
    
    fig.update_layout(
        height=600,
        title="BEAT data - " + os.path.basename(file_path),
        xaxis_title="Time (s)",
        yaxis_title="Pressure (mmHg)",
        legend_title="Variables",
        hovermode="x unified",  # Show all values at the same x position on hover
        paper_bgcolor=bg_colour
    )
    
    return fig

def read_data(file_path):
        
    rows = []
    header = []
    sections = []
    
    # Open the file and read all lines
    with open(file_path, 'r') as file:
        for line in file:
            
            # Extract data lines
            if line.startswith("Data:"):
                row = line.replace("Data:", "").split(";")
                
                # New section
                if not str.isdigit(row[0]): 
                    
                    # Header line
                    if not header:
                        header = row
                        
                    # Start of new data section
                    else:
                        df = pd.DataFrame(rows[1:], columns=header)
                        df = df.set_index('Index')
                        sections.append(df)
                        rows = []
                else:
                    rows.append(row)    
        
        # Append last section
        if rows:
            df = pd.DataFrame(rows[1:], columns=header)
            df = df.set_index('Index')
            sections.append(df)
    
    return sections

def raw_to_mmHg(raw):
    '''
    Convert raw AD-value to mmHg.
    '''
    sensitivity = 0.1761
    return sensitivity * raw.astype(float)

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
    
def convert_data(df):
    
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df = df.rename_axis("Time")
    df.index = df.index / fs
    
    df["Raw0"] = raw_to_mmHg(df["Raw0"])
    df["Fast0"] = raw_to_mmHg(df["Fast0"])
    df["Slow0"] = raw_to_mmHg(df["Slow0"])
    
    df["Raw1"] = raw_to_mmHg(df["Raw1"])
    df["Fast1"] = raw_to_mmHg(df["Fast1"])
    df["Slow1"] = raw_to_mmHg(df["Slow1"])
    
    df["Systolic"] = df["Systolic"] / 10
    df["Diastolic"] = df["Diastolic"] / 10
    df["BPDiff"] = df["BPDiff"] / 10
    df["SlowBPDiff"] = df["SlowBPDiff"] / 10
    
    df["Pulse BPM"] = pulse_bpm(df)
    df["BPStable"] = df["BPStable"].astype(float)
    
    df["BalloonHigh"] = df["BalloonHigh"] / 10
    df["BalloonLow"] =  df["BalloonLow"] / 10
    df["BalloonDiff"] = df["BalloonDiff"] / 10
    
    df["AirTemp"] = df["AirTemp"] / 10
    df["AirPres"] = df["AirPres"] / 10 - 750
    df["SubjTemp"] = df["SubjTemp"] / 10
    
    df["BattRaw"] = (df["BattRaw"] * 100) / 4095
    df["BattFast"] = (df["BattFast"] * 100) / 4095
    df["BattSlow"] = (df["BattSlow"] * 100) / 4095
    
    df["VrefintRaw"] = (df["VrefintRaw"] * 30) / 4095
    df["VrefintFast"] = (df["VrefintFast"] * 30) / 4095
    df["VrefintSlow"] = (df["VrefintSlow"] * 30) / 4095
                                     
    df["MotorPos"] = df["MotorPos"] / 1000              
    df["State"] = df["State"] * 10
    
    df["Inflate"] = df['Buttons'].apply(lambda x: (int(x) & 0x03) * 10)
    df["Deflate"] = df['Buttons'].apply(lambda x: ((int(x) & 0x0C) >> 2) * 10)
    df["Alarm Ack"] = df['Buttons'].apply(lambda x: ((int(x) & 0x30) >> 4) * 10)
    
    df["TgtSpeed"] = df["TgtSpeed"] / 100
    df["CurSpeed"] = df["CurSpeed"] / 100
    
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
    df.rename(columns={'Raw0': 'Tip, raw',
                       'Fast0': 'Tip, fast',
                       'Slow0': 'Tip, slow',
                       'Raw1': 'Balloon, raw',
                       'Fast1': 'Balloon, fast',
                       'Slow1': 'Balloon, slow'
                       }, inplace=True)
    
    
    # Drop unused variables
    df.drop(['PumpWheel', 'Buttons', 'BVDebug', 'TipComp', 'BalloonComp', 'TipJOFR', 'BalloonJOFR'], 
            axis=1, inplace=True)
    #TODO: Comments, alarms
    
    return df

def find_file():
        
    try:
        root = Tk()
        root.attributes('-topmost', True)  # Display the dialog in the foreground.
        root.iconify()  # Hide the little window.
        file_path = askopenfilename(
            title='Select data file', 
            parent=root, 
            filetypes=[("TXT files", "*.txt")])
        print("File selected: ", file_path)
        root.destroy()  # Destroy the root window when folder selected.
        return file_path
    except FileNotFoundError():
        print("File not found")
        return None

def measure_time(df, state_start, state_end):
    """
    Measures the elapsed time during specific events (inflation, deflation, etc.), based on the State and Time signal.
    """
    try:
        if ('Time' != df.index.name) or ('State' not in df):
            raise KeyError("The DataFrame must contain 'Time' and 'State' columns.")

        elapsed_times = []  
        event = False
        for i, value in df['State'].items():
            
            # Start of event
            if (value == state_start) and not event:
                start_time = i
                event = True
            
            # End of event
            if (value == state_end) and event:
                end_time = i
                duration = end_time - start_time
                if duration > 1:
                    elapsed_times.append({
                        "start_time": round(start_time),
                        "end_time": round(end_time),
                        "duration": round(duration)
                    })
                event = False
        return elapsed_times

    except Exception as e:
        print(f"Error in measure_inflation: {e}")
        return None

def measure_inflation():
    
    # Measure inlfation and deflation times
    time_to_inflation = measure_time(df, 30, 50)[0]
    inflation_times = measure_time(df, 50, 80)
    deflation_times = measure_time(df, 100, 30)
    
    fig = display_figure(df)
    for event in inflation_times:
        highlight_area(fig, event['start_time'], event['end_time'], color="darkred", label="inflation")
    for event in deflation_times:
        highlight_area(fig, event['start_time'], event['end_time'], color="darkblue", label="deflation")
    
    # Dynamically generate the event info content
    event_info_content = html.Div(
        style={'display': 'flex', 'justifyContent': 'space-between', 'width': '100%'},
        children=[
            
            # Time to inflation
            html.Div(
                children=[
                    html.Div(
                        f"Time to inflation: [{time_to_inflation['start_time']} - {time_to_inflation['end_time']}] s, Duration = {time_to_inflation['duration']} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    )
                ],
                style={'flex': '1', 'marginRight': '20px'}
            ),
            
            # Inflation events
            html.Div(
                children=[
                    html.Div(
                        f"Inflation event {i+1}: [{event['start_time']} - {event['end_time']}] s, Duration = {event['duration']} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    ) for i, event in enumerate(inflation_times)
                ],
                style={'flex': '1', 'marginRight': '20px'}
            ),
            
            # Deflation events
            html.Div(
                children=[
                    html.Div(
                        f"Deflation event {i+1}: [{event['start_time']} - {event['end_time']}] s, Duration = {event['duration']} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    ) for i, event in enumerate(deflation_times)
                ],
                style={'flex': '1', 'marginLeft': '20px'}
            )
        ]
    )
    
    return fig, event_info_content

def extract_data(zoom_range, variable):
    
    # No zoom range selected, take the full range of the index
    if zoom_range is None or 'x_min' not in zoom_range or 'x_max' not in zoom_range:
        extracted_data = df[variable]
        zoom_info = "Full Range (No Zoom)"
    
    else:
        # Extract the data in the zoomed range
        x_min, x_max = zoom_range['x_min'], zoom_range['x_max']
        mask = (df.index >= x_min) & (df.index <= x_max)
        extracted_data = df.loc[mask, variable]
        zoom_info = f"Zoom Range: [{round(x_min)} - {round(x_max)}] s"
      
    # Display results
    average_pressure = round(sum(extracted_data) / len(extracted_data), 2)
    data = f"Average pressure: {average_pressure} mmHg"
    
    output = html.Div([
        html.P(zoom_info),
        html.P(f"Selected variable: {variable}"),
        html.P(data)
        ])
    
    return output

# -----------------------------------------------------------------------------------
# Start app

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MORPH], title="BEAT")

#------------------------------------------------------------------------------------
# Import and clean data
file_path = find_file()
sections = read_data(file_path)

print("Number of sections detected: ", len(sections))

df = pd.concat(sections, ignore_index=True)

df = convert_data(df)


#-----------------------------------------------------------------------------------
# App layout
bg_colour = '#d6eaf8'  #Light blue-grey

app.layout = html.Div(
    style = {'backgroundColor': bg_colour},
    
    children = [
    
        html.H1("BEAT visualization app", style={'marginLeft': '20px'}),
        
        # html.Button("Select data file", id='file-button', style={'marginLeft': '20px'}),
        
        dcc.Graph(id='plot', figure=display_figure(df), style={"backgroundColor": bg_colour}),
        html.Button("Toggle inflation phases", id='inflation_button', style={'marginLeft': '20px'}, n_clicks=0),
        
        html.H2("Statistics", style={'marginTop': '20px', 'marginLeft': '20px'}),
        
        dcc.Dropdown(
            id='stat_selector',
            options=[
                {'label': 'Select category', 'value': 'none'},
                {'label': 'Inflation', 'value': 'inflation'},
                {'label': 'Pressure', 'value': 'pressure'}
            ],
            value='none', 
            style={'width': '35%', 'marginBottom': '20px', 'marginLeft': '20px'}
            ),
        
        html.Div(id='stat_display', style={'marginLeft': '20px'}),
        
        html.Div(id='event-info', style={'display': 'block', 'marginLeft': '20px'}),
        
        # Store for zoom range
        dcc.Store(id='zoom-store', data=None)
    ])


#----------------------------------------------------------------------------------
# Connect the components

# Callback to toggle inflation phases
@app.callback(
    Output('plot', 'figure'),
    Input('inflation_button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_phases(clicks):
    
    visibility = clicks % 2
    fig = display_figure(df)
    
    if visibility:
        inflation_times = measure_time(df, 50, 80)
        deflation_times = measure_time(df, 100, 30)
        for event in inflation_times:
            highlight_area(fig, event['start_time'], event['end_time'], color="darkred", label="inflation")
        for event in deflation_times:
            highlight_area(fig, event['start_time'], event['end_time'], color="darkblue", label="deflation")
    return fig

# Callback to update the zoom range
@app.callback(
    Output('zoom-store', 'data'),
    Input('plot', 'relayoutData'),
    prevent_initial_call=True
)
def update_zoom_range(relayout_data):
    if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
        return {
            'x_min': relayout_data['xaxis.range[0]'],
            'x_max': relayout_data['xaxis.range[1]']
        }
    return None



@app.callback(
    Output('stat_display', 'children'),
    [Input('stat_selector', 'value'),
     Input('zoom-store', 'data')]
)
def select_stat(selected_stat, zoom_range):
    
    # Display inflation / diflation statistics
    if selected_stat == 'inflation':
        fig, stat = measure_inflation()
        return html.P(stat)
    
    # Display pressure statistics
    elif selected_stat == 'pressure':
        stat = extract_data(zoom_range, "Balloon, slow")
        return stat
    else:
        return html.Div([
            html.P("Select a category to display relevant statistics."),
        ])
 
    
if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8050/")
    app.run_server(debug=True, use_reloader=False)



    