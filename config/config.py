

# -----------------------------------------------------------------------------
# Global CSS definitions
# -----------------------------------------------------------------------------
GLOBAL_CSS = ['''
    
           
/* Import Google Fonts */
@import url("https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap");

:host,
:root {
  --design-primary-color: #151931 !important;
  --design-secondary-color: #00B893 !important;
  --design-primary-text-color: #f2f2ed !important;
  --design-secondary-text-color: #151931 !important;
  --bokeh-base-font: "Barlow", sans-serif, Verdana !important;
  --mdc-typography-font-family: "Barlow", sans-serif, Verdana !important;
  --panel-primary-color: #151931 !important;
  --panel-background-color: #f2f2ed !important;
  --panel-on-background-color: #151931 !important;
  --sidebar-width: 350px;
}

:host(.active) .bar {
    background-color: #ffc233 !important;    
}

:host(.bk-above) .bk-header .bk-tab{
    border: #F2F2ED !important;
    background: #00000014 !important
}


::-webkit-scrollbar-track
{
	background-color: #F5F5F5;
}

::-webkit-scrollbar
{
	width: 5px !important; 
	background-color: #F5F5F5;
}

::-webkit-scrollbar-thumb
{
	background-color: #CCC5B9 !important;
    border-radius: 1px;
}

#sidebar, #main {
    background-color: #F2F2ED !important;
}

hr.dashed {
  border-top: 1px dashed;
  border-bottom: none;
}

.title {
  font-weight: 600 !important;
}

.bar {
        background-color: #b1b1c9;
    }

.bk-btn {
  border-radius: 0.5em !important;
}

.bk-btn bk-btn-primary {
    font-size: normal !important;
}

.bk-btn-group {
  height: 100%;
  display: flex;
  flex-wrap: inherit !important;
  align-items: center;
}

.bk-btn-primary{
    font-size: normal !important;
}

.bk-btn-success{
  background-color: #3872A1;
  background-position: center;
  font-weight: 400 !important;
  font-size: small !important;
  line-height: 1;
  margin: 3px 3px; 
  padding: 5px 10px !important;
  transition: background 0.8s;
  width: fit-content;
}

.bk-btn-warning {
  margin: 3px;
  background-color: #f1b858;   
}

.accordion-header button{
    color: #151931;
    background-color: #B4BFE4;
}


.bk-tab.bk-active {
    background: #d3d3cf !important;
    color: #d9534f !important;
}

.maplegend .legend-title {
            text-align: left;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 90%;
            }
.maplegend .legend-scale ul {
    margin: 0;
    margin-bottom: 5px;
    padding: 0;
    float: left;
    list-style: none;
    }
.maplegend .legend-scale ul li {
    list-style: none;
    margin-left: 0;
    line-height: 18px;
    margin-bottom: 2px;
    }
.maplegend ul.legend-labels li span {
    font-size: smaller;
    display: block;
    float: left;
    height: 16px;
    width: 30px;
    margin-right: 5px;
    margin-left: 0;
    border: 1px solid #999;
    }
.maplegend .legend-source {
    font-size: 80%;
    color: #777;
    clear: both;
    }
.maplegend a {
    color: #777;
    }
    
.Label {
    text-shadow:
    -1px -1px 0 #fff,
    1px -1px 0 #fff,
    -1px 1px 0 #fff,
    1px 1px 0 #fff;  
}

'''
]

miniBox_style = {
    'background': '#e9e9e1',
    'border': '0.7px solid',
    'margin': '10px',
    "box-shadow": '4px 2px 6px #2a407e',
    "display": "flex"
}

buttonGroup_style = {
    'flex-wrap': 'wrap',
    'display': 'flex'
}

js_legend = '''
    $(function() {
        // Ensure the element exists before making it draggable
        if ($('#maplegend').length) {
            $('#maplegend').draggable({
                start: function(event, ui) {
                    // Reset positioning constraints to allow free dragging
                    $(this).css({
                        right: 'auto',   // Reset 'right' so the element can move left
                        top: 'auto',     // Reset 'top' so it can move freely
                        bottom: 'auto'   // Reset 'bottom' to enable dragging downward
                    });
                }
            });
        } else {
            console.error("Element #maplegend not found.");
        }
    });
'''

# -----------------------------------------------------------------------------
# JavaScript files to initialize leaflet-dataclassification and custom legend
# -----------------------------------------------------------------------------



JS_FILES = {
    'leaflet-dataclassification': 'https://raw.githubusercontent.com/balladaniel/leaflet-dataclassification/master/dist/leaflet-dataclassification.js',
}




