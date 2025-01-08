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
import file_handler as fh
import time

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

# file_path = fh.find_file()
file_path = fh.open_datafile()
start_time = time.time()
df = fh.read_preproc_data(file_path) 
elapsed_time = time.time() - start_time
print(f"Data reading time: {round(elapsed_time, 2)} seconds")


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
    app.run_server(debug=True, threaded=False, use_reloader=False)



    