import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import json

# === LOAD DATA ===
with open('oregon_counties.geojson') as f:
    counties_geojson = json.load(f)

all_oregon_counties = [f['properties']['NAME'] for f in counties_geojson['features']]

df = pd.read_csv("fires_with_drought.csv", low_memory=False)

# Clean
bad_counties = ['ERROR: #N/A', 'Not Found', 'Other State']
df = df[~df['County'].isin(bad_counties)]
df['EstTotalAcres'] = pd.to_numeric(df['EstTotalAcres'], errors='coerce')


# === HELPER FUNCTIONS ===
def make_complete_df(by_county, value_col):
    """Ensures all 36 Oregon counties appear in the choropleth."""
    complete = pd.DataFrame({'County': all_oregon_counties})
    complete = complete.merge(by_county, on='County', how='left')
    complete[value_col] = complete[value_col].fillna(0)
    return complete


# === APP SETUP ===
app = dash.Dash(__name__)
app.title = "Oregon Wildfire Dashboard"

app.layout = html.Div([
    html.H1("Oregon Wildfire Dashboard: 2000-2025",
            style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
    
    # Year range slider
    html.Div([
        html.Label("Select year range:", style={'fontWeight': 'bold', 'fontSize': '16px'}),
        dcc.RangeSlider(
            id='year-slider',
            min=2000, max=2025, step=1,
            value=[2000, 2025],
            marks={y: str(y) for y in range(2000, 2026, 5)},
            tooltip={'placement': 'bottom', 'always_visible': True}
        )
    ], style={'padding': '20px 40px'}),
    
    # Top row: two choropleths
    html.Div([
        html.Div([
            html.H3("Acres Burned by County", style={'textAlign': 'center'}),
            dcc.Graph(id='acres-map')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            html.H3("Average Drought Severity (DSCI) by County", style={'textAlign': 'center'}),
            dcc.Graph(id='drought-map')
        ], style={'width': '49%', 'display': 'inline-block'})
    ], style={'fontFamily': 'sans-serif'})
])


# === CALLBACKS ===
@app.callback(
    Output('acres-map', 'figure'),
    Input('year-slider', 'value')
)
def update_acres_map(year_range):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    by_county = filtered.groupby('County', as_index=False)['EstTotalAcres'].sum()
    complete = make_complete_df(by_county, 'EstTotalAcres')
    
    fig = px.choropleth_map(
        complete,
        geojson=counties_geojson,
        locations='County',
        featureidkey='properties.NAME',
        color='EstTotalAcres',
        color_continuous_scale='OrRd',
        map_style='carto-positron',
        center={'lat': 44, 'lon': -120.5},
        zoom=5.3,
        opacity=0.7,
        hover_data={'County': True, 'EstTotalAcres': ':,.0f'},
        labels={'EstTotalAcres': 'Acres burned'}
    )
    fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
    return fig


@app.callback(
    Output('drought-map', 'figure'),
    Input('year-slider', 'value')
)
def update_drought_map(year_range):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    by_county = filtered.groupby('County', as_index=False)['DSCI'].mean()
    complete = make_complete_df(by_county, 'DSCI')
    
    fig = px.choropleth_map(
        complete,
        geojson=counties_geojson,
        locations='County',
        featureidkey='properties.NAME',
        color='DSCI',
        color_continuous_scale='YlOrBr',
        map_style='carto-positron',
        center={'lat': 44, 'lon': -120.5},
        zoom=5.3,
        opacity=0.7,
        hover_data={'County': True, 'DSCI': ':.1f'},
        labels={'DSCI': 'Avg drought score'}
    )
    fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
    return fig


# === RUN ===
if __name__ == '__main__':
    app.run(debug=True)