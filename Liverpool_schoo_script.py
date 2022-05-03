# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import webbrowser
import pandas as pd
import numpy as np
import os
import time
import folium
from folium.plugins import HeatMap
import requests
import json
from selenium import webdriver
import matplotlib
from fpdf import FPDF
import dataframe_image as dfi
from zipfile import ZipFile as Z
from datetime import date


postcode_to_lsoa_link = "https://www.arcgis.com/sharing/rest/content/items/06938ffe68de49de98709b0c2ea7c21a/data"
IMD_scores_link = "https://opendatacommunities.org/downloads/cube-table?uri=http%3A%2F%2Fopendatacommunities.org%2Fdata%2Fsocietal-wellbeing%2Fimd2019%2Findices"
postcode_API_link  = "http://api.getthedata.com/postcode/" #  Retrieve Json response from getthedata API for postcode


# Access web to download data from predefined links
r = requests.get(postcode_to_lsoa_link, allow_redirects=True)
open('postcode_to_lsoa.zip', 'wb').write(r.content)
file_name = "postcode_to_lsoa.zip"
######
with Z(file_name, 'r') as zipped:
    # printing all the contents of the zip file
    zipped.printdir()
  
    # extracting all the files
    print('Extracting all the files now...')
    zipped.extractall()
    print('Done!')
######
r = requests.get(IMD_scores_link, allow_redirects=True)
open('IMDnumbers.csv', 'wb').write(r.content)

#### OLD way of access data from ONS - online
#webbrowser.open(postcode_to_lsoa_link) #Postcode to LSOACode
 
#webbrowser.open(IMD_scores_link) #All IMD data
####

postcode_to_lsoa = pd.read_csv("PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU.csv", encoding = 'latin-1')
IMD_scores = pd.read_csv("IMDnumbers.csv", encoding='latin-1')
school_info = pd.read_csv("School info.csv")

# Creating Dataframes to have postcodes and corrosponding latutude and longitudes
Postcode_Lat_Long_df = pd.DataFrame(columns=['Postcode', 'Latitude', 'Longitude'])
final_postcode_lat_long_df = pd.DataFrame(columns=['Postcode', 'Latitude', 'Longitude'])
today = date.today()
date = today.strftime("%d %B, %Y")

IMD_scores.columns = IMD_scores.columns.str.replace(' ', '_')
IMD_scores = IMD_scores[IMD_scores.Measurement == "Decile "]
#IMD_scores = IMD_scores[IMD_scores.Indices_of_Deprivation != "e. Health Deprivation and Disability Domain" ] # remove this
#IMD_scores = IMD_scores[IMD_scores.Indices_of_Deprivation != "j. Income Deprivation Affecting Older People Index (IDAOPI)"] # remove this

district_council = school_info.at[0, "District_Council"]
postcode_to_lsoa = postcode_to_lsoa[postcode_to_lsoa.ladnm == district_council] # make this based on unique value from column - user input
postcode_to_lsoa = postcode_to_lsoa[["pcd7", "lsoa11cd", "lsoa11nm"]]
postcode_to_lsoa = postcode_to_lsoa.rename(columns = {"pcd7": "Postcode", "lsoa11cd": "LSOACode"})

IMD_scores = IMD_scores.rename(columns = {"FeatureCode": "LSOACode"})

All_Borough_data = pd.merge(IMD_scores, postcode_to_lsoa, how = "inner", on = ["LSOACode"])

pupil_info = pd.read_csv("School pupil info.csv") # change to school pupil info CSV
pupil_info_postcodes = pupil_info[["Postcode", "Pupil_Name"]]# Only postcodes and pupil names
All_Borough_data[["Postcode"]] = All_Borough_data[["Postcode"]].replace(" ", "", regex = True) ######
final_pupil_data = pd.merge(All_Borough_data, pupil_info_postcodes, how = "inner", on = ["Postcode"])

pupil_data_risk = final_pupil_data[["Postcode", "Pupil_Name", "Value", "Indices_of_Deprivation"]]
pupil_data_risk = pupil_data_risk[pupil_data_risk.Indices_of_Deprivation == "a. Index of Multiple Deprivation (IMD)"]
pupil_info_FSM_PP = pupil_info[["Postcode", "Pupil_Name", "FSM", "Pupil_Premium"]]
pupil_data_risk = pd.merge(pupil_data_risk, pupil_info_FSM_PP, on = ["Postcode", "Pupil_Name"])

df_to_show = final_pupil_data[["Postcode","Pupil_Name", "Value", "Indices_of_Deprivation"]]
df_to_show = pd.pivot_table(df_to_show, index = "Postcode", columns = "Indices_of_Deprivation", values = "Value")
Pupil_name_postcode = pupil_info[["Postcode", "Pupil_Name"]]
df_to_show = pd.merge(df_to_show, Pupil_name_postcode, on = "Postcode")
df_to_show.columns = df_to_show.columns.str.strip().str.replace(' ', '_').str.replace('.', '').str.replace('(', '').str.replace(')', '')
df_to_show.insert(1, "Pupil_Name", df_to_show.pop("Pupil_Name"))

########## Changing column names to just letters
# Creating key for IMD table
"""
IMD_table_key_dict = {
                 "IMD Domain": ["Income Deprivation Domain", "Employment Deprivation Domain", "Education,Skills and Training Domain",
                                "Health Deprivation and Disability Domain", "Crime Domain", "Barriers to Housing and Services Domain",
                                "Living Environment Deprivation Domain", "Income Deprivation Affecting Children Index IDACI", "Income Deprivation Affecting Older People Index IDAOPI"],
                 "Column name": ["B", "C", "D", "E", "F", "G", "H", "I", "J"]}
IMD_table_key = pd.DataFrame(IMD_table_key_dict)
"""
# Changing column names

df_to_show = df_to_show.rename(columns= {'a_Index_of_Multiple_Deprivation_IMD' : "A_Index_of_Multiple_Deprivation_IMD",
                                        'b_Income_Deprivation_Domain' : "B",
                                       'c_Employment_Deprivation_Domain' : "C",
                                       'd_Education,_Skills_and_Training_Domain' : "D",
                                       'e_Health_Deprivation_and_Disability_Domain' : "E",
                                       'f_Crime_Domain' : "F",
                                       'g_Barriers_to_Housing_and_Services_Domain' : "G",
                                       'h_Living_Environment_Deprivation_Domain' : "H",
                                       'i_Income_Deprivation_Affecting_Children_Index_IDACI' : "I",
                                       'j_Income_Deprivation_Affecting_Older_People_Index_IDAOPI' : "J"})
########




conditions = [
    (pupil_data_risk["Value"] <= 3),
    (pupil_data_risk["Value"] > 3) & (pupil_data_risk["Value"] <= 6),
    (pupil_data_risk["Value"] > 6)
    ]

colours = ["red", "orange", "green"]


pupil_data_risk["Colour"] = np.select(conditions,colours)
# postcode_colour = pupil_data_risk[["Postcode", "Colour"]]

fsm_conditions = [
    (pupil_data_risk['Colour'] == "red") & (pupil_data_risk["FSM"] == "Unknown"),
    (pupil_data_risk['Colour'] == "red") & (pupil_data_risk["FSM"] == "No"),
    (pupil_data_risk['Colour'] == "orange") & (pupil_data_risk["FSM"] == "Unknown"),
    (pupil_data_risk['Colour'] == "red") & (pupil_data_risk["FSM"] == "Yes"),
    
    (pupil_data_risk['Colour'] == "orange") & (pupil_data_risk["FSM"] == "Yes"),
    (pupil_data_risk['Colour'] == "green") & (pupil_data_risk["FSM"] == "Yes"),
    (pupil_data_risk['Colour'] == "green") & (pupil_data_risk["FSM"] == "Unknown"),
    
    (pupil_data_risk['Colour'] == "orange") & (pupil_data_risk["FSM"] == "No"),
    (pupil_data_risk['Colour'] == "green") & (pupil_data_risk["FSM"] == "No")
    
    ]

Risk_level = ["High", "High", "High", "High", "Medium","Medium", "Medium", "Low", "Low"]

pupil_data_risk["Risk_level"]= np.select(fsm_conditions, Risk_level)

colour_conditions = [
    (pupil_data_risk["Risk_level"] == "High"),
    (pupil_data_risk["Risk_level"] == "Medium"),
    (pupil_data_risk["Risk_level"] == "Low")
    ]

colour_risk_fsm = ["red", "orange", "green"]
HM_intensity_nums = [1,0.5,0]
pupil_data_risk["colour_fsm"]= np.select(colour_conditions, colour_risk_fsm)

postcode_colour = pupil_data_risk[["Postcode", "colour_fsm", "FSM", "Risk_level"]]
Risk_text = ["High Risk", "Medium Risk", "Low Risk"]
postcode_colour["HM_intensity"] = np.select(colour_conditions, HM_intensity_nums)
postcode_colour["Risk_text"] = np.select(colour_conditions, Risk_text)



IMD_only_colour_conditions = [
    (pupil_data_risk['Colour'] == "green"),
    (pupil_data_risk['Colour'] == "orange"),
    (pupil_data_risk['Colour'] == "red")
    ]

IMD_risk_level = ["Low", "Medium", "High"]

pupil_data_risk["IMD_risk"] = np.select(IMD_only_colour_conditions, IMD_risk_level )

"""
pie_chart_conditions = [
    (postcode_colour["Risk_level"] == "red"),
    (postcode_colour["Risk_level"] == "orange"),
    (postcode_colour["Risk_level"] == "green")
    ]

risk_attributes = ["High Risk", "Mid Risk", "Low Risk"]

postcode_colour["Risk"] = np.select(pie_chart_conditions, risk_attributes)

In_risk_postcodes = final_pupil_data.Postcode.unique()
"""


# =============================================================================
# Preparing for plotting - postcodes to lat,long
# =============================================================================
for i in range(len(pupil_info_postcodes)):
    
    postcode = pupil_info_postcodes.at[i, "Postcode"]
    res = requests.get(postcode_API_link + postcode)
    postcode_data_json = res.json()
    
    postcode_tuple = postcode_data_json["data"]["postcode"]
    latitude_tuple = postcode_data_json["data"]["latitude"]
    longitude_tuple = postcode_data_json["data"]["longitude"]
    
    Postcode_Lat_Long_df["Postcode"] = [postcode_tuple]
    Postcode_Lat_Long_df["Latitude"] = [latitude_tuple]
    Postcode_Lat_Long_df["Longitude"] = [longitude_tuple]
    
    final_postcode_lat_long_df = pd.concat([final_postcode_lat_long_df, Postcode_Lat_Long_df], ignore_index=True) 

final_postcode_lat_long_df.Postcode = final_postcode_lat_long_df.Postcode.str.replace(" ", "")

pc_lat_long_colour = pd.merge(final_postcode_lat_long_df, postcode_colour, on = "Postcode")
HM_pc_lat_long = pc_lat_long_colour[["Latitude", "Longitude", "HM_intensity"]]
HM_data = list(zip(HM_pc_lat_long.Latitude, HM_pc_lat_long.Longitude, HM_pc_lat_long.HM_intensity))
########## Using API to make school the centre of the map - dynamically depending on school postcode
postcode = school_info.at[0, "Postcode"]

res_school = requests.get(postcode_API_link + postcode)
school_postcode_json = res_school.json()

postcode_tuple = school_postcode_json["data"]["postcode"]
latitude_tuple = school_postcode_json["data"]["latitude"]
longitude_tuple = school_postcode_json["data"]["longitude"]
#############
# Join pc_lat_long_colour with df_to_show on postcode - move making of df_to_show - higher in the code
##########
pc_lat_long_colour = pd.merge(pc_lat_long_colour, df_to_show, on = "Postcode")


######
# Adding more data to folium markers using HTML
#####


def popup_html(row):
    i = row
    child_name = pc_lat_long_colour['Pupil_Name'].iloc[i]
    Postcode = pc_lat_long_colour['Postcode'].iloc[i]
    IMD_number = pc_lat_long_colour['A_Index_of_Multiple_Deprivation_IMD'].iloc[i]
    FSM = pc_lat_long_colour['FSM'].iloc[i]
    Colour_fsm = pc_lat_long_colour['colour_fsm'].iloc[i]
    Risk_Text = pc_lat_long_colour['Risk_text'].iloc[i]
    
    left_col_color = "#19a7bd"
    right_col_color = "#f2f0d3"
    
    html = """<!DOCTYPE html>
<html>


<body style="background-color: #ff795d;"><h4 style="color: """+ Colour_fsm +""";"margin-bottom:10"; width="200px">{}</h4>""".format(Risk_Text) + """
</p></body>

</head>
    <table style="height: 126px; width: 350px;">
    
<tbody>
<tr>
<td style="background-color: """+  Colour_fsm +""";"><span style="color: #ffffff;">Child name</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(child_name) + """
</tr>  
<tr>
<td style="background-color: """+ Colour_fsm +""";"><span style="color: #ffffff;">Postcode</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(Postcode) + """
</tr>
<tr>
<td style="background-color: """+ Colour_fsm +""";"><span style="color: #ffffff;">IMD Number</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(IMD_number) + """
</tr>
<tr>
<td style="background-color: """+ Colour_fsm +""";"><span style="color: #ffffff;">Free School Meals</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(FSM) + """
</tr>
</tbody>
</table>
</html>
"""
    return html   







#######=============================================
# Creating interactive map and heatmap using folium
#####=================================================



map = folium.Map(location=[latitude_tuple, longitude_tuple], zoom_start=13) # change to Lat and Long of

for i in range(0,len(pc_lat_long_colour)):
    
    html = popup_html(i)
    popup = folium.Popup(folium.Html(html, script = True), max_width=500)
    folium.Marker(
        location = [pc_lat_long_colour.iloc[i]["Latitude"], pc_lat_long_colour.iloc[i]["Longitude"]],
        popup = popup,
        icon = folium.Icon(color = pc_lat_long_colour.iloc[i]["colour_fsm"])).add_to(map)
map.save("Liverpool_school_map.html")


mapObj = folium.Map(location=[latitude_tuple, longitude_tuple], zoom_start = 13)
HeatMap(HM_data).add_to(mapObj)
mapObj.save("Liverpool_school_Heatmap.html")








# =============================================================================
# saving foilum map and Heatmap as static png image for use in report using selenium
# =============================================================================

delay = 5
fn = "Liverpoool_school_map.html"
mapurl = "file://{path}/{mapfile}".format(path = os.getcwd(), mapfile = fn)
map.save(fn)
##########
chromedriverlink = os.getcwd()+"/chromedriver 3"
browser = webdriver.Chrome(chromedriverlink)
browser.get(mapurl)
#############
time.sleep(delay)
browser.save_screenshot("map.png")
browser.quit()

######## Heatmap png
delay = 10
fn = "Liverpool_school_Heatmap.html"
mapurl = "file://{path}/{mapfile}".format(path = os.getcwd(), mapfile = fn)

##########
browser = webdriver.Chrome(chromedriverlink)
browser.get(mapurl)

#############
time.sleep(delay)
browser.save_screenshot("Heatmap.png")
browser.quit()







# =============================================================================
# Creating df for report with corrosponding colours
# =============================================================================



cols = df_to_show.columns
df_to_show[cols[2:]] = df_to_show[cols[2:]].apply(pd.to_numeric, downcast = "integer", errors='coerce')




pupil_data_risk_for_report = pupil_data_risk[["Postcode", "Pupil_Name", "FSM", "Value", "Risk_level"]]
pupil_data_risk_for_report.Risk_level=pd.Categorical(pupil_data_risk_for_report.Risk_level, categories = ["High", "Medium", "Low"]) # move to bottom
pupil_data_risk_for_report = pupil_data_risk_for_report.sort_values(["Risk_level","Value"], ascending = [True,True]) # move to bottom
pupil_data_risk_for_report["Value"] = pupil_data_risk_for_report["Value"].astype("int8")


pupil_data_risk_for_report = pupil_data_risk_for_report.rename(columns = {"Pupil_Name" : "Pupil name",
                                                                          "FSM": "Free school meals",
                                                                          "Value": "IMD number",
                                                                          
                                                                          })

###### Creating frequency table

count_table_pupil_risk = pupil_data_risk_for_report.Risk_level.value_counts()
count_table_pupil_risk = count_table_pupil_risk.to_frame().reset_index()
count_table_pupil_risk.rename(columns = {'index':"Risk_level",
                                         "Risk_level": "Number of Pupils"},
          inplace = True)
count_table_pupil_risk = count_table_pupil_risk.sort_index(ascending=False)

########
def highlight(df):
    if df.A_Index_of_Multiple_Deprivation_IMD <= 3:
        return ['background-color: #ff795d']*12
    if (df.A_Index_of_Multiple_Deprivation_IMD > 3) & (df.A_Index_of_Multiple_Deprivation_IMD <= 6):
        return ['background-color: #ff8d33']*12
    if df.A_Index_of_Multiple_Deprivation_IMD > 6:
        return ['background-color: #70ff70']*12
    
#######
def highlight2(df):
    if df.Risk_level == "High":
        return ['background-color: #ff795d']*5
    if df.Risk_level == "Medium":
        return ['background-color: #ff8d33']*5
    if df.Risk_level == "Low":
        return ['background-color: 70ff70']*5
    
#######
def highlight3(df):
    if df.Risk_level == "High":
        return ['background-color: #ff795d']*2
    if df.Risk_level == "Medium":
        return ['background-color: #ff8d33']*2
    if df.Risk_level == "Low":
        return ['background-color: 70ff70']*2
    
    
    




df_to_show = df_to_show.sort_values(by = "A_Index_of_Multiple_Deprivation_IMD")
# df_styled = df_to_show.style.hide_index()
df_styled = df_to_show.style.apply(highlight, axis = 1)

#pupil_data_risk_for_report_styled = pupil_data_risk_for_report.style.hide_index()


pupil_data_risk_for_report_styled = pupil_data_risk_for_report.style.apply(highlight2, axis = 1)

count_table_pupil_risk_for_report = count_table_pupil_risk.style.apply(highlight3, axis = 1)

######### Piechart
piechart_numbers = postcode_colour['Risk_level'].value_counts()

piechart1 = piechart_numbers.plot(kind = "pie",
                      colors = ['green', 'red', 'orange'],
                      autopct = '%1.0f%%',
                      shadow = True,
                      title = "Percentage of pupils categorised as High, Mid and Low risk")

piechart1.figure.savefig("piechart_for_report.png")

#########
######### Piechart
piechart_numbers_imd = pupil_data_risk['IMD_risk'].value_counts()

piechart2 = piechart_numbers_imd.plot(kind = "pie",
                      colors = ['green', 'red', 'orange'],
                      autopct = '%1.0f%%',
                      shadow = True,
                      title = "Percentage of pupils categorised as High, Mid and Low risk using ONLY IMD")


piechart2.figure.savefig("piechart_using_IMD.png", bbox_inches='tight')
#########

#df_styled = df_styled.style.hide_index()
dfi.export(df_styled, "table_for_report.png")

#IMD_table_key = IMD_table_key.style.hide_index()
#dfi.export(IMD_table_key, "IMD_table_key.png")

#pupil_data_risk_for_report = pupil_data_risk_for_report.style.hide_index()
dfi.export(pupil_data_risk_for_report_styled, "pupil_data_risk_for_report.png")
dfi.export(count_table_pupil_risk_for_report, "count_table_pupil_risk_for_report.png")


dfi.export(pupil_info, "Pupil_info.png")







Name = "Varun"
SCHOOL_NAME = str("Liverpool School")



class PDF(FPDF):
    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')
        
    def header(self):
        self.set_y(5)
        # Select Arial bold 15
        self.set_font('Arial', 'I', 8)
        # Framed title
        self.cell(0, 10, "Produced for "+SCHOOL_NAME+" on "+date, align =  'L')

# =============================================================================
# Creating PDF report using fpdf package
# =============================================================================
pdf = PDF()

pdf.alias_nb_pages()
# first page - all text and explaining how to use report - what the data sources are and how they are produced
pdf.add_page()
pdf.set_font("Arial", style = "B",  size = 24)

pdf.set_x(20)
pdf.set_y(25)
pdf.multi_cell(200, 4.6, txt = SCHOOL_NAME+" \n\nDigital Deprivation Report", align = "C")
pdf.image("Contents_table.png", x = 12, y = 40, w= 200 , h=0)
# First Paragraph text
pdf.set_font("Arial",  size = 12)
pdf.set_x(25)
pdf.set_y(200)
pdf.set_left_margin(22)
pdf.multi_cell(200, 4.6 , txt= "This report displays open source data from the English Indices of Deprivation 2019(IoD2019)"
               "\nalongside pupil data that has been provided by "+ SCHOOL_NAME+" to help identify "
               "\npupils who may be affected by Digital Deprivation through categorisation into three risk "
               "\nlevels of High, Medium and Low."
               "\n\nThis is an automated report that is best used alongside the interactive pupil risk map and "
               "\nHeatmap that can be found in the same folder as this report, all of which have been "
               "\nproduced custom for "+SCHOOL_NAME+" by a software."
               "\n\nThe contents of this report are intended to be used complementarily to "+SCHOOL_NAME+ "'s"
               "\nknowledge and internal data regarding students. It should be used as a platform to"
               "\nstimulate further discussions between schools and its governor for future decisions and"
               "\nadditional funding for certain pupils. This is important to note, as Postcode and Area data"
               "\ncannot be used to represent individuals.", align ="L") 






#########
pdf.add_page()
pdf.set_x(15)
pdf.set_y(25)
pdf.set_font("Arial",style = "B",   size = 18)

pdf.multi_cell(200, 4.6, txt = "What is the IMD and how will this report be using it?", align = "L")

pdf.set_font("Arial",  size = 12)
pdf.set_x(20)
pdf.set_y(40)
pdf.multi_cell(200, 4.6, "The English Indices of Deprivation measure relative levelsof deprivation in 32,844 small "
                       "\nareas or neighbourhoods,called Lower-layer Super Output Areas, in England."
                       "\n\nSince the 1970s the Ministry of Housing, Communities and Local Government and its "
                       "\npredecessors have calculated local measures of deprivation in England. This Statistical"
                       "\nRelease contains the latest iteration of these statistics, the English Indices of Deprivation"
                       "\n2019 (IoD2019). The IoD2019 is an update to the 2015 Indices and retains the same model"
                       "\nof multiple deprivation, using the same approach and utilising data inputs from the most"
                       "\nrecent time points where possible. "
    
                       "\n\nThe Index of Multiple Deprivation (IMD) is the official measure of"
                       " relative deprivation in \nEngland and is part of a suite of outputs "
                       "that form the Indices of Deprivation (IoD). \nIt follows an "
                       "established methodological framework in broadly defining"
                       " deprivation \nto encompass a wide range of an individuals living"
                       " conditions. People may be considered \nto be living in poverty if "
                       "they lack the financial resources to meet their needs, whereas people \ncan be regarded as deprived if they lack any kind of resources, just not income.", align = "l")

pdf.set_font("Arial",style = "B",   size = 14)
pdf.multi_cell(200, 4.6, txt = "\n\nWhat do Deciles mean? (1-10)", align = "L" )
pdf.set_font("Arial",  size = 12)
pdf.multi_cell(200, 4.6, txt = "\nA decile is a quantitative method of splitting up a set of ranked data into 10 equally large"
               "\nsubsections."
               "A decile rank arranges the data in order from lowest to highest and is done on a "
               "\nscale of one to 10 where each successive number corresponds to an increase of "
               "\n10 percentage points.")

pdf.image("Domains_IMD.png", x = 35, y= 155, w=125, h= 0)
pdf.image("IMD_value_categorisation.png", x= 35, y = 205, w = 140, h= 0 )





############# Second page - Main dataset - highlighted individual using IMD and FSM

pdf.add_page()
pdf.image("FSM_IMD_risk_table.png", x= 40, y = 17, w = 130, h = 0 )
pdf.set_x(15)
pdf.set_y(96)
pdf.set_font("Arial",style = "U", size = 11)
pdf.multi_cell(200, 4.6, txt = "In Risk Pupils Dataset", align = "L")
pdf.set_x(130)
pdf.set_y(96)
pdf.cell(200, 4.6, txt = "Number of pupils per Risk Level", align = "C")


pdf.image("pupil_data_risk_for_report.png", x = 10, y= 102, w = 85, h = 160 )
pdf.image("count_table_pupil_risk_for_report.png", x = 110, y = 110, w = 60, h = 0)
pdf.image("piechart_for_report.png", x = 95, y = 190, w = 95, h = 0)




###############

# Third page - Landscape with map
# Adding image
pdf.add_page()
pdf.image("map.png",x=15, y=25, w=180, h=0 )
pdf.set_x(25)
pdf.set_y(125)
pdf.set_font("Arial", size = 11)
pdf.multi_cell(200, 4.6, txt = "Figure 3. This map corelates to the dataset in the previous page with the marker colour"
                              "\n representing the pupils risk level of digital poverty")
pdf.image("Heatmap.png", x=15, y=150, w= 180, h=0)
pdf.set_x(25)
pdf.set_y(250)
pdf.multi_cell(200, 4.6, txt = "Figure 4. This Heatmap works alongside Figure 3 to illustrate areas that have higher "
                               "\nnumbers of pupils identified as high risk")


###########

# Fourth page - Landscape with corrosponding dataframe to the map on previous page
# Adding new page
pdf.add_page(orientation = 'L')
pdf.set_font("Arial",style = "B",   size = 18)
pdf.set_x(150)
pdf.set_y(20)
pdf.cell(200, 4.6, txt = "                                Digital Deprivation Categorisation using IMD only", align = "C")

pdf.image("IMD_table_key.png", x = 140, y = 30, w = 80, h= 0  )
pdf.image("table_for_report.png", x = 15, y = 28, w= 120, h = 170)
pdf.image("piechart_using_IMD.png", x= 150, y= 120, w = 110, h = 0 )

# pdf.image("")


# Fifth page Adding new page - Original dataset
pdf.add_page()
pdf.set_x(15)
pdf.set_y(25)
pdf.set_font("Arial",style = "B",   size = 20)
pdf.multi_cell(200, 4.6, txt = "Original Dataset provided by " +SCHOOL_NAME , align = "L")
pdf.image("Pupil_info.png", x = 45, y = 35, w= 115, h=0 )


pdf.output(name = "Liverpool_school_risk_report.pdf")
########



###
# Make new dataset and report without child names
###



































                 




