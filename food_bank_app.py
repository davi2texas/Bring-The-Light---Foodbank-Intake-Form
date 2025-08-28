import streamlit as st
import pandas as pd

st.title("Food Bank Intake Form")

st.subheader("🔍 Lookup Existing Submission by Phone Number")

lookup_phone = st.text_input("Enter phone number to search")

if st.button("Search"):
    try:
        df_existing = pd.read_csv("submissions.csv", header=None)
        df_existing.columns = [
            "Household", "Male Adults", "Male Ages", "Female Adults", "Female Ages",
            "Kids School", "Kids Ages", "Zip", "Referral", "Phone", "Email"
        ]
        match = df_existing[df_existing["Phone"] == lookup_phone]
        if not match.empty:
            st.success("Match found:")
            st.write(match)
        else:
            st.warning("No match found for that phone number.")
    except FileNotFoundError:
        st.info("No submissions yet.")

household = st.number_input("How many people in your household?", min_value=1)
male_adults = st.number_input("How many male adults?", min_value=0)
male_ages = st.text_input("Male adult ages (comma-separated)")
female_adults = st.number_input("How many female adults?", min_value=0)
female_ages = st.text_input("Female adult ages (comma-separated)")
kids_school = st.text_input("Kids' school(s)")
kids_ages = st.text_input("Kids' ages (comma-separated)")
zip_code = st.text_input("Zip code")
referral = st.text_input("How did you hear about us?")
phone = st.text_input("Phone number")
email = st.text_input("Email")

if st.button("Submit"):
    data = {
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