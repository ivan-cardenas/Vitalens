# main.py

import panel as pn
from config.config import *
from config.ui import build_ui, total_extraction_update, update_indicators
from config.indicators import *

# -----------------------------------------------------------------------------
# Panel configuration
# -----------------------------------------------------------------------------
pn.config.global_css = GLOBAL_CSS
pn.config.css_files = GLOBAL_CSS
pn.config.loading_spinner = 'petal'

# -----------------------------------------------------------------------------
# Initialize Panel extensions
# -----------------------------------------------------------------------------
pn.extension(sizing_mode="stretch_width")
pn.extension("plotly")
pn.extension("echarts")
pn.extension("tabulator", "ace", css_files=["https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"])
pn.extension("floatpanel")
pn.extension(notifications=True)
pn.extension(js_files=JS_FILES)




# -----------------------------------------------------------------------------
# Initialize the app    
total_extraction_update()
update_indicators()
app = build_ui()
app.servable()



