# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 16:53:29 2024

@author: Bence Many

BEAT visualization tool
"""

import os
import dash
from dash import dcc, html
import webbrowser
import dash_bootstrap_components as dbc
import time
import file_handler as fh
import functions as func
from callbacks import register_callbacks

#------------------------------------------------------------------------------------
# Import and clean the data file

file_path = fh.open_datafile()
plot_title="BEAT data - " + os.path.basename(file_path)
start_time = time.time()
df = fh.read_preproc_data(file_path) 
elapsed_time = time.time() - start_time
print(f"Data reading time: {round(elapsed_time, 2)} seconds")


#-----------------------------------------------------------------------------------
# App layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MORPH], title="BEAT")

plot_config = {'displayModeBar': True, 'displaylogo': False,'queueLength': 1}

app.layout = html.Div(
    style = {'backgroundColor': func.bg_colour},
    
    children = [
    
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "10px"},
            children=[
                html.H1("BEAT visualization tool", style={'margin': '0'}),
                html.Span("SW version: " + fh.sw_version, style={'marginRight': '20px', 'fontSize': '16px', 'color': '#555'})
            ]
        ),
        html.Div([
            html.Button(
                "Shutdown", 
                id="shutdown-button", 
                n_clicks=0,
                style={
                    "backgroundColor": "red", 
                    "color": "white", 
                    "padding": "10px 20px", 
                    "border": "none", 
                    "borderRadius": "5px", 
                    "cursor": "pointer"
                }
            )
        ], style={"display": "flex", "justifyContent": "flex-start", "padding":"10px"}),  # Flex container for right alignment
        
        # html.Button("Select data file", id='file-button', style={'marginLeft': '20px'}),
        
        dcc.Graph(id='plot', figure=func.display_figure(df, plot_title), config=plot_config, style={"backgroundColor": func.bg_colour}),
        html.Button("Toggle inflation phases", id='inflation_button', style={'marginLeft': '20px'}, n_clicks=0),
        
        html.H2("Statistics", style={'marginTop': '20px', 'marginLeft': '20px'}),
        
        dcc.Dropdown(
            id='stat_selector',
            options=[
                {'label': 'Select category', 'value': 'none'},
                {'label': 'Inflation', 'value': 'inflation'},
                {'label': 'Measure min, max, avg', 'value': 'measure'}
            ],
            value='none', 
            style={'width': '35%', 'marginBottom': '20px', 'marginLeft': '20px'}
            ),
        
        dcc.Dropdown(
            id='var_selector',
            options=[{'label': column, 'value': column} for column in df.columns],
            value='none', 
            style={'display': 'none', 'width': '35%', 'marginBottom': '20px', 'marginLeft': '20px'}
            ),
        
        html.Div(id='stat_display', style={'marginLeft': '20px'}),
        
        html.Div(id='event-info', style={'display': 'block', 'marginLeft': '20px'}),
        
        # Store for zoom range
        dcc.Store(id='zoom-store', data=None),
        
        dcc.Location(id="redirect", refresh=True)  # Redirect location
    ])


#----------------------------------------------------------------------------------
# Connect the components via callbacks

register_callbacks(app, df, plot_title)

if __name__ == "__main__":
    
    # Open new server
    try:
        webbrowser.open("http://127.0.0.1:8050/")
        app.run_server(debug=True, threaded=False, use_reloader=False)
    except KeyboardInterrupt:
        print("Server stopped gracefully.")


    