# report.py

from config.data import active_wells_df
import config.printingReport as pr

# You can adjust these paths as needed
PNG_FILENAME = "wells_chart.png"

def create_report(
    population_selector,
    small_business_selector,
    toggle_small_wells,
    toggle_natura,
    toggle_import,
    toggle_smart,
    toggle_industry,
    demand_slider,
    total_demand_indicator,
    total_supply_indicator,
    opex_indicator,
    capex_indicator,
    co2_indicator,
    drought_indicator,
    nature_sensitive_indicator,
    nature_very_sensitive_indicator
):
    """
    Generate and export the full Vitalens PDF report using custom functions.

    Args:
        population_selector (pn.widgets.RadioButtonGroup): Scenario selector.
        small_business_selector (pn.widgets.RadioButtonGroup): Small business growth selector.
        toggle_small_wells, toggle_natura, toggle_import,
        toggle_smart, toggle_industry (pn.widgets.Toggle): Measure toggles.
        demand_slider (pn.widgets.FloatSlider): Water demand slider in L/day.
        total_demand_indicator, total_supply_indicator,
        opex_indicator, capex_indicator, co2_indicator, drought_indicator (pn.indicators.Number): Value indicators.
        nature_sensitive_indicator, nature_very_sensitive_indicator (pn.indicators.Number): Environmental indicators.

    Returns:
        str: Path to the generated PDF.
    """

    # 1. Generate styled wells table and save as image
    pr.styledWells(active_wells_df)

    # 2. Generate matplotlib line/bar chart for extraction
    pr.generate_matplotlib_stackbars(active_wells_df, PNG_FILENAME)

    # 3. Generate the PDF report
    pr.createPDF(
        filename1=PNG_FILENAME,
        popScenario=population_selector,
        smallScenario=small_business_selector,
        button3=toggle_small_wells,
        button4=toggle_natura,
        button6=toggle_import,
        button7=toggle_industry,
        ButtonDemand=demand_slider,
        TotalDemand=total_demand_indicator,
        totalSupply=total_supply_indicator,
        OPEX=opex_indicator,
        CAPEX=capex_indicator,
        CO2=co2_indicator,
        ENVDmg=drought_indicator,
        Natura=nature_sensitive_indicator,
        natureHighDamage_value=nature_very_sensitive_indicator,
    )

    print("PDF report saved as Vitalens_report.pdf")
    return "Vitalens_report.pdf"
