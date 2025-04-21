# calculations.py

import numpy as np
import panel as pn
from scipy.optimize import curve_fit

from config.data import (
    active_wells_df,
    industrial,
    hexagons_filterd,
    naturaDamageMid,
    naturaDamageHigh,
    demand_capita,
    smallBusiness, industrialExcess)



# ---------------------------------------------------------
# Core Calculations
# ---------------------------------------------------------


def calculate_total_extraction():
    """Total water extracted from active wells (Mm³/yr)."""
    return active_wells_df[active_wells_df["Active"]]["Value"].sum() + industrialExcess


def calculate_total_Demand():
    """Total demand across all hexagons (Mm³/yr)."""
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1000000
    
    total = ((hexagons_filterd["Water Demand"]).sum()) + (
        (hexagons_filterd["Industrial Demand"]).sum()
    )
    return total


def calculate_difference():
    """Supply minus demand (Mm³/yr)."""
    return calculate_total_extraction() - calculate_total_Demand()


def calculate_available():
    """Permitted but unused capacity (Mm³/yr)."""
    total = (
        active_wells_df["Max_permit"].sum()
        - active_wells_df[active_wells_df["Active"]==True]["Value"].sum()
    ) 
    return total


def calculate_industrial_extract():
    """Industrial water extraction from separate dataset (Mm³/yr)."""
    return industrial["Current_Extraction_2019"].sum()


def calculate_ownership():
    """% of owned wells out of total active."""
    df = active_wells_df[active_wells_df["Active"]]
    if df["Num_Wells"].sum() == 0:
        return 0
    return (df["Ownership"].sum() / df["Num_Wells"].sum()) * 100

# ---------------------------------------------------------
# Financial Calculations
# ---------------------------------------------------------

def calculate_total_OPEX():
    """Total OPEX across all active wells (EUR/yr)."""
    active_wells_df["OPEX"] = active_wells_df["OPEX_m3"] * active_wells_df["Value"] 

    total = (active_wells_df[active_wells_df["Active"]]["OPEX"]).sum()
    return total


def calculate_total_CAPEX():
    active_wells_df["CAPEX"] = np.where(
        active_wells_df["Value"] > active_wells_df["Current Extraction"],
        (active_wells_df["Value"] - active_wells_df["Current Extraction"]) * 10,  # You can adjust the multiplier as needed
        0  # CAPEX is 0 if Value is less than or equal to current extraction
    )

    # Sum the CAPEX for all active wells
    total = active_wells_df[active_wells_df["Active"]]["CAPEX"].sum()
    return total   


def calculate_total_OPEX_by_balance():
    """OPEX grouped by balance area (million EUR/yr)."""
    return (
        active_wells_df[active_wells_df["Active"]].groupby("Balance area")["OPEX"].sum()
    )/1e6


# ---------------------------------------------------------
# Environmental Costs
# ---------------------------------------------------------

def calculate_total_envCost():
    """Environmental costs (EUR/yr)."""
    return active_wells_df[active_wells_df["Active"]]["envCost"].sum()


def calculate_total_envCost_by_balance():
    """Environmental cost grouped by balance area."""
    return (
        active_wells_df[active_wells_df["Active"]]
        .groupby("Balance area")["envCost"]
        .sum()
    )


# ---------------------------------------------------------
# Damage Estimation
# ---------------------------------------------------------

def log_func(x, a, b):
    """Logarithmic damage estimation function."""
    return a * np.log(x) + b


def estimate_Damage_for_well(damage_df, well_name, target_percentage):
    """Estimate environmental damage based on extraction ratio."""
    row = damage_df[damage_df["Name"] == well_name]
    if row.empty:
        return 0

    row = row.iloc[0].drop("Name").dropna()
    if len(row) < 2:
        return 0

    try:
        x = [float(col) for col in row.index]
        y = row.values
        popt, _ = curve_fit(log_func, x, y)
        return log_func(target_percentage, *popt)
    except Exception:
        return 0


def calculate_affected_Sensitive_Nature():
    """Damage to moderately sensitive nature areas (Ha)."""
    names = active_wells_df[active_wells_df["Active"]==True]
    
    midDamage = 0
    
    for index, row in names.iterrows():
        name = row["Name"]
        target = (row["Value"]/row["Max_permit"])*100
        mDamage = estimate_Damage_for_well(naturaDamageMid, name, target) or 0

    
        midDamage = midDamage + mDamage
    return midDamage


def calculate_affected_VerySensitive_Nature():
    """Damage to highly sensitive nature areas (Ha)."""
    names = active_wells_df[active_wells_df["Active"]==True]
    
    midDamage = 0
    for index, row in names.iterrows():
        name = row["Name"]
        target = (row["Value"]/row["Max_permit"])*100
        mDamage = estimate_Damage_for_well(naturaDamageHigh, name, target) or 0
    
        midDamage = midDamage + mDamage

    return midDamage

# ---------------------------------------------------------
# Supply/Demand by Balance Area
# ---------------------------------------------------------

def calculate_demand_by_balance():
    """Demand per balance area."""
    return (
        hexagons_filterd
        .groupby("Balance Area")[["Water Demand", "Industrial Demand"]]
        .sum()
    )


def calculate_lzh():
    """Overall Leveringszekerheid (delivery security) [%]."""
    demand = calculate_total_Demand()
    if demand == 0:
        return 0
    return round((calculate_total_extraction() / demand) * 100, 2)


def calculate_lzh_by_balance():
    """Delivery security (LZH) per balance area [%]."""
    lzh_by_balance = {}
    for area in active_wells_df["Balance area"].unique():
        total_extraction = active_wells_df[
            active_wells_df["Balance area"] == area
        ]["Value"].sum()
        total_demand = hexagons_filterd[
            hexagons_filterd["Balance Area"] == area
        ]["Water Demand"].sum()
        lzh_by_balance[area] = round((total_extraction / total_demand) * 100, 2) if total_demand else 0
    return lzh_by_balance


# ---------------------------------------------------------
# CO2 / Drought Cost Calculations
# ---------------------------------------------------------

def calculate_total_CO2_cost():
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    active_wells["CO2_Cost"] = active_wells_df["Value"] * active_wells_df["CO2_m3"]
    total_environmental_cost = active_wells["CO2_Cost"].sum()
    return total_environmental_cost


def calculate_total_Drought_cost():
    active_wells = active_wells_df[active_wells_df["Active"] == True]
    active_wells["Drought_Cost"] = (
        active_wells_df["Value"] * active_wells_df["Drought_m3"]
    )
    total_environmental_cost = active_wells["Drought_Cost"].sum()
    return total_environmental_cost


# ---------------------------------------------------------
# update indicators
# ---------------------------------------------------------

def spacer(size):
    spacerVertical = pn.Spacer(height=size)
    return spacerVertical

def update_df_display():
    """
    Update the DataFrame display.

    Returns:
        str: The updated DataFrame as a string.
    """
    return f"```python\n{active_wells_df}\n```"



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
    



        



