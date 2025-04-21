# scenarios.py

from config.data import hexagons_filterd
import panel as pn

from config.data import (
smallBusiness, demand_capita)
from config.indicators import update_indicators
# Keep track of the current scenario title
current_scenario_title = "State - 2022"

def ScenarioBase():
    """
    Implement the base scenario with a demand equal to year 2022.

    Args:
        event: The event object.
    """
    global demand_capita
    hexagons_filterd["Current Pop"]= hexagons_filterd["Pop2022"]
    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1000000
    update_scenarioTitle("Population 2022")
    print("Scenario Base restored")
    update_indicators()

def Scenario1():
    """
    Implement the first scenario with a demand increase

    Args:
        event: The event object.
    """
    global demand_capita 
    hexagons_filterd["Current Pop"]= hexagons_filterd["Pop2022"]*1.0209

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365 
    ) / 1000000
    update_scenarioTitle("Autonomous Growth")
    print("Scenario 1 ran perfectly")
    update_indicators()

def Scenario2():
    """
    Implement the second scenario with a demand increase of 2.09%.
    
    
    Args:
        event: The event object.
    """
    hexagons_filterd["Current Pop"] = hexagons_filterd["Pop2022"]*1.0309

    hexagons_filterd["Water Demand"] = (
        hexagons_filterd["Current Pop"] * demand_capita * smallBusiness * 365
    ) / 1e6
    update_scenarioTitle("Population 2035 +1% increase")
        
    update_scenarioTitle("Accelerated Growth")
    update_indicators()
    
def ScenarioSmallBusinessBase():
    global smallBusiness 
    smallBusiness = 1.2
    update_indicators()

def ScenarioSmallBusiness1():
    global smallBusiness
    smallBusiness = 1.2*1.1
    update_indicators()

def ScenarioSmallBusiness2():
    global smallBusiness
    smallBusiness = 1.2*1.35
    update_indicators()

def update_scenarioTitle(title):
    """Update the global scenario label"""
    global current_scenario_title
    current_scenario_title = title
    print(f"Title set: {title}")


def get_scenario_title():
    """Return the current scenario name."""
    return current_scenario_title

def update_scenarios(event):
    if event.new == "Population 2035":
        Scenario1()
        print('scenario 1 active')
    if event.new == "Population 2035 +1% increase":
        print('scenario 2 active')
        Scenario2()
    if event.new == "Population - 2022":
        print("Orginal Scenario")
        ScenarioBase()
    update_indicators()
    
def update_scenariosSmall(event):
    if event.new == 'Small Business +10% Demand':
        ScenarioSmallBusiness1()
        print('scenario 1 Small active')
    if event.new == 'Small Business +35% Demand':
        print('scenario 2 small  active')
        ScenarioSmallBusiness2()
    if event.new == 'State - 2022':
        print("Orginal Scenario")
        ScenarioSmallBusinessBase()
    update_indicators()