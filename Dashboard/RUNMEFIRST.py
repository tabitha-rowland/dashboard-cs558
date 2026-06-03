import json

# Load all US counties
with open('oregon_counties.geojson') as f:
    geo = json.load(f)

# Filter to Oregon only (state FIPS = 41)
oregon_features = [f for f in geo['features'] if f['properties']['STATE'] == '41']

print(f"Filtered to {len(oregon_features)} Oregon counties")
print("Sample names:", [f['properties']['NAME'] for f in oregon_features[:5]])

# Save filtered version
geo['features'] = oregon_features
with open('oregon_counties.geojson', 'w') as f:
    json.dump(geo, f)

print("Saved filtered oregon_counties.geojson")

# OK now go run app.py and open the ip address in your browser to see the dashboard