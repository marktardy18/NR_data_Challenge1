import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Nova Retail Data Dashboard")
st.subheader("Customer Behavior Lead Growth")

try:
    df = pd.read_csv("NR_dataset.csv")
    
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    required_fields = [
        'customerid', 'purchaseamount', 'customersatisfaction', 
        'retailchannel', 'productcategory'
    ]
    
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        st.error(f"Missing required logical fields: {', '.join(missing_fields)}")
        st.write(df.columns)
        st.stop()
        
    channel_mapping = {'online': 1, 'physical store': 2}
    if df['retailchannel'].dtype == object:
        df['retailchannel'] = df['retailchannel'].astype(str).str.lower().str.strip().map(channel_mapping).fillna(df['retailchannel'])
    df['retailchannel'] = pd.to_numeric(df['retailchannel'], errors='coerce')
    
    df = df.dropna()
    
    st.sidebar.header("Filters")
    categories = sorted(df['productcategory'].astype(str).unique().tolist())
    categories.insert(0, "All")
    selected_category = st.sidebar.selectbox("Product Category", categories)
    
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['productcategory'].isin([selected_category])]
        
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        agg_df = filtered_df.groupby('customerid', as_index=False).agg(
            total_customer_spend=('purchaseamount', 'sum'),
            average_customer_satisfaction=('customersatisfaction', 'mean')
        )
        
        avg_spend = agg_df['total_customer_spend'].mean()
        
        fig = px.scatter(
            agg_df,
            x='average_customer_satisfaction',
            y='total_customer_spend',
            hover_data=['customerid'],
            title='Flight Risk vs. Upsell Matrix: Spend vs. Satisfaction',
            labels={
                'average_customer_satisfaction': 'Average Customer Satisfaction',
                'total_customer_spend': 'Total Customer Spend'
            }
        )
        
        fig.add_vline(x=3.0, line_dash="dash", line_color="red")
        fig.add_hline(y=avg_spend, line_dash="dash", line_color="green")
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(filtered_df, hide_index=True)

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    st.error(f"An error occurred: {e}")
