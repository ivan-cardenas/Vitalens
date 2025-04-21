import panel as pn
from config.data import wells, original_demand, original_OPEX, original_excess, original_CO2, original_Draught, active_wells_df, demand_capita, hexagons_filterd

from config.calculations import (calculate_total_extraction, calculate_total_Demand, calculate_difference,
calculate_available, calculate_total_OPEX, calculate_total_CAPEX, calculate_affected_Sensitive_Nature,
                                  calculate_affected_VerySensitive_Nature, calculate_total_CO2_cost, calculate_total_Drought_cost,
                                  calculate_lzh, calculate_lzh_by_balance, calculate_industrial_extract, 
                                  calculate_total_extraction, calculate_total_Demand, calculate_difference, calculate_total_OPEX,
                                  spacer, calculate_total_CAPEX, calculate_affected_Sensitive_Nature,
                                  calculate_affected_VerySensitive_Nature, calculate_total_CO2_cost, calculate_total_Drought_cost,
)
from config.svg_utils import generate_area_SVG, generate_pipes_SVG




# ------------------------------------------------------------------------------
# Indicators
# ------------------------------------------------------------------------------



total_supply = pn.indicators.Number(
    name="Total Supply", value=calculate_total_extraction(),
    format="{value:.2f} Mm³/yr", default_color="blue"
)

total_demand = pn.indicators.Number(
    name="Total Demand", value=calculate_total_Demand(),
    format="{value:.2f} Mm³/yr", default_color="green"
)
difference = pn.indicators.Number(
    name="Water Balance", value=calculate_difference(),
    format="{value:.2f} Mm³/yr", default_color="orange"
)
opex = pn.indicators.Number(
    name="Total OPEX", value=calculate_total_OPEX(),
    format="{value:.2f} M€/yr", default_color="purple"
)
capex = pn.indicators.Number(
    name="Total CAPEX", value=calculate_total_CAPEX(),
    format="{value:.2f} M€", default_color="red"
)

co2_cost = pn.indicators.Number(
    name="CO₂ Cost", value=calculate_total_CO2_cost(),
    format="{value:.2f} €/yr", default_color="black"
)
drought_cost = pn.indicators.Number(
    name="Drought Damage", value=calculate_total_Drought_cost(),
    format="{value:.2f} €/yr", default_color="black"
)

nature_sensitive = pn.indicators.Number(
    name="Sensitive Nature Damage (Ha)",
    value=calculate_affected_Sensitive_Nature(),
    format="{value:.2f}"
)
nature_very_sensitive = pn.indicators.Number(
    name="Very Sensitive Nature Damage (Ha)",
    value=calculate_affected_VerySensitive_Nature(),
    format="{value:.2f}"
)

lzh_gauge = pn.indicators.Gauge(
    name="Leveringszekerheid",
    value=calculate_lzh(),
    bounds=(0, 150),
    format="{value:.0f} %",
    colors=[(0.8, "red"), (0.95, "orange"), (1.2, "green")],
    height=200
)


# ------------------------------------------------------------------------------
# Layouts
# ------------------------------------------------------------------------------


total_extraction = pn.indicators.Number(
    name="Total Supply",
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
    name="Total Water Demand",
    value=calculate_total_Demand,
    format="{value:0,.2f} Mm\u00b3/jr",
    font_size="20pt",
    title_size="12pt",
    default_color='#3850a0',
    sizing_mode="scale_width", align='center',
    colors=[(original_demand - 0.1, '#92C25B'), (original_demand, '#3850a0'), (1000, '#D9534F')]
)

total_difference = pn.indicators.Number(
    name="Water Balance",
    value=calculate_difference(),
    format="{value:.2f} Mm\u00b3/jr",
    colors=[(0, '#d9534f'), (10, '#f2bf58'), (100, '#92c25b')],
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    sizing_mode="scale_width", align='center'
)

total_extraction_TT = pn.widgets.TooltipIcon(value="Total supply is calculated as the sum of volumes of raw water extracted from each location in a year. Total demand is calculated as the yearly consumption of potable water by residents and small businesses.")

total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width",
    colors=[(original_OPEX - 0.1, '#92C25B'), (original_OPEX, '#3850a0'), (1000, '#D9534F')]
)

total_opex_TT = pn.widgets.TooltipIcon(value="Total yearly Operational Expenditure.")

total_capex = pn.indicators.Number(
    name="Total CAPEX",
   value=calculate_total_CAPEX(),
    format="{value:0,.2f} M\u20AC",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width",
    colors=[(0, '#3850a0'), (1000, '#D9534F')]
)

total_capex_TT = pn.widgets.TooltipIcon(value="Total investment expenditure to expand the extraction capacity.")


excess_cap = pn.indicators.Number(
    name="Excess Capacity",
    value=calculate_available(),
    format="{value:0.2f} Mm\u00b3/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_excess-0.1, '#D9534F'), (original_excess, '#3850a0'),(1000, '#92C25B')]

)

excess_cap_TT = pn.widgets.TooltipIcon(value="Yearly available water that is not extracted from wells and is within the Maximum allowed extraction.")
excess_cap_row = pn.Row(excess_cap, excess_cap_TT)

industrial_extract = pn.indicators.Number(
    name="Industrial Water Extraction",
     value=calculate_industrial_extract(),
    format="{value:0.2f} Mm\u00b3/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)
industrial_extract_TT = pn.widgets.TooltipIcon(value="Estimated yearly groundwater extracted by big industries over which Vitens has no control")

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

natureDamage_TT = pn.widgets.TooltipIcon(value='This area correspont to the extent of drought sensitive groundwater dependent nature that might be affected due to groundwater extraction.')

# nature_title = pn.Row(natureMidDamage_value,natureDamage_TT, sizing_mode="scale_both" )

# Use pn.bind to dynamically bind the number of stars to the pane
keukenhofsMid = pn.bind(generate_area_SVG, natureMidDamage_value)
keukenhofsHigh = pn.bind(generate_area_SVG, natureHighDamage_value)
keuk_text = pn.pane.HTML("<p style='font-size: small;'>Represented in number of Keukenhof parks")
natura_pane = pn.Column(natureDamage_TT, natureHighDamage_value, spacer(10), keukenhofsHigh, natureMidDamage_value, spacer(10), keukenhofsMid, keuk_text, sizing_mode='scale_both')


pipes_TT = pn.widgets.TooltipIcon(value="Each icon represents the number of connections between two balance areas, this is an indicator of vulnerability in the system.")

pipes_pane = pn.Row(
    pipes_TT, 
    generate_pipes_SVG("Reggeland", "Stedenband", 1), 
    generate_pipes_SVG("Reggeland", "Hof van Twente", 2), 
    generate_pipes_SVG("Reggeland", "Dinkelland", 1), 
    generate_pipes_SVG("Hof van Twente", "Stedenband", 3), 
    generate_pipes_SVG("Dinkelland", "Stedenband", 1), 
)

co2_pane = pn.indicators.Number(
    name="CO\u2082 Emission Cost",
    value=calculate_total_CO2_cost(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_CO2 - 0.1, '#92C25B'), (original_CO2, '#3850a0'), (1000, '#D9534F')]
    )

drought_pane = pn.indicators.Number(
    name="Drought Damage Cost",
    value=calculate_total_Drought_cost(),
    format="{value:0,.2f} M\u20AC/jr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    colors=[(original_Draught - 0.1, '#92C25B'), (original_Draught, '#3850a0'), (1000, '#D9534F')]
)

lzh = pn.indicators.Gauge(
    name=f"Overall LZH",
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


# ----------------------------------------------------------
# Update Functions
# ----------------------------------------------------------
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
    



def update_balance_lzh_gauges():
    """
    Update Leveringszekerheid gauges for balance areas.
    """
    lzh_by_balance = calculate_lzh_by_balance()
    for area, gauge in balance_lzh_gauges.items():
        gauge.value = lzh_by_balance.get(area, 0)
        

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
    
    
# -------------------------------------------------------------
# Update Function for LZH 
# -------------------------------------------------------------

lzh.param.watch(update_indicators, "value")
lzh_definition = pn.pane.HTML("LZH: Leveringszekerheid, is an indicator of supply security. It is the percentage of drinking water demand that is covered by the supply")
lzh_tooltip = pn.widgets.TooltipIcon(value="LZH: Leveringszekerheid, is an indicator of supply security. It is the percentage of drinking water demand that is covered by the supply. You can see the LZH for each balance area by selecting the tabs on the right. This values assume a closed system.")

