import os
import sys
import fpdf
from fpdf import FPDF
import time
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi
from html2image import Html2Image
import panel as pn



TITLE = "VITALENS Report"
WIDTH = 210
HEIGHT = 297

class PDF(FPDF):

    def footer(self):
        self.set_y(-15)
        self.add_font('DejaVu', 'I', r'Assets\fonts\DejaVuSansCondensed-Oblique.ttf', uni=True)
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
    df["PCT Change"]= ((df["Value"]-df["Current Extraction"])/df["Current Extraction"])*100
    
    df = df.drop(columns=["Num_Wells",'Ownership','OPEX_m3','Drought_m3', 'Env_m3','envCost',"geometry"])
    df = df.rename(columns={'Max_permit': 'Maximum permit', 'Value':'New Extraction', })
    
    
    
    # Apply styling to the DataFrame
    styled_df = df.style.format({
        'Maximum permit': "{:.2f}",
        'Current Extraction': '{:.2f} Mm\u00b3/yr',
        'New Extraction': '{:.2f} Mm\u00b3/yr',
        'CO2 cost m3': "{:.2f}",
        'Drought_m3': "{:.2f}",
        'OPEX': "{:0,.0f} M\u20AC",
        'CAPEX': "{:0,.0f} M\u20AC",
        'Extraction PCT Change': "{:.2f}%",
    }).background_gradient(subset=['PCT Change'], cmap='RdYlGn') \
                      .set_caption("Water Extraction and Cost Overview")

    # Convert the styled DataFrame to HTML
    html = styled_df.to_html()

    # Use html2image to convert the HTML to an image
    hti = Html2Image()

    # Save the HTML content as an image (adjust file path as needed)
    hti.screenshot(html_str=html, save_as='Wells_DF.png')

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
    html_content = lzh_pane.save("./Assets/lzh_panel.html", embed=True)
    
    # Use html2image to convert the HTML to an image
    hti = Html2Image()

    # Capture screenshot from the saved HTML file
    hti.screenshot(html_file="./Assets/lzh_panel.html", save_as=filename)

    
    
def create_letterhead(pdf, WIDTH):
    pdf.image("https://uavonline.nl/wp-content/uploads/2020/11/vitens-logo-1.png", 0, 0, WIDTH/5)
    
def create_title(title, pdf):
    
    # Add main title
    pdf.set_font('DejaVu', 'b', 20)  
    pdf.ln(20)
    pdf.write(5, title)
    pdf.ln(10)
    
    # Add date of report
    pdf.set_font('DejaVu', '', 14)
    pdf.set_text_color(r=128,g=128,b=128)
    today = time.strftime("%d/%m/%Y")
    pdf.write(4, f'{today}')
    
    # Add line break
    pdf.ln(10)
    
def write_to_pdf(pdf, words):
    
    # Set text colour, font size, and font type
    pdf.set_text_color(r=0,g=0,b=0)
    pdf.set_font('DejaVu', '', 12)
    
    pdf.write(5, words)
    
def createPDF(filename1, popScenario, smallScenario, button3, button4, button6, ButtonDemand, TotalDemand, totalSupply, OPEX, CAPEX, CO2, ENVDmg,Natura):
    pdf = PDF() # A4 (210 by 297 mm)
    
    
    # Add a Unicode free font
    # Get the directory where the script is being run
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fontPath= os.path.join(script_dir, 'Assets', 'fonts', 'DejaVuSansCondensed.ttf')
    pdf.add_font('DejaVu', '', fontPath, uni=True)
    pdf.add_font('DejaVu', 'b', r'Assets\fonts\DejaVuSans-Bold.ttf', uni=True)
    '''
    First Page of PDF
    '''
    # Add Page
    pdf.add_page()

    # Add lettterhead and title
    create_letterhead(pdf, WIDTH)
    create_title(TITLE, pdf)
    
    ## Add Scenario Text
    pdf.set_font('DejaVu', 'b', 16)
    write_to_pdf(pdf, "1. Secenario Configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    write_to_pdf(pdf, ("\u2022 Population Scenario: " +popScenario.value))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Small Business Scenario: " +smallScenario.value))
    pdf.ln(15)
    
    ##ADD some measures text
    pdf.set_font('DejaVu', 'b', 16)
    write_to_pdf(pdf, "2. Measures configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    write_to_pdf(pdf, ("\u2022  Closed Small wells:  " +str(button3.value)))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Closed Natura 2000 Wells:  " +str(button4.value)))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Imported Water from WAZ Getelo, NVB Nordhorn and Haaksbergen  " +str(button6.value)))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Water demand per capita:  " +str(ButtonDemand.value) +  " L/d"))
    pdf.ln(15)


    # Add some words to PDF
    pdf.set_font('DejaVu', 'b', 16)
    write_to_pdf(pdf, "3. Wells Configuration:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
    write_to_pdf(pdf, "The table below illustrates the Water extraction configuration for each wells location:")
    pdf.ln(15)
    
    # Add table
    pdf.image("Wells_DF.png", w=WIDTH-20)
    pdf.ln(10)
    
    # Add some words to PDF
    pdf.set_font('DejaVu', 'b', 16)
    write_to_pdf(pdf, "4. Indicators Report:")
    pdf.ln(15)
    pdf.set_font('DejaVu', '', 11)
   
   
    write_to_pdf(pdf, ("\u2022  Total Supply:  " +f"{totalSupply.value:.2f} Mm\u00b3/yr"))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Total Demand:  " +f"{TotalDemand.value:.2f} Mm\u00b3/yr"))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 Leverenszekerheid  " +f"{totalSupply.value * 100 / TotalDemand.value:.2f}"+"%"))
    pdf.ln(10)
    write_to_pdf(pdf, ("\u2022 OPEX " +f'{OPEX.value:.2f}'+  " M/yr"))
    pdf.ln(15)
    write_to_pdf(pdf, ("\u2022 CAPEX " +f'{CAPEX.value:0,.2f}' +  " M/yr"))
    pdf.ln(15)
    write_to_pdf(pdf, ("\u2022 CO2 emission cost " +str(CO2.value) +  " M/yr"))
    pdf.ln(15)
    write_to_pdf(pdf, ("\u2022 Drought Damage cost " +str(ENVDmg.value) +  " M/yr"))
    pdf.ln(15)
    write_to_pdf(pdf, ("\u2022 Natura200 affected area " +str(Natura.value) +  " Ha"))
    pdf.ln(15)
    
    write_to_pdf(pdf, "The table below illustrates the Water extraction configuration for each wells location:")
    pdf.ln(15)
        
    # Add some words to PDF
    write_to_pdf(pdf, "Water extraction per location:")
    pdf.ln(10)
    

    # Add the generated visualisations to the PDF
    pdf.image(filename1,   w=WIDTH/2-10)
    # pdf.image(filename2, 5, 200, WIDTH/2-10)
    
    pdf.ln(10)
    
    # Generate the PDF
    pdf.output("Vitalens_report.pdf", 'F')
