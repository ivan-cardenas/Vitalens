import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Polygon
from config.dataLoad import *

# Function to calculate the total extraction based on active wells
def calculate_total_extraction(active_wells_df):
    total = active_wells_df[active_wells_df["Active"]]["Value"].sum()
    return total

# Calculate Available water
def calculate_available(active_wells_df):
    total = (
        active_wells_df[active_wells_df["Active"]==True]["Max_permit"].sum()
        - active_wells_df[active_wells_df["Active"]==True]["Value"].sum()
    )
    return total

# Calculate Ownership percentage
def calculate_ownership(active_wells_df):
    total = (
        active_wells_df[active_wells_df["Active"]]["Ownership"].sum()
        / active_wells_df[active_wells_df["Active"]]["Num_Wells"].sum()
    )
    return total * 100

# # Function to calculate the total OPEX based on active wells
def calculate_total_OPEX(active_wells_df):
    total = (active_wells_df[active_wells_df["Active"]]["OPEX"]).sum()
    return total/1000000

# Function to calculate the total OPEX grouped by Balance based on active wells
def calculate_total_OPEX_by_balance(active_wells_df):
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )/1000000

# Function to update balance OPEX indicators
def update_balance_opex(active_wells_df, balance_opex_indicators):
    balance_opex = calculate_total_OPEX_by_balance(active_wells_df)
    for balance, indicator in balance_opex_indicators.items():
        indicator.value = balance_opex.get(balance, 0)

# # Function to calculate the total ENV cost based on active wells
def calculate_total_envCost(active_wells_df):
    total = (active_wells_df[active_wells_df["Active"]]["envCost"]).sum()
    return total

# Function to calculate the total Env Cost grouped by Balance based on active wells
def calculate_total_envCost_by_balance(active_wells_df):
    return (
        active_wells_df[active_wells_df["Active"]]
        .groupby("Balance area")["envCost"]
        .sum()
    )

# Calculate affected Area
def calculate_affected_Natura(active_wells_df, hexagons_filtered):
    names = active_wells_df[active_wells_df["Active"]]["Name"]
    restricted = hexagons_filtered[
        (hexagons_filtered["Source_Name"].isin(names))
        & (hexagons_filtered["Type"] == "Source and Restricted")
    ]
    # Count the number of restricted Natura2000 areas
    total = restricted.shape[0]
    return total * 629387.503078 / 100000

def calculate_total_CO2_cost(active_wells_df):
    # Filter active wells
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    # Calculate the total environmental cost
    active_wells["CO2_Cost"] = active_wells_df["Value"] * active_wells_df["CO2_m3"]
    total_environmental_cost = active_wells["CO2_Cost"].sum()
    return total_environmental_cost

def calculate_total_Drought_cost(active_wells_df):
    # Filter active wells
    active_wells = active_wells_df[active_wells_df["Active"] == True]

    # Calculate the total environmental cost
    active_wells["Drought_Cost"] = (
        active_wells_df["Value"] * active_wells_df["Drought_m3"]
    )
    total_environmental_cost = active_wells["Drought_Cost"].sum()

    return total_environmental_cost

# Function to update the DataFrame display
def update_df_display(active_wells_df):
    return f"```python\n{active_wells_df}\n```"

# Function to toggle the active state based on the checkbox
def toggle_well(event, well_name, active_wells_df, map_pane):
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Active"] = event.new
    update_indicators()
    map_pane.object = update_layers(active_wells_df)

# Function to update the slider value in the DataFrame
def update_slider(event, well_name, active_wells_df):
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

# Function to update the extraction value based on the selected radio button option
def update_radio(event, well_name, wells, active_wells_df, active_wells):
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
    # Update the NamePane with the current extraction value and well name
    name_pane = active_wells[well_name]["name_pane"]
    name_pane.object = update_well_Name(well_name)
    update_indicators()


def update_well_Name(well_name, active_wells_df):
    current_extraction = active_wells_df[active_wells_df["Name"]==well_name]["Value"].values[0]
    return f"{current_extraction:.2f} Mm\u00b3/yr"

# Function to update the yearCal variable
def update_year(event, hexagons_filterd, growRate):
    global yearCal
    yearCal = event.new
    if yearCal == 2022:
        hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    else:
        hexagons_filterd["Current Pop"] = round(
            hexagons_filterd["Pop2022"] * ((1 + growRate) ** float((yearCal - 2022))), 0
        )
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * 0.1560 * 365
    ) / 1000000
    update_indicators()  # Update the total demand indicator

def calculate_total_Demand(hexagons_filterd):
    total = ((hexagons_filterd["Water Demand"]).sum()) + (
        (hexagons_filterd["Industrial Demand"]).sum()
    )
    return total

def calculate_demand_by_balance(active_wells_df):
    return active_wells_df.groupby("Balance area")["Water Demand"].sum()

# Function to update balance OPEX indicators
def update_demand():
    total_demand = calculate_demand_by_balance()
    for balance, indicator in calculate_demand_by_balance.items():
        indicator.value = total_demand.get(balance, 0)

def calculate_lzh():
    # Calculate Leveringszekerheid (Delivery Security), replace with actual calculation
    total_extraction = calculate_total_extraction()
    total_demand = calculate_total_Demand()
    return round((total_extraction / total_demand) * 100, 2)

def calculate_lzh_by_balance(active_wells_df, hexagons_filterd):
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

# Function to update LZH gauges by balance area
def update_balance_lzh_gauges(balance_lzh_gauges, active_wells_df, hexagons_filterd):
    lzh_by_balance = calculate_lzh_by_balance(active_wells_df, hexagons_filterd)
    for area, gauge in balance_lzh_gauges.items():
        gauge.value = lzh_by_balance.get(area, 0)

# Function to calculate the centroid of a polygon
def calculate_centroid(coordinates):
    polygon = Polygon(coordinates)
    return polygon.centroid.y, polygon.centroid.x

def calculate_total_Demand(hexagons_filtered):
    total = (hexagons_filtered["Water Demand"]).sum() + (hexagons_filtered["Industrial Demand"]).sum()
    return total

def calculate_demand_by_balance(hexagons_filterd):
    return hexagons_filterd.groupby("Balance area")["Water Demand"].sum()

def calculate_lzh(active_wells_df, hexagons_filterd):
    total_extraction = calculate_total_extraction(active_wells_df)
    total_demand = calculate_total_Demand(hexagons_filterd)
    return round((total_extraction / total_demand) * 100, 2)

def calculate_lzh_by_balance(active_wells_df, hexagons_filterd):
    lzh_by_balance = {}
    balance_areas = active_wells_df["Balance area"].unique()
    for area in balance_areas:
        total_extraction = active_wells_df[active_wells_df["Balance area"] == area]["Value"].sum()
        total_demand = hexagons_filterd[hexagons_filterd["Balance Area"] == area]["Water Demand"].sum()
        lzh_by_balance[area] = round((total_extraction / total_demand) * 100, 2) if total_demand else 0
    return lzh_by_balance

# Function to Display map   
def update_layers(active_wells_df, popup_well,hexagons_filtered, colormap, popup_hex, balance_areas):
    m = folium.Map(
    location=[52.38, 6.7], zoom_start=10,
    tiles="Cartodb Positron"
    ) 
     # Adjust the center and zoom level as necessary
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

    hex = folium.GeoJson(
        hexagons_filtered,
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
        hexagons_filtered,
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
        hexagons_filtered,
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


# Add the update_indicators function
# Update Indicators
def update_indicators(total_extraction, total_opex, excess_cap, own_pane, natura_pane, co2_pane, drought_pane, total_demand, lzh, map_pane, balance_opex_indicators, balance_lzh_gauges, popup_well, colormap, popup_hex):
    total_extraction.value = calculate_total_extraction(active_wells_df)
    total_opex.value = calculate_total_OPEX(active_wells_df)
    excess_cap.value = calculate_available(active_wells_df)
    own_pane.value = calculate_ownership(active_wells_df)
    natura_pane.value = calculate_affected_Natura(active_wells_df, hexagons_filtered)
    co2_pane.value= calculate_total_CO2_cost(active_wells_df)
    drought_pane.value = calculate_total_Drought_cost(active_wells_df)
    update_balance_opex(active_wells_df,balance_opex_indicators)
    total_demand.value = calculate_total_Demand(hexagons_filtered)
    lzh.value = calculate_lzh(active_wells_df,hexagons_filtered)
    update_balance_lzh_gauges(balance_lzh_gauges,active_wells_df, hexagons_filtered)
    map_pane.object=update_layers(active_wells_df, popup_well, hexagons_filtered, colormap, popup_hex, balance_areas)
    
    