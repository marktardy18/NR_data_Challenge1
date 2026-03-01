import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Nova Retail Data Dashboard")
st.subheader("Customer Behavior Lead Growth")

try:
    # Load and clean data
    df = pd.read_csv("NR_dataset.csv")
    
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    required_fields = [
        'customerid', 'purchaseamount', 'customersatisfaction', 
        'retailchannel', 'productcategory', 'customerregion'
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
    
    # Calculate the overall average spend per customer to serve as the baseline threshold
    overall_avg_spend = df.groupby('customerid')['purchaseamount'].sum().mean()
    
    # Interactive Filter Dashboard for Scatter Plot
    st.subheader("Product Category Quadrant Analysis")
    categories = sorted(df['productcategory'].astype(str).unique().tolist())
    categories.insert(0, "All")
    
    selected_category = st.selectbox("Filter by Product Category:", categories)
    
    # Dynamic text logic based on the selected product category
    if selected_category != "All":
        cat_df = df[df['productcategory'] == selected_category]
        cat_spend = cat_df.groupby('customerid')['purchaseamount'].sum().mean()
        cat_sat = cat_df['customersatisfaction'].mean()
        
        # Determine the most frequent region and sales channel
        top_region_raw = cat_df['customerregion'].mode()[0] if not cat_df['customerregion'].empty else "Unknown"
        top_channel_num = cat_df['retailchannel'].mode()[0] if not cat_df['retailchannel'].empty else 1
        top_channel = "Online" if top_channel_num == 1 else "Physical Store"
        
        # Format region to add "ern" (e.g., West -> Western)
        region_map = {"West": "Western", "East": "Eastern", "South": "Southern", "North": "Northern"}
        top_region = region_map.get(top_region_raw, top_region_raw)
        
        # Updated string with bolded fields and formatted region
        region_channel_text = f"Purchases were primarily sold in the **{top_region}** region in a **{top_channel}**."
        
        if cat_spend > overall_avg_spend and cat_sat < 3.0:
            st.error(f"**{selected_category} Insight:** This category is primarily in the **Top-Left Quadrant (Flight Risk)**. Due to high spending but low satisfaction, immediate retention efforts are needed for these buyers. {region_channel_text}")
        elif cat_spend > overall_avg_spend and cat_sat >= 3.0:
            st.success(f"**{selected_category} Insight:** This category is primarily in the **Top-Right Quadrant (Champions)**. Due to high spending and high satisfaction, continue to reward and engage this loyal segment. {region_channel_text}")
        elif cat_spend <= overall_avg_spend and cat_sat < 3.0:
            st.warning(f"**{selected_category} Insight:** This category is primarily in the **Bottom-Left Quadrant (Decline Segment)**. Due to low spending and low satisfaction, investigate core product or experience issues. {region_channel_text}")
        else:
            st.info(f"**{selected_category} Insight:** This category is primarily in the **Bottom-Right Quadrant (Upsell Opportunity)**. Due to high satisfaction and low spending, there is a growth opportunity within this segment. {region_channel_text}")
    else:
        st.markdown("*Select a specific product category from the dropdown above to view its strategic growth insight.*")
        
    st.divider()

    # Filter dataframe for the scatter plot
    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['productcategory'].isin([selected_category])]
        
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        # Group by CustomerID and keep the first product category for coloring
        agg_df = filtered_df.groupby('customerid', as_index=False).agg(
            total_customer_spend=('purchaseamount', 'sum'),
            average_customer_satisfaction=('customersatisfaction', 'mean'),
            productcategory=('productcategory', 'first')
        )
        
        avg_spend = agg_df['total_customer_spend'].mean()
        
        # Scatter Plot Construction
        fig = px.scatter(
            agg_df,
            x='average_customer_satisfaction',
            y='total_customer_spend',
            color='productcategory',
            hover_data=['customerid'],
            title='Flight Risk vs. Upsell Matrix: Spend vs. Satisfaction',
            labels={
                'average_customer_satisfaction': 'Average Customer Satisfaction',
                'total_customer_spend': 'Total Customer Spend',
                'productcategory': 'Product Category'
            }
        )
        
        fig.add_vline(x=3.0, line_dash="dash", line_color="red")
        fig.add_hline(y=avg_spend, line_dash="dash", line_color="green")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Quadrant Descriptions
        st.markdown("""
        ### Quadrant Analysis Guide
        * **Red Dashed Line:** Represents the neutral customer satisfaction threshold (3.0 out of 5.0).
        * **Green Dashed Line:** Represents the average total customer spend across the dataset.
        * **Top-Left (High Spend, < 3.0 Satisfaction): The Flight Risks.** High-value customers at immediate risk of decline or churn. They require immediate retention efforts.
        * **Top-Right (High Spend, > 3.0 Satisfaction): The Champions.** Your most loyal, high-spending, and satisfied customers.
        * **Bottom-Left (Low Spend, < 3.0 Satisfaction): The Decline Segment.** Low-value customers with poor experiences. 
        * **Bottom-Right (Low Spend, > 3.0 Satisfaction): The Upsell Opportunities.** Customers who love the brand but aren't spending much yet. These are prime targets for growth and cross-selling initiatives.
        """)

    # ----------------------------------------------------------------------
    # NEW SECTION: Unfiltered Revenue by Product Pie Chart
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("Total Revenue by Product")
    
    # Use the original UNFILTERED dataframe 'df'
    revenue_df = df.groupby('productcategory', as_index=False)['purchaseamount'].sum()
    revenue_df = revenue_df.sort_values(by='purchaseamount', ascending=False)
    
    # Create a Pie Chart for Total Revenue by Product Category
    fig_pie = px.pie(
        revenue_df,
        names='productcategory',
        values='purchaseamount',
        title='Total Revenue per Product Category',
        labels={
            'productcategory': 'Product Category',
            'purchaseamount': 'Total Revenue ($)'
        }
    )
    
    # Format the data labels to show percentage and category name, and hover for exact currency
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Total Revenue: $%{value:,.2f}<br>Percentage: %{percent}'
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

    # Filtered Data Table at the bottom
    st.subheader("Filtered Data (Applies to Scatter Plot Selection)")
    st.dataframe(filtered_df, hide_index=True)

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    st.error(f"An error occurred: {e}")
