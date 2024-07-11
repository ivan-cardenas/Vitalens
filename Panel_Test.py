import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import json
import pydeck as pdk
from bokeh.models.formatters import PrintfTickFormatter
import folium
from folium.plugins import MarkerCluster
from folium.plugins import Search
import branca

# Styling
ACCENT = "#3c549d"
LOGO = "https://assets.holoviz.org/panel/tutorials/matplotlib-logo.png"

# Initialize extensions
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")
pn.extension("echarts")
pn.extension(design='material', global_css=[
    """
    @import url("https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap");

    :root { 
        --design-primary-color: #3C549D; 
        --design-secondary-color: #B5D99C; 
        --design-primary-text-color: #F8F7F4; 
        --design-secondary-text-color: #2D2D2A;
    } 
    body {
        font-family: 'Barlow', sans-serif;
    }
    """
])
pn.extension(
    "tabulator", "ace", css_files=["https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"]
)



# Load the GeoPackage file
gpkg_file = "../GEOPKG/Thematic_data.gpkg"
layers = fiona.listlayers(gpkg_file)  # Load all layers

# Get Wells Attributes
wells = gpd.read_file(gpkg_file, layer="Well_Capacity_Cost")
# Convert the capacity columns to numeric, setting errors='coerce' will replace non-numeric values with NaN
wells["Permit__Mm3_per_jr_"] = pd.to_numeric(
    wells["Permit__Mm3_per_jr_"], errors="coerce"
)
wells["Extraction_2023__Mm3_per_jr_"] = pd.to_numeric(
    wells["Extraction_2023__Mm3_per_jr_"], errors="coerce"
)
# calculate total costs per m3
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


yearCal = 2022
growRate = 0.0062
demand_capita = 0.130

# Get Destination Attributes
hexagons = gpd.read_file(gpkg_file, layer="H3_Lvl8")
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
        "Water Demand": hexagons["Pop_2022"] * 0.130 * 365 / 1000000,
        "Type": hexagons["Type_T"],
        "Source_Name": hexagons["Source_Name"],
        "geometry": hexagons["geometry"],
    }
)


# Function to calculate the total extraction based on active wells
def calculate_total_extraction():
    total = active_wells_df[active_wells_df["Active"]]["Value"].sum()
    return total


# Calculate Available water
def calculate_available():
    total = (
        active_wells_df[active_wells_df["Active"]]["Max_permit"].sum()
        - active_wells_df[active_wells_df["Active"]]["Value"].sum()
    )
    return total


# Calculate Ownership percentage
def calculate_ownership():
    total = (
        active_wells_df[active_wells_df["Active"]]["Ownership"].sum()
        / active_wells_df[active_wells_df["Active"]]["Num_Wells"].sum()
    )
    return total * 100


# # Function to calculate the total OPEX based on active wells
def calculate_total_OPEX():
    total = (active_wells_df[active_wells_df["Active"]]["OPEX"]).sum()
    return total


# Function to calculate the total OPEX grouped by Balance based on active wells
def calculate_total_OPEX_by_balance():
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )


# Function to update balance OPEX indicators
def update_balance_opex():
    balance_opex = calculate_total_OPEX_by_balance()
    for balance, indicator in balance_opex_indicators.items():
        indicator.value = balance_opex.get(balance, 0)


# # Function to calculate the total ENV cost based on active wells
def calculate_total_envCost():
    total = (active_wells_df[active_wells_df["Active"]]["envCost"]).sum()
    return total


# Function to calculate the total Env Cost grouped by Balance based on active wells
def calculate_total_envCost_by_balance():
    return (
        active_wells_df[active_wells_df["Active"]]
        .groupby("Balance area")["envCost"]
        .sum()
    )


# Calculate affected Area
def calculate_affected_Natura():
    names = active_wells_df[active_wells_df["Active"]]["Name"]
    restricted = hexagons_filterd[
        (hexagons_filterd["Source_Name"].isin(names))
        & (hexagons_filterd["Type"] == "Source and Restricted")
    ]
    # Count the number of restricted Natura2000 areas
    total = restricted.shape[0]
    return total * 629387.503078 / 100000


def calculate_total_CO2_cost():
    # Filter active wells
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    # Calculate the total environmental cost
    active_wells["CO2_Cost"] = active_wells_df["Value"] * active_wells_df["CO2_m3"]
    total_environmental_cost = active_wells["CO2_Cost"].sum()
    return total_environmental_cost*1000000


def calculate_total_Drought_cost():
    # Filter active wells
    active_wells = active_wells_df[active_wells_df["Active"] == True]

    # Calculate the total environmental cost
    active_wells["Drought_Cost"] = (
        active_wells_df["Value"] * active_wells_df["Drought_m3"]
    )
    total_environmental_cost = active_wells["Drought_Cost"].sum()

    return total_environmental_cost*1000000


# Function to update the DataFrame display
def update_df_display():
    return f"```python\n{active_wells_df}\n```"


# Function to toggle the active state based on the checkbox
def toggle_well(event, well_name):
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Active"] = event.new
    update_indicators()


# Function to update the slider value in the DataFrame
def update_slider(event, well_name):
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


# Function to update the yearCal variable
def update_year(event):
    global yearCal
    yearCal = event.new
    if yearCal == 2022:
        hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    else:
        hexagons_filterd["Current Pop"] = round(
            hexagons_filterd["Pop2022"] * ((1 + growRate) ** float((yearCal - 2022))), 0
        )
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * 0.130 * 365
    ) / 1000000
    df_Hexagons.object = hexagons_filterd.head()  # Update the displayed DataFrame
    update_indicators()  # Update the total demand indicator


def calculate_total_Demand():
    total = ((hexagons_filterd["Water Demand"]).sum()) + (
        (hexagons_filterd["Industrial Demand"]).sum()
    )
    return total


def calculate_demand_by_balance():
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


def calculate_lzh_by_balance():
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
def update_balance_lzh_gauges():
    lzh_by_balance = calculate_lzh_by_balance()
    for area, gauge in balance_lzh_gauges.items():
        gauge.value = lzh_by_balance.get(area, 0)


# create map and add attrobutes ### TODO: Check how to join with well active DF
m = folium.Map(
    location=[52.38, 6.7], zoom_start=10
)  # Adjust the center and zoom level as necessary
popup_well = folium.GeoJsonPopup(
    fields=["Name", "Balance area", "Value"],
    aliases=["Well Name", "Balance Area", "Extraction in Mm\u00b3/Year"],
)
popup_hex = folium.GeoJsonPopup(
    fields=["Balance Area", "Water Demand", "Current Pop", "Type"],
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
    caption="Total water demand in Mm\u00b3/Year",
)


def update_layers():
    m = folium.Map(
        location=[52.37, 6.7], zoom_start=10
    )  # Adjust the center and zoom level as necessary
    active = active_wells_df[active_wells_df["Active"]]

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

    h = folium.GeoJson(
        hexagons_filterd,
        name="Hexagons",
        style_function=lambda x: {
            "fillColor": (
                colormap(x["properties"]["Water Demand"])
                if x["properties"]["Water Demand"] is not None
                else "transparent"
            ),
            "color": "darkgray",
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        popup=popup_hex,
        #    tooltip=folium.GeoJsonTooltip(fields=["Balance Area"], aliases=["Balance Area:"]),
        #    style_function=hexagons_filterd["style"]
    ).add_to(m)

    rn = folium.GeoJson(
        hexagons_filterd,
        name="Natura2000 Restricted Area",
        style_function=lambda x: {
            "fillColor": (
                "darkred"
                if x["properties"]["Type"] == "Restricted Natura2000"
                else "transparent"
            ),
            "color": "darkgray",
            "fillOpacity": 0.8,
            "weight": 0.7,
        }, 
        show= False,
        #    tooltip=folium.GeoJsonTooltip(fields=["Balance Area"], aliases=["Balance Area:"]),
        #    style_function=hexagons_filterd["style"]
    ).add_to(m)

    ro = folium.GeoJson(
        hexagons_filterd,
        name="Restricted NNN",
        style_function=lambda x: {
            "fillColor": (
                "#f9aaa2"
                if x["properties"]["Type"] == "Restricted Other"
                else "transparent"
            ),
            "color": "darkgray",
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        show= False,
        #    tooltip=folium.GeoJsonTooltip(fields=["Balance Area"], aliases=["Balance Area:"]),
        #    style_function=hexagons_filterd["style"]
    ).add_to(m)

    m.add_child(colormap)
    folium.LayerControl().add_to(m)

    return m


# Function to create Scenarios
def Scenario1(event):
    demand_capita = 0.13*1.1
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    df_Hexagons.object = hexagons_filterd.head()  # Update the displayed DataFrame
    # update_year(event)
    update_indicators()  # Update the total demand indicator

def Scenario2(event):
    demand_capita = 0.13*1.35
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    df_Hexagons.object = hexagons_filterd.head()  # Update the displayed DataFrame
    # update_year(event)
    update_indicators()  # Update the total demand indicator

def Reset(event):
    demand_capita = 0.13*1.35
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Pop2022"] * demand_capita * 365
    ) / 1000000
    df_Hexagons.object = hexagons_filterd.head()  # Update the displayed DataFrame
    # update_year(event)
    update_indicators()  # Update the total demand indicator

# Update Indicators
def update_indicators():
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    excess_cap.value = calculate_available()
    own_pane.value = calculate_ownership()
    natura_pane.value = calculate_affected_Natura()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    update_balance_opex
    total_demand.value = calculate_total_Demand()
    lzh.value = calculate_lzh()
    update_balance_lzh_gauges  # Add this line to update LZH gauges
    df_display.object = update_df_display()
    map_pane.object = update_layers()


# Initialize a dictionary to hold the active state and slider references
active_wells = {}


# Setup Well Sliders
Sliders = []
for index, row in wells.iterrows():
    wellEnd = row["Permit__Mm3_per_jr_"]
    wellCurrent = row["Extraction_2023__Mm3_per_jr_"]
    wellName = row["Name"]
    Well_slider = pn.widgets.FloatSlider(
        name=wellName,
        start=0,
        end=wellEnd,
        step=0.1,
        value=wellCurrent,
        format=PrintfTickFormatter(format="%.2f Mm\u00b3/Year"),
        width=280,
        margin=(4, 10),
    )
    max_label = pn.pane.Str(
        f"Max: {wellEnd:.2f}", width=200, align="end"
    )  # Create a label for the maximum value
    min_label = pn.pane.Str(f"Min: {0:.2f}", width=200, align="start")

    # add Checkbox and listeners
    checkbox = pn.widgets.Checkbox(name="Active", value=True)

    checkbox.param.watch(
        lambda event, well_name=wellName: toggle_well(event, well_name), "value"
    )

    Well_slider.param.watch(
        lambda event, well_name=wellName: update_slider(event, well_name), "value"
    )

    custom_style = {
        'background': '#f9f9f9',
        'border': '0.7px solid',
        'margin': '10px',
        "box-shadow": '4px 2px 6px #2d3f76'
    }

    minMaxlabel = pn.Row(min_label, max_label, width=300)
    Sliders.append(pn.Column(checkbox, Well_slider, minMaxlabel, styles=custom_style))

    # Store the active state and slider reference
    active_wells[wellName] = {"active": checkbox.value, "value": Well_slider.value}
    wellsDF = pd.DataFrame(active_wells).T

# Widgets for user interaction

# SIDE BAR
# Create a layout for years and buttons
# year_selector = pn.widgets.IntInput(
#     name="Which year do you want to calculate?",
#     value=yearCal,
#     step=1,
#     start=2022,
#     end=2035,
#     width=300,
# )
# year_selector.param.watch(update_year, "value")

Button1 = pn.widgets.Button(
    name='Autonomous growth', button_type="primary", width=300, margin=10
)
Button1.on_click(Scenario1)
Button2 = pn.widgets.Button(
    name="Accelerated growth", button_type="primary", width=300, margin=10
)
Button2.on_click(Scenario2)

textB1 = pn.pane.HTML('''
                      <b>Scenario with demand increase of 10%</b>'''
                      , width=300, align="start", styles={ 'font-family': "Barlow",
                                                          })
textB2 = pn.pane.HTML('''
                      <b>Scenario with demand increase of 35%</b>'''
                      , width=300, align="start", styles={'font-family': "Barlow"})

# Create a layout for the sliders
slider_layout = pn.Column(*Sliders)
scenario_layout = pn.Column(textB1,Button1, textB2, Button2)

# Create a tab for the sidebar and others
tabs = pn.Tabs(("Well Capacities", slider_layout), ("Scenarios", scenario_layout))

# MAIN WINDOW
# Convert the Folium map to a Panel pane
map_pane = pn.pane.plot.Folium(m, sizing_mode="stretch_width", height=500)


# Create an indicator for the total extraction
total_extraction = pn.indicators.Number(
    name="Total Supply",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3/Year",
    font_size="28pt",
    title_size="18pt",
)

# Indicator total OPEX
total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.0f} \u20AC/Year",
    font_size="28pt",
    title_size="18pt",
    align="center",
)

# Create indicators for OPEX by balance area
balance_opex = calculate_total_OPEX_by_balance()
balance_opex_indicators = {
    balance: pn.indicators.Number(
        name=f"OPEX {balance}",
        value=value,
        format="{value:0,.0f} \u20AC/Year",
        font_size="28pt",
        title_size="18pt",
        align="center",
    )
    for balance, value in balance_opex.items()
}

excess_cap = pn.indicators.Number(
    name="Excess Capacity",
    value=calculate_available(),
    format="{value:0.2f} Mm\u00b3/Year",
    font_size="28pt",
    title_size="18pt",
    align="center",
)

own_pane = pn.indicators.Number(
    name="Landownership",
    value=calculate_ownership(),
    format="{value:0.2f} %",
    font_size="28pt",
    title_size="18pt",
    align="center",
    colors=[(75, "red"), (85, "gold"), (100, "green")],
)

natura_pane = pn.indicators.Number(
    name="Aproximate Natura 2000 \n Affected area",
    value=calculate_affected_Natura(),
    format="{value:0.2f} Ha",
    font_size="28pt",
    title_size="18pt",
    align="center",
    sizing_mode="stretch_width"
)

co2_pane = pn.indicators.Number(
    name="CO\u2028 Emmision Cost",
    value=calculate_total_CO2_cost(),
    format="{value:0,.0f} \u20AC/Year",
    font_size="28pt",
    title_size="18pt",
)

drought_pane = pn.indicators.Number(
    name="Drought Damage Cost",
    value=calculate_total_Drought_cost(),
    format="{value:0,.0f} \u20AC/Year",
    font_size="28pt",
    title_size="18pt",
)


# Create a Markdown pane to display the DataFrame BACKEND
df_display = pn.pane.Markdown(update_df_display())

# Create a Markdown pane to display the DataFrame BACKEND
df_Hexagons = pn.pane.DataFrame(hexagons_filterd.head(), name="Hexagons data")

# Create indicator for Total Water demand
total_demand = pn.indicators.Number(
    name="Water Demand",
    value=calculate_total_Demand(),
    format="{value:0,.2f} Mm\u00b3/Year",
    font_size="28pt",
    title_size="18pt",
)

# create Indicator for LEVERENSZEKERHEID
lzh = pn.indicators.Gauge(
    name="Leveringszekerheid",
    value=calculate_lzh(),
    bounds=(70, 150),
    format="{value} %",
    colors=[(0.4, "red"), (0.7, "green"), (1, "Lightblue")],
    custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align="center",
)
lzh.param.watch(update_indicators, "value")

# Create gauges for LZH by balance area
balance_lzh_gauges = {}


balance_lzh_values = calculate_lzh_by_balance()
for area, value in balance_lzh_values.items():
    gauge = pn.indicators.Gauge(
        name=f"LZH \n{area}",
        value=value,
        bounds=(0, 300),
        format="{value} %",
        colors=[(0.4, "red"), (0.7, "green"), (1, "Lightblue")],
        width=200,
        title_size=12,
        custom_opts={
            "pointer": {"interStyle": {"color": "auto"}},
            "detail": {"valueAnimation": True, "color": "inherit", "fontSize": 10},
        },
        align=("center", "center"),
    )
    balance_lzh_gauges[area] = gauge

# create layout for LZH
lzh_Balance = pn.template.SlidesTemplate(
    title="Leveringszekerheid",
    logo="https://raw.githubusercontent.com/holoviz/panel/main/doc/_static/logo_stacked.png",
)
lzh_layout = pn.GridSpec(sizing_mode="stretch_width", align="center", height=400)


lzh_layout[0:1, 0] = lzh
balance_lzh_layout = pn.GridSpec(sizing_mode="stretch_width")
balance_lzh_layout[0, 0] = pn.Row(
    balance_lzh_gauges["Reggeland"], balance_lzh_gauges["Dinkelland"]
)
balance_lzh_layout[1, 0] = pn.Row(
    balance_lzh_gauges["Hof v Twente"], balance_lzh_gauges["Stedenband"]
)

lzh_layout[0, 1] = balance_lzh_layout


# create layout for OPEX
opexTabs = pn.Tabs(
    total_opex, *balance_opex_indicators.values(), align=("center", "center")
)

# create layout for two items
Supp_dem = pn.Row(
    total_extraction, pn.Spacer(width=100), total_demand, sizing_mode="stretch_width"
)

Env_pane = pn.Column(co2_pane, drought_pane)

main1 = pn.GridSpec(height=600, sizing_mode="stretch_width")
main1[0, 0] = pn.Row(map_pane)
main1[0, 1] = pn.Column(lzh, Supp_dem, opexTabs, sizing_mode="stretch_height")

main2 = pn.Row(
    natura_pane,
    pn.Spacer(width=100),
    Env_pane,
    pn.Spacer(width=100),
    excess_cap,
    pn.Spacer(width=70),
    own_pane,
    height=200,
    sizing_mode="stretch_width",
)


# FULL PAGE LAYOUT
Box = pn.template.FastListTemplate(
    # editable=True,
    title="VITALENS",
    logo="https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png",
    sidebar=tabs,
    main=[main1, main2, df_display],
    accent_base_color= "#3C549D",
    background_color = "#F8F7F4",
    header_background = "#2D2D2A",
    corner_radius = 3,
    font_url = "https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap"
)


# Function to update the total extraction value
def total_extraction_update():
    total_extraction.value = calculate_total_extraction()
    df_display.object = update_df_display()
    total_opex.value = calculate_total_OPEX()
    total_demand.value = calculate_total_Demand()
    update_balance_opex()
    update_balance_lzh_gauges()
    update_indicators()
    natura_pane.value = calculate_affected_Natura()
    map_pane.object = update_layers()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()


# Initial calculation of total extraction
total_extraction_update()

Box.servable()
