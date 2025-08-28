import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

# ------------------ Constants ------------------

CSV_FILE = "submissions.csv"
COLUMNS = [
    "Timestamp", "Household", "Male Adults", "Male Ages", "Female Adults", "Female Ages",
    "Kids School", "School Levels", "Kids Ages", "Zip", "Referral", "Phone", "Email", "Arrival Mode"
]

# ------------------ Utilities ------------------

def load_submissions():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=COLUMNS)
    try:
        df = pd.read_csv(CSV_FILE, names=COLUMNS, header=None, on_bad_lines='skip')
        df = df.dropna(how='all')
        return df
    except Exception:
        st.error("There was a problem reading the CSV file. Some rows may be malformed.")
        return pd.DataFrame(columns=COLUMNS)

def save_submissions(df):
    try:
        df.to_csv(CSV_FILE, index=False, header=False)
    except Exception as e:
        st.error(f"Error saving submission: {e}")

def validate_inputs(phone, email, zip_code):
    errors = []
    if not re.match(r"^\d{3}-\d{3}-\d{4}$", phone):
        errors.append("Phone format should be 555-555-1234.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Please enter a valid email address.")
    if not re.match(r"^\d{5}$", zip_code):
        errors.append("Zip code should be 5 digits.")
    return errors

def is_duplicate(df, phone, email):
    return not df[(df["Phone"] == phone) | (df["Email"] == email)].empty

def reset_form():
    reset_values = {
        "household": 1, "male_adults": 0, "male_ages": "", "female_adults": 0, "female_ages": "",
        "number_of_children": 0, "kids_school": "", "school_levels": [], "kids_ages": "", "zip_code": "", "referral": "", "phone": "", "email": ""
    }
    for key, value in reset_values.items():
        st.session_state[key] = value
    del st.session_state["reset_form"]

def normalize_phone(phone):
    # Remove all non-digit characters
    return ''.join(filter(str.isdigit, str(phone)))

def repair_csv_alignment():
    # Read raw CSV lines
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    fixed_rows = []
    for line in lines:
        row = [x.strip() for x in line.strip().split(',')]
        # If row length doesn't match, pad or trim
        if len(row) < len(COLUMNS):
            row += [''] * (len(COLUMNS) - len(row))
        elif len(row) > len(COLUMNS):
            row = row[:len(COLUMNS)]
        fixed_rows.append(row)
    # Write fixed CSV
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(','.join(COLUMNS) + '\n')
        for row in fixed_rows:
            f.write(','.join(row) + '\n')
    st.success("CSV alignment repair complete. Please reload the app.")

# ------------------ UI Sections ------------------

def show_privacy_notice():
    st.info("Your information is kept confidential and used only for food bank intake purposes. Thank you for serving with care.")

def show_lookup_section(df):
    st.markdown("## 🔍 Lookup Existing Submission")
    phone = st.text_input("Enter phone number (e.g. 555-555-5000 or 5555555000)")
    phone_clean = normalize_phone(phone)
    df["Phone_clean"] = df["Phone"].apply(normalize_phone)
    match = df[df["Phone_clean"] == phone_clean]
    if not match.empty:
        st.success("Match found:")
        st.write(match.drop(columns=["Phone_clean"]))
        st.info(f"Total submissions for this contact: {match.shape[0]}")
        today = datetime.now().strftime('%Y-%m-%d')
        already_submitted = match[match["Timestamp"].str.startswith(today)]
        if already_submitted.empty:
            arrival_mode = st.radio("How did you arrive today?", ["Walking", "Driving"], key="lookup_arrival_mode")
            if st.button("Log Submission for Today"):
                new_record = match.iloc[-1].copy()
                new_record["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_record["Arrival Mode"] = arrival_mode
                df_new = pd.DataFrame([new_record.drop(labels=["Phone_clean"])]).reset_index(drop=True)
                df_all = pd.concat([df.drop(columns=["Phone_clean"]), df_new], ignore_index=True)
                save_submissions(df_all)
                st.success("Submission logged for today!")
                st.experimental_rerun()
        else:
            st.warning("Submission for today already logged for this contact.")
        # Option to remove submission by admin
        st.markdown("---")
        st.markdown("### Remove a Submission (Admin Only)")
        remove_index = st.number_input("Enter row index to remove (see leftmost column above)", min_value=0, max_value=len(match)-1, step=1)
        remove_pw = st.text_input("Admin password to remove", type="password", key="remove_pw")
        if st.button("Remove Submission"):
            if remove_pw == "light2025":
                global_index = match.index[remove_index]
                df_removed = df.drop(global_index).reset_index(drop=True)
                save_submissions(df_removed)
                st.success(f"Submission at index {remove_index} removed.")
                st.experimental_rerun()
            else:
                st.error("Incorrect admin password.")
    elif phone:
        st.warning("No match found for that contact number.")

def show_submission_form(df):
    st.markdown("## 📝 New Intake Submission")
    with st.form("submission_form"):
        phone = st.text_input("Contact number (e.g. 555-555-1234)", key="phone")
        # Check if phone already exists
        phone_clean = normalize_phone(phone)
        df["Phone_clean"] = df["Phone"].apply(normalize_phone)
        already_exists = not df[df["Phone_clean"] == phone_clean].empty
        if already_exists:
            st.warning("This phone number already exists in the records. Please use the Lookup section to log a submission.")
            st.write(df[df["Phone_clean"] == phone_clean].drop(columns=["Phone_clean"]))
            st.stop()
        # Continue with new intake if not found
        household = st.number_input("Household size", min_value=1, key="household")
        male_adults = st.number_input("Male adults", min_value=0, key="male_adults")
        male_ages = st.text_input("Ages of male adults (comma-separated)", key="male_ages")
        female_adults = st.number_input("Female adults", min_value=0, key="female_adults")
        female_ages = st.text_input("Ages of female adults (comma-separated)", key="female_ages")
        number_of_children = st.number_input("Number of children", min_value=0, key="number_of_children")
        kids_ages = st.text_input("Children's ages (comma-separated)", key="kids_ages")
        school_levels = st.text_input("School(s) children attend (No school, Pre-K, Elementary, Middle or High School)", key="school_levels")
        zip_code = st.text_input("Zip code", key="zip_code")
        referral = st.text_input("How did you hear about us?", key="referral")
        email = st.text_input("Your e-mail address", key="email")
        arrival_mode = st.radio("How did you arrive today?", ["Walking", "Driving"], key="arrival_mode")

        submitted = st.form_submit_button("Submit")

        if submitted:
            errors = validate_inputs(phone, email, zip_code)
            if errors:
                for err in errors:
                    st.error(err)
                return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_data = pd.DataFrame([{
                "Timestamp": timestamp,
                "Household": household,
                "Male Adults": male_adults,
                "Male Ages": male_ages,
                "Female Adults": female_adults,
                "Female Ages": female_ages,
                "Number of Children": number_of_children,
                "Kids Ages": kids_ages,
                "School Levels": school_levels,
                "Zip": zip_code,
                "Referral": referral,
                "Phone": phone,
                "Email": email,
                "Arrival Mode": arrival_mode
            }], columns=COLUMNS)

            df_all = pd.concat([df.drop(columns=["Phone_clean"]), new_data], ignore_index=True)
            save_submissions(df_all)
            st.success("Submission saved!")

            if "reset_form" not in st.session_state:
                st.session_state["reset_form"] = True
                st.rerun()

def show_update_section(df):
    st.markdown("## ✏️ Update Existing Submission")
    with st.form("update_lookup"):
        phone = st.text_input("Enter contact number to update", placeholder="e.g. 555-555-1234")
        find = st.form_submit_button("Find Submission")

    if find:
        match = df[df["Phone"] == phone]
        if match.empty:
            st.warning("No submission found for that contact number.")
            return

        index = match.index[0]
        st.success("Submission found. You can now edit the fields below.")

        with st.form("update_form"):
            household = st.number_input("Household", value=int(match.at[index, "Household"]), min_value=1)
            male_adults = st.number_input("Male Adults", value=int(match.at[index, "Male Adults"]), min_value=0)
            male_ages = st.text_input("Male Ages", value=match.at[index, "Male Ages"])
            female_adults = st.number_input("Female Adults", value=int(match.at[index, "Female Adults"]), min_value=0)
            female_ages = st.text_input("Female Ages", value=match.at[index, "Female Ages"])
            kids_school = st.text_input("Kids School", value=match.at[index, "Kids School"])
            kids_ages = st.text_input("Kids Ages", value=match.at[index, "Kids Ages"])
            zip_code = st.text_input("Zip", value=match.at[index, "Zip"])
            referral = st.text_input("Referral", value=match.at[index, "Referral"])
            phone = st.text_input("Phone", value=match.at[index, "Phone"])
            email = st.text_input("Email", value=match.at[index, "Email"])
            confirm = st.checkbox("I confirm I want to update this submission.")
            update = st.form_submit_button("Update Submission")

            if update and confirm:
                errors = validate_inputs(phone, email, zip_code)
                if errors:
                    for err in errors:
                        st.error(err)
                    return

                # Prevent duplicate phone/email on update
                if (phone != match.at[index, "Phone"] or email != match.at[index, "Email"]) and is_duplicate(df, phone, email):
                    st.warning("A submission with this phone or email already exists.")
                    return

                df.at[index, "Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df.at[index, "Household"] = household
                df.at[index, "Male Adults"] = male_adults
                df.at[index, "Male Ages"] = male_ages
                df.at[index, "Female Adults"] = female_adults
                df.at[index, "Female Ages"] = female_ages
                df.at[index, "Kids School"] = kids_school
                df.at[index, "Kids Ages"] = kids_ages
                df.at[index, "Zip"] = zip_code
                df.at[index, "Referral"] = referral
                df.at[index, "Phone"] = phone
                df.at[index, "Email"] = email

                save_submissions(df)
                st.success(f"Submission for {phone} updated successfully!")
            elif update and not confirm:
                st.warning("Please confirm before updating.")

def show_admin_download(df):
    st.markdown("## 🔐 Admin Access")
    password = st.text_input("Enter admin password", type="password")
    access = st.button("Access Download")

    if access and password == "light2025":
        csv_data = df.to_csv(index=False)
        st.download_button("Download CSV", csv_data, file_name=f"submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        # Show today's submission count
        today = datetime.now().strftime('%Y-%m-%d')
        todays_count = df[df["Timestamp"].str.startswith(today)].shape[0]
        st.info(f"Forms submitted today: {todays_count}")
        # Show submissions by date (e.g., Saturdays)
        df['date'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.date
        df['weekday'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.day_name()
        saturdays = df[df['weekday'] == 'Saturday']
        sat_counts = saturdays.groupby('date').size()
        if not sat_counts.empty:
            st.markdown("### Saturday Submission Counts")
            st.write(sat_counts)
        # View logs for today
        st.markdown("---")
        st.markdown("### View Today's Logs")
        todays_logs = df[df["Timestamp"].str.startswith(today)]
        if not todays_logs.empty:
            st.write(todays_logs)
        else:
            st.info("No logs for today.")
        # Filter logs by date
        st.markdown("---")
        st.markdown("### Filter Logs by Date")
        filter_date = st.date_input("Select a date to view logs", key="admin_filter_date")
        if filter_date:
            filter_str = filter_date.strftime('%Y-%m-%d')
            filtered_logs = df[df["Timestamp"].str.startswith(filter_str)]
            if not filtered_logs.empty:
                st.write(filtered_logs)
            else:
                st.info(f"No logs found for {filter_str}.")
        # Search logs by any field
        st.markdown("---")
        st.markdown("### Search Logs by Any Field")
        search_term = st.text_input("Enter search term (any value)", key="admin_search")
        if search_term:
            mask = df.apply(lambda row: search_term.lower() in row.astype(str).str.lower().to_string(), axis=1)
            results = df[mask]
            if not results.empty:
                st.write(results)
                # Option to delete a log by index
                del_index = st.number_input("Enter row index to delete (see leftmost column above)", min_value=0, max_value=len(results)-1, step=1, key="admin_del_index")
                del_pw = st.text_input("Admin password to delete", type="password", key="admin_del_pw")
                if st.button("Delete Log"):
                    if del_pw == "light2025":
                        global_index = results.index[del_index]
                        df_removed = df.drop(global_index).reset_index(drop=True)
                        save_submissions(df_removed)
                        st.success(f"Log at index {del_index} deleted.")
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect admin password.")
            else:
                st.warning("No matching logs found.")
        # Option to repair CSV alignment
        st.markdown("---")
        if st.button("Repair CSV Alignment (One-Time)"):
            repair_csv_alignment()
    elif access and password:
        st.error("Incorrect password.")

# ------------------ Main App Logic ------------------

st.set_page_config(page_title="Bring the Light – Intake Form", layout="centered")
st.title("Bring the Light – Food Bank Intake Form")

# Handle reset form logic
if "reset_form" in st.session_state:
    reset_form()

# Ensure CSV file has header if missing
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False, header=True)

# Load submissions
df = load_submissions()

# Sidebar navigation for better UX
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to:", ["Lookup", "New Submission", "Update", "Admin", "Privacy Notice"])

if section == "Lookup":
    show_lookup_section(df)
elif section == "New Submission":
    show_submission_form(df)
elif section == "Update":
    show_update_section(df)
elif section == "Admin":
    show_admin_download(df)
elif section == "Privacy Notice":
    show_privacy_notice()

st.markdown("---")
