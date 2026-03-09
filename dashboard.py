import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"

# Session state for authentication
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

# Helper functions
def get_headers():
    """Get headers with authentication token"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def login(username, password):
    """Login and get JWT token"""
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.user = data["user"]
            return True
        return False
    except Exception as e:
        st.error(f"Connection error: {e}")
        return False

def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user = None

def get_data(endpoint):
    """Fetch data from API"""
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

# Page configuration
st.set_page_config(
    page_title="Healthcare Billing System",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
    <style>
    /* Main content area */
    .main {
        padding: 2rem 3rem;
        background-color: #ffffff;
    }
    
    /* Metrics styling */
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 4px;
        border: 1px solid #e9ecef;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Headers */
    h1 {
        color: #2c3e50;
        font-weight: 600;
        font-size: 2rem !important;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: #34495e;
        font-weight: 500;
        font-size: 1.5rem !important;
    }
    
    h3 {
        color: #495057;
        font-weight: 500;
        font-size: 1.2rem !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #2c3e50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #34495e;
    }
    
    /* Forms */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border: 1px solid #ced4da;
        border-radius: 4px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f8f9fa;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #495057;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Dataframes */
    .dataframe {
        border: 1px solid #dee2e6;
        font-size: 0.9rem;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border-color: #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Healthcare Billing System")
    st.markdown("---")
    
    if st.session_state.token:
        st.write("**Logged in as:**")
        st.code(st.session_state.user['username'])
        st.write(f"**Role:** {st.session_state.user['role'].title()}")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    else:
        st.subheader("Authentication Required")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if login(username, password):
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("---")
        st.caption("**Test Credentials:**")
        st.caption("admin / adminadmin")
        st.caption("doctor1 / Doctor123!")
    
    st.markdown("---")
    st.caption("Version 1.0.0")
    st.caption("© 2026 Healthcare IT")

# Main content
if not st.session_state.token:
    # Landing page
    st.title("Healthcare Billing Management System")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("System Overview")
        st.write("""
        This application provides comprehensive management tools for healthcare billing operations, 
        including patient records, medical procedures, and financial transactions.
        """)
        
        st.subheader("Key Features")
        st.markdown("""
        - **Dashboard Analytics** - Real-time metrics and insights
        - **Patient Management** - Comprehensive patient database
        - **Procedure Catalog** - CPT code and pricing management
        - **Billing Records** - Transaction tracking and reporting
        - **Revenue Analysis** - Financial reports and analytics
        - **User Authentication** - Secure role-based access
        """)
    
    with col2:
        st.subheader("Getting Started")
        st.info("Please authenticate using the sidebar to access the system.")
        
        st.subheader("Technology Stack")
        tech_data = {
            "Component": ["Backend", "Database", "Authentication", "Deployment"],
            "Technology": ["FastAPI", "PostgreSQL", "JWT", "Docker"]
        }
        st.table(pd.DataFrame(tech_data))

else:
    # Dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", 
        "Patients", 
        "Procedures", 
        "Billing", 
        "Reports"
    ])
    
    # Tab 1: Dashboard
    with tab1:
        st.title("Dashboard")
        st.markdown("---")
        
        # Fetch data
        with st.spinner("Loading data..."):
            patients = get_data("patients")
            procedures = get_data("procedures")
            billing_records = get_data("billing")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Patients",
                value=len(patients)
            )
        
        with col2:
            st.metric(
                label="Procedures Available",
                value=len(procedures)
            )
        
        with col3:
            st.metric(
                label="Billing Records",
                value=len(billing_records)
            )
        
        with col4:
            if billing_records:
                total_revenue = sum(record.get('amount', 0) for record in billing_records)
                st.metric(
                    label="Total Revenue",
                    value=f"${total_revenue:,.2f}"
                )
            else:
                st.metric("Total Revenue", "$0.00")
        
        st.markdown("---")
        
        # Two column layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Recent Transactions")
            if billing_records:
                df = pd.DataFrame(billing_records)
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
                display_df = df[['id', 'patient_id', 'procedure_id', 'amount', 'status', 'date']].tail(10)
                display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No billing records available")
        
        with col2:
            st.subheader("Status Summary")
            if billing_records:
                df = pd.DataFrame(billing_records)
                status_counts = df['status'].value_counts()
                
                # Display as table
                status_df = pd.DataFrame({
                    'Status': status_counts.index,
                    'Count': status_counts.values
                })
                st.table(status_df)
                
                # Simple chart
                st.bar_chart(status_counts)
            else:
                st.info("No data available")
    
    # Tab 2: Patients
    with tab2:
        st.title("Patient Management")
        st.markdown("---")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Patient Database")
            patients = get_data("patients")
            if patients:
                df = pd.DataFrame(patients)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"Total Patients: {len(patients)}")
            else:
                st.info("No patients in database")
        
        with col2:
            st.subheader("Add New Patient")
            with st.form("add_patient"):
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                dob = st.date_input("Date of Birth")
                insurance = st.text_input("Insurance Provider")
                
                submitted = st.form_submit_button("Add Patient", use_container_width=True)
                
                if submitted:
                    if first_name and last_name and insurance:
                        data = {
                            "first_name": first_name,
                            "last_name": last_name,
                            "date_of_birth": str(dob),
                            "insurance_provider": insurance
                        }
                        response = requests.post(
                            f"{API_URL}/patients/",
                            json=data,
                            headers=get_headers()
                        )
                        if response.status_code in [200, 201]:
                            st.success("Patient added successfully")
                            st.rerun()
                        else:
                            st.error(f"Failed to add patient: {response.text}")
                    else:
                        st.warning("All fields are required")
    
    # Tab 3: Procedures
    with tab3:
        st.title("Procedure Catalog")
        st.markdown("---")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("Available Procedures")
            procedures = get_data("procedures")
            if procedures:
                df = pd.DataFrame(procedures)
                df['price'] = df['price'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"Total Procedures: {len(procedures)}")
            else:
                st.info("No procedures in catalog")
        
        with col2:
            st.subheader("Add New Procedure")
            with st.form("add_procedure"):
                cpt_code = st.text_input("CPT Code")
                description = st.text_area("Description")
                price = st.number_input("Price (USD)", min_value=0.0, step=1.0)
                
                submitted = st.form_submit_button("Add Procedure", use_container_width=True)
                
                if submitted:
                    if cpt_code and description and price > 0:
                        data = {
                            "cpt_code": cpt_code,
                            "description": description,
                            "price": int(price)
                        }
                        response = requests.post(
                            f"{API_URL}/procedures/",
                            json=data,
                            headers=get_headers()
                        )
                        if response.status_code in [200, 201]:
                            st.success("Procedure added successfully")
                            st.rerun()
                        else:
                            st.error(f"Failed to add procedure: {response.text}")
                    else:
                        st.warning("All fields are required")
    
    # Tab 4: Billing
    with tab4:
        st.title("Billing Records")
        st.markdown("---")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Filter by status
            status_filter = st.selectbox("Filter by Status", ["All", "pending", "paid", "denied"])
            
            if status_filter == "All":
                billing_records = get_data("billing")
            else:
                billing_records = get_data(f"billing/status/{status_filter}")
            
            if billing_records:
                df = pd.DataFrame(billing_records)
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M')
                df['amount'] = df['amount'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Summary statistics
                st.markdown("---")
                col_a, col_b, col_c = st.columns(3)
                
                df_numeric = pd.DataFrame(get_data("billing") if status_filter == "All" else get_data(f"billing/status/{status_filter}"))
                with col_a:
                    st.metric("Total Records", len(df_numeric))
                with col_b:
                    st.metric("Total Amount", f"${df_numeric['amount'].sum():,.2f}")
                with col_c:
                    st.metric("Average Amount", f"${df_numeric['amount'].mean():,.2f}")
            else:
                st.info(f"No billing records found")
        
        with col2:
            st.subheader("Create Billing Record")
            
            patients = get_data("patients")
            procedures = get_data("procedures")
            
            with st.form("add_billing"):
                if patients and procedures:
                    patient_options = {
                        f"{p['id']}: {p['first_name']} {p['last_name']}": p['id'] 
                        for p in patients
                    }
                    procedure_options = {
                        f"{pr['id']}: {pr['cpt_code']}": pr['id'] 
                        for pr in procedures
                    }
                    
                    selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
                    selected_procedure = st.selectbox("Select Procedure", list(procedure_options.keys()))
                    amount = st.number_input("Amount (USD)", min_value=0.0, step=1.0)
                    status = st.selectbox("Status", ["pending", "paid", "denied"])
                    
                    submitted = st.form_submit_button("Create Record", use_container_width=True)
                    
                    if submitted:
                        if amount > 0:
                            data = {
                                "patient_id": patient_options[selected_patient],
                                "procedure_id": procedure_options[selected_procedure],
                                "amount": float(amount),
                                "status": status
                            }
                            response = requests.post(
                                f"{API_URL}/billing/",
                                json=data,
                                headers=get_headers()
                            )
                            if response.status_code in [200, 201]:
                                st.success("Record created successfully")
                                st.rerun()
                            else:
                                st.error(f"Failed to create record: {response.text}")
                        else:
                            st.warning("Amount must be greater than 0")
                else:
                    st.warning("Please add patients and procedures first")
                    st.form_submit_button("Create Record", disabled=True, use_container_width=True)
    
    # Tab 5: Reports
    with tab5:
        st.title("Financial Reports")
        st.markdown("---")
        
        billing_records = get_data("billing")
        
        if billing_records:
            df = pd.DataFrame(billing_records)
            
            # Overall statistics
            st.subheader("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Total Revenue", f"${df['amount'].sum():,.2f}")
            with col3:
                st.metric("Average Transaction", f"${df['amount'].mean():,.2f}")
            with col4:
                paid_records = len(df[df['status'] == 'paid'])
                payment_rate = (paid_records / len(df) * 100) if len(df) > 0 else 0
                st.metric("Payment Rate", f"{payment_rate:.1f}%")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Revenue by Status")
                revenue_by_status = df.groupby('status')['amount'].sum().sort_values(ascending=False)
                
                # Display as table
                revenue_df = pd.DataFrame({
                    'Status': revenue_by_status.index,
                    'Revenue': revenue_by_status.values.round(2)
                })
                revenue_df['Revenue'] = revenue_df['Revenue'].apply(lambda x: f"${x:,.2f}")
                st.table(revenue_df)
                
                # Chart
                st.bar_chart(revenue_by_status)
            
            with col2:
                st.subheader("Top 5 Patients by Billing")
                patient_billing = df.groupby('patient_id')['amount'].sum().sort_values(ascending=False).head(5)
                
                # Display as table
                patient_df = pd.DataFrame({
                    'Patient ID': patient_billing.index,
                    'Total Billed': patient_billing.values.round(2)
                })
                patient_df['Total Billed'] = patient_df['Total Billed'].apply(lambda x: f"${x:,.2f}")
                st.table(patient_df)
                
                # Chart
                st.bar_chart(patient_billing)
            
        else:
            st.info("No data available for reporting. Create billing records to generate reports.")

# Footer
st.markdown("---")
st.caption("Healthcare Billing System | FastAPI + PostgreSQL + Streamlit")