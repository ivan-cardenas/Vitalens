import panel as pn
from config.dataLoad import *
from config.initialization import *
from config.map import *
from config.utilities import *
from config.widgets import * 

# Initialize a dictionary to hold the active state and slider references
active_wells = {}

# Initialize a dictionary to hold the balance area layouts
balance_area_buttons = {}


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
    vmin=hexagons_filtered["Water Demand"].quantile(0.0),
    vmax=hexagons_filtered["Water Demand"].quantile(1),
    caption="Total water demand in Mm\u00b3/yr",
)

# Setup Widgets
radio_layout, active_wells = setup_widgets(wells, active_wells_df, update_indicators, update_layers, update_radio, update_well_Name, toggle_well)


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
map_pane = pn.pane.plot.Folium(update_layers(active_wells_df, popup_well,hexagons_filtered, colormap, popup_hex, balance_areas), sizing_mode="stretch_both")

total_extraction = pn.indicators.Number(
    name="Total Supply",
    value=calculate_total_extraction(active_wells_df),
    format="{value:.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="28pt",
    title_size="18pt",
    sizing_mode="stretch_width"
)

total_opex = pn.indicators.Number(
    name="Total OPEX",
    value=calculate_total_OPEX(active_wells_df),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="28pt",
    title_size="18pt",
    align="center",
    sizing_mode="stretch_width"
)

balance_opex = calculate_total_OPEX_by_balance(active_wells_df)
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
    value=calculate_available(active_wells_df),
    format="{value:0.2f} Mm\u00b3/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
    align="center",
    sizing_mode="stretch_width"
)

own_pane = pn.indicators.Number(
    name="Landownership",
    value=calculate_ownership(active_wells_df),
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
    value=calculate_affected_Natura(active_wells_df, hexagons_filtered),
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
    value=calculate_total_CO2_cost(active_wells_df),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)

drought_pane = pn.indicators.Number(
    name="Drought Damage Cost",
    value=calculate_total_Drought_cost(active_wells_df),
    format="{value:0,.2f} M\u20AC/yr",
    default_color='#3850a0',
    font_size="20pt",
    title_size="12pt",
)

# df_display = pn.pane.Markdown(update_df_display())
df_Hexagons = pn.pane.DataFrame(hexagons_filtered.head(), name="Hexagons data")

total_demand = pn.indicators.Number(
    name="Total Water Demand",
    value=calculate_total_Demand(hexagons_filtered),
    format="{value:0,.2f} Mm\u00b3/yr",
    font_size="28pt",
    title_size="18pt",
    default_color='#3850a0',
    sizing_mode="stretch_width"
)

lzh = pn.indicators.Gauge(
    name="Leveringszekerheid",
    value=calculate_lzh(active_wells_df, hexagons_filtered),
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
balance_lzh_values = calculate_lzh_by_balance(active_wells_df, hexagons_filtered)
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
    header_color= '#f2f2ed',
    sidebar_width = 320
)

def total_extraction_update(total_extraction, total_opex, excess_cap, own_pane, natura_pane, co2_pane, drought_pane, total_demand, lzh, map_pane, popup_well, colormap, popup_hex):
    total_extraction.value = calculate_total_extraction(active_wells_df)
    # df_display.object = update_df_display(active_wells_df)
    total_opex.value = calculate_total_OPEX(active_wells_df)
    total_demand.value = calculate_total_Demand(hexagons_filtered)
    update_balance_opex(active_wells_df,balance_opex_indicators)
    update_balance_lzh_gauges(balance_opex_indicators, active_wells_df, hexagons_filtered)
    update_indicators(total_extraction, total_opex, excess_cap, own_pane, natura_pane, co2_pane, drought_pane, total_demand, lzh, map_pane, balance_opex_indicators, balance_lzh_gauges, popup_well, colormap, popup_hex)
    natura_pane.value = calculate_affected_Natura(active_wells_df,hexagons_filtered)
    map_pane.object = update_layers(active_wells_df, popup_well,hexagons_filtered, colormap, popup_hex, balance_areas)
    co2_pane.value = calculate_total_CO2_cost(active_wells_df)
    drought_pane.value = calculate_total_Drought_cost(active_wells_df)

total_extraction_update(total_extraction, total_opex, excess_cap, own_pane, natura_pane, co2_pane, drought_pane, total_demand, lzh, map_pane, popup_well, colormap, popup_hex)

Box.servable()
