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
    df['label'] = df['label'].astype(str).str.lower().str.strip().map(label_mapping)
    
    channel_mapping = {'online': 1, 'physical store': 2}
    df['retailchannel'] = df['retailchannel'].astype(str).str.lower().str.strip().map(channel_mapping)
    
    df = df.dropna()
    
    categories = sorted(df['productcategory'].unique().tolist())
    categories.insert(0, "All")
    
    st.sidebar.header("Filters")
    selected_category = st.sidebar.selectbox("Product Category", categories)
    
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['productcategory'].isin([selected_category])]
        
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        metric_col1.metric("Total Revenue", f"${filtered_df['purchaseamount'].sum():,.2f}")
        metric_col2.metric("Total Transactions", int(filtered_df['transactionid'].nunique()))
        metric_col3.metric("Avg Satisfaction", f"{filtered_df['customersatisfaction'].mean():.2f}")
        metric_col4.metric("Active Customers", int(filtered_df['customerid'].nunique()))
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            revenue_by_region = filtered_df.groupby('customerregion', as_index=False)['purchaseamount'].sum()
            fig_region = px.bar(
                revenue_by_region,
                x='customerregion',
                y='purchaseamount',
                title='Revenue by Region',
                labels={'customerregion': 'Region', 'purchaseamount': 'Revenue ($)'}
            )
            st.plotly_chart(fig_region, use_container_width=True)
            
        with chart_col2:
            fig_segment = px.pie(
                filtered_df,
                names='label',
                values='purchaseamount',
                title='Revenue by Customer Segment (4=Promising, 1=Decline)'
            )
            st.plotly_chart(fig_segment, use_container_width=True)
            
        fig_scatter = px.scatter(
            filtered_df,
            x='customersatisfaction',
            y='purchaseamount',
            color='label',
            title='Customer Behavior: Purchase Amount vs Satisfaction',
            labels={'customersatisfaction': 'Customer Satisfaction', 'purchaseamount': 'Purchase Amount ($)', 'label': 'Behavior Segment'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.dataframe(filtered_df, hide_index=True)

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
