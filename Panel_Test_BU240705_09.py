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
from bokeh.models.formatters import PrintfTickFormatter

# Styling
ACCENT = "LightBlue"
LOGO = "https://assets.holoviz.org/panel/tutorials/matplotlib-logo.png"

# Initialize extensions
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")


# Load the GeoPackage file
gpkg_file = "./Assets/Thematic_data.gpkg"
layers = fiona.listlayers(gpkg_file)  # Load all layers

# Get Layers Attributes
wells = gpd.read_file(gpkg_file, layer="Well_Capacity_Cost")
# Convert the capacity columns to numeric, setting errors='coerce' will replace non-numeric values with NaN
wells["Permit__Mm3_per_jr_"] = pd.to_numeric(
    wells["Permit__Mm3_per_jr_"], errors="coerce")
wells["Extraction_2023__Mm3_per_jr_"] = pd.to_numeric(
    wells["Extraction_2023__Mm3_per_jr_"], errors="coerce")

# Initialize a DataFrame to hold the active state and slider values
active_wells_df = pd.DataFrame({
    'Name': wells['Name'],
    'Active': [True] * len(wells),
    'Value': wells['Extraction_2023__Mm3_per_jr_']
})


# Function to calculate the total extraction based on active wells
def calculate_total_extraction():
    total = 0
    for well in active_wells:
        if active_wells[well]["active"]:
            total += active_wells[well]["value"]
    return total


# Function to update the dictionary display
def update_df_display():
    df_display.object = f"```\n{active_wells_df.to_string(index=False)}\n```"

# Function to toggle the slider and labels based on the checkbox state
def toggle_well(event, well_name):
    active_wells[well_name]["active"] = event.new
    total_extraction.value = calculate_total_extraction()
    update_df_display()


# Function to update the slider value in the dictionary
def update_slider(event, well_name):
    active_wells[well_name]["value"] = event.new
    total_extraction.value = calculate_total_extraction()
    update_df_display()


# Initialize a dictionary to hold the active state and slider references
active_wells = {}


# Widgets for user interaction

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
        format=PrintfTickFormatter(format="%.2f Mm3"),
        width=300,
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

    minMaxlabel = pn.Row(min_label, max_label)
    Sliders.append(pn.Column(checkbox, Well_slider, minMaxlabel, width=600))

    # Store the active state and slider reference
    active_wells[wellName] = {"active": checkbox.value, "value": Well_slider.value}
    wellsDF = pd.DataFrame(active_wells).T
    

# Create an indicator for the total extraction

total_extraction = pn.indicators.Number(
    name="Total Supply per year",
    value=calculate_total_extraction(),
    format="{value:.2f} Mm\u00b3",
)

# Create a Markdown pane to display the DataFrame
df_display = pn.pane.Markdown(f"```python\n{active_wells_df}\n```")




# Function to update the total extraction value
def total_extraction_update():
    total_extraction.value = calculate_total_extraction()
    update_df_display()


# Create a layout for the sliders
slider_layout = pn.Column(*Sliders)

# Create a tab for the sidebar
tabs = pn.Tabs(("Well Capacities", slider_layout))

Box = pn.template.EditableTemplate(
    editable=True, title="Vitalens", sidebar=tabs, main=[total_extraction, df_display]
)


# Initial calculation of total extraction
calculate_total_extraction()

Box.servable()
