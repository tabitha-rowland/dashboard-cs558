hi

so first things first you need to have these installed:

- plotly
- dash
- pandas

then run this in your terminal to get the geojson file for oregon counties:

curl -o oregon_counties.geojson "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"


great, now use the "RUNMEFIRST.py" file to filter the geojson file to only include oregon counties.

last step is to run "app.py" and open the ip address in your browser to see the dashboard 


