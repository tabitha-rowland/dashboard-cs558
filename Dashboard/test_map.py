import plotly.express as px
import pandas as pd
import json

# Load GeoJSON
with open('oregon_counties.geojson') as f:
    counties_geojson = json.load(f)

# Get all Oregon county names from the GeoJSON
all_oregon_counties = [f['properties']['NAME'] for f in counties_geojson['features']]

# Load fire data
df = pd.read_csv("fires_with_drought.csv", low_memory=False)

# Filter out bad county entries
bad_counties = ['ERROR: #N/A', 'Not Found', 'Other State']
df = df[~df['County'].isin(bad_counties)]

# Make sure EstTotalAcres is numeric
df['EstTotalAcres'] = pd.to_numeric(df['EstTotalAcres'], errors='coerce')

# Aggregate acres burned per county
by_county = df.groupby('County', as_index=False)['EstTotalAcres'].sum()

# Make a complete dataframe with ALL Oregon counties (NaN for missing)
complete = pd.DataFrame({'County': all_oregon_counties})
complete = complete.merge(by_county, on='County', how='left')

# After the merge, fill NaN with 0
complete['EstTotalAcres'] = complete['EstTotalAcres'].fillna(0)

print(complete)

# Make the choropleth
fig = px.choropleth_map(
    complete,
    geojson=counties_geojson,
    locations='County',
    featureidkey='properties.NAME',
    color='EstTotalAcres',
    color_continuous_scale='OrRd',
    map_style='carto-positron',
    center={'lat': 44, 'lon': -120.5},
    zoom=5.5,
    opacity=0.7,
    hover_data={'County': True, 'EstTotalAcres': ':,.0f'}
)

fig.update_layout(margin={'r':0, 't':0, 'l':0, 'b':0})
fig.show()