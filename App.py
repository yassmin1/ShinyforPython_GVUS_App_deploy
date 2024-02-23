from shiny import App, render, ui,reactive
import pandas as pd
from pathlib import Path
import  matplotlib.pyplot as plt 
import shinyswatch
from shinywidgets import output_widget, render_widget
import plotly.express as px
import asyncio
from ipyleaflet import Map,LayerGroup,Circle,Heatmap,LayersControl,LegendControl
from ipywidgets import Layout
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import warnings
warnings.filterwarnings('ignore')

# importing dataset-------------------------------------
all_incidents = pd.read_csv(Path(__file__).parent / "all_incident_census.csv")
# option lists---------------------------------------------------------------------------------------
options_state = all_incidents["state"].sort_values().unique().tolist()
options_year=all_incidents["year"].sort_values().unique().astype(int).tolist()
#----color function----------------------------

def assign_colors_based_on_value_counts(values):
    # Get value counts
    value_counts = values.value_counts()

    # Create a color map
    colors = plt.cm.tab10(np.linspace(0, 1, len(value_counts)))

    # Create a dictionary to store value-color mapping
    value_color_mapping = {}

    # Assign a color to each value based on its frequency
    for value, color in zip(value_counts.index, colors):
        value_color_mapping[value] =  matplotlib.colors.rgb2hex(color.tolist()[:-1])

    return value_color_mapping

#---------- ui input and output-----------------------------------------------------    

app_ui = ui.page_fixed(
        shinyswatch.get_theme('superhero'),  
        ui.layout_columns( ui.tags.h3('DATA'),#ui.img(src='Logo.png',height='50',width='100'),
                          ui.panel_title(ui.tags.h1("Gun Violence in USA",align='center'), window_title="GVUS_App" ),
                        col_widths=(4,8),height='100'),
        
        #ui.markdown("Gun violence refers to the use of firearms to harm or intimidate individuals or groups. 
        # It encompasses a range of acts, from homicides and assaults to suicides and accidental shootings. 
        # Gun violence is a complex societal issue with far-reaching consequences, affecting communities, 
        # families, and individuals"),
        
        ui.layout_sidebar(    
                ui.sidebar(
                    
                   
                    ui.input_selectize("state", ui.tags.h3("State"), choices=options_state,selected=['Illinois'],multiple=False),
                    ui.input_slider("year", ui.tags.h3("Year"), min=options_year[0],max=options_year[-1],value=[2013,2020],step=1,ticks=True,sep=''),              
                     width='250px',   
                        ),     
                
                
          
                    # ----outputs---------
                ui.layout_columns(   
                    ui.card(                                 
                        ui.card_header(ui.tags.h2("Gun Fatality in US (2013-2022)")) ,
                        output_widget("map_all", width="auto", height="auto"),
                        full_screen=True,
                    ) ,
                    ui.card(
                        ui.card_header(ui.tags.h2("Gun Fatality by State and year")) ,
                        output_widget("map", width="auto", height="auto"),
                        full_screen=True,
                    ),
                    ui.card(
                        ui.card_header(ui.tags.h2("Gun Fatality Table")),
                        ui.output_data_frame("dataframe_state"),
                        full_screen=True,
                    ),
                    ui.card(
                        ui.card_header(ui.tags.h2("Gun Fatality Statistics")),   
                        output_widget("barchart",width="auto", height="auto"),
                        full_screen=True,               
                    ) ,   
                    col_widths=(6,6,6,6) ,row_heights='grid-auto-rows' ,  
                 ),
                    
            ),
        )
def server(input, output, session):
    
    @reactive.calc()
    def filter_dataset():
        df_state =all_incidents[all_incidents['state'].isin([input.state()])]
        
        return df_state[df_state['year'].isin(input.year())]
    
    @reactive.calc
    def groups():
        sub_df=filter_dataset()
        return sub_df.groupby(['State'])['n_killed'].value_counts().rename('Incident Count').reset_index()    
    @render.data_frame
    
    def dataframe_state():
        return groups()
        
     
    @output
    @render_widget
       
    def barchart():  

        g = px.bar(groups(),
                   y='n_killed',
            x='Incident Count',text_auto='0.0s',           
            
            labels={'n_killed':'Fatality Number'}, 
            height=300,width=400,template="none",
            orientation='h', 
   
            )
        g.update_layout(
       font=dict(
        #family="Courier New, monospace",
        size=11,
        color="RebeccaPurple"
    ), margin=dict(l=30, r=20, t=20, b=30), )

        

        return g

    @render_widget      
    def map_all():
        map11=Map(center=(33,-95),zoom=4,layout=Layout(width='100%', height='300px'))
        heatmap = Heatmap(locations=all_incidents[['Latitude','Longitude','n_killed']].values.tolist(), radius=10, blur=10)
        map11.add_layer(heatmap)
        return map11     
       
    @render_widget          
    def map():
        colors_set = assign_colors_based_on_value_counts(filter_dataset()['n_killed'])
        filter_dataset()['colors']=filter_dataset()['n_killed'].replace(colors_set)
        locat=filter_dataset()[['Latitude','Longitude','n_killed','colors']].values.tolist()
        # the map and the heatmap
        map11=Map(center=((filter_dataset()['Latitude'].mean(),filter_dataset()['Longitude'].mean())),zoom=5,layout=Layout(width='100%', height='300px'))
        heatmap = Heatmap(locations=locat, radius=10, blur=5)
        map11.add(heatmap)

        # Create a list of markers using list comprehension
        markers = LayerGroup(layers=[Circle(location=(lat, lon), 
                  
                   radius=500, color=color,fill_color=color,fill=False,weight=1 
                   )
           for lat, lon, value,color in locat])

        # Add the markers to the map
        map11.add(markers)
        legend = LegendControl(legend=colors_set,name='', position="bottomright")  
        #custom_layout = Layout(width='20px', height='100px')
        #legend.layout=custom_layout
        map11.add_control(legend)
      
        # Display the map
        map11.add(LayersControl(position='topright'))
        return map11
    
    
    @reactive.effect    
    @reactive.event(input.year)
    def _():
        map.center=(filter_dataset()['Latitude'].mean(),filter_dataset()['Longitude'].mean())
        map.zoom=4
          
# to add a static doc such as logo or img
www_dir = Path(__file__).parent / "www"
app = App(app_ui, server,static_assets=www_dir)
