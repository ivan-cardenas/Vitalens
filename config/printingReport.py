# -*- coding: utf-8 -*-
import os
import sys
import fpdf
from fpdf import FPDF
import time
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi
import imgkit
import panel as pn



TITLE = "VITALENS Report"
WIDTH = 210
HEIGHT = 297

class PDF(FPDF):

    def footer(self):
        self.set_y(-15)
        self.add_font('DejaVu', 'I', r'../Assets/fonts/DejaVuSansCondensed-Oblique.ttf', uni=True)
        self.set_font('DejaVu', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

def color_pos_neg_value(value):
    if value < 0:
        color = 'red'
    elif value > 0:
        color = 'green'
    else:
        color = 'black'
    return 'color: %s' % color

def styledWells(df):
    df["CO2 cost"] = df.loc[df["Active"] == True, "Value"] * df.loc[df["Active"] == True, "CO2_m3"]
    df["Draught damage cost"] =  df.loc[df["Active"] == True, "Value"] * df.loc[df["Active"] == True, "Drought_m3"]
    df["New Extraction"]= df.loc[df["Active"] == True, "Value"]
    
    df["Extraction PCT Change"]= ((df["New Extraction"]-df["Current Extraction"])/df["Current Extraction"])*100
    
    df = df.drop(columns=["Num_Wells",'Ownership','OPEX_m3','Drought_m3', "CO2_m3", 'Env_m3','envCost',"geometry"])
    df = df.rename(columns={'Max_permit': 'Maximum permit' })
    df = df[["Name","Balance area","Active","Current Extraction","New Extraction", "Maximum permit", "CO2 cost", "Draught damage cost", "Extraction PCT Change" ]]
    
    
    # Apply styling to the DataFrame
    styled_df = df.style.format({
        'Maximum permit': "{:.2f} Mm\u00b3/yr",
        'Current Extraction': '{:.2f} Mm\u00b3/yr',
        'New Extraction': '{:.2f} Mm\u00b3/yr',
        'CO2 cost': "{:.2f} M\u20AC/yr",
        'Draught damage cost': "{:.2f} M\u20AC/yr",
        'OPEX': "{:0,.0f} M\u20AC",
        'CAPEX': "{:0,.0f} M\u20AC",
        'Extraction PCT Change': "{:.2f}%",
    }).background_gradient(subset=['Extraction PCT Change'], cmap='RdYlGn') \
                      .set_caption("Water Extraction and Cost Overview")

    # 1. Compute an absolute output folder (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print (f"Script directory: {script_dir}")
    parent_dir = os.path.dirname(script_dir)
    print (f"Parent directory: {parent_dir}")
    output_dir = os.path.abspath(os.path.join(parent_dir, 'Assets', 'images'))
    os.makedirs(output_dir, exist_ok=True)
    
    with open( os.path.join(output_dir, "wells_HTML.html"), "w", encoding="utf-8") as file:
        file.write(styled_df.to_html(border=1))

    # # 3. Save the screenshot — pass save_as as a list or a single filename
    html_path = os.path.abspath('./Assets/images/wells_HTML.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        imgkit.from_file(f, './Assets/images/Wells_DF.png', options={'format': 'png', 'width': 800, 'height': 600})
    print(f"Saved screenshot to {os.path.join(output_dir, 'Wells_DF.png')}")

def generate_matplotlib_stackbars(df, filename):
    
    # Create subplot and bar
    fig, ax = plt.subplots()
    ax.plot(df['Name'].values, df['Value'].values, color="#E63946", marker='D') 

    # Set Title
    ax.set_title('Water extraction per Location', fontweight="bold")

    # Set xticklabels
    ax.set_xticks(range(len(df['Name'])))  # Set the tick positions based on the number of labels
    ax.set_xticklabels(df['Name'].values, rotation=60)
    plt.xticks(df['Name'].values)

    # Set ylabel
    ax.set_ylabel('Total Water extractedn in Mm\u00b3/yr') 

    # Save the plot as a PNG
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    
    
def generate_image_fromInd(pane, filename):
    # Serve or save the panel as HTML first
    
    lzh_pane =pn.Column(pane)
    lzh_pane.save("../Assets/lzh_panel.html", embed=True)
    
    with open("../Assets/lzh_panel.html") as f:
        imgkit.from_file(f, filename, options={'format': 'png', 'width': 800, 'height': 600})
    
    
def create_letterhead(pdf, WIDTH):
    pdf.image("https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png", 0, 0, WIDTH/5)
    
def create_title(title, pdf):
    
    # Add main title
    pdf.set_font('DejaVu', 'b', 20)  
    pdf.ln(20)
    pdf.write(5, title)
    pdf.ln(10)
    
    # Add date of report
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(r=128,g=128,b=128)
    today = time.strftime("%d/%m/%Y")
    pdf.write(4, f'{today}')
    
    # Add line break
    pdf.ln(10)
    
    
def createPDF(filename1, popScenario, smallScenario, button3, button4, button6, button7, ButtonDemand, TotalDemand, totalSupply, OPEX, CAPEX, CO2, ENVDmg,Natura, NaturaHigh):
    pdf = PDF() # A4 (210 by 297 mm)
        
    
    # Add a Unicode free font
    # Get the directory where the script is being run
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = os.path.dirname(current_dir)
    fontPath= os.path.join(script_dir, 'Assets', 'fonts', 'DejaVuSansCondensed.ttf')
    fontPathBold = os.path.join(script_dir, 'Assets', 'fonts', 'DejaVuSansCondensed-Bold.ttf')
    pdf.add_font('DejaVu', '', fontPath, uni=True)
    pdf.add_font('DejaVu', 'b',fontPathBold, uni=True)
    '''
    First Page of PDF
    '''
    # Add Page
    pdf.add_page()

    # Add lettterhead and title
    create_letterhead(pdf, WIDTH)
    create_title(TITLE, pdf)
    
    pdf.set_text_color(r=30,g=30,b=30)
    ## Add Scenario Text
    pdf.set_font('DejaVu', 'b', 16)
    pdf.write(5, "1. Secenario Configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    pdf.write(10, ("\u2022 Population Scenario: " +popScenario.value))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Small Business Scenario: " +smallScenario.value))
    pdf.ln(15)
    
    ##ADD some measures text
    pdf.set_font('DejaVu', 'b', 16)
    pdf.write(5, "2. Measures configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    pdf.write(10, ("\u2022  Closed Small wells:  " +str(button3.value)))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Closed Natura 2000 Wells:  " +str(button4.value)))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Imported Water from WAZ Getelo, NVB Nordhorn and Haaksbergen  " +str(button6.value)))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Water demand per capita:  " +str(ButtonDemand.value) +  " L/d"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Using Industrial water permits excess:  " +str(button7.value)))
    pdf.ln(15)


    # Add some words to PDF
    pdf.set_font('DejaVu', 'b', 16)
    pdf.write(5, "3. Wells Configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    pdf.write(10, "The table below illustrates the Water extraction configuration for each wells location:")
    pdf.ln(10)
    
    # Add table
    pdf.image("Wells_DF.png", w=WIDTH-40)
    pdf.ln(5)
    
    # Add some words to PDF
    pdf.set_font('DejaVu', 'b', 16)
    pdf.write(5, "4. Indicators Report:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
   
   
    pdf.write(10, ("\u2022  Total Supply:  " +f"{totalSupply.value:.2f} Mm\u00b3/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Total Demand:  " +f"{TotalDemand.value:.2f} Mm\u00b3/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Leverenszekerheid  " +f"{totalSupply.value * 100 / TotalDemand.value:.2f}"+"%"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 OPEX " +f'{OPEX.value:.2f}'+  " M\u20AC/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 CAPEX " +f'{CAPEX.value:0,.2f}' +  " M\u20AC/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 CO2 emission cost " +f'{CO2.value:0,.2f}' +  " M\u20AC/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Drought Damage cost " +f'{ENVDmg.value:0,.2f}' +  " M\u20AC/yr"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Natura200 affected area Sensible" +f'{Natura.value:.2f}'+  " Ha"))
    pdf.ln(10)
    pdf.write(10, ("\u2022 Natura200 affected area Very Sensible" +f'{NaturaHigh.value:.2f}'+  " Ha"))
    pdf.ln(10)
            
    # Add some words to PDF
    pdf.write(5, "Water extraction per location:")
    pdf.ln(10)

    # Add the generated visualisations to the PDF
    pdf.image(filename1,   w=WIDTH-20)
    # pdf.image(filename2, 5, 200, WIDTH/2-10)
    
    pdf.ln(10)
    
    # Generate the PDF
    pdf.output("Vitalens_report.pdf", 'F')

    print("PDF generated successfully!")