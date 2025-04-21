# measures.py

from config.data import active_wells_df, industrial, hexagons_filterd, smallBusiness, checkboxes
from config.map_utils import m
from shapely.geometry import Point
import geopandas as gpd
import folium

# Track if industrial excess is being added
industrial_excess = 0

def Measure1On():
    # Update the 'Active' column where 'Max_permit' is less than 5.00
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = False
    
    # Uncheck checkboxes corresponding to the wells that meet the condition
    for well_name in active_wells_df.loc[condition, "Name"]:
        checkboxes[well_name].value = False


def Measure1Off():
    # Update the 'Active' column where 'Max_permit' is less than 5.00
    condition = active_wells_df["Max_permit"] < 5.00
    active_wells_df.loc[condition, "Active"] = True
    
    # Uncheck checkboxes corresponding to the wells that meet the condition
    for well_name in active_wells_df.loc[condition, "Name"]:
        try:
            checkboxes[well_name].value = True
        except: continue
        
def Measure2On():
    """Turn OFF wells located in Natura2000 zones."""
    for name in ["Archemerberg", "Nijverdal"]:
        active_wells_df.loc[active_wells_df["Name"] == name, "Active"] = False
    print("Closed Natura2000 wells")
    
     # Update the checkboxes to reflect the new state
    checkboxes["Archemerberg"].value = False
    checkboxes["Nijverdal"].value = False


def Measure2Off():
    """Turn ON Natura2000 wells again."""
    for name in ["Archemerberg", "Nijverdal"]:
        active_wells_df.loc[active_wells_df["Name"] == name, "Active"] = True
    print("Reopened Natura2000 wells")

     # Update the checkboxes to reflect the new state
    checkboxes["Archemerberg"].value = True
    checkboxes["Nijverdal"].value = True

def Measure3On(ButtonDemand):
    """
    Activate the third measure (using smart meters).
    """
    global demand_capita
    demand_capita  = ButtonDemand.value/1000 * 0.95
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6

def Measure3Off(ButtonDemand):
    """
    Deactivate the third measure (using smart meters).
    """
    global demand_capita
    demand_capita  = ButtonDemand.value/1000
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6


def Measure4On():
    """Add an artificial import well with fixed extraction."""
    new_geometry = Point(253802.6, 498734.2)  # reuse any valid geometry
    active_wells_df.loc[active_wells_df.index.max() + 1] = {
        "Name": "Imports",
        "Num_Wells": 3,
        "Ownership": 0,
        "Max_permit": 4.5,
        "Balance area": "Imported",
        "Active": True,
        "Current Value": 4.38,
        "Value": 4.38,
        "OPEX_m3": 0.0598173515981735,
        "Drought_m3": 0,
        "CO2_m3": 0,
        "Env_m3": 0,
        "envCost": 0,
        "OPEX": 0.262,
        "geometry": new_geometry
    }

    # Select the newly added well for visualization
    new_well = active_wells_df.loc[active_wells_df["Name"] == 'Imports']

    # Convert the selected well into a GeoDataFrame and create the GeoJSON representation.
    new_well_gdf = gpd.GeoDataFrame(new_well, geometry='geometry')
    new_well_gdf = new_well_gdf.to_json()

    # Add the new well as a GeoJson object on the map
    folium.GeoJson(
        new_well_gdf,
        name="Import Water",
        zoom_on_click=True,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#f3f3f3", icon="arrow-up-from-ground-water", prefix="fa", color='cadetblue'
            )
        ),
        show=True
    ).add_to(m)


def Measure4Off():
    """Remove the artificial import well."""
    try:  
        # Use .loc to identify rows where 'Name' is 'Imports' and drop them
        active_wells_df.drop(active_wells_df.loc[active_wells_df["Name"] == 'Imports'].index, inplace=True)     
    except KeyError:
        print("Row does not exist")

def Measure5On():
    """Add industrial excess volume to supply."""
    global industrialExcess
    industrialExcess = industrial["Licensed"].sum()-industrial["Current_Extraction_2019"].sum()
    print(f"Industrial excess added: {industrial_excess:.2f} Mm³/yr")


def Measure5Off():
    """Remove industrial excess from supply."""
    global industrial_excess
    industrial_excess = 0
    print("Industrial excess removed")


def get_industrial_excess():
    """Get the current industrial excess amount."""
    return industrial_excess


