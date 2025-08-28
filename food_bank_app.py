import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Bring the Light – Food Bank Intake Form")

# 🔄 Reset logic before rendering form
if "reset_form" in st.session_state:
    reset_values = {
        "household": 1,
        "male_adults": 0,
        "male_ages": "",
        "female_adults": 0,
        "female_ages": "",
        "kids_school": "",
        "kids_ages": "",
        "zip_code": "",
        "referral": "",
        "phone": "",
        "email": ""
    }
    for key, value in reset_values.items():
        st.session_state[key] = value
    del st.session_state["reset_form"]

# 🔍 Lookup Section
st.markdown("## 🔍 Lookup Existing Submission")
with st.form("lookup_form"):
    st.subheader("Look up by Contact Number")
    lookup_phone = st.text_input("Enter contact number to search", key="lookup_phone", placeholder="e.g. 555-1234")
    search = st.form_submit_button("Search")

    if search:
        try:
            df_existing = pd.read_csv("submissions.csv", header=None)
            df_existing.columns = [
                "Timestamp", "Household", "Male Adults", "Male Ages", "Female Adults", "Female Ages",
                "Kids School", "Kids Ages", "Zip", "Referral", "Phone", "Email"
            ]
            match = df_existing[df_existing["Phone"] == lookup_phone]
            if not match.empty:
                st.success("Match found:")
                st.write(match)
            else:
                st.warning("No match found for that contact number.")
        except FileNotFoundError:
            st.info("No submissions yet.")

st.markdown("---")

# 📝 New Submission Section
st.markdown("## 📝 New Intake Submission")
with st.form("new_submission_form"):
    st.subheader("Fill Out Household Details")

    st.markdown("### 👨‍👩‍👧 Household Info")
    household = st.number_input("Household size", min_value=1, key="household")
    male_adults = st.number_input("Male adults", min_value=0, key="male_adults")
    male_ages = st.text_input("Ages of male adults (comma-separated)", key="male_ages")
    female_adults = st.number_input("Female adults", min_value=0, key="female_adults")
    female_ages = st.text_input("Ages of female adults (comma-separated)", key="female_ages")

    st.markdown("### 🧒 Children Info")
    kids_school = st.text_input("School(s) children attend", key="kids_school")
    kids_ages = st.text_input("Children's ages (comma-separated)", key="kids_ages")

    st.markdown("### 📬 Contact Info")

    # 🚫 Autofill-resistant inputs using custom HTML
    st.markdown("""
        <input type="text" name="phone" placeholder="Contact number (e.g. 555-1234)" autocomplete="off"
        style="width: 100%; padding: 0.5em; margin-bottom: 1em; border: 1px solid #ccc; border-radius: 4px;">
    """, unsafe_allow_html=True)

    st.markdown("""
        <input type="email" name="email" placeholder="Your e-mail address" autocomplete="off"
        style="width: 100%; padding: 0.5em; margin-bottom: 1em; border: 1px solid #ccc; border-radius: 4px;">
    """, unsafe_allow_html=True)

    # Hidden Streamlit inputs to capture values manually if needed
    phone = st.text_input("Phone (manual entry)", key="phone", label_visibility="collapsed")
    email = st.text_input("Email (manual entry)", key="email", label_visibility="collapsed")

    zip_code = st.text_input("Zip code", key="zip_code")
    referral = st.text_input("How did you hear about us?", key="referral")

    submitted = st.form_submit_button("Submit")

    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "Timestamp": timestamp,
            "Household": household,
            "Male Adults": male_adults,
            "Male Ages": male_ages,
            "Female Adults": female_adults,
            "Female Ages": female_ages,
            "Kids School": kids_school,
            "Kids Ages": kids_ages,
            "Zip": zip_code,
            "Referral": referral,
            "Phone": phone,
            "Email": email
        }
        df = pd.DataFrame([data])
        df.to_csv("submissions.csv", mode='a', header=False, index=False)
        st.success("Submission saved!")

        # ✅ Guarded rerun to prevent AttributeError
        if "reset_form" not in st.session_state:
            st.session_state["reset_form"] = True
            st.rerun()

st.markdown("---")

# ✏️ Update Section
st.markdown("## ✏️ Update Existing Submission")
with st.form("update_form"):
    st.subheader("Search and Edit Submission")

    update_phone = st.text_input("Enter contact number to update", key="update_phone", placeholder="e.g. 555-1234")
    find = st.form_submit_button("Find Submission")

    if find:
        try:
            df = pd.read_csv("submissions.csv", header=None)
            df.columns = [
                "Timestamp", "Household", "Male Adults", "Male Ages", "Female Adults", "Female Ages",
                "Kids School", "Kids Ages", "Zip", "Referral", "Phone", "Email"
            ]
            match = df[df["Phone"] == update_phone]

            if not match.empty:
                st.success("Submission found. You can now edit the fields below.")
                st.subheader("🔧 Edit Submission Details")
                index = match.index[0]

                st.markdown("### 👨‍👩‍👧 Household Info")
                household = st.number_input("Household", value=int(match.at[index, "Household"]), min_value=1)
                male_adults = st.number_input("Male Adults", value=int(match.at[index, "Male Adults"]), min_value=0)
                male_ages = st.text_input("Male Ages", value=match.at[index, "Male Ages"])
                female_adults = st.number_input("Female Adults", value=int(match.at[index, "Female Adults"]), min_value=0)
                female_ages = st.text_input("Female Ages", value=match.at[index, "Female Ages"])

                st.markdown("### 🧒 Children Info")
                kids_school = st.text_input("Kids School", value=match.at[index, "Kids School"])
                kids_ages = st.text_input("Kids Ages", value=match.at[index, "Kids Ages"])

                st.markdown("### 📬 Contact Info")
                zip_code = st.text_input("Zip", value=match.at[index, "Zip"])
                referral = st.text_input("Referral", value=match.at[index, "Referral"])
                phone = st.text_input("Phone", value=match.at[index, "Phone"])
                email = st.text_input("Email", value=match.at[index, "Email"])

                update = st.form_submit_button("Update Submission")

                if update:
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

                    df.to_csv("submissions.csv", index=False, header=False)

                    if phone.strip():
                        st.success(f"Submission for {phone} updated successfully!")
                    else:
                        st.success("Submission updated successfully!")
            else:
                st.warning("No submission found for that contact number.")
        except FileNotFoundError:
            st.info("No submissions yet.")

st.markdown("---")
st.caption("Thank you for serving with care. Every submission helps us meet real needs with dignity.")