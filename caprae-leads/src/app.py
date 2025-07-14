import streamlit as st
import pandas as pd
from utils.scoring import PredictiveLeadScorer
from agents.email_generator import EmailGenerator
from agents.research import ResearchAgent
from utils.scraping import scrape_website, extract_tech_stack
import os

# Initialize components
email_generator = EmailGenerator()
research_agent = ResearchAgent()

# Initialize the scorer
lead_scorer = PredictiveLeadScorer()

# Page config
st.set_page_config(
    page_title="Caprae Capital Lead Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tabs for different features
tab1, tab2, tab3 = st.tabs(["Lead Dashboard", "Research Tool", "Lead Generation"])

# Tab 1: Lead Dashboard
with tab1:
    st.title("Lead Dashboard")
    
    # Load existing leads
    @st.cache_data
    def load_data():
        if not os.path.exists('data/leads.csv'):
            from data.generate_mock_data import generate_mock_leads
            return generate_mock_leads()
        return pd.read_csv('data/leads.csv')
    
    leads_data = load_data()
    
    # Filters
    st.sidebar.header("Filters")
    industry_filter = st.sidebar.multiselect("Industry", leads_data['industry'].unique())
    score_range = st.sidebar.slider("Lead Score Range", 0, 100, (0, 100))
    
    # Apply filters
    filtered_data = leads_data.copy()
    if industry_filter:
        filtered_data = filtered_data[filtered_data['industry'].isin(industry_filter)]
    
    # Calculate scores
    filtered_data['lead_score'] = filtered_data.apply(lead_scorer.calculate_lead_score, axis=1)
    filtered_data = filtered_data[
        (filtered_data['lead_score'] >= score_range[0]) & 
        (filtered_data['lead_score'] <= score_range[1])
    ]
    
    # Display leads table
    st.dataframe(
        filtered_data,
        column_config={
            "lead_score": st.column_config.ProgressColumn(
                "Lead Score",
                format="%d",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True
    )

# Tab 2: Research Tool
with tab2:
    st.title("Lead Research Tool")
    
    website_url = st.text_input("Enter company website URL", 
                               placeholder="e.g. https://example.com")
    
    if st.button("Research Company"):
        if not website_url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            try:
                with st.spinner("Researching company..."):
                    company_data = research_agent.gather_data(website_url)
                    
                    # Create three columns for better layout
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.subheader("Company Profile")
                        st.markdown(f"### 🏢 {company_data['company_name']}")
                        if company_data['description']:
                            st.markdown("*" + company_data['description'] + "*")
                        
                        st.markdown("#### Industry & Type")
                        st.markdown(f"🏭 **Industry:** {company_data['industry']}")
                        st.markdown(f"💼 **Business Type:** {company_data['business_type']}")
                    
                    with col2:
                        st.subheader("Market Position")
                        st.markdown(f"🎯 **Target Market:**\n{company_data['target_market']}")
                        st.markdown(f"💫 **USP:**\n{company_data['usp']}")
                        st.markdown(f"📈 **Stage:** {company_data['company_stage']}")
                    
                    with col3:
                        st.subheader("Company Details")
                        st.markdown(f"👥 **Size:** {company_data['company_size']}")
                        
                        # Calculate and display lead score
                        lead_score = lead_scorer.calculate_lead_score(company_data)
                        st.metric("Lead Score", f"{lead_score}/100")
                        
                        # Add quick actions
                        if st.button("Generate Outreach Email"):
                            with st.spinner("Generating email..."):
                                email_content = email_generator.generate_email(company_data)
                                st.code(email_content, language="text")

            except Exception as e:
                st.error(f"Error researching company: {str(e)}")
                st.info("Please check the URL and try again.")

# Tab 3: Lead Generation
with tab3:
    st.title("Lead Generation")
    
    # Industry selection
    target_industry = st.selectbox("Target Industry", 
                                 ['SaaS', 'Fintech', 'Healthcare', 'E-commerce', 'Manufacturing'])
    
    # Company size
    min_employees = st.number_input("Minimum Employees", value=10)
    min_revenue = st.number_input("Minimum Revenue", value=100000)
    
    # Tech stack requirements
    required_tech = st.multiselect("Required Technology", 
                                 ['AWS', 'Azure', 'GCP', 'Salesforce', 'HubSpot'])
    
    if st.button("Generate Leads"):
        with st.spinner("Generating leads..."):
            # Filter existing leads based on criteria
            generated_leads = leads_data[
                (leads_data['industry'] == target_industry) &
                (leads_data['employees'] >= min_employees) &
                (leads_data['revenue'] >= min_revenue)
            ].copy()
            
            # Filter by tech stack
            if required_tech:
                generated_leads['has_tech'] = generated_leads['tech_stack'].apply(
                    lambda x: any(tech.lower() in str(x).lower() for tech in required_tech)
                )
                generated_leads = generated_leads[generated_leads['has_tech']]
            
            # Calculate scores
            generated_leads['lead_score'] = generated_leads.apply(lead_scorer.calculate_lead_score, axis=1)
            
            # Sort by score
            generated_leads = generated_leads.sort_values('lead_score', ascending=False)
            
            # Display results
            st.subheader(f"Generated {len(generated_leads)} Leads")
            st.dataframe(
                generated_leads,
                column_config={
                    "lead_score": st.column_config.ProgressColumn(
                        "Lead Score",
                        format="%d",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True
            )
            
            # Export option
            if not generated_leads.empty:
                st.download_button(
                    "Export Leads",
                    generated_leads.to_csv(index=False),
                    "leads_export.csv",
                    "text/csv"
                )