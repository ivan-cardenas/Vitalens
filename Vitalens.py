import geopandas as gpd
import pandas as pd
import panel as pn
import numpy as np
import fiona
from bokeh.models.formatters import PrintfTickFormatter
import folium
from folium.plugins import MarkerCluster
from folium.plugins import Search
from shapely.geometry import shape, Polygon
import branca
from functools import partial
import ipyleaflet as ipy
from ipyleaflet import Map, basemaps


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

.accordion-header button{
    color: #151931;
    background-color: #B4BFE4;
}

            
'''
]

# Initialize extensions
pn.config.global_css=cssStyle
pn.config.css_files=cssStyle
pn.config.loading_spinner='petal'
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")
pn.extension("echarts")
pn.extension(
    "tabulator", "ace", css_files=["https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"]
)
pn.extension('ipywidgets')



# Load the GeoPackage file
gpkg_file = "./Assets/Thematic_data.gpkg"
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
wells["Agreement__Mm3_per_jr_"] = pd.to_numeric(
    wells["Agreement__Mm3_per_jr_"], errors="coerce"
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
demand_capita = 0.1560

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
        "Water Demand": hexagons["Pop_2022"] * 0.1560 * 365 / 1000000,
        "Type": hexagons["Type_T"],
        "Source_Name": hexagons["Source_Name"],
        "geometry": hexagons["geometry"],
    }
)

balance_areas= hexagons_filterd.dissolve(by="Balance Area", as_index=False)

# Function to calculate the total extraction based on active wells
def calculate_total_extraction():
    total = active_wells_df[active_wells_df["Active"]]["Value"].sum()
    return total

# Calculate Available water
def calculate_available():
    total = (
        active_wells_df[active_wells_df["Active"]==True]["Max_permit"].sum()
        - active_wells_df[active_wells_df["Active"]==True]["Value"].sum()
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
    return total/1000000

# Function to calculate the total OPEX grouped by Balance based on active wells
def calculate_total_OPEX_by_balance():
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )/1000000

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
    return total_environmental_cost

def calculate_total_Drought_cost():
    # Filter active wells
    active_wells = active_wells_df[active_wells_df["Active"] == True]

    # Calculate the total environmental cost
    active_wells["Drought_Cost"] = (
        active_wells_df["Value"] * active_wells_df["Drought_m3"]
    )
    total_environmental_cost = active_wells["Drought_Cost"].sum()

    return total_environmental_cost

# Function to update the DataFrame display
def update_df_display():
    return f"```python\n{active_wells_df}\n```"

# Function to toggle the active state based on the checkbox
def toggle_well(event, well_name):
    active_wells_df.loc[active_wells_df["Name"] == well_name, "Active"] = event.new
    update_indicators()
    # map_pane.object = update_layers()

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

# Function to update the extraction value based on the selected radio button option
def update_radio(event, well_name):
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


def update_well_Name(well_name):
    current_extraction = active_wells_df[active_wells_df["Name"]==well_name]["Value"].values[0]
    return f"{current_extraction:.2f} Mm\u00b3/yr"

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
        hexagons_filterd["Current Pop"] * 0.1560 * 365
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

# create map and add attributes ### TODO: Check how to join with well active DF
basemap = ipy.leaflet.TileLayer(url="https://api.mapbox.com/v4/mapbox.outdoors/{z}/{x}/{y}.png")

m = Map(center=(52.38, 6.7), zoom_start=10, basemap=basemaps.OpenStreetMap.Mapnik)  # Adjust the center and zoom level as necessary


popup_well = folium.GeoJsonPopup(
    fields=["Name", "Balance area", "Value"],
    aliases=["Well Name", "Balance Area", "Extraction in Mm\u00b3/yr"],
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
    caption="Total water demand in Mm\u00b3/yr",
) 

# Function to calculate the centroid of a polygon
def calculate_centroid(coordinates):
    polygon = Polygon(coordinates)
    return polygon.centroid.y, polygon.centroid.x

# Function to Display map   
def update_layers():
    
    active = active_wells_df[active_wells_df["Active"]==True]
    geo_data = ipy.GeoData(
        geo_dataframe=active,
    style={
        "color": "black",
        "fillColor": "#3366cc",
        "opacity": 0.05,
        "weight": 1.9,
        "dashArray": "2",
        "fillOpacity": 0.6,
    },
    hover_style={"fillColor": "red", "fillOpacity": 0.2},
    name="Hexagons",
    )
    
    m.add(geo_data)
    m.add(ipy.LayersControl)

    return m

# Function to update the title of the Box
def update_title(new_title):
    content = '## ' + new_title
    app_title.object = content

# Function to create Scenarios
def Scenario1(event):
    demand_capita = 0.156*1.1
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    update_title("VITALENS - Autonumos Growth")
    update_indicators()  # Update the total demand indicator
    

def Scenario2(event):
    demand_capita = 0.156*1.35
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * 365
    ) / 1000000
    update_title("VITALENS - Accelerated Growth")
    update_indicators()  # Update the total demand indicator
    
    
def Scenario3(event):
    active_wells_df.loc[active_wells_df["Max_permit"] <= 5, "Active"] = False
    update_title("VITALENS - Closed Wells")
    update_indicators()
    
    
def Reset(event):
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
    df_Hexagons.object = hexagons_filterd.head()  # Update the displayed DataFrame
    update_indicators()  # Update the total demand indicator
    update_title("VITALENS - Current Situation")

# Update Indicators
def update_indicators():
    total_extraction.value = calculate_total_extraction()
    total_opex.value = calculate_total_OPEX()
    excess_cap.value = calculate_available()
    own_pane.value = calculate_ownership()
    natura_pane.value = calculate_affected_Natura()
    co2_pane.value= calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()
    update_balance_opex()
    total_demand.value = calculate_total_Demand()
    lzh.value = calculate_lzh()
    update_balance_lzh_gauges()
    map_pane.object=update_layers()
    

# Initialize a dictionary to hold the active state and slider references
active_wells = {}

miniBox_style = {
    'background': '#e9e9e1',
    'border': '0.7px solid',
    'margin': '10px',
    "box-shadow": '4px 2px 6px #2a407e',
    "display": "flex"
}

buttonGroup_style={
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
    
    # add Checkbox and listeners
    checkbox = pn.widgets.Checkbox(name="Active", value=True)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")
    radio_group.param.watch(partial(update_radio, well_name=wellName), "value")
    
    NameP = pn.pane.Str(wellName, styles={
        'font-size': "14px",
        'font-family': "Barlow",
        'font-weight': 'bold',
    })
    
    NamePane = pn.pane.Str(update_well_Name(wellName), styles={
        'font-family': 'Roboto'
    })
    NameState = pn.Row(NameP, pn.Spacer(), checkbox)
    Well_radioB = pn.Column(NameState, NamePane, radio_group,
                            styles=miniBox_style)
    
    # Add the well layout to the appropriate balance area layout
    if balance_area not in balance_area_buttons:
        balance_area_buttons[balance_area] = []
    balance_area_buttons[balance_area].append(Well_radioB)
    
    
    # Store the active state and radio group reference along with the NamePane
    active_wells[wellName] = {"active": True, "value": current_value, "radio_group": radio_group, "name_pane": NamePane}

# Create a layout for the radio buttons
radio_layout = pn.Accordion(styles={'width': '97%', 'color':'#151931'})
for balance_area, layouts in balance_area_buttons.items():
    balance_area_column = pn.Column(*layouts)
    radio_layout.append((balance_area, balance_area_column))

Button1 = pn.widgets.Button(
    name='Autonomous growth', button_type="primary", width=300, margin=10
)
Button1.on_click(Scenario1)
Button2 = pn.widgets.Button(
    name="Accelerated growth", button_type="primary", width=300, margin=10
)
Button2.on_click(Scenario2)

Button3 = pn.widgets.Button(
    name='Close Wells', button_type="primary", width=300, margin=10
)
Button3.on_click(Scenario3)


ButtonR = pn.widgets.Button(
    name='Reset', button_type='warning', width=300, margin=10
)
ButtonR.on_click(Reset)

textB1 = pn.pane.HTML(
    '''
    <h3 align= "center"> Scenarios</h3><hr>
    <b>Scenario with demand increase of 10%</b>''', width=300, align="start"
)
textB2 = pn.pane.HTML(
    '<b>Scenario with demand increase of 35%</b>', width=300, align="start"
)
textB3 = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center"> Measures </h3> <hr>
    <b>Close down all well locations with production less than 5Mm\u00b3/yr</b>''', width=300, align="start", styles={}
)

scenario_layout = pn.Column(textB1, Button1, textB2, Button2, textB3, Button3, ButtonR)

tabs = pn.Tabs(("Well Capacities", radio_layout), ("Scenarios", scenario_layout))

# MAIN WINDOW
map_pane = pn.panel(m, sizing_mode="stretch_both")


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
    name="Aproximate Natura 2000 \n Affected area",
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
    name="CO\u2028 Emmision Cost",
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

df_display = pn.pane.Markdown(update_df_display())
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
    name="Leveringszekerheid",
    value=calculate_lzh(),
    bounds=(0, 150),
    format="{value} %",
    colors=[(0.66, "#F19292"), (0.8, "#F6D186"),(0.9, "#CBE2B0"), (1, "#bee3db")],
    custom_opts={
        "pointer": {"interStyle": {"color": "auto"}},
        "detail": {"valueAnimation": True, "color": "inherit"},
    },
    align="center",
)
lzh.param.watch(update_indicators, "value")

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

opexTabs = pn.Tabs(
    total_opex, *balance_opex_indicators.values(), align=("center", "center")
)

Supp_dem = pn.Row(
    total_extraction, pn.Spacer(width=50), total_demand, sizing_mode="stretch_width"
)

Env_pane = pn.Column(co2_pane, drought_pane, sizing_mode="scale_width")

main1 = pn.GridSpec(sizing_mode="stretch_both")
main1[0, 0] = pn.Row(map_pane)


main2 = pn.Row(
    natura_pane,

    Env_pane,

    excess_cap,
    sizing_mode="scale_width",
    scroll=True
)

main1[0, 1] = pn.Column(lzh, Supp_dem, opexTabs, main2, sizing_mode="stretch_width")


# Create a dynamic title
app_title = pn.pane.Markdown("## Scenario: Current State - 2024", styles={
    "text-align": "right",
    "color": "#00B893"
})

Box = pn.template.MaterialTemplate(
    title="Vitalens",
    logo="https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png",
    sidebar=tabs,
    main=[app_title, main1],
    # background_color = '#f2f2ed',
    # neutral_color='#151931',
    # accent_base_color= '#3850a0',
    header_background= '#3850a0',
    header_color= '#f2f2ed'
)

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
    co2_pane.value = calculate_total_CO2_cost()
    drought_pane.value = calculate_total_Drought_cost()

total_extraction_update()

Box.servable()
