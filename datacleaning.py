import pandas as pd
import re
from datetime import date
import sys
import os

# cleaning each column, starting with patient id number
def clean_patient_id(patient_id):
    # if the patient_id is missing or empty, return na
    if pd.isna(patient_id) or str(patient_id).strip() == '':
        return 'NA'
    return patient_id

# function to clean and standardize the grant_req_date to MM/DD/YYYY format
def clean_grant_req_date(grant_req_date):
    if pd.isna(grant_req_date) or str(grant_req_date).strip() == '':
        return 'NA'
    try:
        date_obj = pd.to_datetime(grant_req_date, errors='raise', dayfirst=False)
        return date_obj.strftime('%m/%d/%Y')
    except (ValueError, TypeError):
        return 'NA'


# cleaning pt id number
# not super necessary since the current state of the excel spreadsheet would only allow numeric answers but probably not a bad idea just for a safety measure 
def clean_app_year(app_year):
    if pd.isna(app_year) or str(app_year).strip().lower() == 'missing' or str(app_year).strip() == '':
        return 'NA'   
    try:
        app_year = int(app_year)
        if app_year <= 0:  # cannot be negative years
            return 'NA'
    except ValueError:
        return 'NA'
    return app_year


# remaining balance cleaning
def clean_remaining_balance(val):
    try:
        num = float(val)
        if pd.isna(num):
            return {"remaining_balance": None, "over_balance": None, "status": "Missing value"}
        elif num < 0:
            return {"remaining_balance": num, "over_balance": True, "status": "Over balance"}
        else:
            return {"remaining_balance": num, "over_balance": False, "status": "OK"}
    except (ValueError, TypeError):
        return {"remaining_balance": None, "over_balance": None, "status": "Invalid entry"}



# cleaning the payment_submitted
def clean_payment_status(value):
    if value == 'Yes':
        return 'Yes'
    elif value == 'No':
        return 'No'
    try:
        parsed_date = pd.to_datetime(value, errors='raise').date()
        return parsed_date
    except (ValueError, TypeError):
        return 'NA'


# step 3: calculate days to support
def calculate_days_to_support(row):
    support_date = row['payment_submitted']
    request_date = row['grant_req_date']

    if isinstance(support_date, str):
        return None
    if pd.isna(support_date) or pd.isna(request_date):
        return None
    return (support_date - request_date).days


# reason pending
def clean_reason_pending(val):
    if pd.isna(val) or not isinstance(val, str) or val.strip() == "":
        return "NA"
    val = val.lower()
    # category: died or hospice
    if "hospice" in val or "deceased" in val:
        return "Hospice/Deceased"
    
    # category: ineligible
    if any(word in val for word in ["over income", "over limit", "not eligible", "no balance", "not charged", "request too high"]):
        return "Ineligible"
    
    # category: follow-up
    if any(word in val for word in ["pfa", "follow up", "waiting on payment"]):
        return "Follow-up"
    
    # category: missing documents
    if any(word in val for word in ["poi", "ev", "hs", "missing", "verify", "needs", "documentation"]):
        return "Missing Docs"
    return "NA"



# function to clean pt_city names
def clean_city(city):
    if pd.isna(city) or city == '' or city.lower() == 'missing':
        return 'NA'
    # remove non-alphabetical characters and replace with a space
    city = re.sub(r'[^a-zA-Z\s]', '', city)
    # handle apostrophes or hyphens (this obviously doesnt occur in the dataset but just to handle future entries like st. louis)
    city = re.sub(r'[^a-zA-Z\s\'-]', '', city)
    # convert to lowercase and capitalize the first letter of each word
    city = ' '.join([word.capitalize() for word in city.strip().split()])
    return city




# Pt_state cleaing
# doing all states because i want it to be compatible with future entries
state_abbreviation_map = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY'
}

def clean_state(state):
    if pd.isna(state) or str(state).strip().lower() == 'missing' or str(state).strip() == '':
        return 'NA' 
    # if it's already an abbreviation, make sure it's uppercase
    if state.upper() in state_abbreviation_map.values():
        return state.upper() 
    # convert full name to abbreviation
    return state_abbreviation_map.get(state, 'NA')



# step 1: TRYING ZIP AGAIN
zip_df = pd.read_csv("uszips.csv", dtype={"zip": str})
zip_df['zip'] = zip_df['zip'].astype(str)

# create a dictionary
zip_dict = dict(zip(zip_df['zip'], zip_df[['lat', 'lng']].values))

# step 2: get lat and lng from og dataset
def get_lat_lng(zip_code):
    if pd.isna(zip_code):
        return None, None
    
    # Look up lat and lng directly from zip_dict
    if zip_code in zip_dict:
        return zip_dict[zip_code]
    else:
        return None, None

# step 3: function to apply get_lat_lng to the dataframe
def apply_lat_lng(row):
    lat, lng = get_lat_lng(row['pt_zip'])
    return pd.Series([lat, lng], index=['lat', 'lng'])



# language column 
# same as states, overcompensating so it is compatible with many languages. I looked up common languages. 
language_list = [
    'english', 'spanish', 'russian', 'romanian', 'bosnian', 'karen',
    'somali', 'ukrainian', 'vietnamese', 'chinese', 'arabic', 'french',
    'german', 'portuguese', 'mandarin', 'cantonese', 'japanese', 'korean',
    'polish', 'thai', 'swahili', 'tagalog', 'urdu', 'bengali'
]

# regex pattern to match any language in the list
lang_pattern = re.compile(r'\b(' + '|'.join(language_list) + r')\b', re.IGNORECASE)

def clean_language_column(value):
    if pd.isna(value) or str(value).strip().lower() in ['na', 'n/a', '', 'missing', '?']:
        return 'NA'

    value = str(value).lower()

    # find all matching languages
    found = re.findall(lang_pattern, value)

    # remove duplicates (just in case)
    found = sorted(set(lang.title() for lang in found))

    if not found:
        return 'Unknown'
    elif len(found) == 1:
        return found[0]  # return the single language
    else:
        return 'Bilingual'


#dob column
def clean_dob(value):
    try:
        parsed = pd.to_datetime(value, format='%Y-%m-%d', errors='coerce')
        if pd.isna(parsed):
            return pd.NA
        return parsed.date()  # return as a date object for age calc later
    except Exception:
        return pd.NA


# add 'age' column based on cleaned 'dob'
def add_age_column(dob_column):
    today = date.today()
    return dob_column.apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        if pd.notna(d) else pd.NA
    ).astype('Int64')


def add_age_category_column(age_column):
    """
    Adds an 'age_category' column based on the 'age' column with these categories:
    - Child: 0-12
    - Teen: 13-19
    - Young Adult: 20-35
    - Adult: 36-50
    - Middle-aged: 51-65
    - Senior: 66+
    """
    def categorize_age(age):
        if pd.isna(age):
            return "NA"
        elif age <= 12:
            return "Child"
        elif age <= 19:
            return "Teen"
        elif age <= 35:
            return "Young Adult"
        elif age <= 50:
            return "Adult"
        elif age <= 65:
            return "Middle-aged"
        else:
            return "Senior"
    
    return age_column.apply(categorize_age)



#cleaning marriage columm 
def clean_marriage_status(status):
    marriage_patterns = {
        'Divorced': r'(?i)(divorced|separated|dissolved)',
        'Married': r'(?i)(married|husband|wife|spouse)',
        'Domestic Partnership': r'(?i)(domestic partnership|partner|civil union)',
        'Single/Widowed': r'(?i)(single|widowed|never married)'}
    
    if pd.isnull(status) or status == "":
        return 'NA'
    
    for category, pattern in marriage_patterns.items():
        if re.search(pattern, str(status)):
            return category

    return 'NA'



# cleaning gender 
# want to be inclusive for future entries so i put a few extra options below :)
gender_mapping = {
    'Female': ['female', 'woman', 'girl', 'f'],
    'Male': ['male', 'man', 'boy', 'm'],
    'Transgender Female': ['transgender female', 'trans woman', 'transwoman', 'ftm'],
    'Transgender Male': ['transgender male', 'trans man', 'transman', 'mtf'],
    'Non-Binary': ['non-binary', 'nonbinary','genderqueer', 'agender', 'queer', 'non binary'],
    'NA': []}

def clean_gender(gender):
    if pd.isna(gender) or gender == '' or gender == ' ':
        return 'NA'
    gender = str(gender).lower()
    # check against each category
    for category, terms in gender_mapping.items():
        if gender in terms:
            return category

    return 'NA'



# race
def clean_race(race):
    if pd.isna(race) or race.strip().lower() in ['missing', 'decline to answer', '']:
        return 'NA'
    
    race = race.strip().lower()

    # standardize race groups, want to be inclusive for future entries
    if re.search(r'american indian|alaska native|native american', race):
        return 'Native American or Alaska Native'
    elif re.search(r'asian|chinese|japanese|korean', race):
        return 'Asian'
    elif re.search(r'black|african american|african', race):
        return 'Black or African American'
    elif re.search(r'white|whiate|caucasian|european|european american', race):  # Fix misspelling 'whiate'
        return 'White'
    elif re.search(r'two or more races|multiracial|mixed|biracial', race):
        return 'Two or More Races'
    elif re.search(r'middle eastern|north african|arab|mena', race):
        return 'Middle Eastern or North African'
    elif re.search(r'pacific islander|polynesian|micronesian|melanesian|native hawaiian|hawaiian', race):
        return 'Pacific Islander'
    elif re.search(r'jewish|jew', race):
        return 'Jewish'
    elif re.search(r'romani|gypsy', race):
        return 'Romani'
    elif re.search(r'afro-caribbean|caribbean', race):
        return 'Afro-Caribbean'
    elif re.search(r'south asian|indian|pakistani|bangladeshi|sri lankan', race):
        return 'South Asian'
    else:
        return 'Other'



# hispanic or latino category 
def clean_hispanic_latino(value):
    value_str = str(value).lower().strip()
    
    if pd.isnull(value) or value == "" or value_str in ['blanks', 'missing']:
        return 'NA'
    
    # check for 'non-hispanic'
    if 'non-hispanic' in value_str:
        return 'No'
    
    if 'no' == value_str:
        return 'No'
    
    # check for 'Yes' or any hispanic/latino-related terms 
    if 'hispanic' in value_str or 'latino' in value_str:
        return 'Yes'
    
    # check for 'decline to answer', grouping with NA bc we dont know what they are.
    if 'decline' in value_str:
        return 'NA'
    
    return 'NA'




# cleaning sex
def clean_sexual_orientation(value):
    value_str = str(value).lower().strip()
    
    if re.match(r'^(missing|n/a|decline to answer|male|female)$', value_str):
        return 'NA'
    
    # check for Heterosexual/Straight
    if re.search(r'(straight|heterosexual)', value_str):
        return 'Heterosexual'
    
    # Gay/Lesbian
    if re.search(r'(gay|lesbian|homosexual|queer)', value_str):
        return 'Homosexual'
    
    # bisexual
    if re.search(r'bisexual', value_str):
        return 'Bisexual'
    
    return 'NA'



#cleaning insurance type
def clean_insurance_type(insurance):
    insurance_patterns = {
        'Public Insurance': r'(?i)(medicare.*(medicaid|other))',
        'Military Insurance': r'(?i)military',
        'Private Insurance': r'(?i)(private)',
        'Uninsured': r'(?i)(uninsured|unisurred|unisured|missing|^$)',
        'NA': r'(?i)(unknown)'
    }
    
    for category, pattern in insurance_patterns.items():
        if re.search(pattern, str(insurance)):
            return category
    
    return 'NA'




# cleaning household size 
def clean_household_size(size):
    try:
        size = int(size)
        
        # check for valid household sizes
        if size < 1 or size > 30:
            return 'NA'  # Flag numbers out of expected range (less than 1 or more than 20), putting as NA so it doesnt show up as invalid in st dashboard but could be beneficial to do invalid otherwise
        elif size == 1:
            return '1'
        elif size == 2:
            return '2'
        elif size == 3:
            return '3'
        elif size == 4:
            return '4'
        elif 5 <= size <= 7:
            return '5-7'
        elif 8 <= size <= 10:
            return '8-10'
        elif size > 10:
            return '10+'
    except ValueError:
        return 'NA'




# total monthly household income 
def clean_income(income):
    if pd.isna(income) or str(income).strip().lower() in ['', 'missing', 'na', 'nan', 'none']:
        return 'NA'
    
    try:
        income = float(income)
        
        if income < 0 or income > 6000: #same as above just doing na for st dashboard for invalids
            return 'NA'

        if income < 3000:
            return 'Low'
        elif 3000 <= income < 7000:
            return 'Middle'
        else:
            return 'High'

    except (ValueError, TypeError):
        return 'NA'



#cleaning distance
def clean_distance(distance):
    if pd.isna(distance):
        return 'NA'

    try:
        distance = float(distance)
        
        # check for unrealistic distances (distances greater than 3000 miles)
        if distance < 0 or distance > 3000:
            return 'Missing'  # flag any unrealistic distance as missing (same as above)
        if distance < 20:
            return 'Short'
        elif 20 <= distance < 120:
            return 'Medium'
        else:
            return 'Long'
        
    except ValueError:
        return 'NA'


# cleaning referral source
def classify_referral_source(referral):
    source_patterns = {
        'Pediatric Hospitals': r'(children|pediatric)',
        'Cancer Centers': r'(cancer|oncology|hematology|nebraska cancer|morrison cancer|june e nylen|heartland oncology|ncs|cpn|mcc|meccspecialists|nebraska hematology|heartland hematology|nho)',
        'Hospital Networks': r'(health|hospital|medical center|clinic|community|practice|mje|st|medical|nemed)',
        'Other': r'.*'
    }

    referral = str(referral).strip().lower()
    referral = re.sub(r'\s+', ' ', referral)

    if referral == '' or referral == 'missing':
        return 'NA'

    for category, pattern in source_patterns.items():
        if re.search(pattern, referral, flags=re.IGNORECASE):
            return category

    return 'Unknown'



# referral name cleaning
def clean_referred_by(name):
    name = str(name).strip()

    missing_values = ['missing', 'na', 'n/a', 'not available', '']
    if name.lower() in missing_values:
        return 'NA' 

    name = name.title()  #(first letter of each word capitalized)
    
    # handle specific exceptions like Dr. which should remain capitalized
    name = name.replace('Dr.', 'Dr.')

    return name




#classification of assistance type
assistance_patterns = {
    'Car Payment': r'car payment',
    'Housing': r'housing',
    'Phone/Internet': r'(phone|internet)',
    'Food/Groceries': r'(food|grocer)',
    'Gas': r'\bgas\b',
    'Medical Supplies/Prescription Co-pay(s)': r'(medical|prescription|co-pay)',
    'Utilities': r'utilit',
    'Multiple': r','  # treat comma-separated entries as multiple
}

# classification function of assistance type
def classify_assistance_type(text):
    if pd.isna(text) or str(text).strip().lower() in ['na', 'missing', '', 'n/a']:
        return 'NA'
    
    text = str(text).strip().lower()

    if text == 'multiple':
        return 'Multiple'
    
    matches = [category for category, pattern in assistance_patterns.items() if re.search(pattern, text)]
    
    if len(matches) > 1:
        return 'Multiple'
    elif matches:
        return matches[0]
    else:
        return 'Other'



#cleaning amount 
def clean_amount(value):
    if pd.isna(value) or str(value).strip().lower() in ['na', 'missing', '', 'n/a']:
        return 'NA'
    
    # remove formatting characters like $ and , even though i think excel corrects this...
    value_str = str(value).replace('$', '').replace(',', '').strip()
    
    # match valid positive dollar amounts
    if re.match(r'^\d+(\.\d{1,2})?$', value_str):
        amount = float(value_str)
        return amount if amount >= 0 else 'NA'
    else:
        return 'NA'



#cleaning payment method 
def clean_payment_method(method):
    if pd.isna(method) or str(method).strip().lower() in ['?', 'na', 'missing', '']:
        return 'NA'
    
    method_str = str(method).strip().lower()

    # numeric-only entries become NA
    if method_str.isnumeric():
        return 'NA'

    # categorize w regex
    if 'pending' in method_str:
        return 'Pending'
    elif 'cash' in method_str:
        return 'Cash'
    elif re.search(r'\bcc\b|\bcredit\b|\bc/c\b', method_str):
        return 'Credit Card'
    elif 'ach' in method_str or 'bank transaction' in method_str or 'eft' in method_str:
        return 'Bank Transfer'
    elif re.match(r'^ck\b.*|^check$', method_str):
        return 'Check'
    elif 'gc' in method_str:
        return 'Gift Card'
    elif re.fullmatch(r'(je|journal entry)', method_str):
        return 'Journal Entry'
    elif 'ncs due' in method_str:
        return 'Internal Transfer'
    else:
        return 'Other'



#cleanign payable to 
def clean_payable_to(name):
    if pd.isna(name) or str(name).strip().lower() in ['na', 'missing', '?', '']:
        return 'NA'
    
    # normalize spaces and strip
    name = re.sub(r'\s+', ' ', str(name)).strip()
    acronyms = ['LLC', 'PC', 'MD', 'INC', 'DBA', 'PLLC', 'PA']
    words = name.split()
    clean_words = []
    
    for word in words:
        if word.upper() in acronyms:
            clean_words.append(word.upper())
        else:
            clean_words.append(word.capitalize())

    cleaned_name = ' '.join(clean_words)
    return cleaned_name


#notified cleaning
def clean_notified(value):
    if pd.isna(value):
        return 'NA'

    val = str(value).strip().lower()

    if val in ['missing', '', '?', 'na', 'n/a']:
        return 'NA'
    elif val == 'no':
        return 'No'
    elif val in ['yes']:
        return 'Yes'
    elif val == 'hold':
        return 'Pending'

    # regex pattern for common date formats since this column is a little inconsistent
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
    if re.match(date_pattern, val):
        return 'Yes'

    return 'NA'



#cleaning application signed 
def clean_application_signed(value):
    if pd.isna(value):
        return 'NA'
    
    val = str(value).strip().lower()

    if val in ['', 'missing', '?', 'na', 'n/a', 'not available']:
        return 'NA'
    elif val in ['yes', 'yeah', 'y']:
        return 'Yes'
    elif val in ['no', 'n']:
        return 'No'
    else:
        return 'NA' 



#notes cleaning
def clean_notes(value):
    if pd.isna(value) or str(value).strip() == '':
        return 'NA' 
    return value  # leave non-empty values as is (not much i can do for this column other than this)
    

def clean_data(input_file, sheet_name=None):
    # Load file based on extension
    if input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file, sheet_name=sheet_name)
    else:
        df = pd.read_csv(input_file)

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
        .str.replace(r'[^\w\s]', '', regex=True)
    )

    # Rename specific columns for easier reference
    df = df.rename(columns={
        'reason__pendingno': 'reason_pending',
        'distance_roundtriptx': 'distance',
        'type_of_assistance_class': 'assistance_type',
        'patient_letter_notified_directlyindirectly_through_rep': 'notified'
    })

    # Apply cleaning functions
    df['patient_id'] = df['patient_id'].apply(clean_patient_id)
    df['grant_req_date'] = df['grant_req_date'].apply(clean_grant_req_date)
    df['app_year'] = df['app_year'].apply(clean_app_year)
    
    # Step 1: Clean remaining_balance
    df['remaining_balance_cleaned'] = df['remaining_balance'].apply(clean_remaining_balance)
    
    # Step 2: Normalize dictionary into separate columns
    df[['remaining_balance', 'over_balance', 'balance_status']] = pd.json_normalize(df['remaining_balance_cleaned'])

    # Step 3: Drop the temporary column
    df.drop(columns=['remaining_balance_cleaned'], inplace=True)

    # Step 4: Clean request_status using allowed values
    allowed_statuses = ['Approved', 'Denied', 'Pending']
    df['request_status'] = df['request_status'].where(df['request_status'].isin(allowed_statuses), 'NA')

    # Clean additional columns
    df['payment_submitted'] = df['payment_submitted'].apply(clean_payment_status)
    df['grant_req_date'] = pd.to_datetime(df['grant_req_date'], errors='coerce').dt.date
    df['days_to_support'] = df.apply(calculate_days_to_support, axis=1)
    
    # Clean other columns
    df['reason_pending'] = df['reason_pending'].apply(clean_reason_pending)
    df['pt_city'] = df['pt_city'].apply(clean_city)
    df['pt_state'] = df['pt_state'].apply(clean_state)
    df['pt_zip'] = df['pt_zip'].astype(str)
    
    # Apply latitude and longitude
    df[['lat', 'lng']] = df.apply(apply_lat_lng, axis=1)
    
    # Clean remaining columns
    df['language'] = df['language'].apply(clean_language_column)
    df['dob'] = df['dob'].apply(clean_dob)
    
    # Apply 'age' and 'age_category' columns
    df['age'] = add_age_column(df['dob'])  # Apply to dob column
    df['age_category'] = add_age_category_column(df['age'])  # Apply to age column

    # Clean marital status, gender, and other columns
    df['marital_status'] = df['marital_status'].apply(clean_marriage_status)
    df['gender'] = df['gender'].apply(clean_gender)
    df['race'] = df['race'].apply(clean_race)
    df['hispaniclatino'] = df['hispaniclatino'].apply(clean_hispanic_latino)
    df['sexual_orientation'] = df['sexual_orientation'].apply(clean_sexual_orientation)
    df['insurance_type'] = df['insurance_type'].apply(clean_insurance_type)
    df['household_size'] = df['household_size'].apply(clean_household_size)
    df['total_household_gross_monthly_income'] = df['total_household_gross_monthly_income'].apply(clean_income)
    df['distance'] = df['distance'].apply(clean_distance)
    df['referral_source'] = df['referral_source'].apply(classify_referral_source)
    df['referred_by'] = df['referred_by'].apply(clean_referred_by)
    df['assistance_type'] = df['assistance_type'].apply(classify_assistance_type)
    df['amount'] = df['amount'].apply(clean_amount)
    df['payment_method'] = df['payment_method'].apply(clean_payment_method)
    df['payable_to'] = df['payable_to'].apply(clean_payable_to)
    df['notified'] = df['notified'].apply(clean_notified)
    df['application_signed'] = df['application_signed'].apply(clean_application_signed)
    df['notes'] = df['notes'].apply(clean_notes)

    return df

def main():
    if len(sys.argv) < 2:
        raise ValueError("No input file provided. Usage: python datacleaning.py <input_file>")
    
    input_file = sys.argv[1]

    # make sure the input file path is correct and exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")
    
    # determine output file
    output_file = os.path.splitext(input_file)[0] + "_CLEANED.csv"
    sheet_name = "Support_Application_Data" if input_file.endswith(".xlsx") else None

    print(f"Reading from: {input_file}")  # **Ensure file path is printed correctly for debugging**

    # **Process the data**
    cleaned_df = clean_data(input_file, sheet_name=sheet_name)

    print(f"Saving cleaned data to: {output_file}")
    cleaned_df.to_csv(output_file, index=False)

    print(f"Cleaning completed: {input_file} -> {output_file}")

# run the main function only if the script is executed
if __name__ == "__main__":
    main()
