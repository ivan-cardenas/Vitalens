# Vitalens Interactive Dashboard for Sustainable Drinking Water Management
 
 

## 📌 Research Information  

- **📖 Research Project**  
  - **Title**: *Balancing Water Supply and Demand – The Vitalens Interactive Dashboard for Sustainable Drinking Water Management*  
  - **👨‍🔬 Authors**: 
    - Johannes Flacke [<img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg" height="20"/>]( https://orcid.org/0000-0001-8906-7719)
    - Iván Cárdenas-Leon [<img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg" height="20"/>](https://orcid.org/0009-0005-0245-633X)
    - Nina Schwarz  [<img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg" height="20"/>]( https://orcid.org/0000-0003-4624-488X) 
    - Pirouz Nourian [<img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg" height="20"/>](https://orcid.org/0000-0002-3817-7931) 
    - Cheryl de Boer [<img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg" height="20"/>](https://orcid.org/0000-0003-3931-9177)
  - **🏛️ Affiliation**: University of Twente, Faculty, Department  
  - **📄 Article or Pre-print DOI**: Article Accepted to CUPUM Conference in July 2025 - Not published yet.

## 📄 SUMMARY

The purpose of the tool is to support discussions over strategies to mitigate the problem of balancing drinking water supply and demand in the future by calculating and visualizing the impacts of different suitable measures affecting the water balance. The tool visualizes the current and potential future drinking water supply and demand in the Overijssel Zuid region. 

The tool allows users to apply changes to specific supply and demand parameters, such as the amount of water extracted at certain wells or changes in drinking water consumption of citizens, and to track levels of supply security, investment and maintenance costs, environmental impacts, and other relevant factors for water supply planning until 2035. It can simulate different water demand scenarios affected by population growth or small business needs to see whether supply can fulfil these demands and at what costs. The tool further calculates environmental costs, such as carbon emissions and drought effects for each extraction area, and displays restrictions for protected areas such as Natura2000. Users can explore detailed information about extraction areas, including security of supply, operational costs, environmental impact, and performance by area. 

The tool aims to provide a basis for discussions about the measures that could be taken and their potential impacts on other key performance indicators until 2035. Therefore, the main target audience is Vitens staff and possibly key stakeholders outside of Vitens. Vitens provided the database embedded in the tool which entails estimates and simplifying assumptions. Actual well performance, environmental impact, and costs may vary due to changing conditions and new regulations. 

**The documentation was written in Dec. 2024 by the team of researchers from the UT.**

### Read More

[Introduction](Documentation/Introduction.md)

[Workflow - Where to click?](Documentation/Workflow.md)


## 🏃 How to run

1. Download the released version into your computer or clone this repository
  ```
  git clone https://github.com/ivan-cardenas/Vitalens
  cd Vitalens	
  ```
2. Open your terminal
3. Install the dependancies
   ```
   pip install -r /path/to/requirements.txt
   ```
4. Run the app - This will open the app in your browser
    ```
    panel serve  Vitalens.py --show
    ```
5. You can also see a running version in [HuggingFace](https://huggingface.co/spaces/cygnus26/Vitalens)

## 📂 Folder Structure  

| 📁 Folder | 📂 Subfolder | 📄 File | 📝 Description |
|-----------|------| --------|---------------|
| **Assets/** | *.*| `Thematic_Data.gpkg` | Input data with five geospatial layers |
|    | **Thematic_Data.gpkg** | `Well_Capacity_Cost`| **POINT** Layer  showing the extraction wells for underground water. `Properties: Name, Location, Water extracted yearly, Unitary costs, Unitary damage costs, and Balance Area Location`|
|   |    | `Industrial_Extraction` | **POINT** Layer with Industrial water extracted per city. `Properties': city name, Industrial licensed extraction, Extraction registered (2019)`|
|   |   | `Pipes_OD`| **LINE** Layer with topological strucuture of Main water pipe network. Properties: `Diameter`|
|   |   | `CitiesHexagonal` | **POLYGON** Layer with the hexagonal representation of city Boundaries. `Properties: Name, population, Daily water Demand, Yearly Water Demand`|
|   |   | 'H3_Lvl18`| **POLYGON** Layer with uniform hexagonal areas of  **63Ha**. `Properties: ID, City Name, population, Daily water Demand, Yearly Water Demand`| 
|   |*.*| `NatuurEffect.csv` | Calculated Damage impact at different Operational rates (Current, 85%, 100%, 115%) for Sensible nature and Very Sensible Nature |
| |**fonts** | `DeJaVuSans.tff` | Font Used in Report Document
| **Root/** | |`PrintingReport.py` | Python code for creating the report of the choices made in the app |
| **Root/** | |`Vitalens.py` | Main python code with the functions, indicators, scenarios, measures and interface for the app |
