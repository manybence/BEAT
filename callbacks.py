# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 13:05:59 2025

@author: Bence Many

BEAT visualization tool - Callback functions
"""

import dash
from dash import Input, Output, State, no_update
from dash import html
import os
import signal
import functions as func

def register_callbacks(app, df, plot_title):
    
    # Callback for the shutdown button
    @app.callback(
        Output("redirect", "href"),
        Input("shutdown-button", "n_clicks"),
        prevent_initial_call=True
    )
    def shutdown_server(n_clicks):
        if n_clicks > 0:
            # Inject a redirect to /shutdown
            return "/shutdown"
        return dash.no_update
            
    @app.server.route('/shutdown')
    def shutdown_page():
        # Send signal to terminate the process
        os.kill(os.getpid(), signal.SIGINT)
        return """
        <script>
            alert("Server is shutting down. This tab will close automatically.");
            window.close();
        </script>
        """

    # Callback to toggle inflation phases
    @app.callback(
        Output('plot', 'figure'),
        Input('inflation_button', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_phases(clicks):
        
        visibility = clicks % 2
        fig = func.display_figure(df, plot_title)
        
        if visibility:
            inflation_times = func.measure_time(df, 50, 80)
            deflation_times = func.measure_time(df, 100, 30)
            pause_times = func.measure_duration(df, 120)
            
            # Highlight plot areas
            for event in inflation_times:
                func.highlight_area(fig, event['start_time'], event['end_time'], color="darkred", label="inflation")
            for event in deflation_times:
                func.highlight_area(fig, event['start_time'], event['end_time'], color="darkblue", label="deflation")
            for event in pause_times:
                func.highlight_area(fig, event['start_time'], event['end_time'], color="gray", label="pause")
                
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
        Output('var_selector', 'style'),
        [Input('stat_selector', 'value')],
         [State('var_selector', 'style')]
    )
    def select_stat(selected_stat, current_style):
        
        updated_style = current_style.copy()
        
        # Display variable selector
        if selected_stat == 'measure':
            updated_style['display'] = 'block'
            return updated_style
        else:
            updated_style['display'] = 'none'
            return updated_style
        
    @app.callback(
        Output('stat_display', 'children'),
        [Input('stat_selector', 'value'),
         Input('zoom-store', 'data'),
         Input('var_selector', 'value')]
    )
    def select_var(selected_stat, zoom_range, selected_var):
        
        # Display inflation / diflation statistics
        if selected_stat == 'inflation':
            stat = func.measure_inflation(df)
            return html.P(stat)
        
        # Display pressure statistics
        elif selected_stat == 'measure' and selected_var:
            stat = func.extract_data(df, zoom_range, selected_var)
            return stat
        
        # Default
        else:
            return html.Div([
                html.P("Select a variable to display relevant statistics.")
            ])
     
        
