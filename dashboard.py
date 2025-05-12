import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import glob

# find cleaned files (all cleaned CSV files follow the __CLEAD.csv pattern from datacleaning.py)
clean_files = glob.glob("*_CLEAN.csv")
print(f"Found cleaned files: {clean_files}")

# combine all cleaned CSV files into a single dataframe
df_list = [pd.read_csv(f) for f in clean_files]
stdf = pd.concat(df_list, ignore_index=True)

#title
st.title("NCS Hope Foundation Dashboard")

# sidebar for navigation
page = st.sidebar.radio("Select a Page", ["Home Page", "Applications Ready for Review", "Support Breakdown by Demographics", "Support Response Time", "Grant Utilization Overview", "Impact & Progress Summary"])

#Home page
if page == "Home Page":
    st.title("Patient Assistance Grant Tracker")
    st.markdown("---")

    st.subheader("About This Dashboard")
    st.markdown("""
    This dashboard was created to provide insights into the impact and performance of the Nebraska Cancer Specialists Hope Foundation's patient assistance grant program.

    It allows users to:
    - Monitor overall grant distribution and spending
    - Track support trends over time
    - Analyze patient reach and return support
    - Identify areas of overspending and efficiency

    The goal is to support decision-making and ensure funds are used effectively to help patients in need.
    """)

    st.subheader("How to Use")
    st.markdown("""
    Use the Sidebar to Navigate Between Sections: 
    
    - **Applications Ready for Review**: View pending requests and their details
    - **Support Breakdowns by Demographic**: Analyze grant distribution across race, gender, age, and more
    - **Support Response Time**: Track how long it takes to process and fulfill requests
    - **Grant Utilization Overview**: Understand how funds are being spent vs. remaining
    - **Impact & Progress Summary**: Review key performance metrics, patient reach, and trends
    
    """)

    st.markdown("---")
    st.caption("Dashboard created using Streamlit · Updated monthly")

# Applications ready for review page
elif page == "Applications Ready for Review":
    st.header("Applications Ready for Review")
    
    ready_for_review = stdf[stdf['request_status'] == 'Pending']

    # handle NA values in 'application_signed' and replace them with 'missing'
    ready_for_review['application_signed'] = ready_for_review['application_signed'].fillna('Missing')

    # dropdown for filtering based on committee signature status
    signature_status = st.selectbox("Select Committee Signature Status", ['All', 'Signed', 'Not Signed', 'Missing'])

    if signature_status != 'All':
        if signature_status == 'Signed':
            ready_for_review = ready_for_review[ready_for_review['application_signed'] == 'Yes']
        elif signature_status == 'Not Signed':
            ready_for_review = ready_for_review[ready_for_review['application_signed'] == 'No']
        elif signature_status == 'Missing':
            ready_for_review = ready_for_review[ready_for_review['application_signed'] == 'Missing']

    # display the filtered applications
    st.write(f"Displaying applications with signature status '{signature_status}'")
    st.dataframe(ready_for_review)

# 2. Support Breakdown by Demographic Page
elif page == "Support Breakdown by Demographics":
    st.header("Support Breakdown by Demographics")
    demographics = [
        'Gender', 'Location', 'Zip Code', 'Language Spoken', 'Hispanic or Latino', 
        'Sexuality', 'Race', 'Insurance Type', 'Total Household Gross Monthly Income', 'Marital Status', 'Household Size', 'Age'
    ]

    # select which demographic to filter by
    demographic_choice = st.selectbox("Select Demographic", demographics)

    # filter & display data based on the selected demographic
    if demographic_choice == "Gender":
        # sum support by amount and _____ (in this case gender)
        gender_support = stdf.groupby("gender")["amount"].sum()  
        st.write(gender_support)
        st.bar_chart(gender_support)

    elif demographic_choice == "Insurance Type":
        insurance_support = stdf.groupby("insurance_type")["amount"].sum()  
        st.write(insurance_support)
        st.bar_chart(insurance_support)

    elif demographic_choice == "Sexuality":
        sexuality_support = stdf.groupby("sexual_orientation")["amount"].sum()  
        st.write(sexuality_support)
        st.bar_chart(sexuality_support)

    elif demographic_choice == "Race":
        racial_support = stdf.groupby("race")["amount"].sum()  
        st.write(racial_support)
        st.bar_chart(racial_support)

    elif demographic_choice == "Language Spoken":
        language_support = stdf.groupby("language")["amount"].sum()  
        st.write(language_support)
        st.bar_chart(language_support)

    elif demographic_choice == "Hispanic or Latino":
        ethnicity_support = stdf.groupby("hispaniclatino")["amount"].sum()  
        st.write(ethnicity_support)
        st.bar_chart(ethnicity_support)

    elif demographic_choice == 'Location':
        state_support = stdf.groupby("pt_state")["amount"].sum()
        st.write(state_support)
        st.bar_chart(state_support)

    elif demographic_choice == "Total Household Gross Monthly Income":
        st.header("Support Breakdown by Total Household Gross Monthly Income")

        # legend/Explanation
        st.markdown("""
            **Legend for Household Income:**
            
            - **High**: Represents households with a gross monthly income **greater than $7,000**.
            - **Middle**: Represents households with a gross monthly income **between $3,000 - $7,000**.
            - **Low**: Represents households with a gross monthly income **less than $3,000**.
            
            This breakdown helps to analyze how support is distributed across different income levels.
        """)

        income_support = stdf.groupby("total_household_gross_monthly_income")["amount"].sum()
        st.write(income_support)
        st.bar_chart(income_support)

    elif demographic_choice == "Zip Code":
        st.header("Support by Zip Code")

        zip_code_support = stdf.groupby("pt_zip")["amount"].sum()
        st.write(zip_code_support)

        map_data = stdf[['lat', 'lng', 'amount', 'pt_zip']] 

        # clean lat/lng to remove invalid values
        map_data["lat"] = pd.to_numeric(map_data["lat"], errors="coerce")
        map_data["lng"] = pd.to_numeric(map_data["lng"], errors="coerce")
        map_data = map_data.dropna(subset=["lat", "lng"])


        # drop rows without coordinates or amount
        map_data = map_data.dropna(subset=["lat", "lng", "amount"])

        map_data["lat"] = map_data["lat"].astype(float)
        map_data["lng"] = map_data["lng"].astype(float)
        map_data["amount"] = map_data["amount"].astype(float)

        # create a pydeck map (full disclosure: i used chatgpt to figure this out and i know you had a great option for this but I already had begun working with this so i decided to just to commit to it)
        deck = pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=map_data['lat'].mean(),
                longitude=map_data['lng'].mean(),
                zoom=7,  #trying 7, 10 was way too close
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    map_data,
                    get_position='[lng, lat]',
                    get_radius=1000,
                    get_fill_color=[255, 0, 0, 140],
                    pickable=True,
                )
            ]
        )

        st.pydeck_chart(deck)


    elif demographic_choice == "Marital Status":
        marriage_support = stdf.groupby('marital_status')['amount'].sum()
        st.write(marriage_support)
        st.bar_chart(marriage_support)

    elif demographic_choice == "Household Size":
        householdsize_support = stdf.groupby('household_size')['amount'].sum()
        st.write(householdsize_support) 
        st.bar_chart(householdsize_support)

    elif demographic_choice == "Age":
        st.markdown("""
            **Legend for Age Categories:**
        
            - Child: 0-19
            - Young Adult: 20-35
            - Adult: 36-65
            - Senior: 66+
        """)

        # define order for the categories
        age_order = ["Child", "Young Adult", "Adult", "Senior"]

        # group by age_category and calculate the sum of the amounts
        age_support = stdf.groupby('age_category')['amount'].sum()

        # ensure the chart shows categories in the desired order
        age_support = age_support.reindex(age_order)
        st.write(age_support)
        st.bar_chart(age_support)
    

elif page == "Support Response Time":
    st.header("Support Response Time")

    # summary statistics
    st.subheader("Summary Statistics")
    st.write(stdf['days_to_support'].dropna().describe())

    # histogram of response times
    st.subheader("Distribution of Response Times (in Days)")
    st.bar_chart(stdf['days_to_support'].value_counts().sort_index())

    

#4. Grant Utilization Page
elif page == "Grant Utilization Overview":
    st.header("Grant Utilization Overview")

    # filter patients with a positive remaining balance
    positive_balance = stdf[stdf['remaining_balance'] > 0]

    # count how many patients have a positive remaining balance
    patients_with_positive_balance = positive_balance['patient_id'].nunique()

    st.subheader(f"Number of Patients with Positive Balance: {patients_with_positive_balance}")

    # binning the remaining_balance into categories by 300 increments
    bin_labels = ['0-300', '301-600', '601-900', '901-1200', '1201-1500', '1501+']
    bins = [0, 300, 600, 900, 1200, 1500, float('inf')]

    positive_balance['balance_bins'] = pd.cut(positive_balance['remaining_balance'], bins=bins, labels=bin_labels)

    st.subheader("Distribution of Remaining Balances (Binned)")
    st.bar_chart(positive_balance['balance_bins'].value_counts().sort_index(), use_container_width=True)


    # *** Grants by Assistance Type *** (same page)

    st.subheader("Grant Distribution by Assistance Type")

    # count number of grants by assistance type
    assistance_type_counts = stdf['assistance_type'].value_counts()


    st.write(assistance_type_counts)
# created the plot using streamlit pie chart option
    fig = assistance_type_counts.plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8), ylabel='', title='Grants by Assistance Type'
    ).get_figure()
    st.pyplot(fig)


#5. Impact & Progress Summary 
elif page == "Impact & Progress Summary":
    st.header("Impact & Progress Summary (All Time)")

    summary_data = stdf.copy()
    summary_data['grant_req_date'] = pd.to_datetime(summary_data['grant_req_date'], errors='coerce')

    st.subheader("Key Metrics")

    approved_grants = summary_data[summary_data['request_status'] == "Approved"]

    total_grants = approved_grants['amount'].sum()
    total_patients = approved_grants['patient_id'].nunique()
    total_approved = len(approved_grants)

    total_remaining = approved_grants[approved_grants['remaining_balance'] > 0]['remaining_balance'].sum()
    overspent = abs(approved_grants[approved_grants['remaining_balance'] < 0]['remaining_balance'].sum())

    returning_patients = approved_grants['patient_id'].value_counts()
    num_returning_patients = (returning_patients > 1).sum()

    # Calculate avg_days if the column exists
    avg_days = summary_data['days_to_support'].mean() if 'days_to_support' in summary_data.columns else None

    # Row 1
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Grant Amount Awarded", f"${total_grants:,.2f}")
    col2.metric("Total Overspent Amount", f"${overspent:,.2f}")
    col3.metric("Total Approved Grants", len(approved_grants))

    # Row 2
    col4, col5, col6 = st.columns(3)
    col4.metric("Unique Patients Served", total_patients)
    col5.metric("Returning Patients Supported", num_returning_patients)
    if avg_days is not None:
        col6.metric("Avg. Days to Support", f"{avg_days:.1f} days")
    else:
        col6.metric("Avg. Days to Support", "N/A")

    # grant trend chart
    st.subheader("Grant Request Trend Over Time")
    if 'grant_req_date' in summary_data.columns:
        summary_data['grant_month'] = summary_data['grant_req_date'].dt.to_period('M')
        monthly_requests = summary_data.dropna(subset=['grant_month']).groupby('grant_month').size()
        monthly_requests.index = monthly_requests.index.to_timestamp()
        monthly_requests.index.name = 'Time' # removes 'grant_month' label from x-axis

        fig = px.line(
            monthly_requests,
            x=monthly_requests.index,
            y=monthly_requests.values,
            labels={'x': 'Month', 'y': 'Number of Requests'},
            title='Monthly Grant Requests Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
