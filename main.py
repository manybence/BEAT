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
import file_handler as fh
import functions as func
from callbacks import register_callbacks

#------------------------------------------------------------------------------------
# Import and clean the data file

file_path = fh.open_datafile()
plot_title="File: " + os.path.basename(file_path)
df = fh.read_preproc_data(file_path) 


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
                html.H1("BEAT visualization tool", style={'marginLeft': '60px'}),
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
        ], style={"display": "flex", "justifyContent": "flex-start", "padding":"10px", "marginLeft":"60px"}),  # Flex container for right alignment
        
        # html.Button("Select data file", id='file-button', style={'marginLeft': '20px'}),
        
        dcc.Graph(id='plot', figure=func.display_figure(df, plot_title), config=plot_config, style={"backgroundColor": func.bg_colour}),
        html.Button("Inflation phases", id='inflation_button', style={'marginLeft': '60px'}, n_clicks=0),
        html.Button("Alarms", id='alarm_button', style={'marginLeft': '60px'}, n_clicks=0),
        html.Button("UI messages", id='ui_button', style={'marginLeft': '60px'}, n_clicks=0),
        html.Button("Catheter", id='wire_button', style={'marginLeft': '60px'}, n_clicks=0),
        
        dcc.Store(id='inf-phases-store', data={
            "inflation": func.measure_time(df, 50, 80),
            "deflation": func.measure_time(df, 100, 30),
            "pause": func.measure_duration(df, 120)
        }),
        
        dcc.Store(id='alarms-store', data=func.measure_text_duration(df, column="Alarm")),
        dcc.Store(id='ui-store', data=func.measure_text_duration(df, column="UI")),
        dcc.Store(id='wire-store', data=func.measure_text_duration(df, column="Wire")),
        
        html.H2("Statistics", style={'marginTop': '20px', 'marginLeft': '60px'}),
        
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


    