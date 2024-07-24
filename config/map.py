import folium
import json
from shapely.geometry import Polygon
import geopandas as gpd
from config.utilities import update_indicators

# Function to Display map   
def update_layers(active_wells_df, popup_well,hexagons_filtered, colormap, popup_hex, balance_areas):
    m = folium.Map(
    location=[52.38, 6.7], zoom_start=10,
    tiles="Cartodb Positron"
    ) 
     # Adjust the center and zoom level as necessary
    active = active_wells_df[active_wells_df["Active"]==True]
    
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

    hex = folium.GeoJson(
        hexagons_filtered,
        name="Hexagons",
        style_function=lambda x: {
            "fillColor": (
                colormap(x["properties"]["Water Demand"])
                if x["properties"]["Water Demand"] is not None
                else "transparent"
            ),
             "color": (
                "darkgray"
                if x["properties"]["Balance Area"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        popup=popup_hex,
    ).add_to(m)

    m.add_child(colormap)

    folium.GeoJson(
        hexagons_filtered,
        name="Natura2000 Restricted Area",
        style_function=lambda x: {
            "fillColor": (
                "darkred"
                if x["properties"]["Type"] == "Restricted Natura2000"
                else "transparent"
            ),
            "color": (
                "darkgray"
                if x["properties"]["Balance Area"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        }, 
        show= False,
    ).add_to(m)

    folium.GeoJson(
        hexagons_filtered,
        name="Restricted NNN",
        style_function=lambda x: {
            "fillColor": (
                "#f9aaa2"
                if x["properties"]["Type"] == "Restricted Other"
                else "transparent"
            ),
             "color": (
                "darkgray"
                if x["properties"]["Balance Area"] is not None
                else "transparent"
                ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        show= False,
    ).add_to(m)
    
    folium.GeoJson(
        balance_areas,
        name="Balance Areas",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#ce9ad6",
            "weight": 3
        },
        show=True,
        tooltip=folium.GeoJsonTooltip(fields=['Balance Area'], labels=True)
    ).add_to(m)
    
    folium.LayerControl().add_to(m)

    return m