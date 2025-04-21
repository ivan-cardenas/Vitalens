# ui.py

import panel as pn
from functools import partial

import config.printingReport as pr

from config.config import * # Ensures Panel is configured


from config.data import checkboxes, active_wells_df, active_wells, balance_area_buttons, wells, hexagons_filterd,industrial
from config.calculations import *
from config.Text_ui import *
from config.indicators import *
from config.map_utils import update_layers
from config.scenarios import *
from config.measures import *

pn.extension()

# ---------------------------------------------------------
# Update display functions
# ---------------------------------------------------------

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
    if event.new == "-15% of Current":
        new_value = current_value * 0.85
    elif event.new == "Current":
        new_value = current_value
    elif event.new == "85% of Max. Permit":
        new_value = max_value * 0.85
    elif event.new == "115% of Max. Permit":
        new_value = max_value * 1.15
    elif event.new == "Maximum Permit":
        new_value = max_value
    else: new_value = 100
    print (new_value)
   
   
    pn.state.notifications.position = 'bottom-left'

    if new_value > max_value:
          pn.state.notifications.error(f"Warning on {well_name} well: This value is avobe the extraction permit. Using this value would require negotiation a larger water extraction permit.", 4000)
    
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

active_scenarios = set()
text = ["## Scenario"]

def update_title(event):
    global text
    text = list(text)

    # Small wells toggle
    if ButtonSmallWells.value:
        if "Small Wells Closed" in text:
            print("Text is already there")
        else:
            text.append("Small Wells Closed")
            Measure1On()
    else:
        Measure1Off()
        if "Small Wells Closed" in text:
            text.remove("Small Wells Closed")
        else:
            print("Text is not there")

    # Natura wells toggle
    if ButtonCloseNatura.value:
        if "Natura Wells Closed" in text:
            print("Text is already there")
        else:
            text.append("Natura Wells Closed")
            Measure2On()
    else:
        Measure2Off()
        if "Natura Wells Closed" in text:
            text.remove("Natura Wells Closed")
        else:
            print("Text is not there")

    # Smart meter usage toggle
    if ButtonSmartMeter.value:
        if "Use of Smart Meters" in text:
            print("Text is already there")
        else:
            text.append("Use of Smart Meters")
            Measure3On(ButtonDemand)
    else:
        Measure3Off(ButtonDemand)
        if "Use of Smart Meters" in text:
            text.remove("Use of Smart Meters")
        else:
            print("Text is not there")

    # Water import toggle
    if ButtonImportWater.value:
        if "Import Water" in text:
            print("Text is already there")
        else:
            text.append("Import Water")
            Measure4On()
    else:
        Measure4Off()
        if "Import Water" in text:
            text.remove("Import Water")
        else:
            print("Text is not there")

    # Extra industrial capacity toggle
    if ButtonAddExtraIndustrial.value:
        if "Use Industrial Overcapacity" in text:
            print("Text is already there")
        else:
            text.append("Use Industrial Overcapacity")
            Measure5On()
    else:
        Measure5Off()
        if "Use Industrial Overcapacity" in text:
            text.remove("Use Industrial Overcapacity")
        else:
            print("Text is not there")

    # Update title and indicators
    text = tuple(text)
    app_title.object = " - ".join(text)
    print(text)
    update_indicators()


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

# ------------------------------------------------------------------------------
# Interactive Controls
# ------------------------------------------------------------------------------



# Setup Well Radio Buttons
Radio_buttons = []
Well_radioB = []
options = ["-15% of Current", "Current", "85% of Max. Permit", "Maximum Permit", "115% of Max. Permit"]

for index, row in wells.iterrows():
    wellName = row["Name"]
    current_value = row["Extraction_2023__Mm3_per_jr_"]
    maxValue =  row["Permit__Mm3_per_jr_"]
    balance_area = row["Balansgebied"]
    radio_group = pn.widgets.RadioButtonGroup(
        name=wellName,
        options=options,
        button_type='success',
        value="Current",
        orientation = "vertical"
    )
    
    # Add Checkbox and listeners
    checkbox = pn.widgets.Switch(name="Active", value=True, max_width=20)
    checkbox.param.watch(partial(toggle_well, well_name=wellName), "value")
    radio_group.param.watch(partial(update_radio, well_name=wellName), "value")
    
    # Store the checkbox in the dictionary for later updates
    checkboxes[wellName] = checkbox
    
    NameP = pn.pane.Str(wellName + f"\nCurrent operation at {(current_value/maxValue)*100:0.2f}%", styles={
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
        value="Current",
        orientation = "vertical"
    )
all_wellsButton.param.watch(update_allRadio,"value")

# Create a layout for the radio buttons
radioButton_layout = pn.Accordion(styles={'width': '95%', 'color':'#151931'})
for balance_area, layouts in balance_area_buttons.items():
    balance_area_column = pn.Column(*layouts)
    radioButton_layout.append((balance_area, balance_area_column))
    

    
Scenario_Button =pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['Population - 2022','Population 2035','Population 2035 +1% increase'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }, orientation='vertical'
                                             )
Scenario_Button.param.watch(update_scenarios, "value")

ScenarioSmall_Button = pn.widgets.RadioButtonGroup(name="Measures Button Group", options=['State - 2022','Small Business +10% Demand','Small Business +35% Demand'], button_type='warning', styles={
    'width': '93%', 'border': '3px' }, orientation='vertical'
                                             )
ScenarioSmall_Button.param.watch(update_scenariosSmall, "value")

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


# Button5= pn.Row(ButtonDemand, align=("center", "center"))

ButtonImportWater = pn.widgets.Toggle(
    name='Import Water', button_type="primary", button_style="outline", width=300, margin=10)
ButtonImportWater.param.watch(update_title, 'value')

ButtonAddExtraIndustrial = pn.widgets.Toggle(name="Add Industrial water",  button_type="primary", button_style="outline", width=300, margin=10,)
ButtonAddExtraIndustrial.param.watch(update_title, 'value')

ButtonSmartMeter = pn.widgets.Toggle(name="Use Smart Meters", button_type='primary', button_style='outline', width=300, margin=10)
ButtonSmartMeter.param.watch(update_title, 'value')

ButtonReset = pn.widgets.Button(
    name='Reset', button_type='danger', width=300, margin=10
)


file_create = pn.widgets.Button(name='Create Report', button_type='primary', width=300, margin=10,)

file_download = pn.widgets.FileDownload(file="Vitalens_report.pdf", button_type="primary" , width=300, margin=10,)

# Create a spinner
spinner = pn.indicators.LoadingSpinner(width=30, height=30, value=False)



# create a disclaimer
flaotingDisclaimer = pn.layout.FloatPanel(disclaimer, name= "Welcome", margin=20, contained=False, position="center") 


# ------------------------------------------------------------------------------
# Layouts   
# ------------------------------------------------------------------------------
scenario_layout = pn.Column(textScenarioPop, Scenario_Button, textDivider3, ScenarioSmall_Button, textEnd, ButtonReset, width=320)

Supply_measures_layout = pn.Column(textMeasureSupp, ButtonSmallWells,textCloseNatura, ButtonCloseNatura, textImport, ButtonImportWater,  textIndustrial, ButtonAddExtraIndustrial, textEnd, ButtonReset, width=320)

Demand_measures_layout = pn.Column(textMeasureDemand, ButtonDemand, textDivider0, textSmartM, ButtonSmartMeter, textEnd, ButtonReset, width = 320)

firstColumn = pn.Column(balance_area_Text,radioButton_layout)
secondColumn = pn.Column(file_create, spinner, file_download)

# ------------------------------------------------------------------------------
# Map Pane
# ------------------------------------------------------------------------------
map_pane = pn.pane.plot.Folium(update_layers(), sizing_mode="stretch_both")

minusSVG= pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M6 12L18 12" stroke="#4139a7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')

equalSVG = pn.pane.SVG('<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M3 8C2.44772 8 2 8.44772 2 9C2 9.55228 2.44772 10 3 10H21C21.5523 10 22 9.55228 22 9C22 8.44772 21.5523 8 21 8H3Z" fill="#4139a7"></path> <path d="M3 14C2.44772 14 2 14.4477 2 15C2 15.5523 2.44772 16 3 16H21C21.5523 16 22 15.5523 22 15C22 14.4477 21.5523 14 21 14H3Z" fill="#4139a7"></path> </g></svg>', max_width=40,sizing_mode='stretch_width', align='center')


# ------------------------------------------------------------------------------
# Results Box
# ------------------------------------------------------------------------------



def printResults(filename1):
    print("Button clicked, generating report...")
    pr.styledWells(active_wells_df)
    pr.generate_matplotlib_stackbars(active_wells_df, filename1)
    print("Image Created")
    pr.createPDF(filename1, Scenario_Button, ScenarioSmall_Button, ButtonSmallWells, ButtonCloseNatura, ButtonImportWater, ButtonAddExtraIndustrial, ButtonDemand,total_demand,total_extraction,total_opex,total_capex, co2_pane,drought_pane,natureMidDamage_value, natureHighDamage_value)
    return print("File Created")

# When clicking the button, show the spinner and run the function
def on_button_click(event):
    spinner.value = True  # Show the spinner
    printResults("./Assets/images/wells_Distribution.png")
    spinner.value = False  # Hide the spinner when done
    # pr.generate_image_fromInd(pane=lzh, filename=filename2)
    pn.state.notifications.position = 'bottom-left'
    pn.state.notifications.success('Report File created, you can download it now', duration=4000)


file_create.on_click(on_button_click)

# ------------------------------------------------------------------------------
# Environmental Indicators
# ------------------------------------------------------------------------------

# lzhTabs = pn.Tabs(lzh, *balance_lzh_gauges.values(), align=("center", "center"))
Env_pane = pn.Column(co2_pane, drought_pane)

# indicatorsArea = pn.GridSpec(sizing_mode="scale_both")
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
Map_help = pn.widgets.TooltipIcon(value="The data represented in this map is static. I.e. it does not change when changing the widgets on the left side of the app. It represents population data from Dec-2022 and the water extraction from 2023 \n\nThe Balance Areas, represent areas inside the Overijssel Zuid Cluster that are fed directly by at least a production site and are linked to another balance area for dynamic water distribution.", width = 10, align='end')

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


tabTop = pn.Tabs(("1. Scenarios", scenario_layout), ("2. Supply", Supply_measures_layout), ("3. Demand", Demand_measures_layout), width = 320)
tabBottom = pn.Tabs(("4. Well Capacities", firstColumn), ("5. Generate Report", secondColumn), width = 320)

tabs = pn.Column(tabTop, tabBottom, sizing_mode="scale_height")

# ------------------------------------------------------------------------------
# Application restructure
# ------------------------------------------------------------------------------


def Reset(event):
    """
    Reset the application to its initial state.

    Args:
        event: The event object.
    """
    demand_capita = 0.135
    smallBusiness = 1.2
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
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
    Scenario_Button.value = 'Population - 2022'
    ScenarioSmall_Button.value = 'State - 2022'
    ButtonDemand.value = 135
    ButtonSmallWells.value, ButtonCloseNatura.value, ButtonImportWater.value, ButtonSmartMeter.value, ButtonDemand.value = False, False, False, False, 135
    update_scenarioTitle("State - 2022")
    update_indicators()


ButtonReset.on_click(Reset)


# -----------------------------------------------------------------------------
# # Build the UI
# -----------------------------------------------------------------------------

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

def build_ui():
    Box = pn.template.MaterialTemplate(
    title="Vitalens",
    #logo="https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png",
    sidebar=[tabs],
    main=[main1],
    header_background= '#3850a0',
    header_color= '#f2f2ed',
    sidebar_width = 350,
    collapsed_sidebar = False,
)
    Box.main.append(flaotingDisclaimer)
    
    return Box
    

