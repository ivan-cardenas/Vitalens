import panel as pn
from functools import partial
import pandas as pd
from config.dataLoad import *
from config.utilities import update_indicators

# Function to update the title of the Box
def update_title(new_title, app_title):
    content = '## ' + new_title
    app_title.object = content

# Function to create Scenarios
def Scenario1(event):
    demand_capita = 0.156*1.1
    hexagons_filtered["Water Demand"] = (
        hexagons_filtered["Current Pop"] * demand_capita * 365
    ) / 1000000
    update_title("VITALENS - Autonumos Growth")
    update_indicators()  # Update the total demand indicator
    

def Scenario2(event):
    demand_capita = 0.156*1.35
    hexagons_filtered["Water Demand"] = (
        hexagons_filtered["Current Pop"] * demand_capita * 365
    ) / 1000000
    update_title("VITALENS - Accelerated Growth")
    update_indicators()  # Update the total demand indicator
    
    
def Scenario3(event):
    active_wells_df.loc[active_wells_df["Max_permit"] <= 5, "Active"] = False
    update_title("VITALENS - Closed Wells")
    update_indicators()
    
    
def Reset(event):
    demand_capita = 0.156
    hexagons_filtered["Water Demand"] = (
        hexagons_filtered["Pop2022"] * demand_capita * 365
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
    update_indicators()  # Update the total demand indicator
    update_title("VITALENS - Current Situation")










def setup_widgets(wells, active_wells_df, update_indicators, update_layers, update_radio, update_well_Name, toggle_well):
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

    active_wells = {}
    balance_area_buttons = {}
    options = ["-10%", "-20%", "Current", "+10%", "+20%", "Maximum Permit", "Agreement"]

    for index, row in wells.iterrows():
        wellName = row["Name"]
        current_value = row["Extraction_2023__Mm3_per_jr_"]
        balance_area = row["Balansgebied"]
        radio_group = pn.widgets.RadioButtonGroup(name=wellName, options=options, button_type='success', value="Current")

        checkbox = pn.widgets.Checkbox(name="Active", value=True)
        checkbox.param.watch(partial(toggle_well, well_name=wellName, active_wells_df=active_wells_df, update_indicators=update_indicators, update_layers=update_layers), "value")
        radio_group.param.watch(partial(update_radio, well_name=wellName, active_wells_df=active_wells_df, update_well_Name=update_well_Name, update_indicators=update_indicators), "value")

        NameP = pn.pane.Str(wellName, styles={'font-size': "14px", 'font-family': "Barlow", 'font-weight': 'bold'})
        NamePane = pn.pane.Str(update_well_Name(wellName, active_wells_df), styles={'font-family': 'Roboto'})
        NameState = pn.Row(NameP, pn.Spacer(), checkbox)
        Well_radioB = pn.Column(NameState, NamePane, radio_group, styles=miniBox_style)

        if balance_area not in balance_area_buttons:
            balance_area_buttons[balance_area] = []
        balance_area_buttons[balance_area].append(Well_radioB)

        active_wells[wellName] = {"active": True, "value": current_value, "radio_group": radio_group, "name_pane": NamePane}

    radio_layout = pn.Accordion(styles={'width': '97%', 'color':'#151931'})
    for balance_area, layouts in balance_area_buttons.items():
        balance_area_column = pn.Column(*layouts)
        radio_layout.append((balance_area, balance_area_column))

    return radio_layout, active_wells