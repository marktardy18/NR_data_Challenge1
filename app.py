import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Nova Retail Dashboard", page_icon="🛍️")

# --- CUSTOM STYLING & HEADERS ---
st.title("🛍️ Nova Retail Data Dashboard")
st.subheader("📊 Customer Behavior Lead Growth")

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
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    st.subheader("🎯 Product Category Quadrant Analysis")
    
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
            },
            template='plotly_white'
        )
        
        fig.add_vline(x=3.0, line_dash="dash", line_color="red")
        fig.add_hline(y=avg_spend, line_dash="dash", line_color="green")
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Quadrant Descriptions hidden behind a clean expander to save vertical space
        with st.expander("📖 Read the Quadrant Analysis Guide", expanded=False):
            st.markdown("""
            * **Red Dashed Line:** Represents the neutral customer satisfaction threshold (3.0 out of 5.0).
            * **Green Dashed Line:** Represents the average total customer spend across the dataset.
            * **Top-Left (High Spend, < 3.0 Satisfaction): The Flight Risks.** High-value customers at immediate risk of decline or churn. They require immediate retention efforts.
            * **Top-Right (High Spend, > 3.0 Satisfaction): The Champions.** Your most loyal, high-spending, and satisfied customers.
            * **Bottom-Left (Low Spend, < 3.0 Satisfaction): The Decline Segment.** Low-value customers with poor experiences. 
            * **Bottom-Right (Low Spend, > 3.0 Satisfaction): The Upsell Opportunities.** Customers who love the brand but aren't spending much yet. These are prime targets for growth and cross-selling initiatives.
            """)

    # ----------------------------------------------------------------------
    # NEW SECTION: Unfiltered Revenue by Region and Product Stacked Bar Chart
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("🌎 Total Revenue by Region and Product")
    
    # Group by region AND product category to get the data for stacking
    revenue_region_df = df.groupby(['customerregion', 'productcategory'], as_index=False)['purchaseamount'].sum()
    
    # Calculate total revenue per region to sort the bars correctly on the x-axis
    region_totals = revenue_region_df.groupby('customerregion')['purchaseamount'].sum().reset_index()
    region_totals = region_totals.sort_values(by='purchaseamount', ascending=False)
    sorted_regions = region_totals['customerregion'].tolist()
    
    # Create the stacked bar chart (Inverse of previous: X is region, color is product)
    fig_stacked_bar = px.bar(
        revenue_region_df,
        x='customerregion',
        y='purchaseamount',
        color='productcategory',
        title='Total Revenue per Region by Product Category',
        labels={
            'customerregion': 'Region',
            'purchaseamount': 'Total Revenue ($)',
            'productcategory': 'Product Category'
        },
        category_orders={'customerregion': sorted_regions},
        template='plotly_white'
    )
    
    # Format the hover labels to display as currency and ensure the chart is stacked
    fig_stacked_bar.update_traces(hovertemplate='<b>%{x}</b> - %{data.name}<br>Total Revenue: $%{y:,.2f}')
    fig_stacked_bar.update_layout(yaxis_title="Total Revenue ($)", barmode='stack', margin=dict(l=20, r=20, t=50, b=20))
    
    st.plotly_chart(fig_stacked_bar, use_container_width=True)

    # ----------------------------------------------------------------------
    # NEW SECTION: Segments at Risk
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("⚠️ Segments at Risk: Immediate Attention Required")
    st.markdown("Customers in the **Flight Risk** segment represent high-value buyers whose satisfaction has dropped below the neutral threshold (< 3.0). Identifying what these customers primarily purchase is critical to minimizing revenue loss.")
    
    # Aggregate customer data from the unfiltered 'df'
    customer_risk_agg = df.groupby('customerid', as_index=False).agg(
        total_spend=('purchaseamount', 'sum'),
        avg_sat=('customersatisfaction', 'mean'),
        primary_product=('productcategory', 'first'),
        primary_region=('customerregion', 'first')
    )
    
    # Identify flight risk customers (Spend > Average, Satisfaction < 3.0)
    flight_risk_df = customer_risk_agg[(customer_risk_agg['total_spend'] > overall_avg_spend) & (customer_risk_agg['avg_sat'] < 3.0)]
    
    col_risk1, col_risk2 = st.columns(2)
    revenue_at_risk = flight_risk_df['total_spend'].sum()
    customers_at_risk = flight_risk_df['customerid'].nunique()
    
    col_risk1.metric("🚨 Revenue at Immediate Risk", f"${revenue_at_risk:,.2f}")
    col_risk2.metric("👥 High-Value Customers at Risk", customers_at_risk)
    
    if not flight_risk_df.empty:
        risk_by_product = flight_risk_df.groupby('primary_product', as_index=False)['total_spend'].sum()
        fig_risk = px.bar(
            risk_by_product.sort_values('total_spend', ascending=False),
            x='primary_product',
            y='total_spend',
            title='Revenue at Risk by Product Category',
            labels={'primary_product': 'Product Category', 'total_spend': 'Revenue at Risk ($)'},
            text='total_spend',
            template='plotly_white'
        )
        fig_risk.update_traces(marker_color='#EF553B', texttemplate='$%{text:,.2f}', textposition='outside')
        fig_risk.update_layout(yaxis_title="Revenue at Risk ($)", margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.success("Great news! There are currently no high-value customers in the Flight Risk quadrant.")
        
    # ----------------------------------------------------------------------
    # NEW SECTION: Investment Focus for Maximum Growth
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("🚀 Investment Focus: Maximizing Future Growth")
    st.markdown("To maximize growth, NovaRetail should focus on the **Upsell Opportunity** segment. These customers love the brand (Satisfaction >= 3.0) but currently spend below the average. Targeted cross-selling, loyalty programs, and volume discounts in these key geographic areas and product lines offer the highest return on investment.")
    
    # Identify upsell opportunity customers (Spend <= Average, Satisfaction >= 3.0)
    upsell_df = customer_risk_agg[(customer_risk_agg['total_spend'] <= overall_avg_spend) & (customer_risk_agg['avg_sat'] >= 3.0)]
    
    col_growth1, col_growth2 = st.columns(2)
    potential_growth_customers = upsell_df['customerid'].nunique()
    avg_upsell_spend = upsell_df['total_spend'].mean() if not upsell_df.empty else 0
    
    col_growth1.metric("⭐ Customers Ripe for Upsell", potential_growth_customers)
    col_growth2.metric("💸 Current Avg Spend of Upsell Segment", f"${avg_upsell_spend:,.2f}")
    
    st.write("") # Small spacer
    # Interactive Toggle Display for Growth Opportunities
    view_by = st.radio("🔍 View Growth Opportunities By:", ["Customer Region", "Product Category"], horizontal=True)
    
    if not upsell_df.empty:
        if view_by == "Customer Region":
            growth_data = upsell_df.groupby('primary_region', as_index=False)['customerid'].nunique()
            growth_data.rename(columns={'customerid': 'customer_count', 'primary_region': 'Region'}, inplace=True)
            
            fig_growth = px.bar(
                growth_data.sort_values('customer_count', ascending=False), 
                x='Region', 
                y='customer_count', 
                title='Target Audience Size by Region', 
                text='customer_count',
                labels={'customer_count': 'Number of Customers'},
                template='plotly_white'
            )
        else:
            growth_data = upsell_df.groupby('primary_product', as_index=False)['customerid'].nunique()
            growth_data.rename(columns={'customerid': 'customer_count', 'primary_product': 'Product Category'}, inplace=True)
            
            fig_growth = px.bar(
                growth_data.sort_values('customer_count', ascending=False), 
                x='Product Category', 
                y='customer_count', 
                title='Target Audience Size by Product Category', 
                text='customer_count',
                labels={'customer_count': 'Number of Customers'},
                template='plotly_white'
            )
            
        fig_growth.update_traces(marker_color='#2CA02C', textposition='outside')
        fig_growth.update_layout(yaxis_title="Number of Customers Ripe for Upsell", margin=dict(l=20, r=20, t=50, b=20))
        
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("There are currently no customers in the Upsell Opportunity quadrant.")

    # ----------------------------------------------------------------------
    # FILTERED DATA TABLE (MOVED TO THE VERY BOTTOM)
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("📋 Filtered Data (Applies to Top Scatter Plot Selection)")
    st.dataframe(filtered_df, hide_index=True, use_container_width=True)

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    st.error(f"An error occurred: {e}")
