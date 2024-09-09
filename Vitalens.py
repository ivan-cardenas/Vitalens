import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
from bokeh.models.formatters import PrintfTickFormatter
import folium
import keplergl
from shapely.geometry import shape, Polygon
from lonboard import Map, PathLayer, ScatterplotLayer
import branca
from functools import partial

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
    background-color: #c2d5f7;    
}

:host(.bk-above) .bk-header .bk-tab{
    border: #F2F2ED !important;
    background: #00000014 !important
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
  flex-wrap: wrap !important;
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
    background: #d3d3cf !imporant;
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
pn.extension("ipywidgets")
pn.extension("echarts")
pn.extension(
    "tabulator", "ace", css_files=["https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"]
)


# Load the GeoPackage file
GPKG_FILE = "./Assets/Thematic_Data.gpkg"
layers = fiona.listlayers(GPKG_FILE)  # Load all layers

# Get Wells Attributes
wells = gpd.read_file(GPKG_FILE, layer="Well_Capacity_Cost")
industrial = gpd.read_file(GPKG_FILE, layer="Industrial_Extraction")
mainPipes = gpd.read_file(GPKG_FILE, layer="Pipes_Topological")


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
demand_capita = 0.135*smallBussiness


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
        "Water Demand": hexagons["Pop_2022"] * demand_capita * 365 / 1000000,
        "Type": hexagons["Type_T"],
        "Source_Name": hexagons["Source_Name"],
        "geometry": hexagons["geometry"],
    }, copy=False
)

balance_areas= hexagons_filterd.dissolve(by="Balance Area", as_index=False)

def calculate_total_extraction():
    """
    Calculate the total water extraction from active wells.

    Returns:
        float: Total water extraction in Mm3/yr.
    """
    total = active_wells_df[active_wells_df["Active"]]["Value"].sum()
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

def calculate_affected_Natura():
    """
    Calculate the total affected area by Natura2000 restrictions.

    Returns:
        float: Total affected area in hectares.
    """
    names = active_wells_df[active_wells_df["Active"]]["Name"]
    restricted = hexagons_filterd[
        (hexagons_filterd["Source_Name"].isin(names))
        & (hexagons_filterd["Type"] == "Source and Restricted")
    ]
    total = restricted.shape[0]
    ha = total * 629387.503078 / 100000
    print ("Affected", ha)
    return ha

def generate_area_SVG (n):
    SVG = '<svg width="64px" height="64px" viewBox="0 -199.5 1423 1423" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M105.124 107.703h1142.109v796.875h-1142.109v-796.875z" fill="#C0D36F"></path><path d="M1069.108 336.219h157.266v353.672h-157.266zM128.562 336.219h157.266v353.672h-157.266z" fill="#FFFFFF"></path><path d="M1120.438 90.125h-887.813c-78.646 0.133-142.367 63.853-142.5 142.488v558.528c0.133 78.647 63.853 142.367 142.488 142.5h887.826c78.646-0.133 142.367-63.853 142.5-142.488v-558.293c0 0 0 0 0 0 0-78.747-63.771-142.601-142.488-142.733zM651.688 626.844c-53.93-11.239-93.867-58.377-93.867-114.844s39.938-103.605 93.106-114.711l0.761 229.554zM698.563 397.156c53.93 11.239 93.867 58.377 93.867 114.844s-39.938 103.605-93.106 114.711l-0.761-229.554zM136.062 347.937h101.25c0 0 0 0 0 0 23.429 0 42.421 18.992 42.421 42.421v243.516c0 0 0 0 0 0 0 23.429-18.992 42.421-42.421 42.421 0 0 0 0 0 0h-101.25v-328.125zM136.062 791.375v-68.438h101.25c49.317 0 89.297-39.98 89.297-89.297v-242.578c0-49.317-39.98-89.297-89.297-89.297 0 0 0 0 0 0h-101.25v-68.438c0.133-52.759 42.867-95.492 95.613-95.625h420.011v212.813c-79.347 12.438-139.329 80.308-139.329 162.188 0 81.879 59.982 149.75 138.403 162.068l0.927 212.932h-419.063c-0.209 0.002-0.457 0.003-0.705 0.003-52.942 0-95.859-42.918-95.859-95.859 0-0.165 0.001-0.331 0.002-0.497zM1120.438 887h-421.875v-212.813c79.347-12.438 139.329-80.308 139.329-162.188 0-81.879-59.982-149.75-138.403-162.068l-0.927-212.932h421.875c52.759 0.133 95.492 42.866 95.625 95.613v68.45h-95.625c0 0 0 0 0 0-49.317 0-89.297 39.98-89.297 89.297v243.516c0 49.317 39.979 89.297 89.297 89.297 0 0 0 0 0 0h93.75v68.438c-0.249 52.012-41.883 94.217-93.648 95.39zM1216.063 347.937v328.125h-95.625c0 0 0 0 0 0-23.429 0-42.421-18.992-42.421-42.421 0 0 0 0 0 0v-242.578c0 0 0 0 0 0 0-23.429 18.992-42.421 42.421-42.421 0 0 0 0 0 0h93.75z" fill="#25274B"></path></g></svg>'
    fig = pn.pane.HTML(SVG*(int(n/0.5)))
    
    return fig

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
        event.new * opex_m3 * 1000000
    )
    env_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "Env_m3"]
    active_wells_df.loc[active_wells_df["Name"] == well_name, "envCost"] = (
        event.new * env_m3 * 1000000
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
    
    if event.new == "-10%":
        new_value = current_value * 0.9
    elif event.new == "-20%":
        new_value = current_value * 0.8
    elif event.new == "Current":
        new_value = current_value
    elif event.new == "+10%":
        new_value = current_value * 1.1
    elif event.new == "+20%":
        new_value = current_value * 1.2
    elif event.new == "Maximum Permit":
        new_value = max_value
   
    
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = new_value
    print('error here')
    opex_m3 = active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX_m3"]
    print('no ut us here')
    active_wells_df.loc[active_wells_df["Name"] == well_name, "OPEX"] = new_value * opex_m3
    
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Name(well_name)
    update_indicators()
    
def update_scenarios(event):
    if event.new == "Autonomous Growth    +10% Demand":
        Scenario1()
        print('scenario 1 active')
    if event.new == "Accelerated Growth    +35% Demand":
        print('scenario 2 active')
        Scenario2()
    if event.new == 'Current state - 2024':
        demand_capita = 0.156
        hexagons_filterd["Water Demand"] = (
         hexagons_filterd["Pop2022"] * demand_capita * 365
        ) / 1000000
        update_scenarioTitle("VITALENS - Current Situation 2024")
    update_indicators()
    

def update_well_Name(well_name):
    """
    Update the well name display.

    Args:
        well_name (str): The name of the well.

    Returns:
        str: Updated well name display.
    """
    current_extraction = active_wells_df[active_wells_df["Name"]==well_name]["Value"].values[0]
    return f"{current_extraction:.2f} Mm\u00b3/yr"


def current_demand(event):
    global demand_capita
    if event.new == 90:
        demand_capita = 0.09*smallBussiness
    if event.new == 100:
        demand_capita = 0.1*smallBussiness
    if event.new == 120:
        demand_capita = 0.12*smallBussiness
    if event.new == 135:
        demand_capita = 0.135*smallBussiness
    update_indicators()
    

def calculate_total_Demand():
    """
    Calculate the total water demand.

    Returns:
        float: Total water demand in Mm3/yr.
    """
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365 
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

# Create map and add attributes
m = folium.Map(
    location=[52.38, 6.7], zoom_start=10,
    tiles="Cartodb Positron"
)

def normalize_height(value, min_value, max_value, target_min, target_max):
    """
    Normalize or scale a property for height visualization.

    Args:
        value (float): The value to normalize.
        min_value (float): Minimum value of the property.
        max_value (float): Maximum value of the property.
        target_min (float): Target minimum height.
        target_max (float): Target maximum height.

    Returns:
        float: Normalized height.
    """
    if value == None:
        return 0
    else: 
        return target_min + (value - min_value) / (max_value - min_value) * (target_max - target_min)

# Format data for use in pydeck
hexagons_4326 = hexagons_filterd.to_crs(epsg=4326)
wells_4326 = active_wells_df.to_crs(epsg=4326)

# Example property scaling
min_height = 100
max_height = 2000
min_property = hexagons_4326['Water Demand'].min()
max_property = hexagons_4326['Water Demand'].max()

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
    m
    
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
            "color": "#d9534f",
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
                "darkred"
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
                "#f9aaa2"
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

def create_map(wellsLayer=active_wells_df,industryLayer=industrial):
    w1 = keplergl.KeplerGl(height=500)
    w1.add_data(data=wellsLayer, name='Wells')
    w1.add_data(data=industryLayer, name='Industrial Wells')
    return w1

active_scenarios = set()
text = ["## Scenario"]


def update_scenarioTitle(new_title):
    global text
    base_title = "VITALENS - Current Situation 2024"
    if Scenario_Button.value == "Autonomous Growth    +10% Demand":
        if ("Accelerated Growth" or base_title) in text:
            text.remove("Accelerated Growth")
        text.append(new_title)
    if Scenario_Button.value == "Accelerated Growth    +35% Demand":
        if ("Autonomous Growth" or base_title) in text:
            text.remove("Autonomous Growth")
        text.append(new_title)
    if Scenario_Button.value == "VITALENS - Current Situation 2024":
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
    if Button3.value:
        if "Closed Small Wells" in text:
            print("Text already there")
        else: text.append("Closed Small Wells")
        Measure1On()
    if Button3.value == False:
        Measure1Off()
        if "Closed Small Wells" in text:
            text.remove("Closed Small Wells")
        else:
            print("Text not there")
    if Button4.value:
        if "Closed Natura Wells" in text:
             print("Text already there")
        else: text.append("Closed Natura Wells")
        Measure2On()
    if Button4.value == False:   
        Measure2Off()
        if "Closed Natura Wells" in text:
            text.remove("Closed Natura Wells")
        else: print("Text not there")
    if Button6.value:
        text.append("Import Water")
        Measure4On()
    if Button6.value == False:     
        Measure4Off()
        if "Import Water" in text:
            text.remove("Import Water") 
        else: print("Text not there")
    
    app_title.object = " - ".join(text)
    print(text)
    update_indicators()
    

def Scenario1():
    """
    Implement the first scenario with a demand increase of 10%.

    Args:
        event: The event object.
    """
    global demand_capita
    hexagons_filterd["Current Pop"]= hexagons_filterd["Pop2022"]*1.1
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365 
    ) / 1000000
    update_scenarioTitle("Autonomous Growth")
    print("Scenario 1 ran perfectly")
    update_indicators()

def Scenario2():
    """
    Implement the second scenario with a demand increase of 35%.
    
    
    Args:
        event: The event object.
    """
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]*1.35
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
        
    update_scenarioTitle("Accelerated Growth")
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
    demand_capita = 0.156 * 0.9
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000

def Measure3Off():
    """
    Deactivate the third measure (using smart meters).
    """
    demand_capita = 0.156
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    
def Measure4On():
    """
    Activate the fourth measure (importing water).
    """
    active_wells_df.loc[active_wells_df.shape[0]] = ["Imports", 3,0, 4.5, "Imported", True, 4.38, 4.38, 0,0,0,0,0,0,0, "POINT (253802.6,498734.2)"]

def Measure4Off():
    """
    Deactivate the fourth measure (importing water).
    """
    try:  
        # Use .loc to identify rows where 'Name' is 'Imports' and drop them
        active_wells_df.drop(active_wells_df.loc[active_wells_df["Name"] == 'Imports'].index, inplace=True)
    except KeyError:
        print("Row does not exist")

    
def Reset(event):
    """
    Reset the application to its initial state.

    Args:
        event: The event object.
    """
    demand_capita = 0.135*smallBussiness
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
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
        "Value": wells["Extraction_2023__Mm3_per_jr_"],
        "OPEX_m3": wells["totOpex_m3"],
        "Drought_m3": wells["DroughtDamage_EUR_m3"],
        "CO2_m3": wells["CO2Cost_EUR_m3"],
        "Env_m3": wells["env_cost_m3"],
        "envCost": wells["env_cost_m3"]
        * wells["Extraction_2023__Mm3_per_jr_"]
        * 1000000,
        "OPEX": wells["totOpex_m3"] * wells["Extraction_2023__Mm3_per_jr_"] * 1000000,
        "geometry": wells["geometry"],
    }
)
    Scenario_Button.value = 'Current state - 2024'
    ButtonDemand.value = 135
    Button3.value, Button4.value,  = False, False
    update_scenarioTitle("VITALENS - Current Situation")
    update_indicators()

def update_indicators(arg=None):
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    total_capex.value = calculate_total_CAPEX()
    excess_cap.value = calculate_available()
    natura_value.value=calculate_affected_Natura()
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

# Setup Well Radio Buttons
Radio_buttons = []
Well_radioB = []
options = ["-10%", "-20%", "Current", "+10%", "+20%", "Maximum Permit"]

for index, row in wells.iterrows():
    wellName = row["Name"]
    current_value = row["Extraction_2023__Mm3_per_jr_"]
    balance_area = row["Balansgebied"]
    radio_group = pn.widgets.RadioButtonGroup(
        name=wellName,
        options=options,
        button_type='success',
        value="Current"
    )
    
    # Add Checkbox and listeners
    checkbox = pn.widgets.Switch(name="Active", value=True)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")
    radio_group.param.watch(partial(update_radio, well_name=wellName), "value")
    
    # Store the checkbox in the dictionary for later updates
    checkboxes[wellName] = checkbox
    
    NameP = pn.pane.Str(wellName, styles={
        'font-size': "14px",
        'font-family': "Barlow",
        'font-weight': 'bold',
    })
    
    NamePane = pn.pane.Str(update_well_Name(wellName), styles={
        'font-family': 'Roboto'
    })
    NameState = pn.Row(NameP, checkbox)
    Well_radioB = pn.Column(NameState, NamePane, radio_group, styles=miniBox_style)
    
    # Add the well layout to the appropriate balance area layout
    if balance_area not in balance_area_buttons:
        balance_area_buttons[balance_area] = []
    balance_area_buttons[balance_area].append(Well_radioB)
    
    # Store the active state and radio group reference along with the NamePane
    active_wells[wellName] = {"active": True, "value": current_value, "radio_group": radio_group, "name_pane": NamePane}

 
    
    
    
# Create HTML Text for Wells Tab
balance_area_Text = pn.pane.HTML('''
    <h3 align= "center" style="margin: 5px;"> Balance Areas</h3><hr>'''
    , width=300, align="start")

# Create a layout for the radio buttons
radioButton_layout = pn.Accordion(styles={'width': '97%', 'color':'#151931'})
for balance_area, layouts in balance_area_buttons.items():
    balance_area_column = pn.Column(*layouts)
    radioButton_layout.append((balance_area, balance_area_column))
    
firstColumn = pn.Column(balance_area_Text,radioButton_layout)
    
Scenario_Button =pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['Current state - 2024','Autonomous Growth    +10% Demand','Accelerated Growth    +35% Demand'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }
                                             )
Scenario_Button.param.watch(update_scenarios, "value")

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

Button3 = pn.widgets.Toggle(
    name='Close Small Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button3.param.watch(update_title, 'value')

Button4 = pn.widgets.Toggle(
    name='Close Natura 2000 Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button4.param.watch(update_title, 'value')

ButtonDemand = pn.widgets.RadioButtonGroup(name='Water Demand per Capita', options=[135,120,100,90], button_type='warning',
                                            width=80, orientation='horizontal', styles={
    'width': '97%', 'flex-wrap': 'no-wrap' })
ButtonDemand.param.watch(current_demand, 'value')

Button5= pn.Row(ButtonDemand)

Button6 = pn.widgets.Toggle(
    name='Import Water', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button6.param.watch(update_title, 'value')

ButtonR = pn.widgets.Button(
    name='Reset', button_type='danger', width=300, margin=10
)
ButtonR.on_click(Reset)

textYears = pn.pane.HTML(
    '''
    <h3 align= "center" style="margin: 5px;"> Year Selection</h3><hr>
  ''', width=300, align="start", styles={"margin": "5px"}
)

textB1 = pn.pane.HTML(
    '''
    <h3 align= "center" style="margin: 5px;"> Scenarios</h3><hr>'''
    # <b>Scenario with demand increase of 10% &#8628;</b>'''
    , width=300, align="start"
)
textB2 = pn.pane.HTML(
    '''<b>Scenario with demand increase of 35% &#8628;</b>''', width=300, align="start"
)
textB3 = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Measures </h3> <hr>
    <b>Close down all well locations with production less than 5Mm\u00b3/yr &#8628;</b>''', width=300, align="start", styles={}
)
textB4 = pn.pane.HTML(
    '''
    <b>Close down all well locations in less than 100m from a Natura 2000 Area &#8628;</b>''', width=300, align="start", styles={}
)

textB5 = pn.pane.HTML(
    '''
    <b>Water Conusmption per Capita in L/d;</b>''', width=300, align="start", styles={}
)

textB6 = pn.pane.HTML(
    '''
    <b>Importing water from WAZ Getelo, NVB Nordhorn and Haaksbergen</b>''', width=300, align="start", styles={}
)

textEnd = pn.pane.HTML(
    '''<hr class="dashed">
    ''', width=300, align="start", styles={}
)

textDivider0 = pn.pane.HTML('''<hr class="dashed">''')
textDivider1 = pn.pane.HTML('''<hr class="dashed">''')
textDivider2 = pn.pane.HTML('''<hr class="dashed">''')

scenario_layout = pn.Column(textB1, Scenario_Button, textEnd, ButtonR)

measures_layout = pn.Column(textB3, Button3,textB4, Button4, textB5, Button5, textB6, Button6, textEnd, ButtonR )

tabs = pn.Tabs(("1. Scenarios", scenario_layout), ("2. Measures", measures_layout),("3. Well Capacities", radioButton_layout))




# MAIN WINDOW

map_pane = pn.pane.plot.Folium(update_layers(), sizing_mode="stretch_both")


minusSVG= pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M6 12L18 12" stroke="#4139a7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')

equalSVG = pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M3 8C2.44772 8 2 8.44772 2 9C2 9.55228 2.44772 10 3 10H21C21.5523 10 22 9.55228 22 9C22 8.44772 21.5523 8 21 8H3Z" fill="#4139a7"></path> <path d="M3 14C2.44772 14 2 14.4477 2 15C2 15.5523 2.44772 16 3 16H21C21.5523 16 22 15.5523 22 15C22 14.4477 21.5523 14 21 14H3Z" fill="#4139a7"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')

total_extraction = pn.indicators.Number(
    name="Total Supply",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
    sizing_mode="stretch_width",
    align='center'
)

total_demand = pn.indicators.Number(
    name="Total Water Demand",
    value=calculate_total_Demand,
    format="{value:0,.2f} Mm\u00b3/yr",
    font_size="24pt",
    title_size="16pt",
    default_color='#3850a0',
    sizing_mode="stretch_width", align='center'
)

total_difference = pn.indicators.Number(
    name="Water Balance",
    value=calculate_difference(),
    format="{value:.2f} Mm\u00b3/yr",
    colors=[(0, '#d9534f'), (10, '#f2bf58'), (100, '#92c25b')],
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
    sizing_mode="stretch_width", align='center'
)

total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
    align="center",
    sizing_mode="stretch_width"
)

total_capex = pn.indicators.Number(
    name="Total CAPEX",
    value=calculate_total_CAPEX(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
    align="center",
    sizing_mode="stretch_width"
)

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
    align="center",
    sizing_mode="stretch_width"
)

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

natura_value = pn.indicators.Number(
    name="Approximate Natura 2000 \n Affected area",
    value=calculate_affected_Natura(),
    format="{value:0.2f} Ha",
    default_color='#3850a0',
    font_size="14pt",
    title_size="10pt",
    align="center",
    sizing_mode="stretch_width",
    styles = {
        'font-family': "Roboto"
    }
)

# Use pn.bind to dynamically bind the number of stars to the pane
football_svg_pane = pn.bind(generate_area_SVG, natura_value)
natura_pane = pn.Column(natura_value, football_svg_pane)

co2_pane = pn.indicators.Number(
    name="CO\u2028 Emmission Cost",
    value=calculate_total_CO2_cost(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
)

drought_pane = pn.indicators.Number(
    name="Drought Damage Cost",
    value=calculate_total_Drought_cost(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="24pt",
    title_size="16pt",
)

# df_display = pn.pane.Markdown(update_df_display())
#df_Hexagons = pn.pane.DataFrame(hexagons_filterd.head(), name="Hexagons data")



lzh = pn.indicators.Gauge(
    name=f"Overall \n LZH",
    value=calculate_lzh(),
    bounds=(0, 150),
    format="{value} %",
    colors=[(0.66, "#D9534F"), (0.8, "#f2bf57"),(0.9, "#92C25B"), (1, "#8DCEC0")],
    custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align=("center",'center')
)
lzh.param.watch(update_indicators, "value")

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
    align=("center",'center'),
    )
    balance_lzh_gauges[area] = gauge


# lzhTabs = pn.Tabs(lzh, *balance_lzh_gauges.values(), align=("center", "center"))
Env_pane = pn.Column(co2_pane, drought_pane, sizing_mode="scale_width")

indicatorsArea = pn.GridSpec(sizing_mode="stretch_both")

indicatorsArea[0,0:2] = pn.Tabs(lzh, *balance_lzh_gauges.values(), align=("center", "center"), sizing_mode="scale_width")
indicatorsArea[0,3] = Env_pane


CostPane = pn.Row(
    total_opex, total_capex, align=("center", "center")
)

Supp_dem = pn.Row(
    total_extraction, minusSVG, total_demand, equalSVG, total_difference, sizing_mode="stretch_width"
)



app_title = pn.pane.Markdown("## Scenario: Current State - 2024", styles={
    "text-align": "right",
    "color": "#00B893"
})

main1 = pn.GridSpec(sizing_mode="stretch_both")
main1[0, 0] = pn.Row(map_pane)

main2 = pn.GridSpec(sizing_mode="stretch_both")
main2[0,0:2] = pn.Row(
    natura_pane,
    sizing_mode="scale_width",
    scroll=True
)
main2[0,2] = pn.Row(
    excess_cap,
    sizing_mode="scale_width",
    scroll=True
)



main1[0, 1] = pn.Column(app_title, indicatorsArea, textDivider0, Supp_dem, textDivider1, CostPane, textDivider2, main2, sizing_mode="stretch_width")

Box = pn.template.MaterialTemplate(
    title="Vitalens",
    logo="https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png",
    sidebar=tabs,
    main=[main1],
    header_background= '#3850a0',
    header_color= '#f2f2ed',
    sidebar_width = 325
)

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
    calculate_affected_Natura()
    map_pane
    co2_pane.value = calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()


total_extraction_update()
Box.servable()