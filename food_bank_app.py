import streamlit as st
import pandas as pd
import re
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DB_FILE = "submissions.db"
COLUMNS = [
    "Timestamp", "Household", "Male Adults", "Male Ages", "Female Adults", "Female Ages",
    "Number of Children", "Kids Ages", "School Levels", "Zip", "Referral", "Phone", "Email", "Name", "Arrival Mode"
]

# SQLAlchemy setup (declarative)
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

# Submission model
class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    Timestamp = Column(String)
    Household = Column(Integer)
    Male_Adults = Column(Integer)
    Male_Ages = Column(String)
    Female_Adults = Column(Integer)
    Female_Ages = Column(String)
    Number_of_Children = Column(Integer)
    Kids_Ages = Column(String)
    School_Levels = Column(String)
    Zip = Column(String)
    Referral = Column(String)
    Phone = Column(String)
    Email = Column(String)
    Name = Column(String)
    Arrival_Mode = Column(String)

# Create table if missing
Base.metadata.create_all(bind=engine)

# Context-managed session utility
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Database setup
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

def normalize_phone(phone):
    return ''.join(filter(str.isdigit, str(phone)))

def validate_inputs(phone, email, zip_code):
    errors = []
    if not phone or len(normalize_phone(phone)) < 10:
        errors.append("Please enter a valid phone number.")
    if email and "@" not in email:
        errors.append("Please enter a valid email address.")
    if zip_code and (not zip_code.isdigit() or len(zip_code) != 5):
        errors.append("Please enter a valid 5-digit zip code.")
    return errors

def load_submissions():
    with SessionLocal() as session:
        submissions = session.query(Submission).all()
        if submissions:
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "Timestamp": s.Timestamp,
                    "Household": s.Household,
                    "Male Adults": s.Male_Adults,
                    "Male Ages": s.Male_Ages,
                    "Female Adults": s.Female_Adults,
                    "Female Ages": s.Female_Ages,
                    "Number of Children": s.Number_of_Children,
                    "Kids Ages": s.Kids_Ages,
                    "School Levels": s.School_Levels,
                    "Zip": s.Zip,
                    "Referral": s.Referral,
                    "Phone": s.Phone,
                    "Email": s.Email,
                    "Name": s.Name,
                    "Arrival Mode": s.Arrival_Mode
                }
                for s in submissions
            ])
            return df
        else:
            return pd.DataFrame(columns=COLUMNS)

def save_submission(row_dict):
    try:
        with SessionLocal() as session:
            submission = Submission(
                Timestamp=row_dict.get("Timestamp"),
                Household=row_dict.get("Household"),
                Male_Adults=row_dict.get("Male Adults"),
                Male_Ages=row_dict.get("Male Ages"),
                Female_Adults=row_dict.get("Female Adults"),
                Female_Ages=row_dict.get("Female Ages"),
                Number_of_Children=row_dict.get("Number of Children"),
                Kids_Ages=row_dict.get("Kids Ages"),
                School_Levels=row_dict.get("School Levels"),
                Zip=row_dict.get("Zip"),
                Referral=row_dict.get("Referral"),
                Phone=row_dict.get("Phone"),
                Email=row_dict.get("Email"),
                Name=row_dict.get("Name"),
                Arrival_Mode=row_dict.get("Arrival Mode")
            )
            session.add(submission)
            session.commit()
        print(f"DEBUG: Submission saved to database: {row_dict}")
    except Exception as e:
        print(f"ERROR: Failed to save submission: {row_dict}")
        print(f"ERROR: Exception: {e}")
        import traceback
        traceback.print_exc()

# Admin delete by id
def delete_submission_by_id(sub_id):
    with SessionLocal() as session:
        obj = session.query(Submission).filter(Submission.id == sub_id).first()
        if obj:
            session.delete(obj)
            session.commit()

# Admin update by id
def update_submission_by_id(sub_id, update_dict):
    with SessionLocal() as session:
        obj = session.query(Submission).filter(Submission.id == sub_id).first()
        if obj:
            for key, value in update_dict.items():
                # Map keys to model attributes
                attr = key.replace(" ", "_").replace("-", "_")
                if hasattr(obj, attr):
                    setattr(obj, attr, value)
            session.commit()

    # ...existing code...
    # Remove duplicate/invalid validation code

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


# ------------------ UI Sections ------------------

def show_privacy_notice():
    st.info("Your information is kept confidential and used only for food bank intake purposes. Thank you for serving with care.")

def show_lookup_section(df):
    st.markdown("## 🔍 Lookup Existing Submission")
    phone = st.text_input("Enter phone number (e.g. 555-555-5000 or 5555555000)")
    phone_clean = normalize_phone(phone)
    df["Phone_clean"] = df["Phone"].astype(str).apply(normalize_phone)
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
                # Save new submission to database
                # Save new submission to database
                save_submission(df_new.iloc[0].to_dict())
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
                # Remove from database: not implemented in SQLite version (admin delete can be added later)
                st.success(f"Submission at index {remove_index} removed (refresh to see changes).")
                st.experimental_rerun()
            else:
                st.error("Incorrect admin password.")
    elif phone:
        st.warning("No match found for that contact number.")

def show_submission_form(df):
    st.markdown("## 📝 New Intake Submission")
    with st.form("intake_form"):
        phone = st.text_input("Contact number (e.g. 555-555-1234)", key="intake_phone")
        email = st.text_input("Your e-mail address", key="intake_email")
        name = st.text_input("Name and Last Name (optional)", key="intake_name")
        household = st.number_input("Household size", min_value=1, key="household")
        male_adults = st.number_input("Male adults", min_value=0, key="male_adults")
        male_ages = st.text_input("Ages of male adults (comma-separated)", key="male_ages")
        female_adults = st.number_input("Female adults", min_value=0, key="female_adults")
        female_ages = st.text_input("Ages of female adults (comma-separated)", key="female_ages")
        number_of_children = st.number_input("Number of children", min_value=0, key="number_of_children")
        kids_ages = st.text_input("Children's ages (comma-separated)", key="kids_ages")
        school_levels = st.text_input("School(s) children attend (No school, Pre-K, Elementary, Middle or High School)", key="intake_school_levels")
        zip_code = st.text_input("Zip code", key="zip_code")
        referral = st.text_input("How did you hear about us?", key="referral")
        arrival_mode = st.radio("How did you arrive today?", ["Walking", "Driving"], key="arrival_mode")

        submitted = st.form_submit_button("Submit")

        if submitted:
            print("DEBUG: Submitted form values:")
            print(f"phone={phone}, email={email}, name={name}, household={household}, male_adults={male_adults}, male_ages={male_ages}, female_adults={female_adults}, female_ages={female_ages}, number_of_children={number_of_children}, kids_ages={kids_ages}, school_levels={school_levels}, zip_code={zip_code}, referral={referral}, arrival_mode={arrival_mode}")
            # Check if phone already exists
            phone_clean = normalize_phone(phone)
            df["Phone_clean"] = df["Phone"].apply(normalize_phone)
            already_exists = not df[df["Phone_clean"] == phone_clean].empty
            print(f"DEBUG: already_exists={already_exists}")
            if already_exists:
                st.warning("This phone number already exists in the records. Please use the Lookup section to log a submission.")
                st.write(df[df["Phone_clean"] == phone_clean].drop(columns=["Phone_clean"]))
                st.stop()

            errors = validate_inputs(phone, email, zip_code)
            print(f"DEBUG: errors={errors}")
            if errors:
                for err in errors:
                    st.error(err)
                return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row_dict = {
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
                "Name": name,
                "Arrival Mode": arrival_mode
            }
            print(f"DEBUG: row_dict={row_dict}")
            save_submission(row_dict)
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
            kids_ages = st.text_input("Kids Ages", value=match.at[index, "Kids Ages"])
            school_levels = st.text_input("School Levels", value=match.at[index, "School Levels"])
            zip_code = st.text_input("Zip", value=match.at[index, "Zip"])
            referral = st.text_input("Referral", value=match.at[index, "Referral"])
            phone = st.text_input("Phone", value=match.at[index, "Phone"])
            email = st.text_input("Email", value=match.at[index, "Email"])
            name = st.text_input("Name and Last Name (optional)", value=match.at[index, "Name"] if "Name" in match.columns else "")
            arrival_mode = st.text_input("Arrival Mode", value=match.at[index, "Arrival Mode"] if "Arrival Mode" in match.columns else "")
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

                # Update in database
                sub_id = match.index[0] + 1  # SQLite id is index+1
                update_dict = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Household": household,
                    "Male Adults": male_adults,
                    "Male Ages": male_ages,
                    "Female Adults": female_adults,
                    "Female Ages": female_ages,
                    "Number of Children": match.at[index, "Number of Children"] if "Number of Children" in match.columns else 0,
                    "Kids Ages": kids_ages,
                    "School Levels": school_levels,
                    "Zip": zip_code,
                    "Referral": referral,
                    "Phone": phone,
                    "Email": email,
                    "Name": name,
                    "Arrival Mode": arrival_mode
                }
                update_submission_by_id(sub_id, update_dict)
                st.success(f"Submission for {phone} updated successfully! (refresh to see changes)")
            elif update and not confirm:
                st.warning("Please confirm before updating.")

def show_admin_download(df):
    st.markdown("## 🔐 Admin Access")
    password = st.text_input("Enter admin password", type="password")
    access = st.button("Access Download")

    if access and password == "light2025":
        # Download CSV from database
        with SessionLocal() as session:
            submissions = session.query(Submission).all()
            df_db = pd.DataFrame([
                {
                    "Timestamp": s.Timestamp,
                    "Household": s.Household,
                    "Male Adults": s.Male_Adults,
                    "Male Ages": s.Male_Ages,
                    "Female Adults": s.Female_Adults,
                    "Female Ages": s.Female_Ages,
                    "Number of Children": s.Number_of_Children,
                    "Kids Ages": s.Kids_Ages,
                    "School Levels": s.School_Levels,
                    "Zip": s.Zip,
                    "Referral": s.Referral,
                    "Phone": s.Phone,
                    "Email": s.Email,
                    "Name": s.Name,
                    "Arrival Mode": s.Arrival_Mode
                }
                for s in submissions
            ])
            # Ensure all columns are present and in correct order
            for col in COLUMNS:
                if col not in df_db.columns:
                    df_db[col] = ""
            df_db = df_db[COLUMNS]
            csv_data = df_db.to_csv(index=False)
        st.download_button("Download CSV", csv_data, file_name=f"submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        # Show today's submission count
        today = datetime.now().strftime('%Y-%m-%d')
        todays_count = df_db[df_db["Timestamp"].str.startswith(today)].shape[0]
        st.info(f"Forms submitted today: {todays_count}")
        # Show submissions by date (e.g., Saturdays)
        df_db['date'] = pd.to_datetime(df_db['Timestamp'], errors='coerce').dt.date
        df_db['weekday'] = pd.to_datetime(df_db['Timestamp'], errors='coerce').dt.day_name()
        saturdays = df_db[df_db['weekday'] == 'Saturday']
        sat_counts = saturdays.groupby('date').size()
        if not sat_counts.empty:
            st.markdown("### Saturday Submission Counts")
            st.write(sat_counts)
        # View logs for today
        st.markdown("---")
        st.markdown("### View Today's Logs")
        todays_logs = df_db[df_db["Timestamp"].str.startswith(today)]
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
            filtered_logs = df_db[df_db["Timestamp"].str.startswith(filter_str)]
            if not filtered_logs.empty:
                st.write(filtered_logs)
            else:
                st.info(f"No logs found for {filter_str}.")
        # Search logs by any field
        st.markdown("---")
        st.markdown("### Search Logs by Any Field")
        search_term = st.text_input("Enter search term (any value)", key="admin_search")
        if search_term:
            mask = df_db.apply(lambda row: search_term.lower() in row.astype(str).str.lower().to_string(), axis=1)
            results = df_db[mask]
            if not results.empty:
                st.write(results)
                # Option to delete a log by id
                del_index = st.number_input("Enter row index to delete (see leftmost column above)", min_value=0, max_value=len(results)-1, step=1, key="admin_del_index")
                del_pw = st.text_input("Admin password to delete", type="password", key="admin_del_pw")
                if st.button("Delete Log"):
                    if del_pw == "light2025":
                        sub_id = results.index[del_index] + 1  # SQLite id is index+1
                        delete_submission_by_id(sub_id)
                        st.success(f"Log at index {del_index} deleted.")
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect admin password.")
                # Option to update a log
                st.markdown("---")
                st.markdown("### Update Log")
                upd_index = st.number_input("Enter row index to update (see leftmost column above)", min_value=0, max_value=len(results)-1, step=1, key="admin_upd_index")
                upd_pw = st.text_input("Admin password to update", type="password", key="admin_upd_pw")
                if st.button("Update Log"):
                    if upd_pw == "light2025":
                        sub_id = results.index[upd_index] + 1
                        upd_dict = {}
                        for col in COLUMNS:
                            upd_dict[col] = st.text_input(f"Update {col}", value=str(results.iloc[upd_index][col]), key=f"upd_{col}")
                        if st.button("Confirm Update"):
                            update_submission_by_id(sub_id, upd_dict)
                            st.success(f"Log at index {upd_index} updated.")
                            st.experimental_rerun()
                    else:
                        st.error("Incorrect admin password.")
            else:
                st.warning("No matching logs found.")
    elif access and password:
        st.error("Incorrect password.")

# ------------------ Main App Logic ------------------

st.set_page_config(page_title="Bring the Light – Intake Form", layout="centered")
st.title("Bring the Light – Food Bank Intake Form")

# Handle reset form logic
if "reset_form" in st.session_state:
    reset_form()

    # CSV file creation removed; only SQLite used

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
