import plotly.express as px
import pandas as pd
import json

# Load GeoJSON
with open('oregon_counties.geojson') as f:
    counties_geojson = json.load(f)

all_oregon_counties = [f['properties']['NAME'] for f in counties_geojson['features']]

# Load fire data
df = pd.read_csv("fires_with_drought.csv", low_memory=False)

# Filter out bad county entries
bad_counties = ['ERROR: #N/A', 'Not Found', 'Other State']
df = df[~df['County'].isin(bad_counties)]

# Average drought severity per county (using DSCI as continuous measure)
drought_by_county = df.groupby('County', as_index=False)['DSCI'].mean()

# Complete dataframe with all Oregon counties
complete = pd.DataFrame({'County': all_oregon_counties})
complete = complete.merge(drought_by_county, on='County', how='left')
complete['DSCI'] = complete['DSCI'].fillna(0)

print(complete)

# Make the choropleth
fig = px.choropleth_map(
    complete,
    geojson=counties_geojson,
    locations='County',
    featureidkey='properties.NAME',
    color='DSCI',
    color_continuous_scale='YlOrBr',  # yellow → brown for drought
    map_style='carto-positron',
    center={'lat': 44, 'lon': -120.5},
    zoom=5.5,
    opacity=0.7,
    hover_data={'County': True, 'DSCI': ':.1f'}
)

fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
fig.show()