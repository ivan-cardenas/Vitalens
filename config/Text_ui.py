import panel as pn
from config.config import * 


# ------------------------------------------------------------------------------
# TEXT Sectiions
# ------------------------------------------------------------------------------

# Create HTML Text for Wells Tab
balance_area_Text = pn.pane.HTML('''
    <h3 align= "center" style="margin: 5px;"> Balance Areas</h3><hr>'''
    , width=300, align="start")

textDivider3 = pn.pane.HTML('''<hr class="dashed"> <h3 align= "center" style="margin: 5px;">Scenarios Small Business  <svg xmlns="http://www.w3.org/2000/svg" height="15px" width="15px" viewBox="0 0 512 512" style="cursor:pointer; color: lightgray;"
     ><g><title>"Small Business include bakeries, hair saloons, retail stores, shopping malls, etc."</title><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M464 256A208 208 0 1 0 48 256a208 208 0 1 0 416 0zM0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm169.8-90.7c7.9-22.3 29.1-37.3 52.8-37.3l58.3 0c34.9 0 63.1 28.3 63.1 63.1c0 22.6-12.1 43.5-31.7 54.8L280 264.4c-.2 13-10.9 23.6-24 23.6c-13.3 0-24-10.7-24-24l0-13.5c0-8.6 4.6-16.5 12.1-20.8l44.3-25.4c4.7-2.7 7.6-7.7 7.6-13.1c0-8.4-6.8-15.1-15.1-15.1l-58.3 0c-3.4 0-6.4 2.1-7.5 5.3l-.4 1.2c-4.4 12.5-18.2 19-30.6 14.6s-19-18.2-14.6-30.6l.4-1.2zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z"/><g></svg> </h3> <hr>''')

textScenarioPop = pn.pane.HTML(
    '''
    <h3 align= "center" style="margin: 5px;">Scenarios Population</h3><hr>'''
    # <b>Scenario with demand increase of 10% &#8628;</b>'''
    , width=300, align="start"
)
textB2 = pn.pane.HTML(
    '''<b>Scenario with demand increase of 35% &#8628;</b>''', width=300, align="start"
    
)
textMeasureSupp = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Supply Measures </h3> <hr>
    <b>Close down all well locations with production less than 5Mm\u00b3/yr &#8628;</b>''', width=300, align="start", styles={}
)
textCloseNatura = pn.pane.HTML(
    '''
    <b>Close down all well locations in less than 100m from a Natura 2000 Area &#8628;</b>''', width=300, align="start", styles={}
)

textMeasureDemand = pn.pane.HTML(
    '''<hr class="dashed"><h3 align= "center" style="margin: 5px;"> Demand Measures </h3> <hr>
    <b>Water consumption per Capita in L/d</b>''', width=300, align="start", styles={}
)

textImport = pn.pane.HTML(
    '''
    <b>Importing water from WAZ Getelo, NVB Nordhorn and Haaksbergen. Importing 4.5  Mm\u00b3/yr</b>''', width=300, align="start", styles={}
)

textSmartM = pn.pane.HTML('''
    <b>Use of smart meters at homes, reduction of 5% of consumption</b>''', width=300, align="start", styles={}
)

textIndustrial = pn.pane.HTML(
    '''
    <b>Add unused water from industrial permits</b>''', width=300, align="start", styles={})

textEnd = pn.pane.HTML(
    '''<hr class="dashed">
    ''', width=300, align="start", styles={}
)

textDivider0 = pn.pane.HTML('''<hr class="dashed">''')
textDivider1 = pn.pane.HTML('''<hr class="dashed">''')
textDivider2 = pn.pane.HTML('''<hr class="dashed">''')

disclaimer = pn.pane.HTML('''    
                         <div style="font-family: Barlow, Arial, sans-serif; padding: 20px; color: #333; font-size: 14px;">
    <div>
  <h1 style="color: #3850A0;">Welcome to the Vitalens App</h1>
  <p>
    This app helps you manage and analyze water wells in the Overijssel Zuid region. It allows users to track well capacities, costs, environmental impact, and other important factors for planning water supplies.
  </p>

  <h2>Key Features</h2>
  <ul>
    <li><strong>Live Data Visualization:</strong> See and interact with well locations, extraction levels, and environmental limits.</li>
    <li><strong>Scenario Analysis:</strong> Simulate different water demand scenarios, such as population growth or small business needs, to see how they might affect water supply and costs.</li>
    <li><strong>Environmental Cost Estimates:</strong> Calculate environmental costs like CO2 emissions and the effects of drought for each well, and see restrictions for protected areas like Natura2000.</li>
    <li><strong>Custom Well Management:</strong> Change the extraction levels and status (active or inactive) of wells to optimize water usage and efficiency.</li>
    <li><strong>Interactive Data Exploration:</strong> Explore detailed well information, including supply security, operating costs, environmental impacts, and performance by area.</li>
  </ul>

  <h2>Disclaimer</h2>
  <p>
    This app gives useful insights and visualizations for managing water, but it is based on estimates and assumptions. Actual well performance, environmental impact, and costs may vary due to real-world factors like changing conditions or new regulations.
  </p>
  <p>
    <strong>Please Note:</strong> The app’s results are for guidance only and may not be exact. For critical decisions, consult local experts and use verified data.
  </p>

  <p style="color: #666; font-size: 14px;">
    © 2024 Vitalens App. Vitens and University of Twente. All rights reserved.
  </p>
</div>

                         
                         ''', width=700, max_height=800)