import pandas as pd
import numpy as np
import math
import streamlit as st
import requests
import plotly.express as px
import altair as alt
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="South Korea's Exports and Companies",
                   page_icon="🇰🇷",
                   layout="wide")

# used to extract south korea's data using api
country_symbol = 'askor'

# side bar for navigation
st.sidebar.title("Navigation")
mode = st.sidebar.radio("Choose an option", 
                        ["South Korea Exports", "South Korea Companies"])


if mode == "South Korea Exports":
    
    # title for export countries
    st.title("South Korea's Export Destinations")
    
    # extract data 
    export_api = requests.get('https://oec.world/api/olap-proxy/data?cube=trade_i_baci_a_92&drilldowns=Year%2CImporter%20Country&measures=Trade%20Value&parents=true&Year=2022&Exporter%20Country=askor&properties=Importer%20Country%20ISO%203')
    export_api.raise_for_status()
    api_data = export_api.json().get('data', [])
    full = pd.DataFrame(api_data)
    full = full.sort_values(by=['Trade Value'], ascending=False)

    # create percentage column
    full = full.assign(Percentage=((full['Trade Value'] / full['Trade Value'].sum()) * 100).round(2))

    # trade values column for displaying the symbol
    full["Trade Values"] = full["Trade Value"].apply(
        lambda x: f"${x / 1_000_000:.2f} M" if x < 1_000_000_000 else f"${x / 1_000_000_000:.2f} B"
        if x >= 1_000_000_000 else None
    )
    full = full[['Continent','Country','Trade Value','Trade Values','Percentage']]

    # utilize log to reduce number of outliers
    full['Log Trade Value'] = np.log1p(full['Trade Value'])
        
    
    # select box for map type selection
    map_type = st.selectbox(
        "Choose Map Type",
        options=["Treemap", "Choropleth"]
    )

    # treemap 
    if map_type == "Treemap":
        fig3 = px.treemap(
            full[full["Trade Value"] > 0], # select countries where trade value is bigger than 0
            path=["Continent", "Country"], # continent -> country
            values="Trade Value", 
            
            # display the following data when hovered
            hover_data={ 
                "Country": False,          
                "Trade Values": True,      
                "Percentage": True,       
                "Continent": False,    
                "Trade Value": False,  
                "Log Trade Value": False, 
            },
            color="Percentage",  
            color_continuous_scale="Viridis", 
            title='Tree Map on Export Countries'
        )
        
        # update layout
        fig3.update_layout(
            title = dict(x=0.5,xanchor='center',font_size=20)
        )
        # display
        st.plotly_chart(fig3)
        
    # choropleth map
    elif map_type == "Choropleth":
        figs = px.choropleth(
            full,
            # column containing country names
            locations="Country",
            # match locations using country names
            locationmode="country names",  
            color="Log Trade Value",      
            hover_name="Country",          
            hover_data={
                "Country": False,          
                "Trade Values": True,      
                "Percentage": True,       
                "Continent": True,
                "Trade Value": False,
                "Log Trade Value": False
            },
            color_continuous_scale="viridis", 
            width=1000,                       
            height=500                         
        )
    
        figs.update_layout(
            paper_bgcolor="black",           
            plot_bgcolor="black",             
            font=dict(color="white"),        
            geo=dict(
                bgcolor="black"               
            ),
            margin=dict(
                l=25,  
                r=25,
                t=50,  
                b=25   
            ),
            title = dict(text='Choropleth Map',x=0.5,
                        font_size=20)
        )
        # display map
        st.plotly_chart(figs)

    # separator
    st.markdown("---")

    # title for export products
    st.title("South Korea's Export Products")

    # extract data using api
    export_product_api = requests.get('https://oec.world/olap-proxy/data?cube=trade_i_baci_a_92&Exporter+Country=askor&drilldowns=HS4&measures=Trade+Value&parents=true&Year=2022&sparse=false&locale=en&q=Trade Value,1')
    export_product_api.raise_for_status()
    api_datas = export_product_api.json().get('data', [])
    exports = pd.DataFrame(api_datas)
    exports = exports.sort_values(by='Trade Value', ascending=False).reset_index(drop=True)
    exports["Percentage"] = ((exports["Trade Value"] / exports["Trade Value"].sum()) * 100).round(2)
    exports = exports[['Section','HS2','HS4','HS4 ID','Trade Value','Percentage']]
    exports["Trade Values"] = exports["Trade Value"].apply(
        lambda x: f"${x / 1_000_000:.2f} M" if x < 1_000_000_000 else f"${x / 1_000_000_000:.2f} B"
        if x >= 1_000_000_000 else None
    )

    # create a new DataFrame where it groups it by section and sums of the percentage
    df = exports.groupby('Section')['Percentage'].sum().reset_index()
    df.loc[df['Percentage'] < 1, 'Section'] = 'Others'  # products with less than 1%, assign it to Others in Section
    df = df.groupby('Section', as_index=False).sum()  # combine Others into a single row 
        


    # select box for graph type
    map_types = st.selectbox(
        "Choose Map Type",
        options=["Treemap", "Bar Chart","Pie Chart"]
    )

    # treemap
    if map_types == "Treemap":
        export_tree = px.treemap(
        exports[exports["Trade Value"] > 0],
        path=["Section", "HS2","HS4"],  # section -> HS2 -> HS4
        values="Trade Value", 
        hover_data={"Percentage": True,"Trade Values":True,"Trade Value":False},  
        color="Percentage", 
        color_continuous_scale="Viridis",  
        title='Tree Map on Export Products'
    )
        export_tree.update_layout(
        title=dict(
            x=0.35,font_size=20
        ))
        st.plotly_chart(export_tree)

    # bar chart
    elif map_types == "Bar Chart":
        bar_export = px.bar(
        df,
        x='Section',
        y='Percentage',
        title='South Korea Export Sections',
        color='Section')
        bar_export.update_layout(
        title=dict(text='Bar Chart on Export Sectors',x=0.35,font_size=20))
        st.plotly_chart(bar_export)

    elif map_types == "Pie Chart":
        pie_export = px.pie(
            df,
            names='Section',
            values='Percentage',
            title='South Korea Export Sections'
    )  
        pie_export.update_layout(
            title=dict(text='Pie Chart on Export Sectors', x=0.35, font_size=20)
    )
        st.plotly_chart(pie_export)

    st.markdown("---")
    
    # dropdown for product and map type selection
    selected_product = st.selectbox(
        "Select a product",
        options=exports['HS4'].tolist()
    )
    map_type = st.selectbox(
        "Choose Map Type",
        options=["Choropleth", "Treemap"]
    )
    
    # submit button
    if st.button("Submit"):
        
        # find the index of the product
        try:
            export_product = exports.loc[exports['HS4'] == selected_product].index[0]
        except IndexError:
            st.error("Product not found.")
            st.stop()

        # use that index to locate the HS4 ID to import data
        export_urls = [
            f"https://oec.world/olap-proxy/data?cube=trade_i_baci_a_92&Exporter+Country={country_symbol}&HS4={exports.iloc[i]['HS4 ID']}"
            f"&Year=2022&drilldowns=Importer+Country&locale=en&measures=Trade+Value&parents=true&sparse=false"
            f"&properties=Importer+Country+ISO+3&q={exports.iloc[i]['HS4 ID']},1"
            for i in range(len(exports))
        ]
        try:
            export_api = requests.get(export_urls[export_product])
            export_api.raise_for_status()
            api_data = export_api.json().get('data', [])
            
            if not api_data:
                st.warning("No data available for this product.")
                st.stop()

            # preprocess the imported data
            ex_country = pd.DataFrame(api_data)
            ex_country["Trade Value"] = ex_country["Trade Value"].apply(lambda x: round(x / 1000000, 2))
            ex_country = ex_country.sort_values(by=['Trade Value'], ascending=False)
            ex_country = ex_country.assign(Percentage=((ex_country['Trade Value'] / ex_country['Trade Value'].sum()) * 100).round(2))
            ex_country["Trade Values"] = ex_country["Trade Value"].apply(
                lambda x: f"${x} M" if x < 1000 else f"${round(x / 1000, 2)} B"
            )
                
            # find missing countries by subtracting the full by ex_country 
            missing_countries = set(full['Country']) - set(ex_country['Country'])

            # for missing countries, add them to ex_country -> By just using ex_country, some countries are omitted from being displayed
            for country in missing_countries:
                ex_country = pd.concat([ex_country, pd.DataFrame({'Country': [country]})], ignore_index=True)

            # use log to reduce number of outliers
            ex_country['Log Trade Value'] = np.log1p(ex_country['Trade Value'])
                
            # choropleth
            fig = px.choropleth(
                ex_country,
                locations="Country",           
                locationmode="country names", 
                color="Log Trade Value",     
                hover_name="Country",         
                hover_data={
                    "Country": False,          
                    "Trade Values": True,      
                    "Percentage": True,        
                    "Continent": False,
                    "Trade Value": False,
                    "Log Trade Value": False
                },
                color_continuous_scale="viridis", 
                width=1000,                        
                height=500                        
            )
            fig.update_layout(
                paper_bgcolor="black",            
                plot_bgcolor="black",             
                font=dict(color="white"),       
                geo=dict(
                    bgcolor="black"             
                ),
                margin=dict(
                    l=25,  
                    r=25,  
                    t=50, 
                    b=25  
                ),
            )

            # treemap
            fig3 = px.treemap(
                ex_country[ex_country["Trade Value"] > 0],
                path=["Continent", "Country"], 
                values="Trade Value",  
                hover_data={
                    "Country": False,         
                    "Trade Values": True,     
                    "Percentage": True,        
                    "Continent": False,        
                    "Trade Value": False,     
                    "Log Trade Value": False, 
                },
                color="Percentage",  
                color_continuous_scale="Viridis",
            )
            fig3.update_layout(
                width=800,
                height=650
            )
    
            st.subheader(f"{selected_product} Export Countries")

            # display graphs based on user's input
            if map_type == "Choropleth":
                st.plotly_chart(fig)
            elif map_type == "Treemap":
                st.plotly_chart(fig3)
    
        except requests.RequestException as e:
            st.error(f"An error occurred while fetching the data: {str(e)}")

    # two columns to display dataframes
    col1, col2 = st.columns(2)
    with col1:
        # Reset the index
        fulls = full.reset_index(drop=True)
        st.dataframe(fulls.drop(columns=['Trade Value', 'Log Trade Value']))
    with col2:
        exporting = exports.reset_index(drop=True)
        st.dataframe(exporting.drop(columns=['Trade Value', 'HS4 ID']))

if mode == "South Korea Companies":
    # title
    st.title("Top South Korean Companies")

    # import company data
    company = pd.read_csv('skcompany.csv')
    
    # display the dataframe
    st.dataframe(company.iloc[:,1:].drop(columns=['Symbol','Market_Cap']))
    st.markdown("---")

    # brush used to select intervals
    brush = alt.selection_interval()

    # scatter plot between market cap and revenue
    points = alt.Chart(company).mark_point().encode(
        alt.X('Market_Cap:Q').scale(type='log').axis(ticks=False,grid=False,title='Market Cap (B)'),
        alt.Y('Revenue:Q').scale(type='log').axis(ticks=False,grid=False,title='Revenue (조)'),
        color = alt.condition(brush,'Sector:N',alt.value('lightgray')),
        tooltip=['Company']
    ).add_params(
            brush)
    
    # bar plot between sector and market cap
    bars = alt.Chart(company).mark_bar().encode(
        alt.X('Sector:N'),
        alt.Y('Market_Cap').axis(title='Market Cap (B)'),
        color='Sector:N',
        tooltip=['Company']).transform_filter(brush)
    # users could select intervals and bar chart would adjust based on selected data

    # string of sector and industry names 
    sector_options = [str(sector) for sector in company['Sector'].unique()]
    industry_options = [str(industry) for industry in company['Industry'].unique()]

    # use binding to display dropdown button
    sector_dropdown = alt.binding_select(options=sector_options, name='Sector ')
    selection = alt.selection_point(fields=['Sector'], bind=sector_dropdown)
    industry_dropdown = alt.binding_select(options=industry_options, name='Industry ')
    selections = alt.selection_point(fields=['Industry'], bind=industry_dropdown)

    # scatterplot that displays selected sector
    fig = alt.Chart(company).mark_point().encode(
        alt.X('Market_Cap:Q').scale(type='log').axis(ticks=False,grid=False,title='Market Cap (B)'),
        alt.Y('Revenue:Q').scale(type='log').axis(ticks=False,grid=False,title='Revenue (조)'),
        color = alt.condition(selection,'Sector:N',alt.value('black')),
        tooltip=['Company','Industry'] # when hovered display company name
    ).add_params(
            selection).interactive()
    
    # scatterplot that displays selected industry
    fig2 = alt.Chart(company).mark_point().encode(
        alt.X('Market_Cap:Q').scale(type='log').axis(ticks=False,grid=False,title='Market Cap (B)'),
        alt.Y('Revenue:Q').scale(type='log').axis(ticks=False,grid=False,title='Revenue (조)'),
        color = alt.condition(selections,'Sector:N',alt.value('black')),
        tooltip=['Company','Sector']
    ).add_params(
            selections).interactive()
    
    st.subheader('Interactive Scatter and Bar plots')
    st.altair_chart(points|bars)
    st.subheader('Select Sector or Industry')
    st.altair_chart(fig|fig2 )



