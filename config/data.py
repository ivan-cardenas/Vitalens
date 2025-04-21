# data.py
"""
This module loads and processes external data for the Vitalens app.
It loads layers from a GeoPackage and a CSV file, converts data types,
computes extra columns, and prepares GeoDataFrames that will be used
by the rest of the application.
"""

import geopandas as gpd
import pandas as pd
import fiona
import numpy as np
from shapely.geometry import Polygon

# These values must be kept in sync with the ones in `data.py`
GPKG_FILE = "./Assets/Thematic_Data.gpkg"
LAYER_WELLS =  "Well_Capacity_Cost"
LAYER_INDUSTRIAL_WELLS = "Industrial_Extraction"
LAYER_PIPES = "Pipes_OD"
NATURE_DAMAGE_CSV = pd.read_csv("./Assets/NatuurEffect.csv")
CITIES_LAYER = "CitiesHexagonal"
YEAR_CALC = 2022
GROW_RATE = 0.0062
SMALL_BUSINESS_RATE = 1.2
DEMAND_PERCAPITA = 0.135
industrialExcess = 0


# Optimized Data Loading: Read all layers and then filter the required columns
def load_data(file_path):
    wells = gpd.read_file(file_path, layer=LAYER_WELLS)
    industrial = gpd.read_file(file_path, layer=LAYER_INDUSTRIAL_WELLS)
    main_pipes = gpd.read_file(file_path, layer=LAYER_PIPES)
    cities = gpd.read_file(file_path, layer=CITIES_LAYER)
    return wells, industrial, main_pipes, cities

wells, industrial, main_pipes, cities = load_data(GPKG_FILE)
hexagons = gpd.read_file(GPKG_FILE, layer="H3_Lvl8")
demand_capita, smallBusiness = DEMAND_PERCAPITA, SMALL_BUSINESS_RATE


# Standardize CRS once for all datasets
target_crs = "EPSG:28992"
wells = wells.to_crs(target_crs)
industrial = industrial.to_crs(target_crs)
main_pipes = main_pipes.to_crs(target_crs)
cities = cities.to_crs(target_crs)

# -----------------------
# Data Type Conversions and Calculations for Wells
# -----------------------

# Convert capacity and extraction columns to numeric values
wells["Permit__Mm3_per_jr_"] = pd.to_numeric(wells["Permit__Mm3_per_jr_"], errors="coerce")
wells["Extraction_2023__Mm3_per_jr_"] = pd.to_numeric(wells["Extraction_2023__Mm3_per_jr_"], errors="coerce")
wells["Agreement__Mm3_per_jr_"] = pd.to_numeric(wells["Agreement__Mm3_per_jr_"], errors="coerce")

# Calculate operational expenditure and environmental cost per m³ for wells
wells["totOpex_m3"] = (wells["OPEX"] + wells["Labor_EUR_m3"] +
                        wells["Energy_EUR_m3"] + wells["Chemicals_EUR_m3"] +
                        wells["Tax_EUR_m3"])
wells["env_cost_m3"] = wells["CO2Cost_EUR_m3"] + wells["DroughtDamage_EUR_m3"]

# -----------------------
# Create Active Wells DataFrame
# -----------------------

# Create a GeoDataFrame for active wells (this dataframe will be updated by user interactions)
active_wells_df = gpd.GeoDataFrame({
    "Name": wells["Name"],
    "Num_Wells": wells["Num_Wells"],
    "Ownership": wells["Inside_Prop"],
    "Max_permit": wells["Permit__Mm3_per_jr_"],
    "Balance area": wells["Balansgebied"],
    "Active": [True] * len(wells),
    "Current Extraction": wells["Extraction_2023__Mm3_per_jr_"],
    "Value": wells["Extraction_2023__Mm3_per_jr_"],
    "OPEX_m3": wells["totOpex_m3"],
    "Drought_m3": wells["DroughtDamage_EUR_m3"],
    "CO2_m3": wells["CO2Cost_EUR_m3"],
    "Env_m3": wells["env_cost_m3"],
    "envCost": wells["env_cost_m3"]
    * wells["Extraction_2023__Mm3_per_jr_"]
    * 1000000,
    "OPEX": wells["totOpex_m3"] * wells["Extraction_2023__Mm3_per_jr_"] * 1000000,
    "CAPEX": 0,
    "geometry": wells["geometry"],
})
active_wells_df.astype({"Num_Wells": "int32", "Ownership": "int32"}, copy=False)
active_wells_df.set_crs(epsg=28992, inplace=True)



# -----------------------
# Initialize dictionaries
# -----------------------

# Initialize a dictionary to hold the active state and slider references
active_wells = {}

# Initialize a dictionary to hold the balance area layouts
balance_area_buttons = {}

# Initialize a dictionary to hold the sliders
checkboxes = {}

# -----------------------
# Process Cities Data
# -----------------------

cities_clean = gpd.GeoDataFrame({
    "cityName": cities["statnaam"],
    "Population 2022": cities["SUM_Pop_2022"],
    "Water Demand": cities["SUM_Water_Demand_m3_YR"] / 1000000,
    "geometry": cities["geometry"],
})
cities_clean.loc[cities_clean["cityName"].isna(), "Water Demand"] = None

# -----------------------
# Process Hexagons Data (Balance Areas)
# -----------------------

# Function to map numeric type codes to descriptive text
def assign_hexagon_type(row):
    if row["Type"] == 1:
        return "Source"
    elif row["Type"] == 2:
        return "Destination"
    elif row["Type"] == 3:
        return "Restricted Natura2000"
    elif row["Type"] == 4:
        return "Restricted Other"
    elif row["Type"] == 5:
        return "Source and Restricted"
    else:
        return "Germany"

hexagons["Type_T"] = hexagons.apply(assign_hexagon_type, axis=1)



# Create a filtered GeoDataFrame for hexagons with selected columns and computed water demand
hexagons_filterd = gpd.GeoDataFrame({
    "GRID_ID": hexagons["GRID_ID"],
    "Balance Area": hexagons["Name"],
    "Pop2022": hexagons["Pop_2022"],
    "Current Pop": hexagons["Pop_2022"],
    "Industrial Demand": hexagons["Ind_Demand"],
    "Water Demand": hexagons["Pop_2022"] * demand_capita * smallBusiness * 365 / 1000000,
    "Type": hexagons["Type_T"],
    "Source_Name": hexagons["Source_Name"],
    "geometry": hexagons["geometry"],
}, copy=False)

# Dissolve hexagons by "Balance Area" to obtain balance area boundaries
balance_areas = hexagons_filterd.dissolve(by="Balance Area", as_index=False)

# -----------------------
# Process NatuurEffect CSV Data for Environmental Damage
# -----------------------

naturaUnfiltered = NATURE_DAMAGE_CSV.copy()

# Create a DataFrame for moderate (Mid) Natura damage
naturaDamageMid = pd.DataFrame()
naturaDamageMid["Name"] = active_wells_df["Name"]

for idx, row in active_wells_df.iterrows():
    name = row["Name"]
    ratio_column = (row["Current Extraction"] / row["Max_permit"]) * 100
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "C-S"]
    if not well_data.empty:
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, f'{ratio_column:.0f}'] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "85-S"]
    if not well_data.empty:
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, "85"] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "P-S"]
    if not well_data.empty:
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, "100"] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "115-S"]
    if not well_data.empty:
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, "115"] = well_data.values[0]

# Create a DataFrame for high (Very Sensitive) Natura damage
naturaDamageHigh = pd.DataFrame()
naturaDamageHigh["Name"] = active_wells_df["Name"]

for idx, row in active_wells_df.iterrows():
    name = row["Name"]
    ratio_column = (row["Current Extraction"] / row["Max_permit"]) * 100
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "C-VS"]
    if not well_data.empty:
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, f'{ratio_column:.0f}'] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "85-VS"]
    if not well_data.empty:
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "85"] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "P-VS"]
    if not well_data.empty:
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "100"] = well_data.values[0]
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "115-VS"]
    if not well_data.empty:
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "115"] = well_data.values[0]

# -----------------------
# Pre-Computed Reference Variables
# -----------------------

original_OPEX = active_wells_df["OPEX"].sum() / 1000000
original_CO2 = (active_wells_df["CO2_m3"] * active_wells_df["Current Extraction"]).sum()
original_Draught = (active_wells_df["Drought_m3"] * active_wells_df["Current Extraction"]).sum()
original_excess = active_wells_df["Max_permit"].sum() - active_wells_df["Current Extraction"].sum()
original_demand = hexagons_filterd["Water Demand"].sum() + hexagons_filterd["Industrial Demand"].sum()


