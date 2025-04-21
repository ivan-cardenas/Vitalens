# map_utils.py

import folium
import branca
from folium.features import DivIcon

from config.data import (
    active_wells_df,
    industrial,
    cities_clean,
    hexagons_filterd,
    main_pipes,
    balance_areas
)

# ------------------------------------------------------------------------------
# Base Map Generator
# ------------------------------------------------------------------------------

m = folium.Map(
    location=[52.28, 6.7], zoom_start=10,
    tiles="Cartodb Positron"
)


# ------------------------------------------------------------------------------
# Popup Templates
# ------------------------------------------------------------------------------

popup_well = folium.GeoJsonPopup(
    fields=["Name", "Balance area", "Value"],
    aliases=["Well Name", "Balance Area", "Extraction (Mm³/yr)"]
)

popup_industrial = folium.GeoJsonPopup(
    fields=["Place", "Licensed", "Current_Extraction_2019"],
    aliases=["Place", "Licensed Extraction", "Current Extraction (Mm³/yr)"]
)

popup_city = folium.GeoJsonPopup(
    fields=["cityName", "Water Demand", "Population 2022"],
    aliases=["City", "Water Demand (Mm³/yr)", "Population"]
)


# ------------------------------------------------------------------------------
# Style Helpers
# ------------------------------------------------------------------------------

def style_hexagon(feature):
    demand = feature["properties"].get("Water Demand", 0)
    if demand is None:
        return {"fillOpacity": 0, "color": "transparent"}

    colormap = branca.colormap.StepColormap(
        colors=["#caf0f8", "#90e0ef", "#00b4d8", "#0077b6", "#03045e"],
        vmin=0, vmax=10,
        index=[0, 2, 4, 6, 8, 10],
        caption="Water Demand (Mm³/yr)"
    )
    return {
        "fillColor": colormap(demand),
        "color": "gray",
        "fillOpacity": 0.7,
        "weight": 0.5,
    }


def style_pipeline(feature):
    diameter = feature["properties"].get("Diameter_mm", 0)
    weight = 1 if diameter < 250 else (2 if diameter <= 350 else 4)
    return {"color": "#E27D79", "weight": weight, "opacity": 0.6}


def style_natura(feature):
    t = feature["properties"].get("Type", "")
    if t == "Restricted Natura2000":
        return {"fillColor": "darkgreen", "color": "green", "fillOpacity": 0.6, "weight": 0.4}
    elif t == "Restricted Other":
        return {"fillColor": "#CAFAA2", "color": "green", "fillOpacity": 0.4, "weight": 0.3}
    else:
        return {"fillOpacity": 0}


# ------------------------------------------------------------------------------
# Map Layer Updater
# ------------------------------------------------------------------------------


def update_layers(wellsLayer=active_wells_df, industryLayer=industrial):
    """
    Update the layers on the map.

    Returns:
        folium.Map: Updated Folium map.
    """
    global m
    
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap",
                     show=False).add_to(m)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', name="Satellite Imagery", 
                     attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community", show=False).add_to(m)
    
    popup_well = folium.GeoJsonPopup(
        fields=["Name", "Balance area", "Value"],
        aliases=["Naam Put", "Balansgebied", "Onttrekking in Mm³/jr"],
    )

    popup_hex = folium.GeoJsonPopup(
        fields=["cityName", "Water Demand", "Population 2022"],
        aliases=["Stadsnaam", "Watervraag in Mm³/jr", "Bevolking - 2022"]
    )

    popup_industrial = folium.GeoJsonPopup(
        fields=["Place", "Licensed", "Current_Extraction_2019"],
        aliases=["Locatie", "Vergunde Onttrekking in Mm³/jr", "Huidige Onttrekking in Mm³/jr"]
    )

    
    colormap = branca.colormap.StepColormap(
        ["#caf0f8", "#90e0ef", "#00b4d8", "#0077b6", "#03045e"],
        vmin=round(hexagons_filterd["Water Demand"].quantile(0.0),1),
        vmax=round(cities_clean["Water Demand"].quantile(1),1),
        caption="Totale watervraag in Mm\u00b3/yr",
    )
    
    active = wellsLayer[wellsLayer["Active"] == True]
    
    folium.GeoJson(
        active,
        name="Winningputten",
        zoom_on_click=True,
        popup=popup_well,
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Well Name:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#f3f3f3", icon="arrow-up-from-ground-water", prefix="fa", color='cadetblue'
            )
        ),
    ).add_to(m)
    
    folium.GeoJson(
        industryLayer,
        name="Industriële Waterwinning",
        zoom_on_click=True,
        popup=popup_industrial,
        tooltip=folium.GeoJsonTooltip(fields=["Place"], aliases=["Place:"]),
        marker=folium.Marker(
            icon=folium.Icon(
                icon_color="#d9534f", icon="industry", prefix="fa", color='lightred'
            )
        ),

    ).add_to(m)
    
    hex_layer = folium.GeoJson(
        cities_clean,
        name="Stadsvraag",
        style_function=lambda x: {
            "fillColor": (
                colormap(x["properties"]["Water Demand"])
                if x["properties"]["Water Demand"] is not None
                else "transparent"
            ),
            "color": (
                "darkgray"
                if x["properties"]["cityName"] is not None
                else "transparent"
            ),
            "fillOpacity": 0.8,
            "weight": 0.7,
        },
        popup=popup_hex,
    ).add_to(m)

    folium.GeoJson(
        main_pipes,
        name="Hoofdleidingen",
        style_function=lambda x: { 
            "color": "#E27D79",
            "weight": (4 if x["properties"]["Diameter_mm"] > 350
                       else (2 if x["properties"]["Diameter_mm"] > 250
                       else 1)),
            "Opacity": 0.6,
        },
        show=False
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Natura2000 Beperkt Gebied",
        style_function=lambda x: {
            "fillColor": (
                "darkgreen"
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
        show=False,
    ).add_to(m)

    folium.GeoJson(
        hexagons_filterd,
        name="Beperkt Natuurnetwerk Nederland",
        style_function=lambda x: {
            "fillColor": (
                "#CAFAA2"
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
        show=False,
    ).add_to(m)
    
    folium.GeoJson(
        balance_areas,
        name="Balansgebieden",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#93419F",
            "weight": 3
        },
        show=True,
        tooltip=folium.GeoJsonTooltip(fields=['Balance Area'], labels=True)
    ).add_to(m)
    
    BA_4326 = balance_areas.to_crs(4326)
    BA_4326["centroid"] = BA_4326.centroid
    
    
    
    for _, r in BA_4326.iterrows():
        lat = r["centroid"].y
        lon = r["centroid"].x
        name = r["Balance Area"]
        folium.Marker(
        location=[lat, lon],
        icon=DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html='<div class="Label" style="font-size: 12pt; color: #F29544; text-align: center;"><b>Balansgebied \n{name}</b></div>'.format(name=name),)
        ).add_to(m)
     
    # cities_4326 = cities_clean.to_crs(4326)   
    # cities_4326["centroid"] = cities_4326.centroid
        
    # for _,r in cities_4326.iterrows():
    #     lat = r["centroid"].y
    #     lon = r["centroid"].x
    #     name = r["cityName"]
    #     print(lat,lon)
    #     folium.Marker(
    #     location=[lat, lon],
    #     icon=DivIcon(
    #         icon_size=(150,36),
    #         icon_anchor=(0,0),
    #         html='<div class="Label" style="font-size: 12pt; color: #282D3D; text-align: center;">{name}</div>'.format(name=name),)
    #     ).add_to(m)

    folium.LayerControl(position='topleft', autoZIndex=True).add_to(m)
    
    industryIcon = '''
        var marker = L.AwesomeMarkers.icon({
                icon_color="#d9534f", icon="industry", prefix="fa", color='lightred'
            )});
            '''
    
    # Use custom CSS to move the colormap legend to the bottom-right corner
    legend_html = '''
    <link rel="stylesheet" href="https://balladaniel.github.io/leaflet-dataclassification/leaflet-dataclassification.css" />
    <script src="https://balladaniel.github.io/leaflet-dataclassification/leaflet-dataclassification.js"></script>
    <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

    <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
           
     <div id='maplegend' class='maplegend' 
         style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
         border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
    
    <div class='legend-scale'>
        Legenda
        <ul class='legend-labels'>
            <li><i class="fa-solid fa-arrow-up-from-ground-water" style='color:#2F4279;'></i> Waterwinlocaties</li>
            <li><i class="fa-solid fa-industry" style='color:#D9534F;'></i> Industriële Waterwinlocaties</li>
            <li>{colormap}</li>
            <li>Leidingen <i class="fa-solid fa-minus fa-sm" style='color:#D9534F;'></i> <250mm 
                    <i class="fa-solid fa-minus fa-lg" style='color:#D9534F;'></i> 250mm - 350mm
                    <i class="fa-solid fa-minus fa-2xl" style='color:#D9534F;'></i> >400mm</li>             
            <li><i class="fa-solid fa-folder" style='color: darkgreen;'></i> Natura2000 Beschermd Gebied</li>
            <li><i class="fa-solid fa-folder" style='color: #CAFAA2;'></i> Beperkt Natuurnetwerk Nederland Gebied</li>
            <li><i class="fa-regular fa-folder" style='color:#93419F;'></i> Balansgebied</li>

        </ul>
     </div>
    </div>
    '''.format(colormap=colormap._repr_html_(), industryIcon=industryIcon)

    
    
    # Add the custom legend to the map
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
