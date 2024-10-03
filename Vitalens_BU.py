import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
from bokeh.models.formatters import PrintfTickFormatter
import folium
from folium.features import Template
# import keplergl
from shapely.geometry import shape, Polygon, Point
from lonboard import Map, PathLayer, ScatterplotLayer
import branca
from functools import partial
import printingReport
import html
from io import StringIO
import sourcetypes
from scipy.optimize import curve_fit
from panel.custom import JSComponent


# Styling
globalCss_route= "Stylesheet.css"
cssStyle = ['''
/* Import Google Fonts */
@import url("https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap");

:host,
:root {
  --design-primary-color: #151931 !important;
  --design-secondary-color: #5266d9 !important;
  --design-primary-text-color: #f2f2ed !important;
  --design-secondary-text-color: #151931 !important;
  --bokeh-base-font: "Barlow", sans-serif, Verdana !important;
  --mdc-typography-font-family: "Barlow", sans-serif, Verdana !important;
  --panel-primary-color: #151931 !important;
  --panel-background-color: #f2f2ed !important;
  --panel-on-background-color: #151931 !important;
  --sidebar-width: 350px;
}

:host(.active) .bar {
    background-color: #ffc233 !important;    
}

:host(.bk-above) .bk-header .bk-tab{
    border: #F2F2ED !important;
    background: #00000014 !important
}


::-webkit-scrollbar-track
{
	background-color: #F5F5F5;
}

::-webkit-scrollbar
{
	width: 5px !important; 
	background-color: #F5F5F5;
}

::-webkit-scrollbar-thumb
{
	background-color: #CCC5B9 !important;
    radius: 1px
}

#sidebar, #main {
    background-color: #F2F2ED !important;
}

hr.dashed {
  border-top: 1px dashed;
  border-bottom: none;
}

.title {
  font-weight: 600 !important;
}

.bar {
        background-color: #6768ab;
    }

.bk-btn {
  border-radius: 0.5em !important;
}

.bk-btn bk-btn-primary {
    font-size: normal !important;
}

.bk-btn-group {
  height: 100%;
  display: flex;
  flex-wrap: inherit !important;
  align-items: center;
}

.bk-btn-primary{
    font-size: normal !important;
}

.bk-btn-success{
  background-position: center;
  font-weight: 400 !important;
  font-size: small !important;
  line-height: 1;
  margin: 3px 3px; 
  padding: 5px 10px !important;
  transition: background 0.8s;
  width: fit-content;
}

.bk-btn-warning {
  margin: 3px;   
}

.accordion-header button{
    color: #151931;
    background-color: #B4BFE4;
}


.bk-tab.bk-active {
    background: #d3d3cf !important;
    color: #d9534f !important;
}
'''
]

miniBox_style = {
    'background': '#e9e9e1',
    'border': '0.7px solid',
    'margin': '10px',
    "box-shadow": '4px 2px 6px #2a407e',
    "display": "flex"
}

buttonGroup_style = {
    'flex-wrap': 'wrap',
    'display': 'flex'
}


# Initialize extensions
pn.config.global_css = cssStyle
pn.config.css_files = cssStyle
pn.config.loading_spinner = 'petal'
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")
# pn.extension("ipywidgets")
pn.extension("echarts")
pn.extension(
    "tabulator", "ace", css_files=["https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"]
)
pn.extension('floatpanel')
pn.extension(notifications=True)


# Load the GeoPackage file
GPKG_FILE = "./Assets/Thematic_Data.gpkg"
layers = fiona.listlayers(GPKG_FILE)  # Load all layers

# Get Wells Attributes
wells = gpd.read_file(GPKG_FILE, layer="Well_Capacity_Cost")
industrial = gpd.read_file(GPKG_FILE, layer="Industrial_Extraction")
mainPipes = gpd.read_file(GPKG_FILE, layer="Pipes_OD")


# Convert the capacity columns to numeric, setting errors='coerce' will replace non-numeric values with NaN
wells["Permit__Mm3_per_jr_"] = pd.to_numeric(
    wells["Permit__Mm3_per_jr_"], errors="coerce"
)
wells["Extraction_2023__Mm3_per_jr_"] = pd.to_numeric(
    wells["Extraction_2023__Mm3_per_jr_"], errors="coerce"
)
wells["Agreement__Mm3_per_jr_"] = pd.to_numeric(
    wells["Agreement__Mm3_per_jr_"], errors="coerce"
)

# Calculate total costs per m3
wells["totOpex_m3"] = (
    wells["OPEX"]
    + wells["Labor_EUR_m3"]
    + wells["Energy_EUR_m3"]
    + wells["Chemicals_EUR_m3"]
    + wells["Tax_EUR_m3"]
)
wells["env_cost_m3"] = wells["CO2Cost_EUR_m3"] + wells["DroughtDamage_EUR_m3"]

# Initialize a DataFrame to hold the active state and slider values
active_wells_df = gpd.GeoDataFrame(
    {
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
    }
)
active_wells_df.astype({"Num_Wells": "int32", "Ownership": "int32"}, copy=False)
active_wells_df.set_crs(epsg=28992)

cities = gpd.read_file(GPKG_FILE, layer="CitiesHexagonal")

cities_clean = gpd.GeoDataFrame(
    {
        "cityName" : cities["statnaam"],
        "Population 2022": cities["SUM_Pop_2022"],
        "Water Demand": cities["SUM_Water_Demand_m3_YR"]/ 1000000,
        "geometry" : cities["geometry"]
    })

cities_clean.loc[cities_clean["cityName"].isna(), "Water Demand"] = None

yearCal = 2022
growRate = 0.0062
smallBussiness = 1.2
demand_capita = 0.135


# Get Destination Attributes
hexagons = gpd.read_file(GPKG_FILE, layer="H3_Lvl8")

# Create a new column 'Type_T' with default values
hexagons["Type_T"] = ""

# Iterate over rows and assign values based on the 'Type' column
for idx, row in hexagons.iterrows():
    if row["Type"] == 1:
        hexagons.at[idx, "Type_T"] = "Source"
    elif row["Type"] == 2:
        hexagons.at[idx, "Type_T"] = "Destination"
    elif row["Type"] == 3:
        hexagons.at[idx, "Type_T"] = "Restricted Natura2000"
    elif row["Type"] == 4:
        hexagons.at[idx, "Type_T"] = "Restricted Other"
    elif row["Type"] == 5:
        hexagons.at[idx, "Type_T"] = "Source and Restricted"
    else:
        hexagons.at[idx, "Type_T"] = "Germany"

hexagons_filterd = gpd.GeoDataFrame(
    {
        "GRID_ID": hexagons["GRID_ID"],
        "Balance Area": hexagons["Name"],
        "Pop2022": hexagons["Pop_2022"],
        "Current Pop": hexagons["Pop_2022"],
        "Industrial Demand": hexagons["Ind_Demand"],
        "Water Demand": hexagons["Pop_2022"] * demand_capita * smallBussiness * 365 / 1000000,
        "Type": hexagons["Type_T"],
        "Source_Name": hexagons["Source_Name"],
        "geometry": hexagons["geometry"],
    }, copy=False
)

balance_areas= hexagons_filterd.dissolve(by="Balance Area", as_index=False)

naturaUnfiltered = pd.read_csv("./Assets/NatuurEffect.csv")


naturaDamageMid = pd.DataFrame()

naturaDamageMid["Name"] = active_wells_df["Name"]
for index, row in active_wells_df.iterrows():
    name = row["Name"]
    ratio_column = (row["Current Extraction"]/row["Max_permit"])*100
    
    # Get the corresponding row from naturaUnfiltered based on the well name
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "C-S"]
    
    if not well_data.empty:  # Check if there's data for the well
        # Create a column in naturaDamage with the extraction ratio as part of the column name
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, f'{ratio_column:.0f}'] = well_data.values[0]  # Assuming single value extraction
    
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "85-S"]
    if not well_data.empty:
        naturaDamageMid.loc[naturaDamageMid["Name"] == name, "85"] = well_data.values[0]
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "P-S"]
    if not well_data.empty: naturaDamageMid.loc[naturaDamageMid["Name"] == name, "100"] = well_data.values[0]
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "115-S"]
    if not well_data.empty: naturaDamageMid.loc[naturaDamageMid["Name"] == name, "115"] = well_data.values[0]
    

naturaDamageHigh = pd.DataFrame()


naturaDamageHigh["Name"] = active_wells_df["Name"]
for index, row in active_wells_df.iterrows():
    name = row["Name"]
    ratio_column = (row["Current Extraction"]/row["Max_permit"])*100
    
    # Get the corresponding row from naturaUnfiltered based on the well name
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "C-VS"]
    
    if not well_data.empty:  # Check if there's data for the well
        # Create a column in naturaDamage with the extraction ratio as part of the column name
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, f'{ratio_column:.0f}'] = well_data.values[0]  # Assuming single value extraction
    
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "85-VS"]
    if not well_data.empty:
        naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "85"] = well_data.values[0]
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "P-VS"]
    if not well_data.empty: naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "100"] = well_data.values[0]
    
    well_data = naturaUnfiltered.loc[naturaUnfiltered["WELL"] == name, "115-VS"]
    if not well_data.empty: naturaDamageHigh.loc[naturaDamageHigh["Name"] == name, "115"] = well_data.values[0]

    
industrialExcess = 0

def calculate_total_extraction():
    """
    Calculate the total water extraction from active wells.

    Returns:
        float: Total water extraction in Mm3/yr.
    """
    global industrialExcess
    total = active_wells_df[active_wells_df["Active"]]["Value"].sum() + industrialExcess
    return total

def calculate_difference():
    """
    Calculate the total water extraction from active wells.

    Returns:
        float: Total water extraction in Mm3/yr.
    """
    total = calculate_total_extraction() - calculate_total_Demand()
    return total

def calculate_available():
    """
    Calculate the available water by subtracting the current extraction from the maximum permitted extraction.

    Returns:
        float: Available water in Mm3/yr.
    """
    total = (
        active_wells_df[active_wells_df["Active"]==True]["Max_permit"].sum()
        - active_wells_df[active_wells_df["Active"]==True]["Value"].sum()
    ) 
    return total

def calculate_industrial_extract():
    total = industrial["Current_Extraction_2019"].sum()
    return total

def calculate_ownership():
    """
    Calculate the percentage of land ownership for active wells.

    Returns:
        float: Percentage of land ownership.
    """
    total = (
        active_wells_df[active_wells_df["Active"]]["Ownership"].sum()
        / active_wells_df[active_wells_df["Active"]]["Num_Wells"].sum()
    )
    return total * 100

def calculate_total_OPEX():
    """
    Calculate the total operational expenditure (OPEX) for active wells.

    Returns:
        float: Total OPEX in million EUR/yr.
    """
    active_wells_df["OPEX"] = active_wells_df["OPEX_m3"] * active_wells_df["Value"] 

    total = (active_wells_df[active_wells_df["Active"]]["OPEX"]).sum()
    return total

def calculate_total_CAPEX():
    # CAPEX is the difference between Value and current extraction, if Value is higher
    active_wells_df["CAPEX"] = np.where(
        active_wells_df["Value"] > active_wells_df["Current Extraction"],
        (active_wells_df["Value"] - active_wells_df["Current Extraction"]) * 10,  # You can adjust the multiplier as needed
        0  # CAPEX is 0 if Value is less than or equal to current extraction
    )

    # Sum the CAPEX for all active wells
    total = active_wells_df[active_wells_df["Active"]]["CAPEX"].sum()
    return total   # Convert to million EUR
#   


def calculate_total_OPEX_by_balance():
    """
    Calculate the total OPEX grouped by balance areas.

    Returns:
        pd.Series: Total OPEX by balance area in million EUR/yr.
    """
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )/1000000

# def update_balance_opex():
#     """
#     Update OPEX indicators for balance areas.
#     """
#     balance_opex = calculate_total_OPEX_by_balance()
#     for balance, indicator in balance_opex_indicators.items():
#         indicator.value = balance_opex.get(balance, 0)

def calculate_total_envCost():
    """
    Calculate the total environmental cost for active wells.

    Returns:
        float: Total environmental cost.
    """
    total = (active_wells_df[active_wells_df["Active"]]["envCost"]).sum()
    return total

def calculate_total_envCost_by_balance():
    """
    Calculate the total environmental cost grouped by balance areas.

    Returns:
        pd.Series: Total environmental cost by balance area.
    """
    return (
        active_wells_df[active_wells_df["Active"]]
        .groupby("Balance area")["envCost"]
        .sum()
    )

def calculate_affected_Sensitive_Nature():
    """
    Calculate the total affected area by Natura2000 restrictions.

    Returns:
        float: Total affected area in hectares.
    """
    names = active_wells_df[active_wells_df["Active"]==True]
    
    midDamage = 0
    
    for index, row in names.iterrows():
        name = row["Name"]
        target = (row["Value"]/row["Max_permit"])*100
        mDamage = estimate_Damage_for_well(naturaDamageMid, name, target) 
    
        midDamage = midDamage + mDamage

    
    # restricted = hexagons_filterd[
    #     (hexagons_filterd["Source_Name"].isin(names))
    #     & (hexagons_filterd["Type"] == "Source and Restricted")
    # ]
    # total = restricted.shape[0]
    # ha = total * 629387.503078 / 100000
    return midDamage

def calculate_affected_VerySensitive_Nature():
    """
    Calculate the total affected area by Natura2000 restrictions.

    Returns:
        float: Total affected area in hectares.
    """
    names = active_wells_df[active_wells_df["Active"]==True]
    
    midDamage = 0
    for index, row in names.iterrows():
        name = row["Name"]
        target = (row["Value"]/row["Max_permit"])*100
        mDamage = estimate_Damage_for_well(naturaDamageHigh, name, target) 
    
        midDamage = midDamage + mDamage

    
    # restricted = hexagons_filterd[
    #     (hexagons_filterd["Source_Name"].isin(names))
    #     & (hexagons_filterd["Type"] == "Source and Restricted")
    # ]
    # total = restricted.shape[0]
    # ha = total * 629387.503078 / 100000
    print (midDamage)
    return midDamage

def generate_area_SVG (n):
    SVG = '''
    <?xml version="1.0" encoding="UTF-8"?><svg height="3em" width="3em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 46 63"><defs><style>.cls-1{fill:#29abe2;}.cls-2{fill:#ee8700;}.cls-3{fill:#fff;}.cls-4{fill:#b8002b;}.cls-5{fill:#64c37d;}.cls-6{isolation:isolate;}.cls-7{fill:#a4e276;}.cls-8{fill:#d8143a;}.cls-9{fill:none;stroke:#fff;stroke-linecap:round;stroke-linejoin:round;}.cls-10{fill:#22b573;}.cls-11{mix-blend-mode:saturation;}</style></defs><g class="cls-6"><g id="Layer_1"><g class="cls-11"><path class="cls-10" d="M25,62.5c-.12,0-.23-.04-.32-.12L5.68,46.38c-.06-.05-.1-.11-.13-.18L.54,35.21c-.09-.19-.05-.41.1-.56l3-3,1.85-2.8v-2.85c0-.09.02-.18.07-.26L20.57.74c.09-.16.26-.24.43-.24.08,0,.16.02.23.06l21,11c.12.06.21.18.25.31s.01.28-.06.4l-6.7,10.53,9.5,4.75c.13.06.23.18.26.32.04.14,0,.29-.08.41l-6.76,9.66,1.7,1.7c.17.17.19.43.06.63l-4,6c-.06.09-.15.16-.26.2l-2.82.94-2.76,4.61.88,1.75c.08.17.07.37-.05.52l-6,8c-.08.11-.21.18-.34.2-.02,0-.04,0-.06,0Z"/><path class="cls-10" d="M21,1l21,11-7,11,10,5-7,10,2,2-4,6-3,1-3,5,1,2-6,8L6,46l-5-11,3-3,2-3v-3L21,1M21,0c-.34,0-.67.17-.86.49L5.14,25.49c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.14.15.26.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82-.07-.28-.26-.52-.52-.65l-9.01-4.5,6.4-10.06c.15-.24.19-.52.12-.79s-.25-.5-.5-.63L21.46.11c-.15-.08-.31-.11-.46-.11h0Z"/></g><path class="cls-1" d="M5,36s1,2,3,1,1-2,3-2,3-2,5-2,3,1,4,0c.64-.64,1.68-1.28,2.35-1.65.29-.16.64.06.61.39-.07.89-.29,2.26-.97,2.26-1,0-1,1-3,1s-3-1-3,0-2,3-2,5-6,2-6,1-1,0-2-2-2-3-1-3Z"/><path class="cls-3" d="M31,30c1.66,0,3,1.34,3,3s-1.34,3-3,3-3-1.34-3-3,1.34-3,3-3M31,29c-2.21,0-4,1.79-4,4s1.79,4,4,4,4-1.79,4-4-1.79-4-4-4h0Z"/><path class="cls-9" d="M32.64,39.93l-2.97-13.77L12.5,15.5l17.17,10.66,3.83,2.34s4.87,3.9,2.11,6.89c-.03.03-1.69,2.23-2.57,3.4-.34.45-.58.61-.4,1.14l.86,2.57-10.96,17.19s-3.04-7.19-4.04-7.19-2-1-2-1c0,0-5-6-6-7s-2-1-3-1-4-4-4-6,3-6,3-6L21.5,6.5"/><line class="cls-9" x1="40.5" y1="31.5" x2="31.1" y2="32.95"/><g id="SVGRepo_iconCarrier"><path class="cls-2" d="M28.09,9.55c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M26.48,9.02c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-8" d="M28.09,9.55c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-4" d="M28.06,12.72l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-7" d="M29.33,15.98s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-5" d="M25.78,14.41v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-2"><path class="cls-2" d="M19.09,21.55c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M17.48,21.02c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-8" d="M19.09,21.55c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-4" d="M19.06,24.72l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-7" d="M20.33,27.98s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-5" d="M16.78,26.41v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-3"><path class="cls-2" d="M20.09,36.55c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M18.48,36.02c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-8" d="M20.09,36.55c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-4" d="M20.06,39.72l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-7" d="M21.33,42.98s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-5" d="M17.78,41.41v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-4"><path class="cls-2" d="M27.09,42.55c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M25.48,42.02c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-8" d="M27.09,42.55c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-4" d="M27.06,45.72l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-7" d="M28.33,48.98s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-5" d="M24.78,47.41v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g></g></g></svg>'''
    
    HaSVG = 31.19
    full = int(n/HaSVG)
    leftover = (n % 1)
    segment = leftover*45
    print(full)

  
    
    partialSVG = '''
    <?xml version="1.0" encoding="UTF-8"?><svg height="0.1em" width="0.1em" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 64 64"><defs><style>.cls-1,.cls-2{fill:#777;}.cls-1,.cls-3{stroke:#fff;stroke-linecap:round;stroke-linejoin:round;}.cls-4{fill:#29abe2;}.cls-5{fill:#ee8700;}.cls-6{fill:#fff;}.cls-7{mask:url(#mask);}.cls-8{fill:#b8002b;}.cls-9{fill:#64c37d;}.cls-10{isolation:isolate;}.cls-11{mix-blend-mode:multiply;}.cls-12{fill:#a4e276;}.cls-13{mix-blend-mode:hue;}.cls-14{fill:#d8143a;}.cls-3{fill:none;}.cls-15{fill:#22b573;}.cls-16{mix-blend-mode:saturation;}'''+f'''</style><mask id="mask" x="8" y="0" width="47" height="45" maskUnits="userSpaceOnUse"><rect class="cls-6" x="8" y="0" width="47" height="{segment}"/></mask>'''+'''</defs><g class="cls-10"><g id="Layer_1"><g class="cls-11"><g class="cls-16"><path class="cls-15" d="M34,63c-.12,0-.23-.04-.32-.12l-19-16c-.06-.05-.1-.11-.13-.18l-5-11c-.09-.19-.05-.41.1-.56l3-3,1.85-2.8v-2.85c0-.09.02-.18.07-.26L29.57,1.24c.09-.16.26-.24.43-.24.08,0,.16.02.23.06l21,11c.12.06.21.18.25.31s.01.28-.06.4l-6.7,10.53,9.5,4.75c.13.06.23.18.26.32.04.14,0,.29-.08.41l-6.76,9.66,1.7,1.7c.17.17.19.43.06.63l-4,6c-.06.09-.15.16-.26.2l-2.82.94-2.76,4.61.88,1.75c.08.17.07.37-.05.52l-6,8c-.08.11-.21.18-.34.2-.02,0-.04,0-.06,0Z"/><path class="cls-15" d="M30,1.5l21,11-7,11,10,5-7,10,2,2-4,6-3,1-3,5,1,2-6,8-19-16-5-11,3-3,2-3v-3L30,1.5M30,.5c-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.14.15.26.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82s-.26-.52-.52-.65l-9.01-4.5,6.4-10.06c.15-.24.19-.52.12-.79-.07-.27-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11h0Z"/></g><path class="cls-4" d="M14,36.5s1,2,3,1,1-2,3-2,3-2,5-2,3,1,4,0c.64-.64,1.68-1.28,2.35-1.65.29-.16.64.06.61.39-.07.89-.29,2.26-.97,2.26-1,0-1,1-3,1s-3-1-3,0-2,3-2,5-6,2-6,1-1,0-2-2-2-3-1-3Z"/><path class="cls-6" d="M40,30.5c1.66,0,3,1.34,3,3s-1.34,3-3,3-3-1.34-3-3,1.34-3,3-3M40,29.5c-2.21,0-4,1.79-4,4s1.79,4,4,4,4-1.79,4-4-1.79-4-4-4h0Z"/><path class="cls-3" d="M41.64,40.43l-2.97-13.77-17.17-10.66,17.17,10.66,3.83,2.34s4.87,3.9,2.11,6.89c-.03.03-1.69,2.23-2.57,3.4-.34.45-.58.61-.4,1.14l.86,2.57-10.96,17.19s-3.04-7.19-4.04-7.19-2-1-2-1c0,0-5-6-6-7s-2-1-3-1-4-4-4-6,3-6,3-6L30.5,7"/><line class="cls-3" x1="49.5" y1="32" x2="40.1" y2="33.45"/><g id="SVGRepo_iconCarrier"><path class="cls-5" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M35.48,9.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M37.06,13.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M38.33,16.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M34.78,14.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-2"><path class="cls-5" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M26.48,21.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M28.06,25.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M29.33,28.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M25.78,26.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-3"><path class="cls-5" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M27.48,36.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M29.06,40.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M30.33,43.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M26.78,41.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-4"><path class="cls-5" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M34.48,42.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M36.06,46.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M37.33,49.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M33.78,47.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g></g><g class="cls-7"><g class="cls-13"><g class="cls-16"><path class="cls-2" d="M34,63c-.12,0-.23-.04-.32-.12l-19-16c-.06-.05-.1-.11-.13-.18l-5-11c-.09-.19-.05-.41.1-.56l3-3,1.85-2.8v-2.85c0-.09.02-.18.07-.26L29.57,1.24c.09-.16.26-.24.43-.24.08,0,.16.02.23.06l21,11c.12.06.21.18.25.31s.01.28-.06.4l-6.7,10.53,9.5,4.75c.13.06.23.18.26.32.04.14,0,.29-.08.41l-6.76,9.66,1.7,1.7c.17.17.19.43.06.63l-4,6c-.06.09-.15.16-.26.2l-2.82.94-2.76,4.61.88,1.75c.08.17.07.37-.05.52l-6,8c-.08.11-.21.18-.34.2-.02,0-.04,0-.06,0Z"/><path class="cls-15" d="M30,1.5l21,11-7,11,10,5-7,10,2,2-4,6-3,1-3,5,1,2-6,8-19-16-5-11,3-3,2-3v-3L30,1.5M30,.5c-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.14.15.26.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82s-.26-.52-.52-.65l-9.01-4.5,6.4-10.06c.15-.24.19-.52.12-.79-.07-.27-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11h0Z"/></g><path class="cls-2" d="M14,36.5s1,2,3,1,1-2,3-2,3-2,5-2,3,1,4,0c.64-.64,1.68-1.28,2.35-1.65.29-.16.64.06.61.39-.07.89-.29,2.26-.97,2.26-1,0-1,1-3,1s-3-1-3,0-2,3-2,5-6,2-6,1-1,0-2-2-2-3-1-3Z"/><circle class="cls-2" cx="40" cy="33.5" r="3.5"/><path class="cls-6" d="M40,30.5c1.66,0,3,1.34,3,3s-1.34,3-3,3-3-1.34-3-3,1.34-3,3-3M40,29.5c-2.21,0-4,1.79-4,4s1.79,4,4,4,4-1.79,4-4-1.79-4-4-4h0Z"/><path class="cls-1" d="M41.64,40.43l-2.97-13.77-17.17-10.66,17.17,10.66,3.83,2.34s4.87,3.9,2.11,6.89c-.03.03-1.69,2.23-2.57,3.4-.34.45-.58.61-.4,1.14l.86,2.57-10.96,17.19s-3.04-7.19-4.04-7.19-2-1-2-1c0,0-5-6-6-7s-2-1-3-1-4-4-4-6,3-6,3-6L30.5,7"/><line class="cls-1" x1="49.5" y1="32" x2="40.1" y2="33.45"/><g id="SVGRepo_iconCarrier-5"><path class="cls-2" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M35.48,9.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M37.06,13.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M38.33,16.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M34.78,14.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-6"><path class="cls-2" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M26.48,21.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M28.06,25.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M29.33,28.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M25.78,26.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-7"><path class="cls-2" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M27.48,36.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M29.06,40.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M30.33,43.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M26.78,41.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-8"><path class="cls-2" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M34.48,42.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M36.06,46.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M37.33,49.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M54.97,28.25c-.07-.28-.26-.52-.52-.65l-9.01-4.5,6.41-10.06c.15-.24.19-.52.12-.79s-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.13.15.25.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82Z"/><path class="cls-2" d="M33.78,47.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g></g></g></g></g></svg>
  '''
    
    
    fig = pn.pane.HTML(SVG*(full))
    fig2 = pn.pane.HTML(partialSVG)
    
    composite = pn.Column(fig)
    
    return composite


def generate_pipes_SVG(origin, destination, n):
    SVG = '''<?xml version="1.0" encoding="UTF-8"?><svg id="Pipeline_1" height="45x" width="35px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 35"><defs><style>.cls-1{fill:#41537b;}.cls-2{fill:#a2aea7;}.cls-3{fill:#bdcbc3;}.cls-4{fill:#d9cdf1;}.cls-5{fill:#3b5b6e;}.cls-6{fill:#4c6fb0;}.cls-7{fill:#374766;}.cls-8{fill:#4d83b1;}.cls-9{fill:#2c535f;}.cls-10{fill:#3a6284;}.cls-11{fill:#3f6697;}.cls-12{fill:#3c6585;}</style></defs><path class="cls-12" d="M34.35,12.01c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M33.5,12.55c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M30.75,7.98c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M33.54,12.53c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M32.69,13.06c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M29.94,8.5c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M32.75,13.04c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M31.9,13.57c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M29.15,9c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-11" d="M25.15,9.94l-.83-.89,1.49-.89c.06-.04.11-.08.17-.11h.01s0,0,0,0c.49-.26,1.15-.21,1.87.2,1.49.85,2.71,2.98,2.71,4.72,0,.76-.23,1.32-.61,1.65h0s0,0,0,0c-.1.08-.21.15-.32.2l-1.5.92-.8-1.55c-1.21-.99-2.14-2.75-2.18-4.25Z"/><path class="cls-10" d="M28.92,13.96c0-1.75-1.22-3.87-2.71-4.72-1.49-.85-2.71-.14-2.71,1.59s1.22,3.85,2.71,4.72c1.49.87,2.71.16,2.71-1.59Z"/><path class="cls-2" d="M28.06,13.47c0-1.19-.83-2.64-1.85-3.22-1.02-.58-1.85-.09-1.85,1.08s.83,2.63,1.85,3.22c1.02.6,1.85.11,1.85-1.08Z"/><path class="cls-4" d="M26.25,14.1c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M25.12,14.8c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M24.12,15.43c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M23.65,16.51c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M22.99,16.13c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M22.1,16.66c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M20.97,17.36c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M19.97,18c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M19.5,19.07c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M18.84,18.7c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M18.02,19.2c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M16.89,19.9c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M15.9,20.53c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M15.42,21.61c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M14.77,21.23c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M13.87,21.76c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M12.74,22.46c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M11.75,23.1c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-6" d="M28.16,13.72c0-1.33-.93-2.94-2.06-3.59-.16-.09-.31-.15-.45-.2h0c-.56-.22-1.04.05-1.04.05l-13.3,8.27-.27.16h0s-.09.05-.13.08l-.52.32-.49.29h0c-.06.03-.11.07-.16.11l-1.97,1.22.51.54s0,.07,0,.11c0,1.25.85,2.79,1.92,3.5l.48.93,1.14-.7c.09-.04.17-.09.25-.15h0s0,0,0,0c0,0,0,0,.01,0l.87-.54c.09-.04.17-.09.25-.15h0s0,0,0,0c0,0,0,0,0,0l2.8-1.72c.07-.03.13-.07.19-.12l.95-.58c.06-.03.12-.07.18-.11l10.25-6.31s.31-.19.4-.47h0c.13-.24.21-.55.21-.93Z"/><path class="cls-3" d="M11.27,24.17c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-2" d="M10.61,23.79c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-11" d="M5.95,20.81l-1-1.07,1.79-1.07c.07-.05.14-.1.21-.14h.01s0,0,0,0c.59-.31,1.38-.26,2.24.24,1.79,1.02,3.26,3.58,3.26,5.68,0,.91-.28,1.59-.74,1.98h0s0,0,0,0c-.12.1-.25.18-.39.24l-1.8,1.11-.96-1.86c-1.46-1.19-2.57-3.31-2.62-5.1Z"/><path class="cls-8" d="M10.48,25.65c0-2.1-1.47-4.65-3.26-5.68-1.79-1.02-3.26-.17-3.26,1.91s1.47,4.63,3.26,5.68c1.79,1.05,3.26.19,3.26-1.91Z"/><path class="cls-12" d="M10.95,25.94c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M10.1,26.48c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M7.35,21.91c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M10.14,26.46c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M9.29,26.99c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M6.54,22.42c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M9.35,26.97c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M8.5,27.5c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M5.75,22.93c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/></svg>'''
    fig =pn.pane.HTML(SVG*n)
    OD = pn.pane.HTML(f'<p style="color:#3850A0; font-size:14px; margin:4px;">Pipes from <b>{origin} to {destination}</b>:  ')
    pane = pn.Row(OD, fig)
    return pane

def calculate_total_CO2_cost():
    """
    Calculate the total CO2 emission cost.

    Returns:
        float: Total CO2 emission cost in EUR/yr.
    """
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    active_wells["CO2_Cost"] = active_wells_df["Value"] * active_wells_df["CO2_m3"]
    total_environmental_cost = active_wells["CO2_Cost"].sum()
    return total_environmental_cost

def calculate_total_Drought_cost():
    """
    Calculate the total cost due to drought damage.

    Returns:
        float: Total drought damage cost in EUR/yr.
    """
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    active_wells["Drought_Cost"] = (
        active_wells_df["Value"] * active_wells_df["Drought_m3"]
    )
    total_environmental_cost = active_wells["Drought_Cost"].sum()
    return total_environmental_cost

def update_df_display():
    """
    Update the DataFrame display.

    Returns:
        str: The updated DataFrame as a string.
    """
    return f"```python\n{active_wells_df}\n```"

def toggle_well(event, well_name):
    """
    Toggle the active state of a well based on a checkbox.

    Args:
        event: The event object.
        well_name (str): The name of the well.
    """
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Active"] = event.new
    update_indicators()
    #map_pane.object = update_layers()
    
def toggle_industrial(event, location):
    """
    Toggle the active state of a well based on a checkbox.

    Args:
        event: The event object.
        well_name (str): The name of the well.
    """
    industrial.loc[industrial["Location"] == location, "Active"] = event.new
    update_indicators()
    #map_pane.object = update_layers()

def update_slider(event, well_name):
    """
    Update the slider value for a well.

    Args:
        event: The event object.
        well_name (str): The name of the well.
    """
    
    current_value = wells.loc[wells["Name"] == well_name, "Extraction_2023__Mm3_per_jr_"].values[0]
    max_value = wells.loc[wells["Name"] == well_name, "Permit__Mm3_per_jr_"].values[0]
    
    new_value = event.new
    
   
    
    
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = new_value
    opex_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX"] = new_value * opex_m3
    
    
    
    
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Value_formatted(well_name)
    update_indicators()
    pn.state.notifications.position = 'bottom-right'

    if new_value > max_value:
         pn.state.notifications.error(f"Warning on {well_name} well: This value is above the extraction permit. Using this value would require negotiation a larger water extraction permit.", 4000)

def update_radio(event, well_name):
    """
    Update the extraction value based on the selected radio button option.

    Args:
        event: The event object.
        well_name (str): The name of the well.
    """
    current_value = wells.loc[wells["Name"] == well_name, "Extraction_2023__Mm3_per_jr_"].values[0]
    max_value = wells.loc[wells["Name"] == well_name, "Permit__Mm3_per_jr_"].values[0]
    # agreement = wells.loc[wells["Name"]== well_name, "Agreement__Mm3_per_jr_"].values[0]
    
    if event.new == "-20% of Current":
        new_value = current_value * 0.8
    elif event.new == "-15% of Current":
        new_value = current_value * 0.85
    elif event.new == "Current":
        new_value = current_value
    elif event.new == "85% of Max. Permit":
        new_value = max_value * 0.85
    elif event.new == "115% of Max. Permit":
        new_value = max_value * 1.15
    elif event.new == "Maximum Permit":
        new_value = max_value
   
   
    pn.state.notifications.position = 'bottom-left'

    if new_value > max_value:
         pn.state.notifications.error(f"Warning on {well_name} well: This value is above the extraction permit. Using this value would require negotiation a larger water extraction permit.", 0)
    
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = new_value
    opex_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX"] = new_value * opex_m3
    
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Value_formatted(well_name)
    update_indicators()
    
def update_scenarios(event):
    if event.new == "Population 2035":
        Scenario1()
        print('scenario 1 active')
    if event.new == "Population 2035 +1%":
        print('scenario 2 active')
        Scenario2()
    if event.new == "Current state - 2024":
        print("Original Scenario")
        ScenarioBase()
    update_indicators()
    
def update_scenariosSmall(event):
    if event.new == "Small Business +10% Demand":
        ScenarioSmallBussiness1()
        print('scenario 1 Small active')
    if event.new == "Small Business +35% Demand":
        print('scenario 2 small  active')
        ScenarioSmallBussiness2()
    if event.new == "Current state - 2024":
        print("Original Scenario")
        ScenarioSmallBussinessBase()
    update_indicators()

def update_well_Value(well_name):
    """
    Update the well name display.

    Args:
        well_name (str): The name of the well.

    Returns:
        str: Updated well name display.
    """
    current_extraction = active_wells_df[active_wells_df["Name"]==well_name]["Value"].values[0]
    
    return current_extraction

def update_well_Value_formatted(well_name):
    """
    Update the well name display.

    Args:
        well_name (str): The name of the well.

    Returns:
        str: Updated well name display.
    """
    current_extraction = active_wells_df[active_wells_df["Name"]==well_name]["Value"].values[0]
    
    return f"{current_extraction:.2f} Mm\u00b3/yr"

def styleWellValue (Wellvalue, maxValue):
    if Wellvalue > maxValue:
        valueStyle = {
            'font-family': 'Roboto',
            'font-size': "14px",
            'font-weight': 'bold', 
            'color': '#d9534f'
        }
    else:
        valueStyle = {
            'font-family': 'Roboto',
            'font-size': "14px",
            'font-weight': "bold",
            'color': '#34407b'
        }
    return valueStyle
    

def current_demand(event):
    global demand_capita 
    global smallBussiness
    if event.new == 90:
        demand_capita  = 0.09*smallBussiness
    if event.new == 100:
        demand_capita  = 0.1*smallBussiness
    if event.new == 120:
        demand_capita  = 0.12*smallBussiness
    if event.new == 135:
        demand_capita  = 0.135*smallBussiness
    update_indicators()
    

def calculate_total_Demand():
    """
    Calculate the total water demand.

    Returns:
        float: Total water demand in Mm3/yr.
    """
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBussiness * 365 
    ) / 1000000
    
    total = ((hexagons_filterd["Water Demand"]).sum()) + (
        (hexagons_filterd["Industrial Demand"]).sum()
    )
    return total

def calculate_demand_by_balance():
    """
    Calculate the water demand grouped by balance areas.

    Returns:
        pd.Series: Water demand by balance area.
    """
    return active_wells_df.groupby("Balance area")["Water Demand"].sum()

def update_demand():
    """
    Update demand indicators.
    """
    total_demand = calculate_demand_by_balance()
    for balance, indicator in calculate_demand_by_balance.items():
        indicator.value = total_demand.get(balance, 0)

def calculate_lzh():
    """
    Calculate Leveringszekerheid (Delivery Security).

    Returns:
        float: Leveringszekerheid as a percentage.
    """
    total_extraction = calculate_total_extraction()
    total_demand = calculate_total_Demand()
    return round((total_extraction / total_demand) * 100, 2)

def calculate_lzh_by_balance():
    """
    Calculate Leveringszekerheid grouped by balance areas.

    Returns:
        dict: Leveringszekerheid by balance area.
    """
    lzh_by_balance = {}
    balance_areas = active_wells_df["Balance area"].unique()

    for area in balance_areas:
        total_extraction = active_wells_df.loc[
            active_wells_df["Balance area"] == area, "Value"
        ].sum()

        total_demand = hexagons_filterd.loc[
            hexagons_filterd["Balance Area"] == area, "Water Demand"
        ].sum()

        lzh_by_balance[area] = (
            round((total_extraction / total_demand) * 100, 2) if total_demand else 0
        )
    
    return lzh_by_balance


def update_balance_lzh_gauges():
    """
    Update Leveringszekerheid gauges for balance areas.
    """
    lzh_by_balance = calculate_lzh_by_balance()
    for area, gauge in balance_lzh_gauges.items():
        gauge.value = lzh_by_balance.get(area, 0)
        
        
        
## MAP SECTION

js_content: sourcetypes.javascript

# Create map and add attributes
def create_map(lat,lon,zoom):
    map_file = StringIO()
    
    js_file = StringIO()
    
    js_content = '''
    
    mapboxgl.accessToken = 'pk.eyJ1IjoiY3lnbnVzMjYiLCJhIjoiY2s5Z2MzeWVvMGx3NTNtbzRnbGtsOXl6biJ9.8SLdJuFQzuN-s4OlHbwzLg';
    const map = new mapboxgl.Map({
        container: 'map', // container ID'''+f'''
        center: {[lon, lat]},
        pitch: 60,
        // starting position [lng, lat]. Note that lat must be set between -90 and 90
        zoom:  {zoom}// starting zoom'''+'''
        });    
    '''
    
   
    html_content: sourcetypes.html = '''
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.6.0/mapbox-gl.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.6.0/mapbox-gl.js"></script>
        <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        </style>
        </head>
        <body>
        <div id="map">map</div>
        <script>'''+f'''
            {js_content}
        '''+'''
        </script>
        </body>
        </html>              
                 '''          
                 
                 
    map_file.write(html_content)
    map_file.seek(0)
    
    # Read the HTML content and escape it
    html_file = map_file.read()
    escaped_html = html.escape(html_file)
    
    iframe = f'<iframe srcdoc="{escaped_html}" style="height:100%; width:100%" frameborder="0"></iframe>'
      
    
    return iframe





m = folium.Map(
    location=[52.38, 6.7], zoom_start=10,
    tiles="Cartodb Positron"
)


popup_well = folium.GeoJsonPopup(
    fields=["Name", "Balance area", "Value"],
    aliases=["Well Name", "Balance Area", "Extraction in Mm\u00b3/yr"],
)
popup_hex = folium.GeoJsonPopup(
    fields=["cityName", "Water Demand", "Population 2022"],
)
popup_industrial = folium.GeoJsonPopup(
    fields=["Place", "Licensed", "Current_Extraction_2019"],
    aliases=["Location", "Licensed Extraction", "Current Extraction"]
)
icon_path = "./Assets/Water Icon.png"
icon = folium.CustomIcon(
    icon_path,
    icon_size=(30, 30),
)

colormap = branca.colormap.LinearColormap(
    ["#caf0f8", "#90e0ef", "#00b4d8", "#0077b6", "#03045e"],
    vmin=cities_clean["Water Demand"].quantile(0.0),
    vmax=cities_clean["Water Demand"].quantile(1),
    caption="Total water demand in Mm\u00b3/yr",
)

def calculate_centroid(coordinates):
    """
    Calculate the centroid of a polygon.

    Args:
        coordinates (list): List of coordinates defining the polygon.

    Returns:
        tuple: Coordinates of the centroid (latitude, longitude).
    """
    polygon = Polygon(coordinates)
    return polygon.centroid.y, polygon.centroid.x

def update_layers(wellsLayer=active_wells_df,industryLayer=industrial):
    """
    Update the layers on the map.

    Returns:
        folium.Map: Updated Folium map.
    """
    global m
    
    active = wellsLayer[wellsLayer["Active"]==True]
    
    folium.GeoJson(
        active,
        name="Wells",
        zoom_on_click=True,
        popup=popup_well,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#f3f3f3", icon="arrow-up-from-ground-water", prefix="fa", color='cadetblue'
            )
        ),
    ).add_to(m)
    
    folium.GeoJson(
        industryLayer,
        name="Industrial Water Extraction",
        zoom_on_click=True,
        popup=popup_industrial,
        tooltip=folium.GeoJsonTooltip(fields=["Place"], aliases=["Place:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#d9534f", icon="industry", prefix="fa", color='lightred'
            )
        ),
    ).add_to(m)
    

    hex = folium.GeoJson(
        cities_clean,
        name="City Demand",
        style_function=lambda x: {
            "fillColor": (
                colormap(x["properties"]["Water Demand"])
                if x["properties"]["Water Demand"] is not None
                else "transparent"
            ),
             "color": (
                "darkgray"
                if x["properties"]["cityName"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        popup=popup_hex,
    ).add_to(m)

    m.add_child(colormap)
    
    folium.GeoJson(
        mainPipes,
        name="Main Pipelines",
        style_function= lambda x:{ 
            "color": "#E27D79",
            "weight": (4 if x["properties"]["Diameter_mm"]>350
                       else(2 if x["properties"]["Diameter_mm"]>250
                       else 1)),
            "Opacity": 0.6,
        },
        show=False
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Natura2000 Restricted Area",
        style_function=lambda x: {
            "fillColor": (
                "darkgreen"
                if x["properties"]["Type"] == "Restricted Natura2000"
                else "transparent"
            ),
            "color": (
                "darkgray"
                if x["properties"]["Balance Area"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        }, 
        show= False,
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Restricted NNN",
        style_function=lambda x: {
            "fillColor": (
                "#CAFAA2"
                if x["properties"]["Type"] == "Restricted Other"
                else "transparent"
            ),
             "color": (
                "darkgray"
                if x["properties"]["Balance Area"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        show= False,
    ).add_to(m)
    
    
    
    folium.GeoJson(
        balance_areas,
        name="Balance Areas",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#93419F",
            "weight": 3
        },
        show=True,
        tooltip=folium.GeoJsonTooltip(fields=['Balance Area'], labels=True)
    ).add_to(m)
    
    
    
    folium.LayerControl().add_to(m)

    return m


# Logarithmic function
def log_func(x, a, b):
    return a * np.log(x) + b


# Function to estimate extent for a specific well
def estimate_Damage_for_well(type, well_name, target_percentage):
    # Find the row corresponding to the given well
    well_row = type[type['Name'] == well_name]
    
    if well_row.empty:
        print(f"Well '{well_name}' not found in the dataset.")
    
    # Extract the available percentage columns (non-NaN values)
    well_row = well_row.iloc[0]  # Select the first row as Series
    perc_columns = well_row.dropna().index[1:]  # Exclude the 'Name' column
    perc_values = [float(col) for col in perc_columns]
    extents = well_row[perc_columns].values
    
    if len(perc_values) < 2:
        print(f"Not enough data points to fit a curve for well '{well_name}'.")
        return 0
    
    # Fit a logarithmic curve to the data
    try:
        popt, _ = curve_fit(log_func, perc_values, extents)
        # Use the fitted curve to predict the extent at the target percentage
        estimated_extent = log_func(target_percentage, *popt)                
        return estimated_extent
    except Exception as e:
        print(f"Error in fitting the curve: {e}")
        return 0
        
    

active_scenarios = set()
text = ["## Scenario"]


def update_scenarioTitle(new_title):
    global text
    base_title = "Current state - 2024"
    if Scenario_Button.value == "Population 2035":
        if "Accelerated Growth" in text:
            text.remove("Accelerated Growth")
        if base_title in text:
            text.remove(base_title)
        text.append(new_title)
    if Scenario_Button.value == "Population 2035 +1%":
        if "Autonomous Growth" in text:
            text.remove("Autonomous Growth")
        if base_title in text:
            text.remove(base_title)
        text.append(new_title)
    if Scenario_Button.value == "Current state - 2024":
        if "Accelerated Growth" in text:
            text.remove("Accelerated Growth")
        if "Autonomous Growth" in text:
            text.remove("Autonomous Growth")
        else:
            if Scenario_Button.value in text: 
                print(text)
            else: text.append(new_title)            
    app_title.object = " - ".join(text)
    print (text)


def update_title(event):
    if ButtonSmallWells.value:
        if "Closed Small Wells" in text:
            print("Text already there")
        else: 
            text.append("Closed Small Wells")
            Measure1On()
    if ButtonSmallWells.value == False:
        Measure1Off()
        if "Closed Small Wells" in text:
            text.remove("Closed Small Wells")
        else:
            print("Text not there")
    if ButtonCloseNatura.value:
        if "Closed Natura Wells" in text:
             print("Text already there")
        else: 
            text.append("Closed Natura Wells")
            Measure2On()
    if ButtonCloseNatura.value == False:   
        Measure2Off()
        if "Closed Natura Wells" in text:
            text.remove("Closed Natura Wells")
        else: print("Text not there")
    if ButtonImportWater.value:
        if "Import Water" in text:
            print("Text already there")
        else: 
            text.append("Import Water")
            Measure4On()
    if ButtonImportWater.value == False:     
        Measure4Off()
        if "Import Water" in text:
            text.remove("Import Water") 
        else: print("Text not there")
    if ButtonAddExtraIndustrial.value:
        if "Use industrial excess" in text:
            print("Text already there")
        else: text.append("Use industrial excess")
        Measure5On()
    if ButtonAddExtraIndustrial.value == False:
        Measure5Off()
        if "Use industrial excess" in text:
            text.remove("Use industrial excess")
        else: print("Text not there")
    if Button5.value:
        if "Use of Smart Meters" in text:
            print("Text already there")
        else: text.append("Use of Smart Meters")
        Measure3On()
    if Button5.value == False:
        Measure3Off()
        if "Use of Smart Meters" in text:
            text.remove("Use of Smart Meters")
        else: print("Text not there")
        
    
    app_title.object = " - ".join(text)
    print(text)
    update_indicators()
    


def ScenarioBase():
    """
    Implement the base scenario with a demand equal to year 2022.

    Args:
        event: The event object.
    """
    global demand_capita
    hexagons_filterd["Current Pop"]= hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBussiness * 365 
    ) / 1000000
    update_scenarioTitle("Current state - 2024")
    print("Scenario Base restored")
    update_indicators()

def Scenario1():
    """
    Implement the first scenario with a demand increase of 1.6%.

    Args:
        event: The event object.
    """
    global demand_capita 
    hexagons_filterd["Current Pop"]= hexagons_filterd["Pop2022"]*1.0209

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBussiness * 365 
    ) / 1000000
    update_scenarioTitle("Autonomous Growth")
    print("Scenario 1 ran perfectly")
    update_indicators()

def Scenario2():
    """
    Implement the second scenario with a demand increase of 2.09%.
    
    
    Args:
        event: The event object.
    """
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]*1.0309

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBussiness * 365
    ) / 1000000
        
    update_scenarioTitle("Accelerated Growth")
    update_indicators()
    
def ScenarioSmallBussinessBase():
    global smallBussiness
    global demand_capita 
    smallBussiness = 1.2
    update_indicators()

def ScenarioSmallBussiness1():
    global smallBussiness
    global demand_capita 
    smallBussiness = 1.2*1.1
    update_indicators()

def ScenarioSmallBussiness2():
    global smallBussiness
    global demand_capita 
    smallBussiness = 1.2*1.35
    update_indicators()


def Measure1On():
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = False
    
    # Update the checkboxes to reflect the new state
    for well_name in active_wells_df.loc[condition, "Name"]:
        checkboxes[well_name].value = False  # Uncheck the checkbox

def Measure1Off():
    condition = active_wells_df["Max_permit"] >= 5.00
    active_wells_df.loc[condition, "Active"] = True

    # Update the checkboxes to reflect the new state
    for well_name in active_wells_df.loc[condition, "Name"]:
        checkboxes[well_name].value = True  # Check the checkbox

def Measure2On():
    """
    Activate the second measure (closing Natura 2000 wells).
    """
    active_wells_df.loc[active_wells_df["Name"] == "Archemerberg", "Active"] = False
    active_wells_df.loc[active_wells_df["Name"] == "Nijverdal", "Active"] = False
    
    # Update the checkboxes to reflect the new state
    checkboxes["Archemerberg"].value = False
    checkboxes["Nijverdal"].value = False

def Measure2Off():
    """
    Deactivate the second measure (closing Natura 2000 wells).
    """
    active_wells_df.loc[active_wells_df["Name"] == "Archemerberg", "Active"] = True
    active_wells_df.loc[active_wells_df["Name"] == "Nijverdal", "Active"] = True
    
    # Update the checkboxes to reflect the new state
    checkboxes["Archemerberg"].value = True
    checkboxes["Nijverdal"].value = True
    
def Measure3On():
    """
    Activate the third measure (using smart meters).
    """
    global demand_capita
    demand_capita = ButtonDemand.value*0.95
    update_indicators()

def Measure3Off():
    """
    Deactivate the third measure (using smart meters).
    """
    global demand_capita
    demand_capita  = ButtonDemand.value
    update_indicators()
    
def Measure4On():
    """
    Activate the fourth measure (importing water).
    """
    # Assign the geometry directly with proper coordinates
    new_geometry = Point(253802.6, 498734.2)  # Projected coordinates
    active_wells_df.loc[active_wells_df.shape[0]] = ["Imports", 3,0, 4.5, "Imported", True, 4.38, 4.38, 0,0,0,0,0,0.262,0, new_geometry]
    new_well = active_wells_df.loc[active_wells_df["Name"] == 'Imports']
    
    new_well_gdf = gpd.GeoDataFrame(new_well, geometry='geometry')
    new_well_gdf =  new_well_gdf.to_json()
 
    folium.GeoJson(
        new_well_gdf,
        name="Import Water",
        zoom_on_click=True,
        popup=popup_well,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#f3f3f3", icon="arrow-up-from-ground-water", prefix="fa", color='cadetblue'
            )
        ),
        show = True
    ).add_to(m)
    # folium.GeoJson(
    #     mainPipes,
    #     name="Main Pipelines",
    #     style_function= lambda x:{ 
    #         "color": "#d9534f",
    #         "weight": (4 if x["properties"]["Diameter_mm"]>350
    #                    else(2 if x["properties"]["Diameter_mm"]>250
    #                    else 1)),
    #         "Opacity": 0.6,
    #     },
    #     show=False
    # )

def Measure4Off():
    """
    Deactivate the fourth measure (importing water).
    """
    try:  
        # Use .loc to identify rows where 'Name' is 'Imports' and drop them
        active_wells_df.drop(active_wells_df.loc[active_wells_df["Name"] == 'Imports'].index, inplace=True)
        print(active_wells_df.tail())
    except KeyError:
        print("Row does not exist")

def Measure5On():
    global industrialExcess
    industrialExcess = industrial["Licensed"].sum()-industrial["Current_Extraction_2019"].sum()
    
def Measure5Off():
    global industrialExcess
    industrialExcess = 0  

    
    
def Reset(event):
    """
    Reset the application to its initial state.

    Args:
        event: The event object.
    """
    demand_capita = 0.135
    smallBussiness = 1.2
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBussiness * 365
    ) / 1000000
    global active_wells_df
    active_wells_df = gpd.GeoDataFrame(
    {
        "Name": wells["Name"],
        "Num_Wells": wells["Num_Wells"],
        "Ownership": wells["Inside_Prop"],
        "Max_permit": wells["Permit__Mm3_per_jr_"],
        "Balance area": wells["Balansgebied"],
        "Active": [True] * len(wells),
        "Current Extraction" : wells["Extraction_2023__Mm3_per_jr_"],
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
    }
)
    Scenario_Button.value = 'Current state - 2024'
    ScenarioSmall_Button.value = 'Current state - 2024'
    ButtonDemand.value = 135
    ButtonSmallWells.value, ButtonCloseNatura.value, Button5.value  = False, False, False
    update_scenarioTitle("Current state - 2024")
    update_indicators()

def update_indicators(arg=None):
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    total_capex.value = calculate_total_CAPEX()
    excess_cap.value = calculate_available()
    natureMidDamage_value.value=calculate_affected_Sensitive_Nature()
    natureHighDamage_value.value=calculate_affected_VerySensitive_Nature()
    own_pane.value = calculate_ownership()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    # update_balance_opex()
    update_balance_lzh_gauges()
    total_demand.value = calculate_total_Demand()
    total_difference.value = calculate_difference()
    lzh.value = calculate_lzh()
    


# Initialize a dictionary to hold the active state and slider references
active_wells = {}

# Initialize a dictionary to hold the balance area layouts
balance_area_buttons = {}

# Initialize a dictionary to hold the sliders
checkboxes = {}


# Setup Well Sliders
Sliders = []
for index, row in wells.iterrows():
    wellEnd = row["Permit__Mm3_per_jr_"]*1.15
    wellPermit = row["Permit__Mm3_per_jr_"]
    wellCurrent = row["Extraction_2023__Mm3_per_jr_"]
    wellName = row["Name"]
    wellStart = row["Extraction_2023__Mm3_per_jr_"]*0.8
    balance_area = row["Balansgebied"]
    Well_slider = pn.widgets.FloatSlider(
        name="",
        start=wellStart,
        end=wellEnd*1.15,
        step=wellEnd*0.15,
        value=wellCurrent,
        format=PrintfTickFormatter(format="%.2f Mm\u00b3/Year"),
        width=250,
        margin=(4, 10),
        show_value= False,
        bar_color= '#e9e9e1'
    )
    max_label = pn.pane.HTML(
        f"Max. +15%",  align="end"
    )  # Create a label for the maximum value
    min_label = pn.pane.HTML(f"-15%", align="start")
    current_label = pn.pane.HTML (f"2024 extraction: {wellCurrent:0.2f}", align = "center")
    permitLabel = pn.pane.HTML(f"Max. Permit: {wellEnd:0.2f}")
    minMaxlabel = pn.Row(min_label, current_label, permitLabel, max_label, width=290)

    # Add Checkbox and listeners
    checkbox = pn.widgets.Switch(name="Active", value=True, max_width=20)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")

    Well_slider.param.watch(
        lambda event, well_name=wellName: update_slider(event, well_name), "value"
    )
    
    # Store the checkbox in the dictionary for later updates
    checkboxes[wellName] = checkbox
    
    NameP = pn.pane.Str(wellName + "   On/Off", styles={
        'font-size': "14px",
        'font-family': "Barlow",
        'font-weight': 'bold',
    })
    
    Wellvalue = update_well_Value(wellName)
    well_style=styleWellValue(Wellvalue,wellEnd)
    
    extractionPerWell = pn.pane.HTML(object=update_well_Value_formatted(wellName), styles=well_style)
    NameState = pn.Row(NameP, checkbox)
    Well_radioB = pn.Column(NameState, extractionPerWell, Well_slider, minMaxlabel, styles=miniBox_style)
    
    # Add the well layout to the appropriate balance area layout
    if balance_area not in balance_area_buttons:
        balance_area_buttons[balance_area] = []
    balance_area_buttons[balance_area].append(Well_radioB)
    
    # Store the active state and radio group reference along with the NamePane
    active_wells[wellName] = {"active": True, "value": wellCurrent, "radio_group": Well_slider, "name_pane": extractionPerWell}

    
    
# Create HTML Text for Wells Tab
balance_area_Text = pn.pane.HTML('''
    <h3 align= "center" style="margin: 5px;"> Balance Areas</h3><hr>'''
    , width=300, align="start")

# Create a layout for the radio buttons
radioButton_layout = pn.Accordion(styles={'width': '95%', 'color':'#151931'})
for balance_area, layouts in balance_area_buttons.items():
    balance_area_column = pn.Column(*layouts)
    radioButton_layout.append((balance_area, balance_area_column))
    

    
Scenario_Button =pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['Current state - 2024','Population 2035','Population 2035 +1%'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }, orientation='vertical'
                                             )
Scenario_Button.param.watch(update_scenarios, "value")

ScenarioSmall_Button = pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['Current state - 2024','Small Business +10% Demand','Small Business +35% Demand'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }, orientation='vertical'
                                             )
ScenarioSmall_Button.param.watch(update_scenariosSmall, "value")

# Button1 = pn.widgets.Button(
#     name='Autonomous growth', button_type="primary", width=300, margin=10,
# )
# Button1.param.watch(update_title, 'value')
# Button1.on_click(Scenario1)

# Button2 = pn.widgets.Button(
#     name="Accelerated growth", button_type="primary", width=300, margin=10, 
# )
# Button2.param.watch(update_title, 'value')
# Button2.on_click(Scenario2)

ButtonSmallWells = pn.widgets.Toggle(
    name='Close Small Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
ButtonSmallWells.param.watch(update_title, 'value')

ButtonCloseNatura = pn.widgets.Toggle(
    name='Close Natura 2000 Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
ButtonCloseNatura.param.watch(update_title, 'value')

ButtonDemand = pn.widgets.RadioButtonGroup(name='Water Demand per Capita', options=[135,120,100,90], button_type='warning',
                                            width=80, orientation='horizontal', styles={
    'width': '97%', 'flex-wrap': 'no-wrap' }, align=("center", "center"))
ButtonDemand.param.watch(current_demand, 'value')

Button5 = pn.widgets.Toggle(
    name='Include Smart Meters', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button5.param.watch(update_title, 'value')

ButtonImportWater = pn.widgets.Toggle(
    name='Import Water', button_type="primary", button_style="outline", width=300, margin=10, 
)
ButtonImportWater.param.watch(update_title, 'value')

ButtonAddExtraIndustrial = pn.widgets.Toggle(name="Add Industrial water",  button_type="primary", button_style="outline", width=300, margin=10,)
ButtonAddExtraIndustrial.param.watch(update_title, 'value')

ButtonReset = pn.widgets.Button(
    name='Reset', button_type='danger', width=300, margin=10
)
ButtonReset.on_click(Reset)

# textYears = pn.pane.HTML(
#     '''
#     <h3 align= "center" style="margin: 5px;"> Year Selection</h3><hr>
#   ''', width=300, align="start", styles={"margin": "5px"}
# )

textDivider3 = pn.pane.HTML('''<hr class="dashed"> <h3 align= "center" style="margin: 5px;">Scenarios Small bussiness</h3><hr>''')

textScenarioPop = pn.pane.HTML(
    '''
    <h3 align= "center" style="margin: 5px;">Scenarios Population</h3><hr>'''
    # <b>Scenario with demand increase of 10% &#8628;</b>'''
    , width=300, align="start"
)
textB2 = pn.pane.HTML(
    '''<b>Scenario with demand increase of 35% &#8628;</b>''', width=300, align="start"
    
)

textB5 = pn.pane.HTML(
    '''
    <b>Installation of Water Smartmeters: Reduction of 5% on demand. &#8628;</b>''', width=300, align="start", styles={}
)

textMeasureSupp = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Supply Measures </h3> <hr>
    <p>These measures are in possible changes in the water extraction and the way water is supplied. Most of them are in control of the Water company.</p> <hr>
    <b>Close down all well locations with production less than 5Mm\u00b3/yr &#8628;</b>''', width=300, align="start", styles={}
)
textCloseNatura = pn.pane.HTML(
    '''
    <b>Close down all well locations in less than 100m from a Natura 2000 Area &#8628;</b>''', width=300, align="start", styles={}
)

textMeasureDemand = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Demand Measures </h3> <hr>
    <p> These measures assume a change in the behaviour of users and the will to reduce their water consumption.</p> <hr>
    <b>Water Consumption per Capita in L/d. This is a target of water consumption</b>''', width=300, align="start", styles={}
)

textImport = pn.pane.HTML(
    '''
    <b>Importing water from WAZ Getelo, NVB Nordhorn and Haaksbergen</b>''', width=300, align="start", styles={}
)

textIndustrial = pn.pane.HTML(
    '''
    <b>Add unused water from industrial permits </b>''', width=300, align="start", styles={})

textEnd = pn.pane.HTML(
    '''<hr class="dashed">
    ''', width=300, align="start", styles={}
)

textDivider0 = pn.pane.HTML('''<hr class="dashed">''')
textDivider1 = pn.pane.HTML('''<hr class="dashed">''')
textDivider2 = pn.pane.HTML('''<hr class="dashed">''')

file_create = pn.widgets.Button(name='Create Report', button_type='primary', width=300, margin=10,)

file_download = pn.widgets.FileDownload(file="Vitalens_report.pdf", button_type="primary" , width=300, margin=10,)

# Create a spinner
spinner = pn.indicators.LoadingSpinner(width=30, height=30, value=False)

def spacer(size):
    spacerVertical = pn.Spacer(height=size)
    return spacerVertical

disclaimer = pn.pane.HTML('''    
                         <div style="font-family: Barlow, Arial, sans-serif; padding: 20px; color: #333; font-size: 14px;">
    <h1 style="color: #3850A0;">Welcome to Vitalens App</h1>
    <p>
        This application provides a comprehensive tool for managing and analyzing water wells within the Overijssel Zuid region. It enables users to monitor well extraction capacities, operational costs, environmental impact, and other critical factors affecting water supply planning.
    </p>
    
    <h2>Key Features</h2>
    <ul>
        <li><strong>Real-Time Data Visualization:</strong> View and interact with dynamic maps that display well locations, extraction levels, and environmental restrictions.</li>
        <li><strong>Scenario Analysis:</strong> Simulate different water demand scenarios, including changes in population or small bussiness usage, to understand their potential impact on water supply and operational costs.</li>
        <li><strong>Environmental Cost Assessment:</strong> Estimate environmental costs associated with CO2 emissions and drought impact for each well, and assess potential restrictions due to protected areas like Natura2000.</li>
        <li><strong>Custom Well Management:</strong> Adjust well extraction levels and status (active or inactive) to optimize water resources and operational efficiency.</li>
        <li><strong>Interactive Data Exploration:</strong> Easily explore detailed well data, including security of supply,  OPEX, environmental costs, and performance per balance area.</li>
    </ul>
    
    <h2>Disclaimer</h2>
    <p>
        While this application provides valuable insights and data visualization for water management, the data used within this tool is based on various assumptions and estimates. Actual well performance, environmental impact, and operational costs may vary due to a range of factors such as real-time environmental conditions, regulatory changes, or unforeseen operational challenges.
    </p>
    <p>
        <strong>Please note:</strong> The results and outputs provided by this app should be used as indicative guidance rather than precise measurements. Users are advised to consult with local experts and use verified data sources for critical decision-making.
    </p>
    
    <p style="color: #666; font-size: 14px;">
        © 2024 Vitalens App. Vitens and University of Twente. All rights reserved.
    </p>
</div>
                         
                         ''', width=700, max_height=800)

flaotingDisclaimer = pn.layout.FloatPanel(disclaimer, name= "Welcome", margin=20, contained=False, position="center") 



scenario_layout = pn.Column(textScenarioPop, Scenario_Button, textDivider3, ScenarioSmall_Button, textEnd, ButtonReset, width=320)

Supply_measures_layout = pn.Column(textMeasureSupp, ButtonSmallWells,textCloseNatura, ButtonCloseNatura, textImport, ButtonImportWater,  textIndustrial, ButtonAddExtraIndustrial, textEnd, ButtonReset, width=320)

Demand_measures_layout = pn.Column(textMeasureDemand, ButtonDemand, textDivider0, textB5, Button5, textEnd, ButtonReset, width = 320)

firstColumn = pn.Column(balance_area_Text,radioButton_layout)
secondColumn = pn.Column(file_create, spinner, file_download)




tabTop = pn.Tabs(("1. Scenarios", scenario_layout), ("2. Supply", Supply_measures_layout), ("3. Demand", Demand_measures_layout), width = 320)
tabBottom = pn.Tabs(("4. Well Capacities", firstColumn), ("5. Generate Report", secondColumn), width = 320)

tabs = pn.Column(tabTop, tabBottom, sizing_mode="scale_height")

# MAIN WINDOW

# map_pane = pn.pane.HTML(create_map(52.38, 6.7, 10), sizing_mode="stretch_both")
map_pane = pn.pane.plot.Folium(update_layers(), sizing_mode="stretch_both")

minusSVG= pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M6 12L18 12" stroke="#4139a7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>', max_width=40,sizing_mode='scale_width', align='center')

equalSVG = pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M3 8C2.44772 8 2 8.44772 2 9C2 9.55228 2.44772 10 3 10H21C21.5523 10 22 9.55228 22 9C22 8.44772 21.5523 8 21 8H3Z" fill="#4139a7"></path> <path d="M3 14C2.44772 14 2 14.4477 2 15C2 15.5523 2.44772 16 3 16H21C21.5523 16 22 15.5523 22 15C22 14.4477 21.5523 14 21 14H3Z" fill="#4139a7"></path> </g></svg>', max_width=40,sizing_mode='scale_width', align='center')

total_extraction = pn.indicators.Number(
    name="Total Supply",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    sizing_mode="scale_width",
    align='center'
)



total_demand = pn.indicators.Number(
    name="Total Water Demand",
    value=calculate_total_Demand,
    format="{value:0,.2f} Mm\u00b3/yr",
    font_size="20pt",
    title_size="12pt",
    default_color='#3850a0',
    sizing_mode="scale_width", align='center'
)

total_difference = pn.indicators.Number(
    name="Water Balance",
    value=calculate_difference(),
    format="{value:.2f} Mm\u00b3/yr",
    colors=[(0, '#d9534f'), (10, '#f2bf58'), (100, '#92c25b')],
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    sizing_mode="scale_width", align='center'
)

total_extraction_TT = pn.widgets.TooltipIcon(value="Total supply is calculated as the sum of volumes of raw water extracted from each location in a year. Total demand is calculated as the yearly consumption of potable water by residents and small business.")

total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width"
)

total_opex_TT = pn.widgets.TooltipIcon(value="Total yearly Operational costs.")

total_capex = pn.indicators.Number(
    name="Total CAPEX",
    value=calculate_total_CAPEX(),
    format="{value:0,.2f} M\u20AC",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width"
)

total_capex_TT = pn.widgets.TooltipIcon(value="Total investment costs to expand the extraction capacity.")


# balance_opex = calculate_total_OPEX_by_balance()
# balance_opex_indicators = {
#     balance: pn.indicators.Number(
#         name=f"OPEX {balance}",
#         value=value,
#         format="{value:0,.2f} M\u20AC/yr",
#         default_color='#3850a0',
#         font_size="28pt",
#         title_size="18pt",
#         align="center",
#     )
#     for balance, value in balance_opex.items()
# }

excess_cap = pn.indicators.Number(
    name="Excess Capacity",
    value=calculate_available(),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",

)

excess_cap_TT = pn.widgets.TooltipIcon(value="Yearly available water that is not extracted from wells and is within the Maximum allowed extraction.")
excess_cap_row = pn.Row(excess_cap, excess_cap_TT)

industrial_extract = pn.indicators.Number(
    name="Industrial Water Extraction",
    value=calculate_industrial_extract(),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)
industrial_extract_TT = pn.widgets.TooltipIcon(value="Estimated yearly groundwater extracted by big industries over which Vitens has no control")

industrial_extract_row = pn.Row(industrial_extract, industrial_extract_TT)


right_pane = pn.Column(excess_cap_row,industrial_extract_row)

own_pane = pn.indicators.Number(
    name="Landownership",
    value=calculate_ownership(),
    format="{value:0.2f} %",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    colors=[(75, "#F19292"), (85, "#F6D186"), (100, "#CBE2B0")],
    sizing_mode="stretch_width"
)

natureMidDamage_value = pn.indicators.Number(
    name="Approximate <b>Sensitive</b> Nature affected area",
    value=calculate_affected_Sensitive_Nature(),
    format="{value:0.2f} Ha",
    default_color='#3850a0',
    font_size="14pt",
    title_size="10pt",
    sizing_mode="stretch_both",
    styles = {
        'font-family': "Roboto"
    }
)

natureHighDamage_value = pn.indicators.Number(
    name="Approximate <b>Very Sensitive</b> Nature affected area",
    value=calculate_affected_VerySensitive_Nature(),
    format="{value:0.2f} Ha",
    default_color='#3850a0',
    font_size="14pt",
    title_size="10pt",
    # sizing_mode="stretch_both",
    styles = {
        'font-family': "Roboto"
    }
)

natureDamage_TT = pn.widgets.TooltipIcon(value='This area corresponds to the extent of drought sensitive groundwater dependent nature that might be affected due to groundwater extraction.')

# nature_title = pn.Row(natureMidDamage_value,natureDamage_TT, sizing_mode="scale_both" )

# Use pn.bind to dynamically bind the number of stars to the pane
keukenhofsMid = pn.bind(generate_area_SVG, natureMidDamage_value)
keukenhofsHigh = pn.bind(generate_area_SVG, natureHighDamage_value)
keuk_text = pn.pane.HTML("<p style='font-size: small;'>Represented in number of Keukenhof parks")
natura_pane = pn.Column(natureDamage_TT, natureHighDamage_value,  spacer(10),keukenhofsHigh,  natureMidDamage_value, spacer(20),keukenhofsMid, keuk_text)


pipes_TT = pn.widgets.TooltipIcon(value="Each icon represents the number of connections between two balance areas, this is an indicator of vulnerability in the system.")

pipes_pane =pn.Column(pipes_TT, generate_pipes_SVG("Reggeland","Stedenband",1), generate_pipes_SVG("Reggeland","Hof van Twente", 2), generate_pipes_SVG("Reggeland","Dinkelland", 1), generate_pipes_SVG("Hof van Twente", "Stedeban", 3), generate_pipes_SVG("Dinkelland", "Stedeband", 1), width=250)

co2_pane = pn.indicators.Number(
    name="CO\u2082 Emission Cost",
    value=calculate_total_CO2_cost(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)

drought_pane = pn.indicators.Number(
    name="Drought Damage Cost",
    value=calculate_total_Drought_cost(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)

# df_display = pn.pane.Markdown(update_df_display())
#df_Hexagons = pn.pane.DataFrame(hexagons_filterd.head(), name="Hexagons data")



lzh = pn.indicators.Gauge(
    name=f"Overall LZH",
    value=calculate_lzh(),
    bounds=(0, 150),
    format="{value} %",
    colors=[(0.66, "#D9534F"), (0.8, "#f2bf57"),(0.9, "#92C25B"), (1, "#8DCEC0")],
    custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align=("center",'center'), height = 250, title_size = 14
)
lzh.param.watch(update_indicators, "value")
lzh_definition = pn.pane.HTML("LZH: Leveringszekerheid, is an indicator of supply security. It is the percentage of drinking water demand that is covered by the supply")
lzh_tooltip = pn.widgets.TooltipIcon(value="LZH: Leveringszekerheid, is an indicator of supply security. It is the percentage of drinking water demand that is covered by the supply. You can see the LZH for each balance area by selecting the tabs on the right. These values assume a closed system.")

balance_lzh_gauges = {}
balance_lzh_values = calculate_lzh_by_balance()
for area, value in balance_lzh_values.items():
    gauge = pn.indicators.Gauge(
        name=f"LZH \n{area}",
        value=value,
        bounds=(0, 630),
        format="{value} %",
        colors=[(0.2, "#D9534F"), (0.24, "#f2bf57"),(0.27, "#92C25B"), (1, "#8DCEC0")],
        custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align=("center",'center'), height = 250, title_size = 14
    )
    balance_lzh_gauges[area] = gauge
    


def printResults(filename1):
    print("Button clicked, generating report...")

    printingReport.styledWells(active_wells_df)
    printingReport.generate_matplotlib_stackbars(active_wells_df, filename1)
    # printingReport.generate_image_fromInd(pane=lzh, filename=filename2)
    printingReport.createPDF(filename1, Scenario_Button, ScenarioSmall_Button, ButtonSmallWells, ButtonCloseNatura, ButtonImportWater, ButtonAddExtraIndustrial, ButtonDemand,total_demand,total_extraction,total_opex,total_capex, co2_pane,drought_pane,natureMidDamage_value, natureHighDamage_value)
    return print("File Created")

# When clicking the button, show the spinner and run the function
def on_button_click(event):
    spinner.value = True  # Show the spinner
    printResults("wells_Distribution.png")
    spinner.value = False  # Hide the spinner when done
    pn.state.notifications.position = 'bottom-left'
    pn.state.notifications.success('Report File created, you can download it now', duration=4000)


file_create.on_click(on_button_click)


# lzhTabs = pn.Tabs(lzh, *balance_lzh_gauges.values(), align=("center", "center"))
Env_pane = pn.Column(co2_pane, drought_pane)

# indicatorsArea = pn.GridSpec(sizing_mode="scale_both")
indicatorsArea = pn.Tabs(lzh, *balance_lzh_gauges.values(), ("Help",lzh_tooltip), align=("center", "center"), sizing_mode="scale_height", tabs_location="right")
# indicatorsArea = Env_pane



CostPane = pn.Row(
    total_opex, total_opex_TT, total_capex, total_capex_TT, align=("center", "center")
)

verticalLine = pn.pane.HTML(
    '''
    <hr style="width: 1px; height: 100px; display: flex;">
    '''
)

Supp_dem =  pn.Row(
    total_extraction, minusSVG, total_demand, equalSVG, total_difference, total_extraction_TT)

app_title = pn.pane.Markdown("## Scenario: Current State - 2024", styles={
    "text-align": "right",
    "color": "#5266d9"
})


# Define a JSComponent to inject Google Translate
class GoogleTranslateWidget(JSComponent):
    _template = """
    <div id="google_translate_element"><button>Transnlate</button></div>
    <script type="text/javascript">
      function googleTranslateElementInit() {
          new google.translate.TranslateElement({pageLanguage: 'en', includedLanguages: 'en,nl,fr,es,de,', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');
      }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    """

# Create your Google Translate component
translate_widget = pn.pane.HTML("""
    <div id="google_translate_element"><button>Transnlate</button></div>
    <script type="text/javascript">
      function googleTranslateElementInit() {
          new google.translate.TranslateElement({pageLanguage: 'en', includedLanguages: 'en,nl,fr,es,de,', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');
      }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    """)



main1 = pn.GridSpec(sizing_mode="scale_both")
main1[0, 0:1] = pn.Column(map_pane)

main2 = pn.GridSpec(sizing_mode="stretch_both")
main2[0,0:2] = pn.Column(
    indicatorsArea, lzh_definition, textDivider0, Supp_dem, textDivider1, CostPane, textDivider2, natura_pane,
    scroll=True
)
main2[0,2] = pn.Column(
    Env_pane, right_pane, textDivider0, pipes_pane,
    sizing_mode="scale_width",
    scroll=True
)

main1[0, 1] = pn.Column(app_title, main2, sizing_mode="scale_both")


Box = pn.template.MaterialTemplate(
    title="Vitalens",
    logo="https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png",
    sidebar=[tabs],
    main=[main1],
    header_background= '#3850a0',
    header_color= '#f2f2ed',
    sidebar_width = 350,
    collapsed_sidebar = False,
)

Box.main.append(flaotingDisclaimer)




def total_extraction_update():
    """
    Update the total extraction and related indicators.
    """
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    # update_balance_opex()
    update_balance_lzh_gauges()
    update_indicators()
    total_demand.value = calculate_total_Demand()
    total_difference.value = calculate_difference()
    calculate_affected_Sensitive_Nature()
    map_pane
    co2_pane.value = calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    flaotingDisclaimer

total_extraction_update()
Box.servable()