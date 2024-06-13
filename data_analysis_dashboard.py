import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
from flask import Flask
from dash.exceptions import PreventUpdate
import plotly.express as px

# Load data
df1 = pd.read_csv('Merged_Local_Authority_Data.csv')
df2 = pd.read_csv('Oflog.csv')

# Ensure 'local_authority_name' is a string and handle NaN values
df1['local_authority_name'] = df1['local_authority_name'].astype(str)
df2['Local authority name'] = df2['Local authority name'].astype(str)

# Initialize the Dash app and Server
external_stylesheets = ['assets/styles.css']
server = Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)


# Define the app layout with navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Div([
            html.H1("Data Explorer", style={'textAlign': 'center', 'color': '#007BFF'}),  # Blue color for header
            html.P("Navigate to different pages using the links below:", style={'textAlign': 'center', 'color': '#555'}),
            html.Div([
                html.Div(dcc.Link('Home', href='/', className='nav-link'), className='nav-box'),
                html.Div(dcc.Link('Social Care and EHCP Data', href='/explore-merged', className='nav-link'), className='nav-box'),
                html.Div(dcc.Link('Oflog Yearly Data', href='/explore-oflog', className='nav-link'), className='nav-box'),
                html.Div(dcc.Link('Compare Local Authorities', href='/compare-local-authorities', className='nav-link'), className='nav-box'),
                html.Div(dcc.Link('Regional Analysis', href='/regional-analysis', className='nav-link'), className='nav-box')
            ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'gap': '10px', 'margin': '20px'})
        ], className='header'),
        html.Div(id='page-content', className='content')
    ]),

], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9'})

# Define the home page layout
home_page = html.Div([
    html.H1("Welcome to the Agilisys Data Explorer Page", style={'textAlign': 'center', 'color': '#007BFF'}),  # Blue color for header
    html.P("Use the links above to navigate to different pages.", style={'textAlign': 'center', 'color': '#555'}),
    html.Div([
        html.Img(src='assets/transform_logo.png', style={'width': '100%', 'borderRadius': '10px'}),
        html.H2("Benchmark Local Authorities Performance Across Multiple Metrics", style={'textAlign': 'center', 'color': '#007BFF', 'marginTop': '20px'}),  # Blue color for subheader
        html.P("Dive into the datasets and uncover insights through interactive visualizations and comparisons.",
               style={'textAlign': 'center', 'color': '#555'}),
        html.P("Click on the links above to get started.", style={'textAlign': 'center', 'color': '#555'})
    ], style={'maxWidth': '800px', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.1)'})
])

# Define the page layout to explore merged local authorities data
explore_merged_page = html.Div([
    html.H3("Explore Social Care and EHCP Data"),
    dash_table.DataTable(
        id='merged-table',
        columns=[{"name": i, "id": i} for i in df1.columns],
        data=df1.to_dict('records')
    )
])

# Define the page layout to explore oflog data
explore_oflog_page = html.Div([
    html.H3("Explore Oflog Data"),
    dash_table.DataTable(
        id='oflog-table',
        columns=[{"name": i, "id": i} for i in df2.columns],
        data=df2.to_dict('records')
    )
])

# Define the page layout for comparing local authorities
compare_local_authorities_page = html.Div([
    html.H3("Compare Local Authorities"),
    dcc.Dropdown(
        id='local-authority-dropdown-compare',
        options=[{'label': i, 'value': i} for i in sorted(df1['local_authority_name'].dropna().unique())],
        value=[df1['local_authority_name'].dropna().unique()[0]],
        multi=True  # Allow multiple selections
    ),
    dcc.Dropdown(
        id='measure-dropdown-compare-df1',
        options=[
            {'label': f"{i}", 'value': f"{i}"} for i in df1.columns if i not in ['local_authority_name', 'region']
        ],
        value=df1.columns[2],  # Default to the third column (first measure column)
    ),
    dcc.Dropdown(
        id='measure-dropdown-compare-df2',
        options=[
            {'label': f"{i}", 'value': f"{i}"} for i in df2.columns if i not in ['Local authority name', 'Region', 'Financial year']
        ],
        value=df2.columns[3],  # Default to the fourth column (first measure column)
    ),
    dcc.Graph(id='comparison-chart-df1'),
    dcc.Graph(id='comparison-chart-df2')
])

# Define the regional analysis page layout with additional year selection
regional_analysis_page = html.Div([
    html.H3("Regional Analysis"),
    dcc.Dropdown(
        id='measure-dropdown-df1',
        options=[{'label': i, 'value': i} for i in df1.columns if i not in ['local_authority_name', 'region']],
        value=df1.columns[2]  # Default to the third column (first measure column)
    ),
    dcc.Dropdown(
        id='measure-dropdown-df2',
        options=[{'label': i, 'value': i} for i in df2.columns if i not in ['Financial year', 'Local authority name', 'Region']],
        value=df2.columns[3]  # Default to the fourth column (first measure column)
    ),
    dcc.Graph(id='regional-bar-chart-df1'),
    dcc.Graph(id='regional-line-chart-df2')
])

# Callback to update page content based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/explore-merged':
        return explore_merged_page
    elif pathname == '/explore-oflog':
        return explore_oflog_page
    elif pathname == '/compare-local-authorities':
        return compare_local_authorities_page
    elif pathname == '/regional-analysis':
        return regional_analysis_page
    else:
        return home_page

# Callback to update comparison charts for local authorities
@app.callback(
    Output('comparison-chart-df1', 'figure'),
    [Input('local-authority-dropdown-compare', 'value'),
     Input('measure-dropdown-compare-df1', 'value')]
)
def update_comparison_chart_df1(selected_local_authorities, selected_measure_df1):
    if not selected_local_authorities or not selected_measure_df1:
        raise PreventUpdate

    # Filter the DataFrame based on selections and explicitly copy it
    filtered_df = df1[df1['local_authority_name'].isin(selected_local_authorities)].copy()

    # Convert selected_measure to numeric using .loc, coerce errors to NaN
    filtered_df.loc[:, selected_measure_df1] = pd.to_numeric(filtered_df[selected_measure_df1], errors='coerce')

    # Drop rows where the selected measure is NaN after coercion
    filtered_df.dropna(subset=[selected_measure_df1], inplace=True)

    # Create a Plotly bar chart
    fig = px.bar(
        filtered_df,
        x='local_authority_name',
        y=selected_measure_df1,
        color='local_authority_name',
        title=f"Comparison of {selected_measure_df1} Across Local Authorities",
        labels={selected_measure_df1: selected_measure_df1}  # Update y-axis label
    )

    return fig

@app.callback(
    Output('comparison-chart-df2', 'figure'),
    [Input('local-authority-dropdown-compare', 'value'),
     Input('measure-dropdown-compare-df2', 'value')]
)
def update_comparison_chart_df2(selected_local_authorities, selected_measure_df2):
    if not selected_local_authorities or not selected_measure_df2:
        raise PreventUpdate

    # Filter the DataFrame based on selections and explicitly copy it
    filtered_df = df2[df2['Local authority name'].isin(selected_local_authorities)].copy()

    # Convert selected_measure to numeric using .loc, coerce errors to NaN
    filtered_df.loc[:, selected_measure_df2] = pd.to_numeric(filtered_df[selected_measure_df2], errors='coerce')

    # Drop rows where the selected measure is NaN after coercion
    filtered_df.dropna(subset=[selected_measure_df2], inplace=True)

    # Create a Plotly line chart
    fig = px.line(
        filtered_df,
        x='Financial year',
        y=selected_measure_df2,
        color='Local authority name',
        title=f"Comparison of {selected_measure_df2} Over Time",
        labels={selected_measure_df2: selected_measure_df2}  # Update y-axis label
    )

    return fig

# Callback to update the regional bar chart for df1
@app.callback(
    Output('regional-bar-chart-df1', 'figure'),
    [Input('measure-dropdown-df1', 'value')]
)
def update_regional_bar_chart_df1(selected_measure_df1):
    if not selected_measure_df1:
        raise PreventUpdate

    # Group by region and calculate average
    avg_df = df1.groupby('region')[selected_measure_df1].mean().reset_index()

    # Create a Plotly bar chart
    fig = px.bar(
        avg_df,
        x='region',
        y=selected_measure_df1,
        title=f"Average {selected_measure_df1} by Region",
        labels={selected_measure_df1: selected_measure_df1}  # Update y-axis label
    )

    return fig

# Callback to update the regional line chart for df2
@app.callback(
    Output('regional-line-chart-df2', 'figure'),
    [Input('measure-dropdown-df2', 'value')]
)

def update_regional_line_chart_df2(selected_measure_df2):
    if not selected_measure_df2:
        raise PreventUpdate

    # Convert selected_measure to numeric, if not already
    df2[selected_measure_df2] = pd.to_numeric(df2[selected_measure_df2], errors='coerce')

    # Group by region and financial year and calculate average
    grouped_df = df2.groupby(['Region', 'Financial year'])[selected_measure_df2].mean().reset_index()

    # Create a Plotly line chart
    fig = px.line(
        grouped_df,
        x='Financial year',
        y=selected_measure_df2,
        color='Region',
        title=f"{selected_measure_df2} Over Time by Region",
        labels={selected_measure_df2: selected_measure_df2}  # Update y-axis label
    )

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
