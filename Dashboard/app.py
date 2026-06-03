import dash
from dash import dcc, html, Input, Output, State, ALL, ctx
import plotly.express as px
import pandas as pd
import json

# === LOAD DATA ===
with open('oregon_counties.geojson') as f:
    counties_geojson = json.load(f)

all_oregon_counties = [f['properties']['NAME'] for f in counties_geojson['features']]

df = pd.read_csv("fires_with_drought.csv", low_memory=False)
bad_counties = ['ERROR: #N/A', 'Not Found', 'Other State']
df = df[~df['County'].isin(bad_counties)]
df['EstTotalAcres'] = pd.to_numeric(df['EstTotalAcres'], errors='coerce')


def make_complete_df(by_county, value_col):
    complete = pd.DataFrame({'County': all_oregon_counties})
    complete = complete.merge(by_county, on='County', how='left')
    complete[value_col] = complete[value_col].fillna(0)
    return complete


def uncertainty_to_tier(score):
    """Convert mean uncertainty score to glyph tier."""
    if score == 0:
        return 'tier_none'
    elif score <= 0.5:
        return 'tier_0'
    elif score <= 1.0:
        return 'tier_1'
    elif score <= 2.0:
        return 'tier_2'
    else:
        return 'tier_3'


# === APP SETUP ===
app = dash.Dash(__name__)
app.title = "Oregon Wildfire Dashboard"

app.layout = html.Div([
    html.H1("Oregon Wildfire Dashboard: 2000-2025",
            style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),

    # Year slider
    html.Div([
        html.Label("Select year range:", style={'fontWeight': 'bold'}),
        dcc.RangeSlider(
            id='year-slider',
            min=2000, max=2025, step=1, value=[2000, 2025],
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
            html.H3("Avg Drought Severity by County", style={'textAlign': 'center'}),
            dcc.Graph(id='drought-map')
        ], style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.Hr(),

    # Middle row: cause glyphs + fire points map
    html.Div([
        html.Div([
            html.H3("Fire Causes (click to filter)", style={'textAlign': 'center'}),

            # Uncertainty legend
            html.Div([
                html.Div("Glyph color = attribution uncertainty",
                         style={'fontSize': '12px', 'fontWeight': 'bold',
                                'textAlign': 'center', 'marginBottom': '8px'}),
                html.Div([
                    html.Div([
                        html.Img(src='/assets/tier_none.png',
                                 style={'width': '30px', 'height': '30px'}),
                        html.Div("None (0)", style={'fontSize': '10px'})
                    ], style={'display': 'inline-block', 'margin': '0 8px', 'textAlign': 'center'}),
                    html.Div([
                        html.Img(src='/assets/tier_0.png',
                                 style={'width': '30px', 'height': '30px'}),
                        html.Div("Very low", style={'fontSize': '10px'})
                    ], style={'display': 'inline-block', 'margin': '0 8px', 'textAlign': 'center'}),
                    html.Div([
                        html.Img(src='/assets/tier_1.png',
                                 style={'width': '30px', 'height': '30px'}),
                        html.Div("Low", style={'fontSize': '10px'})
                    ], style={'display': 'inline-block', 'margin': '0 8px', 'textAlign': 'center'}),
                    html.Div([
                        html.Img(src='/assets/tier_2.png',
                                 style={'width': '30px', 'height': '30px'}),
                        html.Div("Medium", style={'fontSize': '10px'})
                    ], style={'display': 'inline-block', 'margin': '0 8px', 'textAlign': 'center'}),
                    html.Div([
                        html.Img(src='/assets/tier_3.png',
                                 style={'width': '30px', 'height': '30px'}),
                        html.Div("High", style={'fontSize': '10px'})
                    ], style={'display': 'inline-block', 'margin': '0 8px', 'textAlign': 'center'})
                ], style={'textAlign': 'center'}),
                html.Div("Size = fire count", style={
                    'fontSize': '11px', 'textAlign': 'center',
                    'marginTop': '8px', 'fontStyle': 'italic'
                })
            ], style={
                'border': '1px solid #ddd', 'borderRadius': '8px',
                'padding': '12px', 'margin': '10px', 'background': '#fafafa'
            }),

            html.Div([
                html.Button("Reset", id='reset-button',
                            style={'margin': '5px', 'padding': '8px 16px'})
            ], style={'textAlign': 'center'}),

            html.Div(id='cause-glyphs', style={
                'display': 'flex', 'flexWrap': 'wrap',
                'justifyContent': 'center', 'padding': '20px'
            })
        ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.H3(id='fire-map-title', style={'textAlign': 'center'}),
            dcc.Graph(id='fire-points-map')
        ], style={'width': '59%', 'display': 'inline-block'})
    ]),

    dcc.Store(id='selected-cause', data=None)
], style={'fontFamily': 'sans-serif'})


# === CALLBACKS ===
@app.callback(Output('acres-map', 'figure'), Input('year-slider', 'value'))
def update_acres_map(year_range):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    by_county = filtered.groupby('County', as_index=False)['EstTotalAcres'].sum()
    complete = make_complete_df(by_county, 'EstTotalAcres')
    fig = px.choropleth_map(
        complete, geojson=counties_geojson, locations='County',
        featureidkey='properties.NAME', color='EstTotalAcres',
        color_continuous_scale='OrRd', map_style='carto-positron',
        center={'lat': 44, 'lon': -120.5}, zoom=5.3, opacity=0.7,
        hover_data={'County': True, 'EstTotalAcres': ':,.0f'},
        labels={'EstTotalAcres': 'Acres burned'}
    )
    fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
    return fig


@app.callback(Output('drought-map', 'figure'), Input('year-slider', 'value'))
def update_drought_map(year_range):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    by_county = filtered.groupby('County', as_index=False)['DSCI'].mean()
    complete = make_complete_df(by_county, 'DSCI')
    fig = px.choropleth_map(
        complete, geojson=counties_geojson, locations='County',
        featureidkey='properties.NAME', color='DSCI',
        color_continuous_scale='YlOrBr', map_style='carto-positron',
        center={'lat': 44, 'lon': -120.5}, zoom=5.3, opacity=0.7,
        hover_data={'County': True, 'DSCI': ':.1f'},
        labels={'DSCI': 'Avg drought'}
    )
    fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
    return fig


@app.callback(
    Output('cause-glyphs', 'children'),
    Input('year-slider', 'value')
)
def update_cause_glyphs(year_range):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    stats = filtered.groupby('GeneralCause').agg(
        count=('GeneralCause', 'size'),
        uncertainty=('UncertaintyScore', 'mean')
    ).reset_index()
    stats = stats.sort_values('count', ascending=False)

    max_count = stats['count'].max() if len(stats) > 0 else 1

    glyphs = []
    for _, row in stats.iterrows():
        size = 50 + (row['count'] / max_count) * 80
        tier = uncertainty_to_tier(row['uncertainty'])

        glyphs.append(
            html.Div([
                html.Img(
                    src=f'/assets/{tier}.png',
                    id={'type': 'cause-btn', 'cause': row['GeneralCause']},
                    style={
                        'width': f'{size}px', 'height': f'{size}px',
                        'cursor': 'pointer', 'margin': '5px'
                    }
                ),
                html.Div(row['GeneralCause'], style={
                    'textAlign': 'center', 'fontSize': '11px',
                    'maxWidth': f'{size}px', 'wordWrap': 'break-word'
                }),
                html.Div(f"n={row['count']}", style={
                    'textAlign': 'center', 'fontSize': '10px', 'color': '#888'
                })
            ], style={'margin': '10px', 'textAlign': 'center'})
        )
    return glyphs


@app.callback(
    Output('selected-cause', 'data'),
    [Input({'type': 'cause-btn', 'cause': ALL}, 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def update_selected_cause(glyph_clicks, reset_click):
    triggered = ctx.triggered_id
    if triggered == 'reset-button':
        return None
    if isinstance(triggered, dict) and triggered.get('type') == 'cause-btn':
        return triggered['cause']
    return None


@app.callback(
    [Output('fire-points-map', 'figure'),
     Output('fire-map-title', 'children')],
    [Input('year-slider', 'value'),
     Input('selected-cause', 'data')]
)
def update_fire_points(year_range, selected_cause):
    filtered = df[(df['FireYear'] >= year_range[0]) & (df['FireYear'] <= year_range[1])]
    title = f"Fire Locations ({year_range[0]}–{year_range[1]})"

    if selected_cause:
        filtered = filtered[filtered['GeneralCause'] == selected_cause]
        title = f"{selected_cause} fires ({year_range[0]}–{year_range[1]})"

    plot_df = filtered.dropna(subset=['Lat_DD', 'Long_DD']).copy()
    plot_df['EstTotalAcres'] = plot_df['EstTotalAcres'].fillna(0).clip(lower=0.1)

    fig = px.scatter_map(
        plot_df, lat='Lat_DD', lon='Long_DD',
        size='EstTotalAcres', size_max=15,
        hover_data=['FireName', 'GeneralCause', 'SpecificCause', 'County', 'EstTotalAcres'],
        map_style='carto-positron',
        center={'lat': 44, 'lon': -120.5}, zoom=5.3,
        opacity=0.6,
        color_discrete_sequence=['#C8102E']
    )
    fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
    return fig, title


if __name__ == '__main__':
    app.run(debug=True)