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
        'idx', 'label', 'customerid', 'transactionid', 'transactiondate',
        'productcategory', 'purchaseamount', 'customeragegroup', 'customergender',
        'customerregion', 'customersatisfaction', 'retailchannel'
    ]
    
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        st.error(f"Missing required logical fields: {', '.join(missing_fields)}")
        st.write(df.columns)
        st.stop()
        
    label_mapping = {'promising': 4, 'growth': 3, 'stable': 2, 'decline': 1}
    df['label'] = df['label'].astype(str).str.lower().str.strip().map(label_mapping).fillna(df['label'])
    df['label'] = pd.to_numeric(df['label'], errors='coerce')
    
    channel_mapping = {'online': 1, 'physical store': 2}
    df['retailchannel'] = df['retailchannel'].astype(str).str.lower().str.strip().map(channel_mapping).fillna(df['retailchannel'])
    df['retailchannel'] = pd.to_numeric(df['retailchannel'], errors='coerce')
    
    df = df.dropna()
    
    st.sidebar.header("Filters")
    
    categories = sorted(df['productcategory'].unique().tolist())
    categories.insert(0, "All")
    selected_category = st.sidebar.selectbox("Product Category", categories)
    
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['productcategory'].isin([selected_category])]
        
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"${filtered_df['purchaseamount'].sum():,.2f}")
        c2.metric("Total Transactions", int(filtered_df['transactionid'].nunique()))
        c3.metric("Avg Satisfaction", f"{filtered_df['customersatisfaction'].mean():.2f}/5")
        c4.metric("Active Customers", int(filtered_df['customerid'].nunique()))
        
        col1, col2 = st.columns(2)
        
        with col1:
            revenue_by_region = filtered_df.groupby('customerregion', as_index=False)['purchaseamount'].sum()
            fig_region = px.bar(
                revenue_by_region,
                x='customerregion',
                y='purchaseamount',
                title='Revenue by Region',
                labels={'customerregion': 'Region', 'purchaseamount': 'Revenue'}
            )
            st.plotly_chart(fig_region, use_container_width=True)
            
        with col2:
            fig_age = px.pie(
                filtered_df,
                names='customeragegroup',
                values='purchaseamount',
                title='Revenue Distribution by Age Group'
            )
            st.plotly_chart(fig_age, use_container_width=True)
            
        fig_scatter = px.scatter(
            filtered_df,
            x='customersatisfaction',
            y='purchaseamount',
            color='label',
            title='Customer Behavior: Purchase Amount vs Satisfaction',
            labels={'customersatisfaction': 'Customer Satisfaction', 'purchaseamount': 'Purchase Amount ($)', 'label': 'Behavior Segment (4=Promising, 1=Decline)'},
            hover_data=['customerid', 'productcategory']
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.subheader("Filtered Data")
        st.dataframe(filtered_df, hide_index=True)

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
