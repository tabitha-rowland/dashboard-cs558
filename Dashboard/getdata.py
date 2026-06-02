import pandas as pd

# Load datasets
fires = pd.read_csv("ODF_Fire_Occurrence_25_years.csv", low_memory=False)
drought = pd.read_csv("drought_monitor_by_counties.csv")

# Clean drought data
drought['MapDate'] = pd.to_datetime(drought['MapDate'], format='%Y%m%d').astype('datetime64[ns]')
drought['County'] = drought['County'].str.replace(' County', '', regex=False).str.strip()
drought['DSCI'] = (drought['D0'] * 1 + drought['D1'] * 2 + drought['D2'] * 3 + 
                   drought['D3'] * 4 + drought['D4'] * 5)

def drought_bucket(dsci):
    if dsci == 0:
        return 'No Drought'
    elif dsci < 100:
        return 'Mild Drought'
    elif dsci < 200:
        return 'Moderate Drought'
    elif dsci < 350:
        return 'Severe Drought'
    else:
        return 'Extreme Drought'

drought['DroughtLevel'] = drought['DSCI'].apply(drought_bucket)

# Clean fire data
fires['Ign_DateTime'] = pd.to_datetime(fires['Ign_DateTime'], format='mixed', errors='coerce')
fires['IgnDate'] = pd.to_datetime(fires['Ign_DateTime'].dt.date).astype('datetime64[ns]')

# Merge: each fire gets the most recent drought reading for its county
drought_sorted = drought.sort_values('MapDate')
fires_sorted = fires.sort_values('IgnDate')

merged = pd.merge_asof(
    fires_sorted.dropna(subset=['IgnDate', 'County']),
    drought_sorted[['MapDate', 'County', 'DSCI', 'DroughtLevel']],
    left_on='IgnDate',
    right_on='MapDate',
    by='County',
    direction='backward'
)

merged = merged[merged['IgnDate'] >= '2000-01-04']

# Compute UncertaintyScore (mutually exclusive tiers)
def fire_uncertainty(row):
    gc = str(row['GeneralCause']) if pd.notna(row['GeneralCause']) else ''
    sc_is_null = pd.isna(row['SpecificCause'])
    sc = str(row['SpecificCause']) if pd.notna(row['SpecificCause']) else ''
    
    if gc == 'Under Invest':
        return 3
    if gc == 'Miscellaneous':
        return 2
    if sc_is_null or 'Other' in sc:
        return 1
    return 0

merged['UncertaintyScore'] = merged.apply(fire_uncertainty, axis=1)

# Keep just the columns needed
keep_cols = ['FireYear', 'FireName', 'EstTotalAcres', 'HumanOrLightning', 
             'CauseBy', 'GeneralCause', 'SpecificCause',
             'County', 'IgnDate', 'DSCI', 'DroughtLevel', 'UncertaintyScore',
             'Lat_DD', 'Long_DD']

merged = merged[keep_cols]
merged.to_csv('fires_with_drought.csv', index=False)

print(f"Done! {len(merged)} fires with full data")
print(f"Lat/long coverage: {merged['Lat_DD'].notna().sum()}/{len(merged)}")