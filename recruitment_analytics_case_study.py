
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
import io
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Recruitment Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 2rem;
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.3rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .highlight {
        background-color: #ffffcc;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)




# Load data function with caching
@st.cache_data
def load_data():
    # Option 1: Load from the same GitHub repository (recommended)
    # Upload your practice.xlsx file to your GitHub repo and use the raw URL
    candidates_details_excel_url = "https://github.com/Harshithareddy9/Recruitment-Analytics-Dashboard/blob/e2264cda7fe0ca60379d768104792777972f54c2/CandidateDetails.xlsx"

    recruitment_activity_excel_url = "https://github.com/Harshithareddy9/Recruitment-Analytics-Dashboard/blob/e2264cda7fe0ca60379d768104792777972f54c2/RecruitingActivity.xlsx"
    
    # Download the file
    response1 = requests.get(candidates_details_excel_url)
    candidates_details_excel_file = io.BytesIO(response1.content)
    response2 = requests.get(recruitment_activity_excel_url)
    recruitment_activity_excel_file = io.BytesIO(response2.content)

    # Read the Excel file
    candidates_df = pd.read_excel(candidates_details_excel_file)
    activity_df = pd.read_excel(recruitment_activity_excel_file)

    return candidates_df, activity_df

# Load data
try:
    candidates_df, activity_df = load_data()
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please make sure your Excel file is available at the specified URL")
    st.stop()

# Main header
st.markdown('<h1 class="main-header">Recruitment Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

# Overview metrics
st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    total_candidates = candidates_df['Candidate ID Number'].nunique()
    st.metric("Total Candidates", f"{total_candidates:,}")
with col2:
    offer_sent_count = (candidates_df['Furthest Recruiting Stage Reached'].isin(['Offer Sent','Offer Accepted','Offer Declined'])).sum()
    st.metric("Offers Sent", f"{offer_sent_count}")
with col3:
    hired_count = (candidates_df['Furthest Recruiting Stage Reached'] == 'Offer Accepted').sum()
    st.metric("Hired", f"{hired_count}")
with col4:
    offer_declined = (candidates_df['Furthest Recruiting Stage Reached'] == 'Offer Declined').sum()
    st.metric("Declined", f"{offer_declined}")
with col5:
    No_response_from_candidate = (candidates_df['Furthest Recruiting Stage Reached'] == 'Offer Sent').sum()
    st.metric("No response from Candidate", f"{No_response_from_candidate}")
with col6:
    # Calculate conversion rate from offer sent to offer accepted
    total_offers = offer_sent_count
    if total_offers > 0:
        conversion_rate = (hired_count / total_offers) * 100
        st.metric("Offer Acceptance", f"{conversion_rate:.1f}%")
    else:
        st.metric("Offer Acceptance", "N/A")

# Create tabs for better organization
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Recruitment Funnel", 
    "Application Source Analysis", 
    "Position Title Analysis", 
    "Process Analysis",
    "Seasonality Analysis"
])

with tab1:
    # Funnel chart
    st.markdown('<h2 class="section-header">Recruitment Funnel Across All These Years</h2>', unsafe_allow_html=True)

    stage_counts = (
        activity_df.groupby("Stage Name")["Candidate ID Number"]
        .nunique()
        .sort_values(ascending=False)
    )

    # Trim "Date" from stage names for better representation and understanding
    stage_counts.index = stage_counts.index.str.replace(' Date', '', regex=False)

    offer_accepted_count = (candidates_df["Furthest Recruiting Stage Reached"] == "Offer Accepted").sum()
    stage_counts["Offer Accepted"] = offer_accepted_count

    funnel_df = stage_counts.reset_index()
    funnel_df.columns = ["Stage", "Candidates"]

    fig_funnel = go.Figure(go.Funnel(
        y=funnel_df["Stage"],
        x=funnel_df["Candidates"],
        textinfo="value+percent previous"
    ))

    fig_funnel.update_layout(
        title="Recruitment Funnel",
        height=500
    )

    st.plotly_chart(fig_funnel, use_container_width=True)

    # Add detailed year-wise breakdown table
    st.markdown('<h3 class="section-header">Year-wise Stage Counts</h3>', unsafe_allow_html=True)

    # First, get application dates for each candidate
    application_dates = activity_df[activity_df['Stage Name'] == 'New Application Date'][['Candidate ID Number', 'Date When Reached the Stage']]
    application_dates = application_dates.rename(columns={'Date When Reached the Stage': 'Application Date'})

    # Merge application dates with activity data
    activity_with_app_year = activity_df.merge(application_dates, on='Candidate ID Number', how='left')

    # Extract year from application date (not stage date)
    activity_with_app_year['Application_Year'] = activity_with_app_year['Application Date'].dt.year

    # Get all unique application years and stages
    all_years = sorted(activity_with_app_year['Application_Year'].dropna().unique())
    all_stages = stage_counts.index.tolist() 

    # Create pivot table with application year as columns and stages as rows
    yearly_data = []

    for stage in all_stages:
        if stage == "Offer Accepted":
            # Handle offer accepted separately because offer_accepted data is not present in activity_df, so we get data from candidates_df
            row_data = {"Stage": stage}
            for year in all_years:
                # Get candidates who applied in this year
                yearly_candidates = activity_with_app_year[activity_with_app_year['Application_Year'] == year]['Candidate ID Number'].unique()
                offer_count = candidates_df[
                    (candidates_df['Candidate ID Number'].isin(yearly_candidates)) &
                    (candidates_df['Furthest Recruiting Stage Reached'] == "Offer Accepted")
                ].shape[0]
                row_data[str(year)] = offer_count
        else:
            # Handle regular stages - filter by application year, not stage year
            stage_with_year = activity_with_app_year[
                (activity_with_app_year['Stage Name'].str.contains(stage, na=False)) &
                (activity_with_app_year['Application_Year'].notna())
            ]
            stage_year_counts = stage_with_year.groupby('Application_Year')['Candidate ID Number'].nunique()
            row_data = {"Stage": stage}
            for year in all_years:
                row_data[str(year)] = stage_year_counts.get(year, 0)
        
        yearly_data.append(row_data)

    # Create DataFrame and calculate totals
    yearly_df = pd.DataFrame(yearly_data)
    yearly_df = yearly_df.set_index('Stage')

    # Add total column
    yearly_df['Total'] = yearly_df.sum(axis=1)

    # Add percentage column for the funnel conversion
    if 'New Application' in yearly_df.index:
        new_apps_total = yearly_df.loc['New Application', 'Total']
        yearly_df['Conversion %'] = (yearly_df['Total'] / new_apps_total * 100).round(1)
        yearly_df['Conversion %'] = yearly_df['Conversion %'].astype(str) + '%'

    # Display the table
    st.dataframe(
        yearly_df,
        use_container_width=True,
        column_config={
            "Total": st.column_config.NumberColumn("Total"),
            "Conversion %": st.column_config.TextColumn("Conversion Rate")
        }
    )

    # Add some insights
    st.markdown("**Key Insights:**")

    if len(all_years) > 1:
        # Create year filter that excludes the minimum year (since we need at least 2 years for comparison)
        comparable_years = [year for year in all_years if year != min(all_years)]
        
        if comparable_years:
            selected_year = st.selectbox(
                "Select Year to Compare:",
                options=comparable_years,
                index=0,  # Default to first comparable year
                help="Select a year to compare with the previous year (minimum year excluded)"
            )
            
            # Find the previous year for comparison
            year_index = all_years.index(selected_year)
            if year_index > 0:
                prev_year = all_years[year_index - 1]
                
                if 'New Application' in yearly_df.index and 'Offer Accepted' in yearly_df.index:
                    recent_apps = yearly_df.loc['New Application', str(selected_year)]
                    recent_offers = yearly_df.loc['Offer Accepted', str(selected_year)]
                    recent_conversion = (recent_offers / recent_apps * 100) if recent_apps > 0 else 0
                    
                    prev_apps = yearly_df.loc['New Application', str(prev_year)]
                    prev_offers = yearly_df.loc['Offer Accepted', str(prev_year)]
                    prev_conversion = (prev_offers / prev_apps * 100) if prev_apps > 0 else 0
                    
                    # Calculate PERCENTAGE CHANGE (not percentage point difference)
                    if prev_conversion > 0:
                        conversion_change = (recent_conversion - prev_conversion) / prev_conversion * 100
                    else:
                        conversion_change = recent_conversion 
                    
                    st.write(f"• **{selected_year} vs {prev_year} Comparison:**")
                    st.write(f"  - {selected_year} Conversion Rate: {recent_conversion:.1f}%")
                    st.write(f"  - {prev_year} Conversion Rate: {prev_conversion:.1f}%")
                    st.write(f"  - Percentage Change: {conversion_change:+.1f}%")
                    
                    # Additional insights with percentage change context
                    if conversion_change > 20:  # >20% improvement
                        st.success(f"🎯 **Exceptional growth**: Conversion rate improved by {conversion_change:.1f}% from {prev_year}")
                    elif conversion_change > 10:  # 10-20% improvement
                        st.success(f"✅ **Strong growth**: Conversion rate improved by {conversion_change:.1f}% from {prev_year}")
                    elif conversion_change > 0:  # 0-10% improvement
                        st.success(f"📈 **Moderate growth**: Conversion rate improved by {conversion_change:.1f}% from {prev_year}")
                    elif conversion_change == 0:  # No change
                        st.info(f"➡️ **No change**: Conversion rate remained the same as {prev_year}")
                    elif conversion_change > -10:  # 0 to -10% decline
                        st.warning(f"⚠️ **Moderate decline**: Conversion rate decreased by {abs(conversion_change):.1f}% from {prev_year}")
                    elif conversion_change > -20:  # -10 to -20% decline
                        st.error(f"🔴 **Significant decline**: Conversion rate decreased by {abs(conversion_change):.1f}% from {prev_year}")
                    else:  # > -20% decline
                        st.error(f"🚨 **Critical decline**: Conversion rate decreased by {abs(conversion_change):.1f}% from {prev_year}")
    st.subheader('Summary of Funnel Analysis (2020-2023)')
    st.write("""
    Between 2020 and 2023, the company received **4,959 applications**, with interest **steadily growing and nearly doubling** from 2020 to 2022. The hiring process is **highly selective**, with a **steep drop-off at every stage**: only **32%** of applicants got a phone screen, **16%** an interview, and **2.5%** an offer. Ultimately, just **1.9% of all applicants joined the company**.

    However, when the company makes an offer, it's **very effective—77% of people accepted**. This shows that while the **initial screening is very strict**, the company is **successful at closing** the candidates it wants.
    """)

with tab2:
    # Source Analysis
    st.markdown('<h2 class="section-header">Performance by Application Source</h2>', unsafe_allow_html=True)

    # Hire conversion rate by source
    hire_conversion_rate = (
        candidates_df.groupby("Application Source")["Furthest Recruiting Stage Reached"]
        .apply(lambda x: (x == "Offer Accepted").mean())
        .reset_index()
    )
    hire_conversion_rate.columns = ["Application Source", "Hired Percent"]
    hire_conversion_rate['Hired Percent'] = round(hire_conversion_rate['Hired Percent'] * 100, 2)
    hire_conversion_rate = hire_conversion_rate.sort_values('Hired Percent', ascending=False)

    fig_hire_rate = px.bar(
        hire_conversion_rate,
        x="Application Source",
        y="Hired Percent",
        text=hire_conversion_rate["Hired Percent"].astype(str) + '%',
        title="Hire Conversion Rate by Application Source",
        color="Hired Percent",
        color_continuous_scale="greens",
        height=400
    )
    fig_hire_rate.update_traces(textposition="outside")
    fig_hire_rate.update_layout(
        xaxis_title="Application Source",
        yaxis_title="Hired Percent (%)",
        title_x=0.5
    )

    st.plotly_chart(fig_hire_rate, use_container_width=True)

    # Offer acceptance vs declined rates by source
    offer_extended_candidates = candidates_df[
        candidates_df['Furthest Recruiting Stage Reached'].str.contains('Offer', na=False)
    ]['Candidate ID Number'].unique()

    offers_df = candidates_df[candidates_df['Candidate ID Number'].isin(offer_extended_candidates)].copy()

    offer_analysis = (
        offers_df.groupby('Application Source')['Furthest Recruiting Stage Reached']
        .agg(
            Offers_Extended='count',
            Accepted=lambda x: (x == 'Offer Accepted').sum(),
            Declined=lambda x: (x == 'Offer Declined').sum()
        )
        .reset_index()
    )

    offer_analysis['Acceptance Rate'] = round((offer_analysis['Accepted'] / offer_analysis['Offers_Extended']) * 100, 1)
    offer_analysis['Declined Rate'] = round((offer_analysis['Declined'] / offer_analysis['Offers_Extended']) * 100, 1)
    offer_analysis = offer_analysis.sort_values('Acceptance Rate', ascending=False)

    plot_df = offer_analysis.melt(
        id_vars=['Application Source'],
        value_vars=['Acceptance Rate', 'Declined Rate'],
        var_name='Metric',
        value_name='Rate (%)'
    )

    fig_offer = px.bar(
        plot_df,
        x="Application Source",
        y="Rate (%)",
        color="Metric",
        barmode='group',
        text=plot_df["Rate (%)"].astype(str) + '%',
        title="Offer Acceptance vs. Declined Rates by Application Source",
        color_discrete_map={
            "Acceptance Rate": "#2E8B57",
            "Declined Rate": "#DC143C"
        },
        height=400
    )

    fig_offer.update_traces(textposition='outside')
    fig_offer.update_layout(
        title_x=0.5,
        xaxis_title="Application Source",
        yaxis_title="Rate (%)",
        legend_title="Outcome"
    )

    st.plotly_chart(fig_offer, use_container_width=True)

    # Time to offer by source
    pivot = activity_df.pivot(index="Candidate ID Number", 
                           columns="Stage Name", 
                           values="Date When Reached the Stage")

    pivot["time_to_offer"] = (pivot["Offer Sent Date"] - pivot["New Application Date"]).dt.days
    pivot = pivot.merge(candidates_df[["Candidate ID Number", "Application Source", "Furthest Recruiting Stage Reached"]], 
                        on="Candidate ID Number", how="left")

    pivot_offers = pivot[pivot['Furthest Recruiting Stage Reached'].str.contains('Offer', na=False)]
    time_to_offer_by_source = pivot_offers.groupby("Application Source")["time_to_offer"].mean().reset_index()
    time_to_offer_by_source['time_to_offer'] = time_to_offer_by_source['time_to_offer'].round(1)
    time_to_offer_by_source = time_to_offer_by_source.sort_values('time_to_offer', ascending=True)

    fig_tto_source = px.bar(
        time_to_offer_by_source,
        x="Application Source",
        y="time_to_offer",
        text=time_to_offer_by_source["time_to_offer"].round(1),
        title="Average Time from Application-to-Offer by Application Source (Days)",
        color="time_to_offer",
        color_continuous_scale="Viridis", 
        height=400
    )
    fig_tto_source.update_traces(textposition="outside", texttemplate='%{text} days')
    fig_tto_source.update_layout(
        xaxis_title="Application Source",
        yaxis_title="Average Time (Days)",
        title_x=0.5
    )

    st.plotly_chart(fig_tto_source, use_container_width=True)
    st.subheader('Summary:')
    st.write("""

    **Conversion (Application → Hire):**  
    Best: Campus Events (4.9%) and Agencies (2.6%)  
    Weakest: Internal Referrals (0%), Campus Job Board (1.1%), Advertisement (1.2%)

    **Offer Acceptance:**  
    Highest: Campus Events (91%), Campus Job Board (91%), Career Fair (86%)  
    Lowest: Agencies (39%), Internal Referrals (0%), Outsourced (50%)

    **Time to Offer:**  
    Fastest: Agency (42 days), Website (44 days)  
    Slowest: Internal Referral (63 days), Career Fair (52 days)  
    Most others are between 47–49 days.

    **In short:** Campus Events bring the most hires with the best acceptance rates, Agencies are faster but face low acceptance, and Internal Referrals are least effective (no hires, longest hiring duration).

    **Recommendation:** The data suggests a strong correlation between longer hiring timelines and higher offer declination rates. To improve acceptance rates, particularly for slow sources like Internal Referrals 
      and Career Fairs,we recommend **standardizing and reducing the overall hiring process duration.** Streamlining time-to-offer could significantly decrease offer declination.
 """)

with tab3:
    # Position Analysis
    st.markdown('<h2 class="section-header">Performance by Position</h2>', unsafe_allow_html=True)

    # Calculate time to hire by position
    pivot = activity_df.pivot(index="Candidate ID Number", 
                           columns="Stage Name", 
                           values="Date When Reached the Stage")

    pivot["time_to_offer"] = (pivot["Offer Sent Date"] - pivot["New Application Date"]).dt.days
    pivot = pivot.merge(candidates_df[["Candidate ID Number", "Position Title"]], on="Candidate ID Number", how="left")
    time_to_hire = pivot.groupby("Position Title")["time_to_offer"].mean().reset_index()
    time_to_hire['time_to_offer'] = time_to_hire['time_to_offer'].round(1)

    # Calculate offer outcomes by position
    offer_extended_candidates = candidates_df[
        candidates_df['Furthest Recruiting Stage Reached'].str.contains('Offer', na=False)
    ]['Candidate ID Number'].unique()

    offers_df = candidates_df[candidates_df['Candidate ID Number'].isin(offer_extended_candidates)].copy()

    offer_rates = (
        offers_df.groupby("Position Title")["Furthest Recruiting Stage Reached"]
        .agg(
            Total_Offers='count',
            Accepted=lambda x: (x == "Offer Accepted").sum(),
            Declined=lambda x: (x == "Offer Declined").sum(),
            No_Response=lambda x: (x == "Offer Sent").sum()
        )
        .reset_index()
    )

    offer_rates['Acceptance Rate'] = round((offer_rates['Accepted'] / offer_rates['Total_Offers']) * 100, 1)
    offer_rates['Rejection Rate'] = round((offer_rates['Declined'] / offer_rates['Total_Offers']) * 100, 1)
    offer_rates['No Response Rate'] = round((offer_rates['No_Response'] / offer_rates['Total_Offers']) * 100, 1)
    offer_rates = offer_rates[['Position Title', 'Acceptance Rate', 'Rejection Rate', 'No Response Rate', 'Total_Offers']]

    # Merge data
    position_analysis_df = time_to_hire.merge(offer_rates, on="Position Title")
    position_analysis_df = position_analysis_df.sort_values('Position Title')

    # Create subplots
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=('Time-to-Offer by Position (Days)', 
                        'Offer Acceptance Rate by Position (%)',
                        'Offer Rejection Rate by Position (%)',
                        'No Response Rate by Position (%)'),
        vertical_spacing=0.10,
        shared_xaxes=True
    )

    # Add Time-to-Offer chart
    fig.add_trace(
        go.Bar(
            x=position_analysis_df['Position Title'],
            y=position_analysis_df['time_to_offer'],
            name='Time-to-Offer',
            marker_color='#FF7F0E',
            text=position_analysis_df['time_to_offer'],
            texttemplate='%{text} days',
            textposition='auto'
        ),
        row=1, col=1
    )

    # Add Acceptance Rate chart
    fig.add_trace(
        go.Bar(
            x=position_analysis_df['Position Title'],
            y=position_analysis_df['Acceptance Rate'],
            name='Acceptance Rate',
            marker_color='#2E8B57',
            text=position_analysis_df['Acceptance Rate'],
            texttemplate='%{text}%',
            textposition='auto'
        ),
        row=2, col=1
    )

    # Add Rejection Rate chart
    fig.add_trace(
        go.Bar(
            x=position_analysis_df['Position Title'],
            y=position_analysis_df['Rejection Rate'],
            name='Rejection Rate',
            marker_color='#DC143C',
            text=position_analysis_df['Rejection Rate'],
            texttemplate='%{text}%',
            textposition='auto'
        ),
        row=3, col=1
    )

    # Add No Response Rate chart
    fig.add_trace(
        go.Bar(
            x=position_analysis_df['Position Title'],
            y=position_analysis_df['No Response Rate'],
            name='No Response Rate',
            marker_color='#6A5ACD',
            text=position_analysis_df['No Response Rate'],
            texttemplate='%{text}%',
            textposition='auto'
        ),
        row=4, col=1
    )

    # Add company average lines
    company_avg_time = position_analysis_df['time_to_offer'].mean()
    company_avg_acceptance = position_analysis_df['Acceptance Rate'].mean()
    company_avg_rejection = position_analysis_df['Rejection Rate'].mean()
    company_avg_no_response = position_analysis_df['No Response Rate'].mean()

    fig.add_hline(y=company_avg_time, line_dash="dash", line_color="blue", 
                  annotation_text=f"Avg: {company_avg_time:.1f} days", 
                  row=1, col=1)

    fig.add_hline(y=company_avg_acceptance, line_dash="dash", line_color="blue",
                  annotation_text=f"Avg: {company_avg_acceptance:.1f}%",
                  row=2, col=1)

    fig.add_hline(y=company_avg_rejection, line_dash="dash", line_color="blue",
                  annotation_text=f"Avg: {company_avg_rejection:.1f}%",
                  row=3, col=1)

    fig.add_hline(y=company_avg_no_response, line_dash="dash", line_color="blue",
                  annotation_text=f"Avg: {company_avg_no_response:.1f}%",
                  row=4, col=1)

    # Update layout
    fig.update_layout(
        title='Complete Hiring Performance Dashboard by Position',
        height=1000,
        width=1000,
        template='plotly_white',
        showlegend=False
    )

    # Update axes
    fig.update_xaxes(tickangle=45, row=4, col=1)
    fig.update_yaxes(title_text="Days", row=1, col=1)
    fig.update_yaxes(title_text="Percentage", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Percentage", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Percentage", row=4, col=1, range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

    # Display company averages
    st.success("Averages Across All Positions:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Time-to-Offer", f"{company_avg_time:.1f} days")
    with col2:
        st.metric("Acceptance Rate", f"{company_avg_acceptance:.1f}%")
    with col3:
        st.metric("Rejection Rate", f"{company_avg_rejection:.1f}%")
    with col4:
        st.metric("No Response Rate", f"{company_avg_no_response:.1f}%")

    st.subheader("📋 Summary")
    st.markdown("""
    ### ⏱️ **Positions with Longest Time-to-Offer**
    - **Average Time-to-Offer**: 48.7 days
    - **Finance Analyst**: 59.5 days  
    - **IT Analyst**: 55.3 days  
    - **UX Designer**: 54.0 days  
    - **Sr. Software Engineer**: 52.3 days  
    These roles exceed the average time-to-offer, indicating a complex or protracted hiring process.
    """)

    st.markdown("""
    ### 📉 **Offer Acceptance Rate Trends**
    **Highest Acceptance Rates**:
    - **UX Designer**: 100%  
    - **Associate Software Developer**: 95.8%  
    - **Associate Relationship Manager**: 95.2%  

    **Lowest Acceptance Rates**:
    - **Sr. Business Analyst**: 25%  
    - **Business Operations Manager**: 37.5%  
    - **Finance Analyst, IT Analyst, Sr. Customer Service Operations Associate**: 50%
    """)

    st.markdown("""
    ### ❌ **High Offer Rejection Rates**
    - **Account Executive**: 75% rejection  
    - **Sr. Business Analyst, IT Analyst, Business Operations Manager, Financial Manager, Sr. Customer Service Operations Associate**: 50%
    """)

    st.markdown("""
    ### 🔍 **Key Findings**
    - A strong correlation exists between **extended time-to-offer** and **lower offer acceptance rates** for specialist and senior individual contributor roles.
    - **Associate-level positions** show both **efficient hiring timelines** and **high acceptance rates**.
    - The **UX Designer** role is a notable outlier, showing **100% acceptance** despite a long hiring process, indicating high desirability.
    """)

    st.markdown("""
    ### 💡 **Recommendations**
    1. **Accelerate Hiring for Critical Roles**  
    Streamline processes to reduce time-to-offer for positions with high declination rates; adopt a standardized hiring workflow.

    2. **Launch Post-Decline Surveys**  
    Implement structured feedback mechanisms to capture reasons behind declined offers (e.g., compensation, process delays, competitor offers).
    """)


with tab4:
    # Process Analysis
    st.markdown('<h2 class="section-header">Hiring Process Analysis</h2>', unsafe_allow_html=True)
    
    # Calculate stage durations
    pivot["App_to_Phone"] = (pivot["Phone Screen Date"] - pivot["New Application Date"]).dt.days
    pivot["Phone_to_Interview"] = (pivot["In-House Interview Date"] - pivot["Phone Screen Date"]).dt.days
    pivot["Interview_to_Offer"] = (pivot["Offer Sent Date"] - pivot["In-House Interview Date"]).dt.days
    
    # Calculate average duration per stage transition
    bottlenecks_by_position = pivot.groupby("Position Title")[["App_to_Phone", "Phone_to_Interview", "Interview_to_Offer"]].mean().reset_index()
    bottlenecks_by_position = bottlenecks_by_position.melt(id_vars=["Position Title"], 
                                                          var_name="Stage Transition", 
                                                          value_name="Avg Days")
    
    # Map stage transitions to readable names
    stage_mapping = {
        "App_to_Phone": "Application → Phone Screen",
        "Phone_to_Interview": "Phone Screen → Interview", 
        "Interview_to_Offer": "Interview → Offer"
    }
    bottlenecks_by_position["Stage Transition"] = bottlenecks_by_position["Stage Transition"].map(stage_mapping)
    
    # Define the correct order of stages
    stage_order = ["Application → Phone Screen", "Phone Screen → Interview", "Interview → Offer"]
    bottlenecks_by_position['Stage Transition'] = pd.Categorical(
        bottlenecks_by_position['Stage Transition'], 
        categories=stage_order, 
        ordered=True
    )
    
    # Sort the dataframe by Position Title and Stage Transition
    bottlenecks_by_position = bottlenecks_by_position.sort_values(['Position Title', 'Stage Transition'])
    
    # Create a modern, sleek color palette with transparency
    modern_colors = [
        'rgba(100, 181, 246, 0.8)',  # Light blue with transparency
        'rgba(77, 208, 225, 0.8)',   # Aqua/cyan with transparency  
        'rgba(129, 199, 132, 0.8)'   # Soft green with transparency
    ]
    
    # Create the grouped bar chart
    fig_grid = px.bar(
        bottlenecks_by_position,
        x="Position Title",
        y="Avg Days",
        color="Stage Transition",
        barmode='group',
        text=bottlenecks_by_position["Avg Days"].round(1),
        title="<b>Hiring Process Analysis</b><br>Average Stage Duration by Position",
        color_discrete_sequence=modern_colors,
        height=500
    )
    
    # Update traces for a modern, shining appearance
    fig_grid.update_traces(
        textposition='outside',
        textfont=dict(size=10, color='rgba(0,0,0,0.8)'),
        marker=dict(
            line=dict(
                color='rgba(255,255,255,0.9)',  # Very subtle white border for shine effect
                width=1.5
            ),
            opacity=0.85  # Slight transparency for modern look
        )
    )
    
    # Update layout for a sleek, professional appearance
    fig_grid.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="Position Title",
        yaxis_title="Average Duration (Days)",
        legend_title="Process Stage",
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color='rgba(0,0,0,0.8)'),
        plot_bgcolor='rgba(248,250,252,0.9)',  # Very light, almost white background
        paper_bgcolor='rgba(255,255,255,0.95)',  # Slightly transparent paper
        title_font_size=20,
        title_x=0.5,  # Center the title
        hovermode='x unified'
    )
    
    fig_grid.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99,
        bgcolor='rgba(255,255,255,0.7)',
        bordercolor='rgba(200,200,200,0.4)',
        borderwidth=1,
        font=dict(size=11)
    ))
    
    # Add some final styling touches
    fig_grid.update_xaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.05)',
        gridwidth=1
    )
    
    fig_grid.update_yaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.05)',
        gridwidth=1
    )
    
    st.plotly_chart(fig_grid, use_container_width=True)
    
    # Campus vs Experienced Analysis
    st.markdown('<h3 class="section-header">Candidate Type Analysis</h3>', unsafe_allow_html=True)
    
    # Create a pivot for candidate type analysis
    pivot_ce = pivot.merge(candidates_df[["Candidate ID Number", "Candidate Type", "Furthest Recruiting Stage Reached"]], 
                          on="Candidate ID Number", how="left")
    
    # Filter for candidates who received offers
    pivot_ce_offers = pivot_ce[pivot_ce['Furthest Recruiting Stage Reached'].str.contains('Offer', na=False)]
    
    # Calculate response counts
    response_counts = pivot_ce_offers.groupby(["Candidate Type", "Furthest Recruiting Stage Reached"]).size().unstack(fill_value=0)
    
    # Define the expected columns and handle missing ones
    expected_columns = ['Offer Accepted', 'Offer Declined', 'Offer Sent']
    for col in expected_columns:
        if col not in response_counts.columns:
            response_counts[col] = 0
    
    # Rename columns for clarity
    response_counts = response_counts.rename(columns={
        'Offer Accepted': 'Accepted',
        'Offer Declined': 'Declined', 
        'Offer Sent': 'No Response'
    })
    
    # Calculate totals and percentages
    response_counts['Total'] = response_counts[['Accepted', 'Declined', 'No Response']].sum(axis=1)
    response_counts = response_counts.reset_index()
    
    # Create donut charts
    colors = ['rgba(76, 175, 80, 0.85)',   # Green for Accepted
              'rgba(244, 67, 54, 0.85)',   # Red for Declined
              'rgba(158, 158, 158, 0.85)'] # Grey for No Response
    
    # Get the candidate types
    candidate_types = response_counts["Candidate Type"].tolist()
    
    # Create the enhanced donut chart
    fig_donut_enhanced = make_subplots(
        rows=1, cols=len(candidate_types),
        specs=[[{"type": "domain"}] * len(candidate_types)],
        subplot_titles=[f"<b>{ctype}</b>" for ctype in candidate_types]
    )
    
    # Add donut charts with percentage labels in each section
    for i, candidate_type in enumerate(candidate_types):
        # Get the row for this candidate type
        row_data = response_counts[response_counts["Candidate Type"] == candidate_type].iloc[0]
        
        values = [row_data["Accepted"], row_data["Declined"], row_data["No Response"]]
        total = row_data["Total"]
        
        # Calculate percentages for each section
        percentages = [(val / total) * 100 for val in values]
        
        # Create custom text for each section (percentage + label)
        section_text = [f"{pct:.1f}%<br>{label}" for pct, label in zip(percentages, ["Accepted", "Declined", "No Response"])]
        
        fig_donut_enhanced.add_trace(go.Pie(
            values=values,
            labels=section_text,
            hole=0.6,
            name=candidate_type,
            marker_colors=colors,
            textinfo='label',
            textposition='inside',
            textfont=dict(size=12, color='white', family="Arial", weight="bold"),
            showlegend=False
        ), 1, i+1)
        
    
    # Update layout for a professional appearance
    fig_donut_enhanced.update_layout(
        title_text="<b>Candidate Response Distribution by Candidate Type</b>",
        title_x=0.5,
        title_font_size=20,
        height=500
    )
    
    # Add total candidate counts as annotations
    for i, candidate_type in enumerate(candidate_types):
        total = response_counts[response_counts["Candidate Type"] == candidate_type]["Total"].iloc[0]
        fig_donut_enhanced.add_annotation(
            x=i/len(candidate_types) + 0.5/len(candidate_types),
            y=-0.15,
            text=f"Total Candidates: {total}",
            showarrow=False,
            font=dict(size=12, color="gray", family="Arial"),
            xref="paper",
            yref="paper"
        )
    
    st.plotly_chart(fig_donut_enhanced, use_container_width=True)
    
    # Role Type Analysis (Tech vs Non-Tech)
    st.markdown('<h3 class="section-header">Role Type Analysis (Tech vs Non-Tech)</h3>', unsafe_allow_html=True)
    
    # Define role types
    tech_roles = [
        'Associate Software Developer', 'Sr. Software Engineer', 'IT Analyst', 
        'UX Designer', 'Associate Product Manager', 'Sr. Product Manager'
    ]
    
    non_tech_roles = [
        'Finance Manager', 'Financial Analyst', 'Operations Coordinator', 
        'Business Operations Manager', 'Sr. Customer Service Operations Associate', 
        'Operations Generalist', 'Associate Relationship Manager', 'Account Executive'
    ]
    
    hybrid_role = ['Sr. Business Analyst']
    
    # Define Tech vs Non-Tech based on Position Title
    def role_type(title):
        if title in tech_roles:
            return "Tech-Roles"
        elif title in non_tech_roles:
            return "Non-Tech-Roles"
        elif title in hybrid_role:
            return "Hybrid-Roles"
        else:
            return "Other"
    
    pivot["Role Type"] = pivot["Position Title"].apply(role_type)
    
    # Average duration per stage by role type
    stage_durations = pivot.groupby("Role Type")[["App_to_Phone","Phone_to_Interview","Interview_to_Offer"]].mean().reset_index()
    
    # Heatmap - perfect for executive presentations
    pivot_heatmap = stage_durations.set_index("Role Type")
    
    fig_heatmap = px.imshow(
        pivot_heatmap,
        labels=dict(x="Stage Transition", y="Role Type", color="Days"),
        aspect="auto",
        title="<b>Hiring Process Heatmap: Stage Duration by Role Type</b>",
        color_continuous_scale="Viridis",
        height=400
    )
    
    # Add annotations
    for i, row in enumerate(pivot_heatmap.values):
        for j, value in enumerate(row):
            fig_heatmap.add_annotation(
                x=j,
                y=i,
                text=f"{value:.1f}",
                showarrow=False,
                font=dict(color="white" if value > pivot_heatmap.values.mean() else "black", size=12)
            )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.subheader('Summary:')
    st.markdown("""
    ### 🛑 **Bottlenecks Are Role-Specific**
    (As seen, these roles have the longest time-to-offer from 'Position Title Analysis' Tab. Let’s look at where delays are happening):

    - **Finance Analyst**: Slow early screening  
    - **IT Analyst & UX Designer**: Delayed final offer stage  
    - **Sr. Software Engineer**: Slow interview scheduling  

    ➡️ **Overall Bottleneck**: The **"Interview to Offer"** stage is the longest on average, increasing the risk of candidate drop-off.
    """)

    st.markdown("""
    ### 👥 **Candidate Type Analysis**

    - **Campus Candidates**: Highly efficient — **88.2% acceptance rate**
    - **Experienced Candidates**: Struggling — **45.2% decline rate**

    ➡️ **Key Takeaway**: The offer process for **experienced professionals** requires urgent improvement:
    - Review **compensation**
    - Clarify **role expectations**
    - Improve **speed**
    """)

    st.markdown("""
    ### 🧩 **Role Type Efficiency**

    - **Fastest**: Non-Tech Roles – Efficient end-to-end process  
    - **Slowest**: Tech Roles – Bottlenecked in **final offer stage** (avg. **16.2 days**)  
    - **Hybrid Roles**: Mixed efficiency – **Slow start, fast finish**

    ➡️ **Strategic Recommendation**:  
    **Standardize and accelerate the "Interview-to-Offer" timeline**, especially for **Tech roles** and **experienced candidates**, to reduce declinations and secure top talent.
    """)


with tab5:
    # Seasonality Analysis
    st.markdown('<h2 class="section-header">Seasonality Trends Analysis</h2>', unsafe_allow_html=True)
    
    # First, let's merge the application dates from activity_df
    # Get the earliest date for each candidate (application date)
    application_dates = activity_df[activity_df['Stage Name'] == 'New Application Date'][['Candidate ID Number', 'Date When Reached the Stage']]
    application_dates = application_dates.rename(columns={'Date When Reached the Stage': 'Application Date'})
    
    # Merge application dates with candidate data
    candidates_with_dates = candidates_df.merge(application_dates, on='Candidate ID Number', how='left') #candidates_with_dates is nothing but candidates_df_with_application_dates_info
    
    # Filter out candidates without application dates
    candidates_with_dates = candidates_with_dates.dropna(subset=['Application Date'])
    
    # Extract year and month from application date
    candidates_with_dates['Application_Year'] = candidates_with_dates['Application Date'].dt.year
    candidates_with_dates['Application_Month'] = candidates_with_dates['Application Date'].dt.month
    candidates_with_dates['Application_Month_Name'] = candidates_with_dates['Application Date'].dt.strftime('%B')

    # Let the user select the year to analyze
    available_years = sorted(candidates_with_dates['Application_Year'].dropna().unique())
    selected_year = st.selectbox("Select Year for Seasonality Analysis", available_years, index=available_years.index(2022))
    
    # Filter for the latest year only
    # Filter the data based on the selected year
    latest_year_df = candidates_with_dates[candidates_with_dates['Application_Year'] == selected_year]
    
    def run_seasonality_analysis(year, candidates_with_dates):
        year_df = candidates_with_dates[candidates_with_dates['Application_Year'] == year]

        if year_df.empty:
            st.warning(f"No application data found for year {year}")
            return

        st.subheader(f"📊 Seasonality Analysis for {year}")
        
        # ---- Monthly Volume Chart ----
        monthly_volume = (
            year_df.groupby(['Application_Month', 'Application_Month_Name'])
            .size()
            .reset_index(name='Application_Count')
            .sort_values('Application_Month')
        )
        
        fig_monthly_volume = px.bar(
            monthly_volume,
            x='Application_Month_Name',
            y='Application_Count',
            title=f"<b>Application Volume by Month - {year}</b>",
            color='Application_Count',
            color_continuous_scale='tealrose',
            text='Application_Count',
            width=1000,
            height=500
        )
        fig_monthly_volume.update_traces(textposition='outside')
        fig_monthly_volume.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Applications",
            xaxis={'categoryorder': 'array', 'categoryarray': [
                'January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December'
            ]},
            title_x=0.5
        )
        st.plotly_chart(fig_monthly_volume)

        # ---- Acceptance Rate Chart ----
        monthly_acceptance = (
            year_df.groupby(['Application_Month', 'Application_Month_Name'])
            ['Furthest Recruiting Stage Reached']
            .apply(lambda x: (x == "Offer Accepted").mean() * 100)
            .reset_index(name='Acceptance_Rate')
            .sort_values('Application_Month')
        )
        
        fig_acceptance_monthly = px.line(
            monthly_acceptance,
            x='Application_Month_Name',
            y='Acceptance_Rate',
            title=f"<b>Offer Acceptance Rate by Application Month - {year}</b>",
            markers=True,
            line_shape='spline',
            width=1000,
            height=500
        )
        fig_acceptance_monthly.add_trace(
            go.Scatter(
                x=monthly_acceptance['Application_Month_Name'],
                y=monthly_acceptance['Acceptance_Rate'],
                mode='markers+text',
                text=monthly_acceptance['Acceptance_Rate'].round(1),
                textposition='top center',
                marker=dict(size=10, color='red'),
                showlegend=False
            )
        )
        fig_acceptance_monthly.update_layout(
            xaxis_title="Application Month",
            yaxis_title="Acceptance Rate (%)",
            xaxis={'categoryorder': 'array', 'categoryarray': [
                'January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December'
            ]},
            yaxis=dict(range=[0, max(monthly_acceptance['Acceptance_Rate']) * 1.2]),
            title_x=0.5
        )
        st.plotly_chart(fig_acceptance_monthly)

        # ---- Candidate Type by Month ----
        candidate_type_monthly = (
            year_df.groupby(['Application_Month_Name', 'Candidate Type'])
            .size()
            .reset_index(name='Count')
        )

        fig_candidate_type = px.bar(
            candidate_type_monthly,
            x='Application_Month_Name',
            y='Count',
            color='Candidate Type',
            title=f"<b>Candidate Type Distribution by Month - {year}</b>",
            barmode='stack',
            text='Count',  # This adds the count values to the bars
            width=1000,
            height=500
        )

        # Customize the text appearance - this is the key part
        fig_candidate_type.update_traces(
            texttemplate='%{text}', 
            textposition='outside',  # Changed from 'inside' to 'outside'
            textfont=dict(size=10, color='black')
        )

        fig_candidate_type.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Applications",
            xaxis={'categoryorder': 'array', 'categoryarray': [
                'January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December'
            ]},
            title_x=0.5,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        st.plotly_chart(fig_candidate_type)

        # ---- Insights ----
        st.markdown("### 📈 Seasonality Insights & Recommendations")

        peak_months = monthly_volume.nlargest(3, 'Application_Count')
        st.markdown("🏆 **Peak Application Months:**")
        for _, row in peak_months.iterrows():
            st.write(f"• {row['Application_Month_Name']}: {row['Application_Count']} applications")

        best_acceptance = monthly_acceptance.nlargest(3, 'Acceptance_Rate')
        st.markdown("✅ **Highest Acceptance Rate Months:**")
        for _, row in best_acceptance.iterrows():
            st.write(f"• {row['Application_Month_Name']}: {row['Acceptance_Rate']:.1f}% acceptance")

        st.markdown("🌐 **Top 5 Sources with Seasonality:**")
        top_sources_analysis = year_df.groupby('Application Source').agg({
            'Candidate ID Number': 'count',
            'Furthest Recruiting Stage Reached': [
                lambda x: (x == "Offer Accepted").mean() * 100,  # Offer acceptance rate
                lambda x: (x.isin(["Offer Sent", "Offer Accepted", "Offer Declined"]).mean() * 100 )      # Offer sent rate
            ]
        }).round(1)

        # Flatten the multi-level column names
        top_sources_analysis.columns = ['Application_Count', 'Offer_Acceptance_Rate', 'Offer_Sent_Rate']

        # Get top 5 sources by application count
        top_sources_analysis = top_sources_analysis.nlargest(5, 'Application_Count')

        for source, row in top_sources_analysis.iterrows():
            st.write(f"• **{source}**: {row['Application_Count']} applications, "
                    f"{row['Offer_Acceptance_Rate']}% offer acceptance, "
                    f"{row['Offer_Sent_Rate']}% offer sent rate")
    
        st.write("""
        **📌 Multi-Year Pattern:** Consistent data shows application volume peaks from **September to November**.
        This is the ideal window for mass recruitment drives if we need to scale hiring efforts.

        **🎯 Recommendation:** Focus mass recruitment efforts in **September-November** using **Campus Events** or **Career Fairs**
        for optimal results. Audit the **Campus Job Board** process to improve conversion rates.
        """)
    # ---- Call the function after Streamlit filter ----
    run_seasonality_analysis(selected_year, candidates_with_dates)





