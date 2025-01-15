# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 13:08:35 2025

@author: Bence Many

BEAT visualization tool - Functions
"""
import plotly.graph_objects as go
import psutil
from dash import html

bg_colour = '#d6eaf8'  #Light blue-grey

def release_port(port):
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        connections = proc.info.get('connections', [])
        if connections:  # Only proceed if there are connections to check
            for conn in connections:
                if conn.laddr.port == port:
                    proc.terminate()  # Terminate the process holding the port
                    return

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
    
def display_figure(df, title):
    
    default_items = ["Systolic", "Battery", "Inflate", "Catheter", "Balloon, slow", "State"]
    color_mapping = {
        "State": "black",
        "Inflate": "red"
    }
    
    fig = go.Figure()
    
    for column in df.columns:
        visibility = True if column in default_items else False
        fig.add_trace(
            go.Scatter(
                x=df.index, 
                y=df[column], 
                name=column, 
                mode="lines", 
                visible=visibility if visibility else "legendonly",
                line=dict(color=color_mapping.get(column))
        ))

    fig.update_layout(
        height=600,
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Pressure (mmHg)",
        legend_title="Variables",
        uirevision='dynamic',  # Preserve zoom state across updates
        hovermode="x unified",  # Show all values at the same x position on hover
        hoverdistance=15,       # Distance of hover label
        paper_bgcolor=bg_colour,
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
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration
                    })
                event = False
        return elapsed_times

    except Exception as e:
        print(f"Error in measure_time: {e}")
        return None
    
def measure_duration(df, state):
    """
    Measures the duration of specific states (Pause, etc.), based on the State and Time signal.
    """
    try:
        if ('Time' != df.index.name) or ('State' not in df):
            raise KeyError("The DataFrame must contain 'Time' and 'State' columns.")

        elapsed_times = []  
        event = False
        for i, value in df['State'].items():
            
            # Start of event
            if (value == state) and not event:
                start_time = i
                event = True
            
            # End of event
            if (value != state) and event:
                end_time = i
                duration = end_time - start_time
                if duration > 1:
                    elapsed_times.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration
                    })
                event = False
        return elapsed_times

    except Exception as e:
        print(f"Error in measure_inflation: {e}")
        return None

def measure_inflation(df):
    
    # Measure inlfation and deflation times
    time_to_inflation = measure_time(df, 30, 50)[0]
    inflation_times = measure_time(df, 50, 80)
    deflation_times = measure_time(df, 100, 30)
    pause_times = measure_duration(df, 120)
    
    # Dynamically generate the event info content
    event_info_content = html.Div(
        style={'display': 'flex', 'justifyContent': 'space-between', 'width': '100%'},
        children=[
            
            # Time to inflation
            html.Div(
                children=[
                    html.Div(
                        f"Time to inflation: [{round(time_to_inflation['start_time'])} - {round(time_to_inflation['end_time'])}] s, Duration = {round(time_to_inflation['duration'])} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    )
                ],
                style={'flex': '1', 'marginRight': '20px'}
            ),
            
            # Inflation events
            html.Div(
                children=[
                    html.Div(
                        f"Inflation event {i+1}: [{round(event['start_time'])} - {round(event['end_time'])}] s, Duration = {round(event['duration'])} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    ) for i, event in enumerate(inflation_times)
                ],
                style={'flex': '1', 'marginRight': '20px'}
            ),
            
            # Deflation events
            html.Div(
                children=[
                    html.Div(
                        f"Deflation event {i+1}: [{round(event['start_time'])} - {round(event['end_time'])}] s, Duration = {round(event['duration'])} s", 
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    ) for i, event in enumerate(deflation_times)
                ],
                style={'flex': '1', 'marginLeft': '20px'}
            ),
            
            # Pause events
            html.Div(
                children=[
                    html.Div(
                        f"Pause event {i+1}: [{round(event['start_time'])} - {round(event['end_time'])}] s, Duration = {round(event['duration'])} s",
                        style={'marginBottom': '10px', 'fontSize': '16px'}
                    ) for i, event in enumerate(pause_times)
                ],
                style={'flex': '1', 'marginLeft': '20px'}
            )
        ]
    )
    
    return event_info_content

def extract_data(df, zoom_range, variable):
    
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
    average_data = round(sum(extracted_data) / len(extracted_data), 2)
    min_data = round(min(extracted_data), 2)
    max_data = round(max(extracted_data), 2)
    
    output = html.Div([
        html.P(zoom_info),
        html.P(f"Selected variable: {variable}"),
        html.P(f"Average: {average_data}", style={'fontWeight': 'bold'}),
        html.P(f"Min: {min_data}", style={'fontWeight': 'bold'}),
        html.P(f"Max: {max_data}", style={'fontWeight': 'bold'}),        
        ])
    
    return output

