import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
from bokeh.models.formatters import PrintfTickFormatter
import folium
from folium.features import Template, DivIcon
# import keplergl
from shapely.geometry import shape, Polygon, Point
import branca
from branca.element import Template, MacroElement
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
  --design-secondary-color: #00B893 !important;
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
    border-radius: 1px;
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
        background-color: #b1b1c9;
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
  background-color: #3872A1;
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
  background-color: #f1b858;   
}

.accordion-header button{
    color: #151931;
    background-color: #B4BFE4;
}


.bk-tab.bk-active {
    background: #d3d3cf !important;
    color: #d9534f !important;
}

.maplegend .legend-title {
            text-align: left;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 90%;
            }
.maplegend .legend-scale ul {
    margin: 0;
    margin-bottom: 5px;
    padding: 0;
    float: left;
    list-style: none;
    }
.maplegend .legend-scale ul li {
    list-style: none;
    margin-left: 0;
    line-height: 18px;
    margin-bottom: 2px;
    }
.maplegend ul.legend-labels li span {
    font-size: smaller;
    display: block;
    float: left;
    height: 16px;
    width: 30px;
    margin-right: 5px;
    margin-left: 0;
    border: 1px solid #999;
    }
.maplegend .legend-source {
    font-size: 80%;
    color: #777;
    clear: both;
    }
.maplegend a {
    color: #777;
    }
    
.Label {
    text-shadow:
    -1px -1px 0 #fff,
    1px -1px 0 #fff,
    -1px 1px 0 #fff,
    1px 1px 0 #fff;  
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

js_legend = '''
    $(function() {
        // Ensure the element exists before making it draggable
        if ($('#maplegend').length) {
            $('#maplegend').draggable({
                start: function(event, ui) {
                    // Reset positioning constraints to allow free dragging
                    $(this).css({
                        right: 'auto',   // Reset 'right' so the element can move left
                        top: 'auto',     // Reset 'top' so it can move freely
                        bottom: 'auto'   // Reset 'bottom' to enable dragging downward
                    });
                }
            });
        } else {
            console.error("Element #maplegend not found.");
        }
    });
'''

js_files = {'leaflet-dataclassification': 'https://raw.githubusercontent.com/balladaniel/leaflet-dataclassification/master/dist/leaflet-dataclassification.js',
            'jsLegend': './Assets/test.js'}

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
pn.extension(js_files=js_files)

# VARIABLES
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


# Optimized Data Loading: Read all layers and then filter the required columns
def load_data(file_path):
    wells = gpd.read_file(file_path, layer=LAYER_WELLS)
    industrial = gpd.read_file(file_path, layer=LAYER_INDUSTRIAL_WELLS)
    main_pipes = gpd.read_file(file_path, layer=LAYER_PIPES)
    cities = gpd.read_file(file_path, layer=CITIES_LAYER)
    return wells, industrial, main_pipes, cities

wells, industrial, main_pipes, cities = load_data(GPKG_FILE)

# Standardize CRS once for all datasets
target_crs = "EPSG:28992"
wells = wells.to_crs(target_crs)
industrial = industrial.to_crs(target_crs)
main_pipes = main_pipes.to_crs(target_crs)
cities = cities.to_crs(target_crs)

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
        * 1e6,
        "OPEX": wells["totOpex_m3"] * wells["Extraction_2023__Mm3_per_jr_"] * 1e6,
        "CAPEX": 0,
        "geometry": wells["geometry"],
    }
)
active_wells_df.astype({"Num_Wells": "int32", "Ownership": "int32"}, copy=False)


original_OPEX = active_wells_df["OPEX"].sum()/1e6
original_CO2 = (active_wells_df["CO2_m3"]*active_wells_df["Current Extraction"]).sum()
original_Draught = (active_wells_df["Drought_m3"]*active_wells_df["Current Extraction"]).sum()
original_excess = active_wells_df["Max_permit"].sum() - active_wells_df["Current Extraction"].sum()

cities_clean = gpd.GeoDataFrame(
    {
        "cityName" : cities["statnaam"],
        "Population 2022": cities["SUM_Pop_2022"],
        "Water Demand": cities["SUM_Water_Demand_m3_YR"]/ 1e6,
        "geometry" : cities["geometry"]
    })

cities_clean.loc[cities_clean["cityName"].isna(), "Water Demand"] = None

demand_capita, smallBusiness = DEMAND_PERCAPITA, SMALL_BUSINESS_RATE

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
        "Water Demand": hexagons["Pop_2022"] * demand_capita * smallBusiness * 365 / 1e6,
        "Type": hexagons["Type_T"],
        "Source_Name": hexagons["Source_Name"],
        "geometry": hexagons["geometry"],
    }, copy=False
)
original_demand = hexagons_filterd["Water Demand"].sum()+hexagons_filterd["Industrial Demand"].sum()

balance_areas= hexagons_filterd.dissolve(by="Balance Area", as_index=False)

naturaUnfiltered = NATURE_DAMAGE_CSV
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
        active_wells_df["Max_permit"].sum()
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
    )/1e6

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
        mDamage = estimate_Damage_for_well(naturaDamageMid, name, target) or 0

    
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
        mDamage = estimate_Damage_for_well(naturaDamageHigh, name, target) or 0
    
        midDamage = midDamage + mDamage

    
    # restricted = hexagons_filterd[
    #     (hexagons_filterd["Source_Name"].isin(names))
    #     & (hexagons_filterd["Type"] == "Source and Restricted")
    # ]
    # total = restricted.shape[0]
    # ha = total * 629387.503078 / 100000
    return midDamage

def generate_area_SVG (n):
    SVG = '''<?xml version="1.0" encoding="UTF-8"?><svg id="Layer_1" height="45px" width="45px" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 64 64"><defs><style>.cls-1{stroke-linejoin:bevel;}.cls-1,.cls-2,.cls-3,.cls-4,.cls-5,.cls-6{fill:none;}.cls-1,.cls-3,.cls-4{stroke-width:.7px;}.cls-1,.cls-3,.cls-4,.cls-5,.cls-6{stroke:#e6e6e6;}.cls-1,.cls-4,.cls-5{stroke-linecap:round;}.cls-7{fill:#9bc45b;}.cls-3,.cls-8,.cls-4,.cls-6{stroke-miterlimit:10;}.cls-8{fill:#ccc;stroke:#ccc;}.cls-5{stroke-linejoin:round;}.cls-5,.cls-6{stroke-width:.4px;}.cls-9{fill:#b3b3b3;}.cls-10{clip-path:url(#clippath);}</style><clipPath id="clippath"><path class="cls-2" d="M26.52,4.49c2.42.46,4.79,1.44,7.25,1.25,2.49-.18,4.78-1.54,7.27-1.72,3.17-.24,6.61,1.39,9.39-.15,1.9-1.05,3.24-3.49,5.4-3.34,1.12.08,2.07.91,2.61,1.89s.73,2.11.9,3.22c2.76,17.36,3.68,34.95,4.6,52.5.05.98-.03,2.19-.91,2.61-.5.23-1.08.12-1.61,0-8.39-1.89-16.69-4.15-24.99-6.41-3.43-.94-6.86-1.87-10.3-2.81-1.56-.42-3.16-.87-4.46-1.83-2.55-1.89-3.35-5.28-4.07-8.37-.68-2.9-1.64-6.07-4.18-7.63-1.52-.93-3.43-1.16-4.79-2.3-1.3-1.09-1.86-2.8-2.31-4.43-.74-2.72-1.3-5.49-1.69-8.28-.19-1.4-.35-2.8-.45-4.21-.07-.97-.55-2.93-.14-3.83.68-1.48,4.61-2.59,6.06-3.24,2.49-1.1,5.06-2.07,7.73-2.65,2.85-.63,5.81-.81,8.68-.26Z"/></clipPath></defs><path class="cls-7" d="M26.52,4.49c2.42.46,4.79,1.44,7.25,1.25,2.49-.18,4.78-1.54,7.27-1.72,3.17-.24,6.61,1.39,9.39-.15,1.9-1.05,3.24-3.49,5.4-3.34,1.12.08,2.07.91,2.61,1.89s.73,2.11.9,3.22c2.76,17.36,3.68,34.95,4.6,52.5.05.98-.03,2.19-.91,2.61-.5.23-1.08.12-1.61,0-8.39-1.89-16.69-4.15-24.99-6.41-3.43-.94-6.86-1.87-10.3-2.81-1.56-.42-3.16-.87-4.46-1.83-2.55-1.89-3.35-5.28-4.07-8.37-.68-2.9-1.64-6.07-4.18-7.63-1.52-.93-3.43-1.16-4.79-2.3-1.3-1.09-1.86-2.8-2.31-4.43-.74-2.72-1.3-5.49-1.69-8.28-.19-1.4-.35-2.8-.45-4.21-.07-.97-.55-2.93-.14-3.83.68-1.48,4.61-2.59,6.06-3.24,2.49-1.1,5.06-2.07,7.73-2.65,2.85-.63,5.81-.81,8.68-.26Z"/><g class="cls-10"><path class="cls-8" d="M61.19,60.69c-3.27.07-6.45-1.04-9.49-2.24-.73-.29-1.46-.58-2.24-.7-.72-.11-1.45-.08-2.17-.16-1.02-.12-2.02-.48-2.82-1.11s-1.41-1.53-1.61-2.54c-.18-.9-.02-1.84-.16-2.75-.18-1.19-.87-2.29-1.87-2.96l4.23-1.21,2.65-1.09,2.62-1.45,2.44-.2-4.95,11.67.24.95,13.14,3.79Z"/><path class="cls-4" d="M34.71,28.24c3.5,9.05,5.02,9.96,5.97,19.7"/><path class="cls-9" d="M31.4,20.57l-.74.29,2.33,6.5.57.64s.88.62,2.36-.5,1.87-2.08,1.87-2.08c0,0,1.11-3.06,0-3.74s-2.05-1.32-3.32-1.37-3.08.26-3.08.26Z"/><path class="cls-5" d="M20.56,18.27c-.43-1.19.03-2.19.85-3.14s1.96-1.58,3.1-2.13c2.27-1.12,4.66-2.08,7.18-2.31,3.73-.34,7.4.96,10.87,2.38,1.83.75,3.67,1.56,5.13,2.89,1.97,1.79,3.06,4.33,3.86,6.87,1.59,5.07,2.2,10.44,1.86,15.74-.09,1.43-.27,2.92-1.08,4.1-.63.93-1.58,1.59-2.55,2.16-3.14,1.87-6.69,3.13-10.35,3.29-3.65.17-7.4-.81-10.32-3.01-4.03-3.04-6.11-8.04-7.1-12.99-1-4.95-.43-8.91-1.45-13.85"/><path class="cls-6" d="M27.07,15.76c1.85-.96,4.05-.99,6.13-.73,3.98.49,7.98,2.04,10.62,5.04,3.2,3.64,3.97,8.75,4.61,13.55.17,1.29.33,2.64-.12,3.86-.74,2.01-2.89,3.06-4.85,3.92-2.42,1.07-5.06,2.16-7.64,1.56-2.24-.52-4.01-2.24-5.43-4.05-3.97-5.07-6.75-12.35-6.25-18.88.14-1.81,1.32-3.44,2.92-4.27Z"/><path class="cls-4" d="M4.48,22.48c8.35-2.28,18.94-3.49,27.48-2.06.42.07.79-.29.72-.71-.4-2.23-1.04-4.41-1.33-6.65-.32-2.53-.14-5.25,1.24-7.4"/><path class="cls-4" d="M29.67,45.35c1.02-2.69,3.03-4.67,5.56-6.05s5.33-2.14,8.1-2.89c3.41-.92,6.49-1.85,9.9-2.77"/><path class="cls-4" d="M50.34,20.14c-1.33.33-2.18,1.58-2.99,2.68s-1.87,2.26-3.24,2.25c-1.27,0-2.27-1.01-3.25-1.8-2.32-1.87-6.03-2.91-9.01-2.84"/><path class="cls-4" d="M44.53,14.2c-.38,1.46-.93,3.13-2.34,3.69-.64.26-1.37.23-2.01.47-1.5.56-2.1,2.32-2.53,3.86-.32,1.17-.56,2.62.35,3.41.47.4,1.11.5,1.71.66,2.84.76,5.09,3.39,5.4,6.32.07.65.52,2.5.7,3.13"/><path class="cls-4" d="M13.9,34.05c.98-2.27,1.97-4.55,3.1-6.75.67-1.3,1.39-2.58,1.72-4,.84-3.6-.99-7.24-1.35-10.92-.23-2.35.53-8.33.91-10.66"/><path class="cls-4" d="M14.52,34.97c.91.92.93,2.53,1.98,3.28.67.48,1.57.46,2.37.27,2.8-.66,5.74-3.25,8.57-3.8"/><path class="cls-1" d="M52.55,25.9l5.15-18.43c.97-.67,2.27-1.01,3.44-1.13"/><path class="cls-3" d="M44.94,14.1c.88-3.08,1.88-6.19,3.65-8.86S53.02.34,56.17-.26"/></g></svg>
   '''
    
    HaSVG = 31.74
    full = int(n/HaSVG)
    leftover = (n % 1)
    segment = leftover*45
 
    
    partialSVG = '''
    <?xml version="1.0" encoding="UTF-8"?><svg height="45px" width="45px" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 64 64"><defs><style>.cls-1,.cls-2{fill:#777;}.cls-1,.cls-3{stroke:#fff;stroke-linecap:round;stroke-linejoin:round;}.cls-4{fill:#29abe2;}.cls-5{fill:#ee8700;}.cls-6{fill:#fff;}.cls-7{mask:url(#mask);}.cls-8{fill:#b8002b;}.cls-9{fill:#64c37d;}.cls-10{isolation:isolate;}.cls-11{mix-blend-mode:multiply;}.cls-12{fill:#a4e276;}.cls-13{mix-blend-mode:hue;}.cls-14{fill:#d8143a;}.cls-3{fill:none;}.cls-15{fill:#22b573;}.cls-16{mix-blend-mode:saturation;}'''+f'''</style><mask id="mask" x="8" y="0" width="47" height="45" maskUnits="userSpaceOnUse"><rect class="cls-6" x="8" y="0" width="47" height="{segment}"/></mask>'''+'''</defs><g class="cls-10"><g id="Layer_1"><g class="cls-11"><g class="cls-16"><path class="cls-15" d="M34,63c-.12,0-.23-.04-.32-.12l-19-16c-.06-.05-.1-.11-.13-.18l-5-11c-.09-.19-.05-.41.1-.56l3-3,1.85-2.8v-2.85c0-.09.02-.18.07-.26L29.57,1.24c.09-.16.26-.24.43-.24.08,0,.16.02.23.06l21,11c.12.06.21.18.25.31s.01.28-.06.4l-6.7,10.53,9.5,4.75c.13.06.23.18.26.32.04.14,0,.29-.08.41l-6.76,9.66,1.7,1.7c.17.17.19.43.06.63l-4,6c-.06.09-.15.16-.26.2l-2.82.94-2.76,4.61.88,1.75c.08.17.07.37-.05.52l-6,8c-.08.11-.21.18-.34.2-.02,0-.04,0-.06,0Z"/><path class="cls-15" d="M30,1.5l21,11-7,11,10,5-7,10,2,2-4,6-3,1-3,5,1,2-6,8-19-16-5-11,3-3,2-3v-3L30,1.5M30,.5c-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.14.15.26.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82s-.26-.52-.52-.65l-9.01-4.5,6.4-10.06c.15-.24.19-.52.12-.79-.07-.27-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11h0Z"/></g><path class="cls-4" d="M14,36.5s1,2,3,1,1-2,3-2,3-2,5-2,3,1,4,0c.64-.64,1.68-1.28,2.35-1.65.29-.16.64.06.61.39-.07.89-.29,2.26-.97,2.26-1,0-1,1-3,1s-3-1-3,0-2,3-2,5-6,2-6,1-1,0-2-2-2-3-1-3Z"/><path class="cls-6" d="M40,30.5c1.66,0,3,1.34,3,3s-1.34,3-3,3-3-1.34-3-3,1.34-3,3-3M40,29.5c-2.21,0-4,1.79-4,4s1.79,4,4,4,4-1.79,4-4-1.79-4-4-4h0Z"/><path class="cls-3" d="M41.64,40.43l-2.97-13.77-17.17-10.66,17.17,10.66,3.83,2.34s4.87,3.9,2.11,6.89c-.03.03-1.69,2.23-2.57,3.4-.34.45-.58.61-.4,1.14l.86,2.57-10.96,17.19s-3.04-7.19-4.04-7.19-2-1-2-1c0,0-5-6-6-7s-2-1-3-1-4-4-4-6,3-6,3-6L30.5,7"/><line class="cls-3" x1="49.5" y1="32" x2="40.1" y2="33.45"/><g id="SVGRepo_iconCarrier"><path class="cls-5" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M35.48,9.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M37.06,13.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M38.33,16.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M34.78,14.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-2"><path class="cls-5" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M26.48,21.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M28.06,25.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M29.33,28.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M25.78,26.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-3"><path class="cls-5" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M27.48,36.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M29.06,40.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M30.33,43.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M26.78,41.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-4"><path class="cls-5" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-5" d="M34.48,42.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-14" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-8" d="M36.06,46.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-12" d="M37.33,49.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-9" d="M33.78,47.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g></g><g class="cls-7"><g class="cls-13"><g class="cls-16"><path class="cls-2" d="M34,63c-.12,0-.23-.04-.32-.12l-19-16c-.06-.05-.1-.11-.13-.18l-5-11c-.09-.19-.05-.41.1-.56l3-3,1.85-2.8v-2.85c0-.09.02-.18.07-.26L29.57,1.24c.09-.16.26-.24.43-.24.08,0,.16.02.23.06l21,11c.12.06.21.18.25.31s.01.28-.06.4l-6.7,10.53,9.5,4.75c.13.06.23.18.26.32.04.14,0,.29-.08.41l-6.76,9.66,1.7,1.7c.17.17.19.43.06.63l-4,6c-.06.09-.15.16-.26.2l-2.82.94-2.76,4.61.88,1.75c.08.17.07.37-.05.52l-6,8c-.08.11-.21.18-.34.2-.02,0-.04,0-.06,0Z"/><path class="cls-15" d="M30,1.5l21,11-7,11,10,5-7,10,2,2-4,6-3,1-3,5,1,2-6,8-19-16-5-11,3-3,2-3v-3L30,1.5M30,.5c-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.14.15.26.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82s-.26-.52-.52-.65l-9.01-4.5,6.4-10.06c.15-.24.19-.52.12-.79-.07-.27-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11h0Z"/></g><path class="cls-2" d="M14,36.5s1,2,3,1,1-2,3-2,3-2,5-2,3,1,4,0c.64-.64,1.68-1.28,2.35-1.65.29-.16.64.06.61.39-.07.89-.29,2.26-.97,2.26-1,0-1,1-3,1s-3-1-3,0-2,3-2,5-6,2-6,1-1,0-2-2-2-3-1-3Z"/><circle class="cls-2" cx="40" cy="33.5" r="3.5"/><path class="cls-6" d="M40,30.5c1.66,0,3,1.34,3,3s-1.34,3-3,3-3-1.34-3-3,1.34-3,3-3M40,29.5c-2.21,0-4,1.79-4,4s1.79,4,4,4,4-1.79,4-4-1.79-4-4-4h0Z"/><path class="cls-1" d="M41.64,40.43l-2.97-13.77-17.17-10.66,17.17,10.66,3.83,2.34s4.87,3.9,2.11,6.89c-.03.03-1.69,2.23-2.57,3.4-.34.45-.58.61-.4,1.14l.86,2.57-10.96,17.19s-3.04-7.19-4.04-7.19-2-1-2-1c0,0-5-6-6-7s-2-1-3-1-4-4-4-6,3-6,3-6L30.5,7"/><line class="cls-1" x1="49.5" y1="32" x2="40.1" y2="33.45"/><g id="SVGRepo_iconCarrier-5"><path class="cls-2" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M35.48,9.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M37.09,10.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M37.06,13.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M38.33,16.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M34.78,14.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-6"><path class="cls-2" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M26.48,21.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M28.09,22.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M28.06,25.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M29.33,28.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M25.78,26.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-7"><path class="cls-2" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M27.48,36.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M29.09,37.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M29.06,40.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M30.33,43.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M26.78,41.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g><g id="SVGRepo_iconCarrier-8"><path class="cls-2" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.89-.88c-.16-.16-.42-.16-.58,0l-.88.87-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M34.48,42.52c-.16-.16-.42-.16-.58,0l-.88.87.3.28.92.86.22-.22.33-.33.29-.29.29-.29-.89-.88Z"/><path class="cls-2" d="M36.09,43.05c-.15-.06-.33-.03-.45.09l-.26.26-.29.29-.29.29-.33.33-.22.22.29.27s0,0,0,0h.01s.3.29.3.29l.37.34.69.64.15.14c.13.12.17.31.09.47,0,0,0,0,0,0,0,0,0,0,0,0,.13-.28.19-.58.19-.88v-2.37c0-.17-.1-.32-.25-.38Z"/><path class="cls-2" d="M36.06,46.22l-.15-.14-.69-.64-.37-.34-.3-.28h-.01s0-.01,0-.01l-.29-.27-.92-.86-.3-.28-.28-.26c-.12-.11-.29-.14-.45-.08-.15.07-.25.21-.25.38v2.37c0,1.04.75,1.92,1.74,2.11.13.03.27.04.41.04s.28-.01.41-.04c.67-.13,1.26-.58,1.55-1.22,0,0,0,0,0,0,.07-.16.03-.35-.09-.47Z"/><path class="cls-2" d="M37.33,49.48s-.65-1.07-1.74-1.07c-.39,0-.71.13-.98.3v-.8c-.13.03-.27.04-.41.04s-.28-.01-.41-.04v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41s.41-.18.41-.41v-.48c.28.19.62.35.98.35,1.09,0,1.72-1.03,1.74-1.07.08-.13.08-.29,0-.42Z"/><path class="cls-2" d="M54.97,28.25c-.07-.28-.26-.52-.52-.65l-9.01-4.5,6.41-10.06c.15-.24.19-.52.12-.79s-.25-.5-.5-.63L30.46.61c-.15-.08-.31-.11-.46-.11-.34,0-.67.17-.86.49l-15,25c-.09.16-.14.33-.14.51v2.7l-1.78,2.67-2.93,2.93c-.29.29-.38.74-.2,1.12l5,11c.06.13.15.25.27.35l19,16c.18.15.41.24.64.24.04,0,.08,0,.11,0,.27-.03.52-.17.69-.39l6-8c.23-.3.26-.71.09-1.05l-.75-1.51,2.53-4.21,2.65-.88c.21-.07.39-.21.52-.39l4-6c.26-.4.21-.92-.12-1.26l-1.41-1.41,6.52-9.31c.17-.24.22-.54.15-.82Z"/><path class="cls-2" d="M33.78,47.91v.8c-.26-.17-.59-.3-.98-.3-1.09,0-1.72,1.03-1.74,1.07-.09.15-.08.34.03.47.08.1.84,1.02,1.71,1.02.39,0,.71-.13.98-.3v.43c0,.23.18.41.41.41v-3.57c-.14,0-.28-.01-.41-.04Z"/></g></g></g></g></g></svg>
  '''
    
    fig = pn.pane.HTML(SVG*(full))
    fig2 = pn.pane.HTML(partialSVG)
    
    composite = pn.Column(fig)
    
    return composite


def generate_pipes_SVG(origin, destination, n):
    SVG = '''<?xml version="1.0" encoding="UTF-8"?><svg id="Pipeline_1" height="45px" width="45px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 35"><defs><style>.cls-1{fill:#41537b;}.cls-2{fill:#a2aea7;}.cls-3{fill:#bdcbc3;}.cls-4{fill:#d9cdf1;}.cls-5{fill:#3b5b6e;}.cls-6{fill:#4c6fb0;}.cls-7{fill:#374766;}.cls-8{fill:#4d83b1;}.cls-9{fill:#2c535f;}.cls-10{fill:#3a6284;}.cls-11{fill:#3f6697;}.cls-12{fill:#3c6585;}</style></defs><path class="cls-12" d="M34.35,12.01c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M33.5,12.55c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M30.75,7.98c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M33.54,12.53c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M32.69,13.06c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M29.94,8.5c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M32.75,13.04c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M31.9,13.57c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M29.15,9c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-11" d="M25.15,9.94l-.83-.89,1.49-.89c.06-.04.11-.08.17-.11h.01s0,0,0,0c.49-.26,1.15-.21,1.87.2,1.49.85,2.71,2.98,2.71,4.72,0,.76-.23,1.32-.61,1.65h0s0,0,0,0c-.1.08-.21.15-.32.2l-1.5.92-.8-1.55c-1.21-.99-2.14-2.75-2.18-4.25Z"/><path class="cls-10" d="M28.92,13.96c0-1.75-1.22-3.87-2.71-4.72-1.49-.85-2.71-.14-2.71,1.59s1.22,3.85,2.71,4.72c1.49.87,2.71.16,2.71-1.59Z"/><path class="cls-2" d="M28.06,13.47c0-1.19-.83-2.64-1.85-3.22-1.02-.58-1.85-.09-1.85,1.08s.83,2.63,1.85,3.22c1.02.6,1.85.11,1.85-1.08Z"/><path class="cls-4" d="M26.25,14.1c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M25.12,14.8c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M24.12,15.43c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M23.65,16.51c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M22.99,16.13c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M22.1,16.66c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M20.97,17.36c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M19.97,18c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M19.5,19.07c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M18.84,18.7c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M18.02,19.2c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M16.89,19.9c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M15.9,20.53c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-1" d="M15.42,21.61c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-7" d="M14.77,21.23c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M13.87,21.76c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M12.74,22.46c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-4" d="M11.75,23.1c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-6" d="M28.16,13.72c0-1.33-.93-2.94-2.06-3.59-.16-.09-.31-.15-.45-.2h0c-.56-.22-1.04.05-1.04.05l-13.3,8.27-.27.16h0s-.09.05-.13.08l-.52.32-.49.29h0c-.06.03-.11.07-.16.11l-1.97,1.22.51.54s0,.07,0,.11c0,1.25.85,2.79,1.92,3.5l.48.93,1.14-.7c.09-.04.17-.09.25-.15h0s0,0,0,0c0,0,0,0,.01,0l.87-.54c.09-.04.17-.09.25-.15h0s0,0,0,0c0,0,0,0,0,0l2.8-1.72c.07-.03.13-.07.19-.12l.95-.58c.06-.03.12-.07.18-.11l10.25-6.31s.31-.19.4-.47h0c.13-.24.21-.55.21-.93Z"/><path class="cls-3" d="M11.27,24.17c0-1.33-.93-2.94-2.06-3.59-1.13-.65-2.06-.1-2.06,1.21s.93,2.93,2.06,3.59c1.13.66,2.06.12,2.06-1.21Z"/><path class="cls-2" d="M10.61,23.79c0-.91-.63-2.01-1.41-2.45-.77-.44-1.41-.07-1.41.82s.63,2,1.41,2.45c.77.45,1.41.08,1.41-.82Z"/><path class="cls-11" d="M5.95,20.81l-1-1.07,1.79-1.07c.07-.05.14-.1.21-.14h.01s0,0,0,0c.59-.31,1.38-.26,2.24.24,1.79,1.02,3.26,3.58,3.26,5.68,0,.91-.28,1.59-.74,1.98h0s0,0,0,0c-.12.1-.25.18-.39.24l-1.8,1.11-.96-1.86c-1.46-1.19-2.57-3.31-2.62-5.1Z"/><path class="cls-8" d="M10.48,25.65c0-2.1-1.47-4.65-3.26-5.68-1.79-1.02-3.26-.17-3.26,1.91s1.47,4.63,3.26,5.68c1.79,1.05,3.26.19,3.26-1.91Z"/><path class="cls-12" d="M10.95,25.94c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M10.1,26.48c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M7.35,21.91c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M10.14,26.46c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M9.29,26.99c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M6.54,22.42c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/><path class="cls-12" d="M9.35,26.97c0-2.53-1.77-5.6-3.92-6.83-1.11-.64-2.12-.67-2.84-.21h0l-.68.44h.2c-.38.48-.61,1.18-.61,2.07,0,2.49,1.77,5.57,3.92,6.83.79.46,1.52.61,2.14.5l-.11.23.67-.43h0c.75-.4,1.22-1.3,1.22-2.61Z"/><path class="cls-5" d="M8.5,27.5c0-2.53-1.77-5.6-3.92-6.83-2.16-1.23-3.92-.2-3.92,2.3s1.77,5.57,3.92,6.83c2.16,1.26,3.92.23,3.92-2.3Z"/><path class="cls-9" d="M5.75,22.93c-.36-.4-.75-.73-1.17-.97-1.55-.88-2.81-.14-2.81,1.64,0,1.68,1.11,3.72,2.53,4.71.09.07.19.13.28.18,1.55.9,2.81.16,2.81-1.64,0-1.32-.68-2.85-1.64-3.93Z"/></svg>'''
    fig =pn.pane.HTML(SVG*n)
    OD = pn.pane.HTML(f'<p style="color:#3850A0; font-size:14px; margin:4px;">Leidingen van \n<b>{origin} naar {destination}</b>:  ')
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
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = event.new
    opex_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX"] = (
        event.new * opex_m3 * 1e6
    )
    env_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "Env_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "envCost"] = (
        event.new * env_m3 * 1e6
    )
    update_indicators()

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
    
    if event.new == "-20% van Huidige":
        new_value = current_value * 0.8
    elif event.new == "-15% van Huidige":
        new_value = current_value * 0.85
    elif event.new == "Huidige":
        new_value = current_value
    elif event.new == "85% van Max. Vergunning":
        new_value = max_value * 0.85
    elif event.new == "115% van Max. Vergunning":
        new_value = max_value * 1.15
    elif event.new == "Maximale Vergunning":
        new_value = max_value

    pn.state.notifications.position = 'bottom-left'

    if new_value > max_value:
     pn.state.notifications.error(f"Waarschuwing bij {well_name} put: Deze waarde ligt boven de extractievergunning. Gebruik van deze waarde vereist onderhandelingen voor een grotere waterextractievergunning.", 4000)

    
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = new_value
    opex_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX"] = new_value * opex_m3
    
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Value_formatted(well_name)
    update_indicators()

def update_allRadio(event):
    """
    Update all individual radio buttons to match the master selection.
    
    Args:
        event: The event object from the master radio button group.
    """
    # Get the selected value from the master radio button group
    selected_value = event.new
    
    # Update all individual radio groups with the selected value
    for well_data in active_wells.values():
        well_data["radio_group"].value = selected_value

    
def update_scenarios(event):
    if event.new == "Bevolking 2035":
        Scenario1()
        print('scenario 1 actief')
    if event.new == "Bevolking 2035 +1% toename":
        print('scenario 2 actief')
        Scenario2()
    if event.new == "Bevolking - 2022":
        print("Origineel Scenario")
        ScenarioBase()
    update_indicators()
    
def update_scenariosSmall(event):
    if event.new == "Kleine Bedrijven   +10% Vraag":
        ScenarioSmallBusiness1()
        print('scenario 1 klein actief')
    if event.new == "Kleine Bedrijven   +35% Vraag":
        print('scenario 2 klein actief')
        ScenarioSmallBusiness2()
    if event.new == "Kleine Bedrijven - 2022":
        print("Origineel Scenario")
        ScenarioSmallBusinessBase()
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
            'color': '#2d4c4d'
        }
    return valueStyle
    

def current_demand(event):
    global demand_capita 
    if ButtonSmartMeter.value:
        sm=0.95
    else: sm=1
    if event.new == 90:
        demand_capita  = 0.09*sm
    if event.new == 100:
        demand_capita  = 0.1*sm
    if event.new == 120:
        demand_capita  = 0.12*sm
    if event.new == 135:
        demand_capita  = 0.135*sm
    update_indicators()
    

def calculate_total_Demand():
    """
    Calculate the total water demand.

    Returns:
        float: Total water demand in Mm3/yr.
    """
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1e6
    
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
    location=[52.28, 6.7], zoom_start=11,
    tiles="Cartodb Positron",
)


icon_path = "./Assets/Water Icon.png"
icon = folium.CustomIcon(
        icon_path,
        icon_size=(30, 30),
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

def update_layers(wellsLayer=active_wells_df, industryLayer=industrial):
    """
    Update the layers on the map.

    Returns:
        folium.Map: Updated Folium map.
    """
    global m
    
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap",
                     show=False).add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', name="Satellite Imagery", 
                     attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community", show=False).add_to(m)
    
    popup_well = folium.GeoJsonPopup(
        fields=["Name", "Balance area", "Value"],
        aliases=["Naam Put", "Balansgebied", "Onttrekking in Mm³/jr"],
    )

    popup_hex = folium.GeoJsonPopup(
        fields=["cityName", "Water Demand", "Population 2022"],
        aliases=["Stadsnaam", "Watervraag in Mm³/jr", "Bevolking - 2022"]
    )

    popup_industrial = folium.GeoJsonPopup(
        fields=["Place", "Licensed", "Current_Extraction_2019"],
        aliases=["Locatie", "Vergunde Onttrekking in Mm³/jr", "Huidige Onttrekking in Mm³/jr"]
    )

    
    colormap = branca.colormap.StepColormap(
        ["#caf0f8", "#90e0ef", "#00b4d8", "#0077b6", "#03045e"],
        vmin=round(hexagons_filterd["Water Demand"].quantile(0.0),1),
        vmax=round(cities_clean["Water Demand"].quantile(1),1),
        caption="Totale watervraag in Mm\u00b3/yr",
    )
    
    active = wellsLayer[wellsLayer["Active"] == True]
    
    folium.GeoJson(
        active,
        name="Winningputten",
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
        name="Industriële Waterwinning",
        zoom_on_click=True,
        popup=popup_industrial,
        tooltip=folium.GeoJsonTooltip(fields=["Place"], aliases=["Place:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#d9534f", icon="industry", prefix="fa", color='lightred'
            )
        ),

    ).add_to(m)
    
    hex_layer = folium.GeoJson(
        cities_clean,
        name="Stadsvraag",
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

    folium.GeoJson(
        main_pipes,
        name="Hoofdleidingen",
        style_function=lambda x: { 
            "color": "#E27D79",
            "weight": (4 if x["properties"]["Diameter_mm"] > 350
                       else (2 if x["properties"]["Diameter_mm"] > 250
                       else 1)),
            "Opacity": 0.6,
        },
        show=False
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Natura2000 Beperkt Gebied",
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
        show=False,
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Beperkt Natuurnetwerk Nederland",
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
        show=False,
    ).add_to(m)
    
    folium.GeoJson(
        balance_areas,
        name="Balansgebieden",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#93419F",
            "weight": 3
        },
        show=True,
        tooltip=folium.GeoJsonTooltip(fields=['Balance Area'], labels=True)
    ).add_to(m)
    
    BA_4326 = balance_areas.to_crs(4326)
    BA_4326["centroid"] = BA_4326.centroid
    
    
    
    for _, r in BA_4326.iterrows():
        lat = r["centroid"].y
        lon = r["centroid"].x
        name = r["Balance Area"]
        print(lat,lon)
        folium.Marker(
        location=[lat, lon],
        icon=DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html='<div class="Label" style="font-size: 12pt; color: #F29544; text-align: center;"><b>Balansgebied \n{name}</b></div>'.format(name=name),)
        ).add_to(m)
     
    # cities_4326 = cities_clean.to_crs(4326)   
    # cities_4326["centroid"] = cities_4326.centroid
        
    # for _,r in cities_4326.iterrows():
    #     lat = r["centroid"].y
    #     lon = r["centroid"].x
    #     name = r["cityName"]
    #     print(lat,lon)
    #     folium.Marker(
    #     location=[lat, lon],
    #     icon=DivIcon(
    #         icon_size=(150,36),
    #         icon_anchor=(0,0),
    #         html='<div class="Label" style="font-size: 12pt; color: #282D3D; text-align: center;">{name}</div>'.format(name=name),)
    #     ).add_to(m)

    folium.LayerControl(position='topleft', autoZIndex=True).add_to(m)
    
    industryIcon = '''
        var marker = L.AwesomeMarkers.icon({
                icon_color="#d9534f", icon="industry", prefix="fa", color='lightred'
            )});
            '''
    
    # Use custom CSS to move the colormap legend to the bottom-right corner
    legend_html = '''
    <link rel="stylesheet" href="https://balladaniel.github.io/leaflet-dataclassification/leaflet-dataclassification.css" />
    <script src="https://balladaniel.github.io/leaflet-dataclassification/leaflet-dataclassification.js"></script>
    <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

    <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
           
     <div id='maplegend' class='maplegend' 
         style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
         border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
    
    <div class='legend-scale'>
        Legenda
        <ul class='legend-labels'>
            <li><i class="fa-solid fa-arrow-up-from-ground-water" style='color:#2F4279;'></i> Waterwinlocaties</li>
            <li><i class="fa-solid fa-industry" style='color:#D9534F;'></i> Industriële Waterwinlocaties</li>
            <li>{colormap}</li>
            <li>Leidingen <i class="fa-solid fa-minus fa-sm" style='color:#D9534F;'></i> <250mm 
                    <i class="fa-solid fa-minus fa-lg" style='color:#D9534F;'></i> 250mm - 350mm
                    <i class="fa-solid fa-minus fa-2xl" style='color:#D9534F;'></i> >400mm</li>             
            <li><i class="fa-solid fa-folder" style='color: darkgreen;'></i> Natura200 Beschermd Gebied</li>
            <li><i class="fa-solid fa-folder" style='color: #CAFAA2;'></i> Beperkt Natuurnetwerk Nederland Gebied</li>
            <li><i class="fa-regular fa-folder" style='color:#93419F;'></i> Balansgebied</li>

        </ul>
     </div>
    </div>
    '''.format(colormap=colormap._repr_html_(), industryIcon=industryIcon)

    
    
    # Add the custom legend to the map
    m.get_root().html.add_child(folium.Element(legend_html))

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
        pass
    else:
        # Extract the available percentage columns (non-NaN values)
        well_row = well_row.iloc[0]  # Select the first row as Series
        perc_columns = well_row.dropna().index[1:]  # Exclude the 'Name' column
        perc_values = [float(col) for col in perc_columns]
        extents = well_row[perc_columns].values
        
        if len(perc_values) < 2:
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
    base_title = "Status - 2022"

    # Convert tuple to a list for modification
    text = list(text)
    # Update for main population scenarios
    if Scenario_Button.value == "Bevolking 2035":
        if "Versnelde Groei" in text:
            text.remove("Versnelde Groei")
        if base_title in text:
            text.remove(base_title)
        if new_title not in text:
            text.append(new_title)
    elif Scenario_Button.value == "Bevolking 2035 +1% toename":
        if "Autonome Groei" in text:
            text.remove("Autonome Groei")
        if base_title in text:
            text.remove(base_title)
        if new_title not in text:
            text.append(new_title)
    elif Scenario_Button.value == "Bevolking - 2022":
        if "Versnelde Groei" in text:
            text.remove("Versnelde Groei")
        if "Autonome Groei" in text:
            text.remove("Autonome Groei")
        if Scenario_Button.value not in text:
            if new_title not in text:
                text.append(new_title)

    # Update for small business scenarios
    if ScenarioSmall_Button.value == "Kleine Bedrijven   +10% Vraag":
        if "Kleine Bedrijven Versnelde Groei" in text:
            text.remove("Kleine Bedrijven Versnelde Groei")
        if base_title in text:
            text.remove(base_title)
        if new_title not in text:
            text.append(new_title)
    elif ScenarioSmall_Button.value == "Kleine Bedrijven   +35% Vraag":
        if "Kleine Bedrijven Autonome Groei" in text:
            text.remove("Kleine Bedrijven Autonome Groei")
        if base_title in text:
            text.remove(base_title)
        if new_title not in text:
            text.append(new_title)
    elif ScenarioSmall_Button.value == "Kleine Bedrijven - 2022":
        if "Kleine Bedrijven Versnelde Groei" in text:
            text.remove("Kleine Bedrijven Versnelde Groei")
        if "Kleine Bedrijven Autonome Groei" in text:
            text.remove("Kleine Bedrijven Autonome Groei")
        if Scenario_Button.value not in text:
            if new_title not in text:
                text.append(new_title)
    
    # Convert the list back to a tuple for immutability
    text = tuple(text)
    
    # Update the app title with the updated text list
    app_title.object = " - ".join(text)
    print(text)



def update_title(event):
    global text
    text =list(text)
    if ButtonSmallWells.value:
        if "Kleine Putten Gesloten" in text:
            print("Tekst is er al")
        else: 
            text.append("Kleine Putten Gesloten")
            Measure1On()
    if ButtonSmallWells.value == False:
        Measure1Off()
        if "Kleine Putten Gesloten" in text:
            text.remove("Kleine Putten Gesloten")
        else:
            print("Tekst is er niet")
    if ButtonCloseNatura.value:
        if "Natura Putten Gesloten" in text:
            print("Tekst is er al")
        else: 
            text.append("Natura Putten Gesloten")
            Measure2On()
    if ButtonCloseNatura.value == False:   
        Measure2Off()
        if "Natura Putten Gesloten" in text:
            text.remove("Natura Putten Gesloten")
        else:
            print("Tekst is er niet")
    if ButtonSmartMeter.value:
        if "Gebruik van Slimme Meters" in text:
            print("Tekst is er al")
        else: 
            text.append("Gebruik van Slimme Meters")
            Measure3On()
    if ButtonSmartMeter.value == False:     
        Measure3Off()
        if "Gebruik van Slimme Meters" in text:
            text.remove("Gebruik van Slimme Meters") 
        else:
            print("Tekst is er niet")
    if ButtonImportWater.value:
        if "Water Importeren" in text:
            print("Tekst is er al")
        else: 
            text.append("Water Importeren")
            Measure4On()
    if ButtonImportWater.value == False:     
        Measure4Off()
        if "Water Importeren" in text:
            text.remove("Water Importeren") 
        else:
            print("Tekst is er niet")
    if ButtonAddExtraIndustrial.value:
        if "Gebruik industriële overcapaciteit" in text:
            print("Tekst is er al")
        else:
            text.append("Gebruik industriële overcapaciteit")
            Measure5On()
    if ButtonAddExtraIndustrial.value == False:
        Measure5Off()
        if "Gebruik industriële overcapaciteit" in text:
            text.remove("Gebruik industriële overcapaciteit")
        else:
            print("Tekst is er niet")
    
    text = tuple(text)
        
    app_title.object = " - ".join(text)
    print(text)
    update_indicators()

    


def ScenarioBase():
    """
    Voer het basisscenario uit met een vraag gelijk aan het jaar 2022.

    Args:
        event: Het gebeurtenisobject.
    """
    global demand_capita
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1e6
    update_scenarioTitle("Bevolking - 2022")
    print("Basisscenario hersteld")
    update_indicators()

def Scenario1():
    """
    Voer het eerste scenario uit met een toename van de vraag.

    Args:
        event: Het gebeurtenisobject.
    """
    global demand_capita 
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"] * 1.0209

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1e6
    update_scenarioTitle("Autonome Groei")
    print("Scenario 1 succesvol uitgevoerd")
    update_indicators()

def Scenario2():
    """
    Voer het tweede scenario uit met een vraagtoename van 2,09%.
    
    Args:
        event: Het gebeurtenisobject.
    """
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"] * 1.0309

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6
        
    update_scenarioTitle("Versnelde Groei")
    print("Scenario 2 succesvol uitgevoerd")
    update_indicators()

    
def ScenarioSmallBusinessBase():
    global smallBusiness
    global demand_capita 
    smallBusiness = 1.2
    update_scenarioTitle("Kleine Bedrijven Status 2022")
    update_indicators()

def ScenarioSmallBusiness1():
    global smallBusiness
    global demand_capita 
    smallBusiness = 1.2*1.1
    update_scenarioTitle("Kleine Bedrijven Autonome Groei")
    update_indicators()

def ScenarioSmallBusiness2():
    global smallBusiness
    global demand_capita 
    smallBusiness = 1.2*1.35
    update_scenarioTitle("Kleine Bedrijven Versnelde Groei")
    update_indicators()


def Measure1On():
    # Update the 'Active' column where 'Max_permit' is less than 5.00
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = False
    
    # Uncheck checkboxes corresponding to the wells that meet the condition
    for well_name in active_wells_df.loc[condition, "Name"]:
        checkboxes[well_name].value = False


def Measure1Off():
    # Update the 'Active' column where 'Max_permit' is less than 5.00
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = True
    
    # Uncheck checkboxes corresponding to the wells that meet the condition
    for well_name in active_wells_df.loc[condition, "Name"]:
        try:
            checkboxes[well_name].value = True
        except: continue


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
    demand_capita  = ButtonDemand.value/1000 * 0.95
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6

def Measure3Off():
    """
    Deactivate the third measure (using smart meters).
    """
    global demand_capita
    demand_capita  = ButtonDemand.value/1000
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6
    
from shapely.geometry import Point
import geopandas as gpd
import folium

def Measure4On():
    """
    Activate the fourth measure (importing water).
    """
    # Define the geometry point for the new well.
    new_geometry = Point(253802.6, 498734.2)  # Projected coordinates

    # Add a new row using .loc by assigning to a new index (e.g., 'Imports')
    active_wells_df.loc[active_wells_df.index.max() + 1] = {
        "Name": "Imports",
        "Num_Wells": 3,
        "Ownership": 0,
        "Max_permit": 4.5,
        "Balance area": "Imported",
        "Active": True,
        "Current Value": 4.38,
        "Value": 4.38,
        "OPEX_m3": 0.0598173515981735,
        "Drought_m3": 0,
        "CO2_m3": 0,
        "Env_m3": 0,
        "envCost": 0,
        "OPEX": 0.262,
        "geometry": new_geometry
    }

    # Select the newly added well for visualization
    new_well = active_wells_df.loc[active_wells_df["Name"] == 'Imports']

    # Convert the selected well into a GeoDataFrame and create the GeoJSON representation.
    new_well_gdf = gpd.GeoDataFrame(new_well, geometry='geometry')
    new_well_gdf = new_well_gdf.to_json()

    # Add the new well as a GeoJson object on the map
    folium.GeoJson(
        new_well_gdf,
        name="Import Water",
        zoom_on_click=True,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#f3f3f3", icon="arrow-up-from-ground-water", prefix="fa", color='cadetblue'
            )
        ),
        show=True
    ).add_to(m)

 

def Measure4Off():
    """
    Deactivate the fourth measure (importing water).
    """
    try:  
        # Use .loc to identify rows where 'Name' is 'Imports' and drop them
        active_wells_df.drop(active_wells_df.loc[active_wells_df["Name"] == 'Imports'].index, inplace=True)     
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
    global demand_capita
    global smallBusiness
    demand_capita = 0.135
    smallBusiness = 1.2
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6
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
        * 1e6,
        "OPEX": wells["totOpex_m3"] * wells["Extraction_2023__Mm3_per_jr_"] * 1e6,
        "CAPEX": 0,
        "geometry": wells["geometry"],
    }
)
    Scenario_Button.value = 'Bevolking - 2022'
    ScenarioSmall_Button.value = 'Kleine Bedrijven - 2022'
    ButtonDemand.value = 135
    ButtonSmallWells.value, ButtonCloseNatura.value, ButtonImportWater.value, ButtonSmartMeter.value, ButtonAddExtraIndustrial.value = False, False, False, False, False
    update_scenarioTitle("Status - 2022")
    update_indicators()

def update_indicators(arg=None):
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    total_capex.value = calculate_total_CAPEX()
    excess_cap.value = calculate_available()
    natureMidDamage_value.value=calculate_affected_Sensitive_Nature()
    natureHighDamage_value.value=calculate_affected_VerySensitive_Nature()
    # own_pane.value = calculate_ownership()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    # update_balance_opex()
    update_balance_lzh_gauges()
    total_demand.value = calculate_total_Demand()
    total_difference.value = total_extraction.value - total_demand.value
    lzh.value = calculate_lzh()
    Pop_pane.value = hexagons_filterd["Current Pop"].sum()
    consumption_pane.value = demand_capita*1000
    


# Initialize a dictionary to hold the active state and slider references
active_wells = {}

# Initialize a dictionary to hold the balance area layouts
balance_area_buttons = {}

# Initialize a dictionary to hold the sliders
checkboxes = {}

# Setup Well Radio Buttons
Radio_buttons = []
Well_radioB = []
options = ["-15% van Huidige", "Huidige", "85% van Max. Vergunning", "Maximale Vergunning", "115% van Max. Vergunning"]



for index, row in wells.iterrows():
    wellName = row["Name"]
    current_value = row["Extraction_2023__Mm3_per_jr_"]
    maxValue =  row["Permit__Mm3_per_jr_"]
    balance_area = row["Balansgebied"]
    radio_group = pn.widgets.RadioButtonGroup(
        name=wellName,
        options=options,
        button_type='success',
        value="Huidige",
        orientation = "vertical"
    )
    
    # Add Checkbox and listeners
    checkbox = pn.widgets.Switch(name="Active", value=True, max_width=20)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")
    radio_group.param.watch(partial(update_radio, well_name=wellName), "value")
    
    # Store the checkbox in the dictionary for later updates
    checkboxes[wellName] = checkbox
    
    NameP = pn.pane.Str(wellName + f"\nHuidige operatie op {(current_value/maxValue)*100:0.2f}%", styles={
        'font-size': "14px",
        'font-family': "Barlow",
        'font-weight': 'bold',
    })

    
    Wellvalue = update_well_Value(wellName)
    well_style=styleWellValue(Wellvalue,maxValue)
    
    extractionPerWell = pn.pane.HTML(object=update_well_Value_formatted(wellName), styles=well_style)
    NameState = pn.Row(NameP, checkbox)
    Well_radioB = pn.Column(NameState, extractionPerWell, radio_group, styles=miniBox_style)
    
    # Add the well layout to the appropriate balance area layout
    if balance_area not in balance_area_buttons:
        balance_area_buttons[balance_area] = []
    balance_area_buttons[balance_area].append(Well_radioB)
    
    # Store the active state and radio group reference along with the NamePane
    active_wells[wellName] = {"active": True, "value": current_value, "radio_group": radio_group, "name_pane": extractionPerWell}

 
all_wellsButton = pn.widgets.RadioButtonGroup(
        name="All Wells",
        options=options,
        button_type='success',
        value="Huidige",
        orientation = "vertical"
    )
all_wellsButton.param.watch(update_allRadio,"value")
    
    
# Maak HTML-tekst voor Wells-tabblad
balance_area_Text = pn.pane.HTML('''
    <h3 align= "center" style="margin: 5px;"> Balansgebieden</h3><hr>
    <p> Hoofdcontrole: Met deze optie kunt u de putten tegelijkertijd bedienen. Anders kunt u ook put voor put bedienen via het uitklapmenu.</p>
    '''
    , width=300, align="start")

# Maak een lay-out voor de radioknoppen
radioButton_layout = pn.Accordion(styles={'width': '95%', 'color':'#151931'})
for balance_area, layouts in balance_area_buttons.items():
    balance_area_column = pn.Column(*layouts)
    radioButton_layout.append((balance_area, balance_area_column))

    

    
Scenario_Button = pn.widgets.RadioButtonGroup(name="Maatregelenknop Groep", options=['Bevolking - 2022', 'Bevolking 2035', 'Bevolking 2035 +1% toename'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }, orientation='vertical'
                                             )
Scenario_Button.param.watch(update_scenarios, "value")

ScenarioSmall_Button = pn.widgets.RadioButtonGroup(name="Maatregelenknop Groep", options=['Kleine Bedrijven - 2022', 'Kleine Bedrijven   +10% Vraag', 'Kleine Bedrijven   +35% Vraag'], button_type='warning', styles={
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
    name='Sluit Kleine Putten', button_type="primary", button_style="outline", width=300, margin=10, 
)
ButtonSmallWells.param.watch(update_title, 'value')

ButtonCloseNatura = pn.widgets.Toggle(
    name='Sluit Natura 2000 Putten', button_type="primary", button_style="outline", width=300, margin=10, 
)
ButtonCloseNatura.param.watch(update_title, 'value')

ButtonDemand = pn.widgets.RadioButtonGroup(name='Waterbehoefte per Hoofd van de Bevolking', options=[135,120,100,90], button_type='warning',
                                            width=80, orientation='horizontal', styles={
    'width': '97%', 'flex-wrap': 'no-wrap' }, align=("center", "center"))
ButtonDemand.param.watch(current_demand, 'value')

# Button5= pn.Row(ButtonDemand, align=("center", "center"))

ButtonImportWater = pn.widgets.Toggle(
    name='Importeer Water', button_type="primary", button_style="outline", width=300, margin=10)
ButtonImportWater.param.watch(update_title, 'value')

ButtonAddExtraIndustrial = pn.widgets.Toggle(name="Voeg Industrieel Water Toe",  button_type="primary", button_style="outline", width=300, margin=10,)
ButtonAddExtraIndustrial.param.watch(update_title, 'value')

ButtonSmartMeter = pn.widgets.Toggle(name="Gebruik Slimme Meters", button_type='primary', button_style='outline', width=300, margin=10)
ButtonSmartMeter.param.watch(update_title, 'value')

ButtonReset = pn.widgets.Button(
    name='Reset', button_type='danger', width=300, margin=10
)
ButtonReset.on_click(Reset)


# textYears = pn.pane.HTML(
#     '''
#     <h3 align= "center" style="margin: 5px;"> Year Selection</h3><hr>
#   ''', width=300, align="start", styles={"margin": "5px"}
# )

textDivider3 = pn.pane.HTML('''<hr class="dashed"> <h3 align= "center" style="margin: 5px;">Scenario's Kleine Bedrijven  <svg xmlns="http://www.w3.org/2000/svg" height="15px" width="15px" viewBox="0 0 512 512" style="cursor:pointer; color: lightgray;"
     ><g><title>"Small Business include bakeries, hair saloons, retail stores, shopping malls, etc."</title><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm169.8-90.7c7.9-22.3 29.1-37.3 52.8-37.3l58.3 0c34.9 0 63.1 28.3 63.1 63.1c0 22.6-12.1 43.5-31.7 54.8L280 264.4c-.2 13-10.9 23.6-24 23.6c-13.3 0-24-10.7-24-24l0-13.5c0-8.6 4.6-16.5 12.1-20.8l44.3-25.4c4.7-2.7 7.6-7.7 7.6-13.1c0-8.4-6.8-15.1-15.1-15.1l-58.3 0c-3.4 0-6.4 2.1-7.5 5.3l-.4 1.2c-4.4 12.5-18.2 19-30.6 14.6s-19-18.2-14.6-30.6l.4-1.2zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z"/><g></svg> </h3> <hr>''')

textScenarioPop = pn.pane.HTML(
    '''
    <h3 align= "center" style="margin: 5px;">Scenario's Bevolking</h3><hr>'''
    , width=300, align="start"
)

textB2 = pn.pane.HTML(
    '''<b>Scenario met een vraagtoename van 35% &#8628;</b>''', width=300, align="start"
)

textMeasureSupp = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Aanvoermaatregelen </h3> <hr>
    <b>Sluit alle putlocaties met een productie van minder dan 5 Mm\u00b3/jr &#8628;</b>''', width=300, align="start", styles={}
)

textCloseNatura = pn.pane.HTML(
    '''
    <b>Sluit alle putlocaties binnen 100m van een Natura 2000-gebied &#8628;</b>''', width=300, align="start", styles={}
)

textMeasureDemand = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Vraagmaatregelen </h3> <hr>
    <b>Waterverbruik per hoofd van de bevolking in L/d</b>''', width=300, align="start", styles={}
)

textImport = pn.pane.HTML(
    '''
    <b>Water importeren uit WAZ Getelo, NVB Nordhorn en Haaksbergen. Import van 4,5 Mm\u00b3/jr &#8628;</b>''', width=300, align="start", styles={}
)

textSmartM = pn.pane.HTML('''
    <b>Gebruik van slimme meters thuis, vermindering van 5% van het verbruik &#8628;</b>''', width=300, align="start", styles={}
)

textIndustrial = pn.pane.HTML(
    '''<b>Voeg ongebruikt water uit industriële vergunningen toe. Voeg 1,66 Mm³/jr toe &#8628;</b>
''', width=300, align="start"
)

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

disclaimer = pn.pane.HTML('''<div style="font-family: Barlow, Arial, sans-serif; padding: 20px; color: #333; font-size: 14px;">
  <div>
    <h1 style="color: #3850A0;">Welkom bij de Vitalens App</h1>
    <p>
      Deze app helpt je om waterputten in de regio Overijssel Zuid te beheren en te analyseren. Het stelt gebruikers in staat om de capaciteit van de putten, kosten, milieu-impact en andere belangrijke factoren voor de planning van watervoorzieningen bij te houden.
    </p>

    <h2>Belangrijkste functies</h2>
    <ul>
      <li><strong>Live Datavisualisatie:</strong> Bekijk en werk samen met putlocaties, extractieniveaus en milieugrenzen.</li>
      <li><strong>Scenarioanalyse:</strong> Simuleer verschillende vraagscenario's voor water, zoals bevolkingsgroei of de behoeften van kleine bedrijven, om te zien hoe deze de watervoorziening en kosten kunnen beïnvloeden.</li>
      <li><strong>Milieukostenramingen:</strong> Bereken milieukosten zoals CO2-uitstoot en de effecten van droogte voor elke put, en bekijk de beperkingen voor beschermde gebieden zoals Natura2000.</li>
      <li><strong>Aangepast putbeheer:</strong> Verander de extractieniveaus en status (actief of inactief) van putten om watergebruik en efficiëntie te optimaliseren.</li>
      <li><strong>Interactieve data-exploratie:</strong> Verken gedetailleerde informatie over putten, waaronder leveringszekerheid, operationele kosten, milieu-impact en prestaties per gebied.</li>
    </ul>

    <h2>Disclaimer</h2>
    <p>
      Deze app biedt nuttige inzichten en visualisaties voor het beheer van water, maar is gebaseerd op schattingen en aannames. De daadwerkelijke prestaties van putten, milieu-impact en kosten kunnen variëren door factoren in de echte wereld, zoals veranderende omstandigheden of nieuwe regelgeving.
    </p>
    <p>
      <strong>Let op:</strong> De resultaten van de app zijn alleen bedoeld als richtlijn en zijn mogelijk niet exact. Voor kritieke beslissingen, raadpleeg lokale experts en gebruik geverifieerde gegevens.
    </p>

    <p style="color: #666; font-size: 14px;">
      © 2024 Vitalens App. Vitens en Universiteit Twente. Alle rechten voorbehouden.
    </p>
  </div>
</div>


                         
                         ''', width=700, max_height=800)

flaotingDisclaimer = pn.layout.FloatPanel(disclaimer, name= "Welcome", margin=20, contained=False, position="center") 



scenario_layout = pn.Column(textScenarioPop, Scenario_Button, textDivider3, ScenarioSmall_Button, textEnd, ButtonReset, width=320)

Supply_measures_layout = pn.Column(textMeasureSupp, ButtonSmallWells,textCloseNatura, ButtonCloseNatura, textImport, ButtonImportWater,  textIndustrial, ButtonAddExtraIndustrial, textEnd, ButtonReset, width=320)

Demand_measures_layout = pn.Column(textMeasureDemand, ButtonDemand, textDivider0, textSmartM, ButtonSmartMeter, textEnd, ButtonReset, width = 320)

firstColumn = pn.Column(balance_area_Text,all_wellsButton, radioButton_layout)
secondColumn = pn.Column(file_create, spinner, file_download)




tabTop = pn.Tabs(("1. Scenario's", scenario_layout), ("2. Aanbod", Supply_measures_layout), ("3. Vraag", Demand_measures_layout), width = 320)
tabBottom = pn.Tabs(("4. Putcapaciteiten", firstColumn), ("5. Rapport genereren", secondColumn), width = 320)

tabs = pn.Column(tabTop, tabBottom, sizing_mode="scale_height")

# MAIN WINDOW

# map_pane = pn.pane.HTML(create_map(52.38, 6.7, 10), sizing_mode="stretch_both")
map_pane = pn.pane.plot.Folium(update_layers(), sizing_mode="stretch_both")

minusSVG= pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M6 12L18 12" stroke="#4139a7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')

equalSVG = pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M3 8C2.44772 8 2 8.44772 2 9C2 9.55228 2.44772 10 3 10H21C21.5523 10 22 9.55228 22 9C22 8.44772 21.5523 8 21 8H3Z" fill="#4139a7"></path> <path d="M3 14C2.44772 14 2 14.4477 2 15C2 15.5523 2.44772 16 3 16H21C21.5523 16 22 15.5523 22 15C22 14.4477 21.5523 14 21 14H3Z" fill="#4139a7"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')

total_extraction = pn.indicators.Number(
    name="Totale Levering",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    sizing_mode="scale_width",
    align='center',
    colors=[(wells["Extraction_2023__Mm3_per_jr_"].sum() - 0.1, '#D9534F'), (wells["Extraction_2023__Mm3_per_jr_"].sum(), '#3850a0'), (1000, '#92C25B')]
)

total_demand = pn.indicators.Number(
    name="Totale Watervraag",
    value=calculate_total_Demand,
    format="{value:0,.2f} Mm\u00b3/jr",
    font_size="20pt",
    title_size="12pt",
    default_color='#3850a0',
    sizing_mode="scale_width", align='center',
    colors=[(original_demand - 0.1, '#92C25B'), (original_demand, '#3850a0'), (1000, '#D9534F')]
)

total_difference = pn.indicators.Number(
    name="Waterbalans",
    value=calculate_difference(),
    format="{value:.2f} Mm\u00b3/jr",
    colors=[(0, '#d9534f'), (10, '#f2bf58'), (100, '#92c25b')],
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    sizing_mode="scale_width", align='center'
)

total_extraction_TT = pn.widgets.TooltipIcon(value="De totale levering wordt berekend als de som van de volumes grondwater die per locatie in een jaar worden onttrokken. De totale vraag wordt berekend als het jaarlijkse verbruik van drinkwater door inwoners en kleine bedrijven.")

total_opex = pn.indicators.Number(
    name="Totale OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width",
    colors=[(original_OPEX - 0.1, '#92C25B'), (original_OPEX, '#3850a0'), (1000, '#D9534F')]
)

total_opex_TT = pn.widgets.TooltipIcon(value="Totale jaarlijkse operationele uitgaven (OPEX).")

total_capex = pn.indicators.Number(
    name="Totale CAPEX",
    value=calculate_total_CAPEX(),
    format="{value:0,.2f} M\u20AC",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width",
    colors=[(0, '#3850a0'), (1000, '#D9534F')]
)


total_capex_TT = pn.widgets.TooltipIcon(value="Totale investeringsuitgaven (CAPEX) voor het uitbreiden van de onttrekkingscapaciteit.")


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
    name="Overcapaciteit",
    value=calculate_available(),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_excess-0.1, '#D9534F'), (original_excess, '#3850a0'),(1000, '#92C25B')]

)

excess_cap_TT = pn.widgets.TooltipIcon(value="Jaarlijks beschikbaar water dat niet uit de putten wordt gewonnen en binnen de maximaal toegestane onttrekking valt.")
excess_cap_row = pn.Row(excess_cap, excess_cap_TT)

industrial_extract = pn.indicators.Number(
    name="Industriële Wateronttrekking",
    value=calculate_industrial_extract(),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)
industrial_extract_TT = pn.widgets.TooltipIcon(value="Geschatte jaarlijkse grondwateronttrekking door grote industrieën waar Vitens geen controle over heeft.")


industrial_extract_row = pn.Row(industrial_extract, industrial_extract_TT)


right_pane = pn.Column(excess_cap_row,industrial_extract_row)

# own_pane = pn.indicators.Number(
#     name="Landownership",
#     value=calculate_ownership(),
#     format="{value:0.2f} %",
#     default_color='#3850a0',
#     font_size="20pt",
#     title_size="12pt",
#     align="center",
#     colors=[(75, "#F19292"), (85, "#F6D186"), (100, "#CBE2B0")],
#     sizing_mode="stretch_width"
# )

natureMidDamage_value = pn.indicators.Number(
    name="Geschatte <b>Gevoelige</b> Natuur getroffen gebied",
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
    name="Geschatte <b>Zeer Gevoelige</b> Natuur getroffen gebied",
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

natureDamage_TT = pn.widgets.TooltipIcon(value='Dit gebied komt overeen met de omvang van droogtegevoelige, grondwaterafhankelijke natuur die mogelijk wordt beïnvloed door grondwaterwinning.')


# nature_title = pn.Row(natureMidDamage_value,natureDamage_TT, sizing_mode="scale_both" )

# Use pn.bind to dynamically bind the number of stars to the pane
keukenhofsMid = pn.bind(generate_area_SVG, natureMidDamage_value)
keukenhofsHigh = pn.bind(generate_area_SVG, natureHighDamage_value)
keuk_text = pn.pane.HTML("<p style='font-size: small;'>Weergegeven in aantal stadscentra van Enschede</p>")
natura_pane = pn.Column(natureDamage_TT, natureHighDamage_value, spacer(10), keukenhofsHigh, natureMidDamage_value, spacer(10), keukenhofsMid, keuk_text, sizing_mode='scale_both')

pipes_TT = pn.widgets.TooltipIcon(value="Elk pictogram vertegenwoordigt het aantal verbindingen tussen twee balansgebieden, dit is een indicator van kwetsbaarheid in het systeem.")

pipes_pane = pn.Row(
    pipes_TT, 
    generate_pipes_SVG("Reggeland", "Stedenband", 1), 
    generate_pipes_SVG("Reggeland", "Hof van Twente", 2), 
    generate_pipes_SVG("Reggeland", "Dinkelland", 1), 
    generate_pipes_SVG("Hof van Twente", "Stedenband", 3), 
    generate_pipes_SVG("Dinkelland", "Stedenband", 1), 
)

co2_pane = pn.indicators.Number(
    name="CO\u2082 Emissiekosten",
    value=calculate_total_CO2_cost(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_CO2 - 0.1, '#92C25B'), (original_CO2, '#3850a0'), (1000, '#D9534F')]
)

drought_pane = pn.indicators.Number(
    name="Schadekosten door Droogte",
    value=calculate_total_Drought_cost(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_Draught - 0.1, '#92C25B'), (original_Draught, '#3850a0'), (1000, '#D9534F')]
)

lzh = pn.indicators.Gauge(
    name="Algemene LZH",
    value=calculate_lzh(),
    bounds=(0, 220),
    format="{value} %",
    colors=[(0.455, "#D9534F"), (0.545, "#f2bf57"), (0.6136, "#92C25B"), (1, "#446526")],
    custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align=("center", 'center'), height=250, title_size=14
)

lzh.param.watch(update_indicators, "value")
lzh_definition = pn.pane.HTML("LZH: Het is het percentage van de vraag naar drinkwater dat door de levering wordt gedekt")
lzh_tooltip = pn.pane.HTML("LZH: Leveringszekerheid, is het percentage van de vraag naar drinkwater dat door de levering wordt gedekt. Je kunt de LZH voor elk balansgebied zien door de tabbladen aan de rechterkant te selecteren. Deze waarden gaan uit van een gesloten systeem.")


balance_lzh_gauges = {}
balance_lzh_values = calculate_lzh_by_balance()
for area, value in balance_lzh_values.items():
    gauge = pn.indicators.Gauge(
        name=f"LZH \n{area}",
        value=value,
        bounds=(0, 780),
        format="{value} %",
        colors=[(0.128, "#D9534F"), (0.154, "#f2bf57"),(0.173, "#92C25B"), (1, "#446526")],
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

indicatorsArea = pn.GridSpec(sizing_mode="scale_both")
indicatorsArea = pn.Tabs(lzh, *balance_lzh_gauges.values(), ("Help",lzh_tooltip), align=("center", "center"), sizing_mode="scale_height", tabs_location="right")


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

app_title = pn.pane.Markdown("## Scenario: State - 2022", styles={
    "text-align": "right",
    "color": "#2f4279"
})

Pop_pane = pn.indicators.Number(
    name="Bevolking",
    value=0,
    format="{value:0,.0f} inwoners",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)

consumption_pane = pn.indicators.Number(
    name="Verbruik",
    value=demand_capita*1000,
    format="{value:0,.0f} L/inwoner",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(135 - 0.1, '#92C25B'), (135, '#3850a0'), (1000, '#D9534F')]
)

MapTitle = pn.pane.HTML('''<b style="font-size: large; float: right; color: #2f4279;">Overijssel Zuid</b>''')
Map_help = pn.widgets.TooltipIcon(value="De gegevens die op deze kaart worden weergegeven zijn statisch. Dit betekent dat ze niet veranderen wanneer de widgets aan de linkerkant van de app worden aangepast. Ze vertegenwoordigen bevolkingsgegevens van december 2022 en de waterwinning van 2023.\n\nDe Balansgebieden vertegenwoordigen gebieden binnen het Overijssel Zuid Cluster die direct worden gevoed door ten minste een productielocatie en zijn gekoppeld aan een ander balansgebied voor dynamische waterverdeling.", width=10, align='end')


MapTitle_TT = pn.Row( Map_help,MapTitle, align="end", sizing_mode="scale_width")

main1 = pn.GridSpec(sizing_mode="scale_both")
main1[0, 2:5] = pn.Column(MapTitle_TT, map_pane, pipes_pane )

IndicatorsPane = pn.GridSpec(sizing_mode="stretch_both")
IndicatorsPane[0,0:3] = pn.Column(
    indicatorsArea, textDivider0, Supp_dem, textDivider1, CostPane, textDivider2, natura_pane,
    scroll=True
)
IndicatorsPane[0,3:5] = pn.Column(
    Pop_pane, consumption_pane, textDivider1, Env_pane, right_pane,
    sizing_mode="scale_width",
    scroll=True
)

main1[0, 0:2] = pn.Column(app_title, IndicatorsPane, sizing_mode="scale_both")


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
    # update_balance_lzh_gauges()
    update_indicators()
    total_demand.value = calculate_total_Demand()
    total_difference.value = calculate_difference()
    calculate_affected_Sensitive_Nature()
    map_pane
    co2_pane.value = calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    flaotingDisclaimer
    Pop_pane.value = hexagons_filterd["Current Pop"].sum()

total_extraction_update()
Box.servable()