import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
from bokeh.models.formatters import PrintfTickFormatter
import folium
from shapely.geometry import shape, Polygon
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

.bk-btn-warning{
  background-position: center;
  font-weight: 400 !important;
  font-size: small !important;
  line-height: 1;
  margin: 3px 3px; 
  padding: 5px 10px !important;
  transition: background 0.8s;
  width: fit-content;
}

.accordion-header button{
    color: #151931;
    background-color: #B4BFE4;
}
'''
]

# Initialize extensions
pn.config.global_css = cssStyle
pn.config.css_files = cssStyle
pn.config.loading_spinner = 'petal'
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")
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
active_wells_df.astype({"Num_Wells": "int32", "Ownership": "int32"}, copy=False)

yearCal = 2022
growRate = 0.0062
demand_capita = 0.1560

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
        "Water Demand": hexagons["Pop_2022"] * 0.1560 * 365 / 1000000,
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

def calculate_industrial():
    total = industrial["Current_Extraction_2019"].sum()
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
    industrial_total = industrial["Licensed"].sum() - industrial["Current_Extraction_2019"].sum()
    return total + industrial_total

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
    total = (active_wells_df[active_wells_df["Active"]]["OPEX"]).sum()
    return total/1000000

def calculate_total_OPEX_by_balance():
    """
    Calculate the total OPEX grouped by balance areas.

    Returns:
        pd.Series: Total OPEX by balance area in million EUR/yr.
    """
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )/1000000

def update_balance_opex():
    """
    Update OPEX indicators for balance areas.
    """
    balance_opex = calculate_total_OPEX_by_balance()
    for balance, indicator in balance_opex_indicators.items():
        indicator.value = balance_opex.get(balance, 0)

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
    return total * 629387.503078 / 100000

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
    map_pane.object = update_layers()
    
def toggle_industrial(event, location):
    """
    Toggle the active state of a well based on a checkbox.

    Args:
        event: The event object.
        well_name (str): The name of the well.
    """
    industrial.loc[industrial["Location"] == location, "Active"] = event.new
    update_indicators()
    map_pane.object = update_layers()

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
    agreement = wells.loc[wells["Name"]== well_name, "Agreement__Mm3_per_jr_"].values[0]
    
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
    elif event.new == "Agreement":
        new_value = agreement
    
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Value"] = new_value
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Name(well_name)
    update_indicators()
    
def update_scenarios(event):
    if event.new == "Autonomous Growth":
        Scenario1()
        print('scenario 1 active')
    if event.new == "Accelerated Growth":
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

# Function to update the yearCal variable
# def update_year(event):     
#     if event.new == 2024:
#         hexagons_filterd["Current Pop"] = round(
#             hexagons_filterd["Pop2022"] * ((1 + growRate) ** float((2024 - 2022))), 0
#         )
#     if event.new == 2035:
#         hexagons_filterd["Current Pop"] = round(
#             hexagons_filterd["Pop2022"] * ((1 + growRate) ** float((2035 - 2022))), 0
#         )
#     hexagons_filterd["Water Demand"] = (
#         hexagons_filterd["Current Pop"] * 0.1560 * 365
#     ) / 1000000
#     update_indicators()  # Update the total demand indicator

def calculate_total_Demand():
    """
    Calculate the total water demand.

    Returns:
        float: Total water demand in Mm3/yr.
    """
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
        total_extraction = active_wells_df[
            active_wells_df["Balance area"] == area
        ][  # Extraction per area
            "Value"
        ].sum()
        total_demand = hexagons_filterd[
            hexagons_filterd["Balance Area"] == area
        ][  # Demand per area
            "Water Demand"
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
    fields=["Balance Area", "Water Demand", "Current Pop", "Type"],
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
    vmin=hexagons_filterd["Water Demand"].quantile(0.0),
    vmax=hexagons_filterd["Water Demand"].quantile(1),
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

def update_layers():
    """
    Update the layers on the map.

    Returns:
        folium.Map: Updated Folium map.
    """
    global active_wells_df
    m = folium.Map(
        location=[52.38, 6.7], zoom_start=10,
        tiles="Cartodb Positron"
    ) 
    active = active_wells_df[active_wells_df["Active"]==True]
    
    folium.GeoJson(
        active,
        name="Wells",
        zoom_on_click=True,
        popup=popup_well,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#F9F6EE", icon="arrow-up-from-ground-water", prefix="fa"
            )
        ),
    ).add_to(m)
    
    folium.GeoJson(
        industrial,
        name="Industrial Water Extraction",
        zoom_on_click=True,
        popup=popup_industrial,
        tooltip=folium.GeoJsonTooltip(fields=["Place"], aliases=["Place:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#d9534f", icon="industry", prefix="fa"
            )
        ),
    ).add_to(m)
    

    hex = folium.GeoJson(
        hexagons_filterd,
        name="Hexagons",
        style_function=lambda x: {
            "fillColor": (
                colormap(x["properties"]["Water Demand"])
                if x["properties"]["Water Demand"] is not None
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
        popup=popup_hex,
    ).add_to(m)

    m.add_child(colormap)

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
            "color": "#ce9ad6",
            "weight": 3
        },
        show=True,
        tooltip=folium.GeoJsonTooltip(fields=['Balance Area'], labels=True)
    ).add_to(m)
    
    folium.LayerControl().add_to(m)

    return m

active_scenarios = set()
text = ["## Scenario"]


def update_scenarioTitle(new_title):
    global text
    base_title = "VITALENS - Current Situation 2024"
    if Scenario_Button.value == "Autonomous Growth":
        if ("Accelerated Growth" or base_title) in text:
            text.remove("Accelerated Growth")
        text.append(new_title)
    if Scenario_Button.value == "Accelerated Growth":
        if ("Autonomous Growth" or base_title) in text:
            text.remove("Autonomous Growth")
        text.append(new_title)
    if Scenario_Button.value == "Current State - 2024":
        if "Accelerated Growth" in text:
            text.remove("Accelerated Growth")
        if "Autonomous Growth" in text:
            text.remove("Autonomous Growth")
        text.append(new_title)
            
    app_title.object = " - ".join(text)
    print (text)


def update_title(event):
    global active_wells_df
    global text
    # if (Button1.value or Measures_Button.value == "Autonomous Growth" ):
    #     if "Accelerated Growth" in text:
    #         text.remove("Accelerated Growth")
    #     text.append("Autonomous Growth")
    # if (Button2.value or Measures_Button.value == "Accelerated Growth"):
    #     if "Autonomous Growth" in text:
    #         text.remove("Autonomous Growth")
    #     text.append("Accelerated Growth")
    # if Measures_Button.value == "Current State - 2024":
    #     if "Accelerated Growth" in text:
    #         text.remove("Accelerated Growth")
    #     if "Autonomous Growth" in text:
    #         text.remove("Autonomous Growth")
    if Button3.value == True:
        try: text.remove("Closed Small Wells")
        finally: 
            text.append("Closed Small Wells")
            Measure1On()
    if Button3.value == False:
        try: text.remove("Closed Small Wells")
        except: print("Name does not exist -- skipping step")
        finally:
            Measure1Off()
    if Button4.value == True:
        try: text.remove("Closed Natura Wells")
        finally:
            text.append("Closed Natura Wells")
            Measure2On()
    if Button4.value == False:
        try: text.remove("Closed Natura Wells")
        except: print("Name does not exist -- skipping step")
        finally:
            Measure2Off()
    if Button5.value == True:
        try: text.remove("Use of Smart Meters")
        finally: 
            text.append("Use of Smart Meters")
            Measure3On()
    if Button5.value == False:
        try: text.remove("Use of Smart Meters")
        except: print("Name does not exist -- skipping step")
        finally:
            Measure3Off()
    if Button6.value == True:
        try: text.remove("Import Water")
        finally:
            text.append("Import Water")
            Measure4On()
    if Button6.value == False:
        try: text.remove("Import Water")
        except: print("Name does not exist -- skipping step")
        finally:
            Measure4Off()
    
    app_title.object = " - ".join(text)
    print(text)
    print(active_wells_df.head())
    update_indicators()
    

def Scenario1():
    """
    Implement the first scenario with a demand increase of 10%.

    Args:
        event: The event object.
    """
    global hexagons_filterd
    demand_capita = 0.156*1.1
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

def Scenario2():
    global hexagons_filterd
    demand_capita = 0.156*1.35
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    update_scenarioTitle("Accelerated Growth")
    update_indicators()

def Measure1On():
    global active_wells_df
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = False
    

def Measure1Off():
    global active_wells_df
    condition = active_wells_df["Max_permit"] >= 5.00
    active_wells_df.loc[condition, "Active"] = True


def Measure2On():
    """
    Activate the second measure (closing Natura 2000 wells).
    """
    active_wells_df.loc[active_wells_df["Name"] == "Archemerberg", "Active"] = False
    active_wells_df.loc[active_wells_df["Name"] == "Nijverdal", "Active"] = False

def Measure2Off():
    """
    Deactivate the second measure (closing Natura 2000 wells).
    """
    active_wells_df.loc[active_wells_df["Name"] == "Archemerberg", "Active"] = True
    active_wells_df.loc[active_wells_df["Name"] == "Nijverdal", "Active"] = True
    
def Measure3On():
    """
    Activate the third measure (using smart meters).
    """
    demand_capita = 0.156 * 0.9
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Pop2022"] * demand_capita * 365
    ) / 1000000

def Measure3Off():
    """
    Deactivate the third measure (using smart meters).
    """
    demand_capita = 0.156
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Pop2022"] * demand_capita * 365
    ) / 1000000
    
def Measure4On():
    """
    Activate the fourth measure (importing water).
    """
    active_wells_df.loc[active_wells_df.shape[0]] = ["Imports", 3,0, 4.5, "Imported", True, 4.38, 0,0,0,0,0,0, "POINT (253802.6,498734.2)"]

def Measure4Off():
    """
    Deactivate the fourth measure (importing water).
    """
    try:
        active_wells_df.drop(active_wells_df[active_wells_df["Name"]=='Imports'].index, inplace=True)
    except:
        print("Row does not exist")

    
def Reset(event):
    """
    Reset the application to its initial state.

    Args:
        event: The event object.
    """
    demand_capita = 0.156
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Pop2022"] * demand_capita * 365
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
    Button1.value, Button2.value, Button3.value, Button4.value, Button5.value = False, False, False, False, False
    update_scenarioTitle("VITALENS - Current Situation")
    update_indicators()

def update_indicators(arg=None):
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    excess_cap.value = calculate_available()
    own_pane.value = calculate_ownership()
    natura_pane.value = calculate_affected_Natura()
    industrial_cap.value=calculate_industrial()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    update_balance_opex()
    update_balance_lzh_gauges()
    total_demand.value = calculate_total_Demand()
    lzh.value = calculate_lzh()
    

# Initialize a dictionary to hold the active state and slider references
active_wells = {}

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

# Initialize a dictionary to hold the balance area layouts
balance_area_buttons = {}

# Setup Well Radio Buttons
Radio_buttons = []
Well_radioB = []
options = ["-10%", "-20%", "Current", "+10%", "+20%", "Maximum Permit", "Agreement"]
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
    checkbox = pn.widgets.Checkbox(name="Active", value=True)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")
    radio_group.param.watch(partial(update_radio, well_name=wellName), "value")
    
    NameP = pn.pane.Str(wellName, styles={
        'font-size': "14px",
        'font-family': "Barlow",
        'font-weight': 'bold',
    })
    
    NamePane = pn.pane.Str(update_well_Name(wellName), styles={
        'font-family': 'Roboto',
        'font-size': "16px",
        'font-weight': 'bold'
    })
    NameState = pn.Row(NameP, pn.Spacer(), checkbox)
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
    
Scenario_Button =pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['Current state - 2024','Autonomous Growth','Accelerated Growth'], button_type='warning', styles={
    'width': '97%', }
                                             )
Scenario_Button.param.watch(update_scenarios, "value")

Button1 = pn.widgets.Button(
    name='Autonomous growth', button_type="primary", width=300, margin=10,
)
Button1.param.watch(update_title, 'value')
Button1.on_click(Scenario1)

Button2 = pn.widgets.Button(
    name="Accelerated growth", button_type="primary", width=300, margin=10, 
)
Button2.param.watch(update_title, 'value')
Button2.on_click(Scenario2)

Button3 = pn.widgets.Toggle(
    name='Close Small Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button3.param.watch(update_title, 'value')

Button4 = pn.widgets.Toggle(
    name='Close Natura 2000 Wells', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button4.param.watch(update_title, 'value')

Button5 = pn.widgets.Toggle(
    name='Include Smart Meters', button_type="primary", button_style="outline", width=300, margin=10, 
)
Button5.param.watch(update_title, 'value')

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
    <b>Installation of Water Smartmeters: Reduction of 10% on demand &#8628;</b>''', width=300, align="start", styles={}
)

textB6 = pn.pane.HTML(
    '''
    <b>Importing water from WAZ Getelo, NVB Nordhorn and Haaksbergen</b>''', width=300, align="start", styles={}
)

textEnd = pn.pane.HTML(
    '''<hr class="dashed">
    ''', width=300, align="start", styles={}
)

scenario_layout = pn.Column(textB1, Scenario_Button, textB3, Button3, textB4, Button4, textB5, Button5, textB6, Button6, textEnd, ButtonR)

tabs = pn.Tabs(("Well Capacities", firstColumn), ("Scenarios", scenario_layout))

# MAIN WINDOW
map_pane = pn.pane.plot.Folium(update_layers(), sizing_mode="stretch_both")

total_extraction = pn.indicators.Number(
    name="Total Supply",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="28pt",
    title_size="18pt",
    sizing_mode="stretch_width"
)

total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="28pt",
    title_size="18pt",
    align="center",
    sizing_mode="stretch_width"
)

balance_opex = calculate_total_OPEX_by_balance()
balance_opex_indicators = {
    balance: pn.indicators.Number(
        name=f"OPEX {balance}",
        value=value,
        format="{value:0,.2f} M\u20AC/yr",
        default_color='#3850a0',
        font_size="28pt",
        title_size="18pt",
        align="center",
    )
    for balance, value in balance_opex.items()
}

industrial_cap = pn.indicators.Number(
    name="Industrial Extraction",
    value=calculate_industrial(),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width"
)

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

natura_pane = pn.indicators.Number(
    name="Approximate Natura 2000 \n Affected area",
    value=calculate_affected_Natura(),
    format="{value:0.2f} Ha",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width",
    styles = {
        'font-family': "Roboto"
    }
)

co2_pane = pn.indicators.Number(
    name="CO\u2082 Emmission Cost",
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
df_Hexagons = pn.pane.DataFrame(hexagons_filterd.head(), name="Hexagons data")

total_demand = pn.indicators.Number(
    name="Total Water Demand",
    value=calculate_total_Demand(),
    format="{value:0,.2f} Mm\u00b3/yr",
    font_size="28pt",
    title_size="18pt",
    default_color='#3850a0',
    sizing_mode="stretch_width"
)

lzh = pn.indicators.Gauge(
    name=f"Overall \n Leveringszekerheid",
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
        bounds=(0, 400),
        format="{value} %",
        colors=[(0.25, "#D9534F"), (0.3, "#f2bf57"),(0.3375, "#92C25B"), (1, "#8DCEC0")],
        custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align=("center",'center'),
    )
    balance_lzh_gauges[area] = gauge


lzhTabs = pn.Tabs(lzh, *balance_lzh_gauges.values(), align=("center", "center"),  sizing_mode="scale_width"
                  )

opexTabs = pn.Tabs(
    total_opex, *balance_opex_indicators.values(), align=("center", "center")
)

Supp_dem = pn.Row(
    total_extraction, pn.Spacer(width=50), total_demand, sizing_mode="stretch_width"
)

Env_pane = pn.Column(co2_pane, drought_pane, sizing_mode="scale_width")
Extra_water_pane = pn.Column(industrial_cap,excess_cap, sizing_mode="scale_width")

app_title = pn.pane.Markdown("## Scenario: Current State - 2024", styles={
    "text-align": "right",
    "color": "#00B893"
})

main1 = pn.GridSpec(sizing_mode="stretch_both")
main1[0, 0] = pn.Row(map_pane)

main2 = pn.Row(
    natura_pane,
    Env_pane,
    Extra_water_pane,
    sizing_mode="scale_width",
    scroll=True
)

main1[0, 1] = pn.Column(app_title, lzhTabs, Supp_dem, opexTabs, main2, sizing_mode="stretch_width")

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
    # df_display.object = update_df_display()
    total_opex.value = calculate_total_OPEX()
    total_demand.value = calculate_total_Demand()
    update_balance_opex()
    update_balance_lzh_gauges()
    update_indicators()
    natura_pane.value = calculate_affected_Natura()
    map_pane.object = update_layers()
    co2_pane.value = calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()


total_extraction_update()
Box.servable()
