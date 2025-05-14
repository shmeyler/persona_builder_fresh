import streamlit as st

st.set_page_config(page_title="Persona Builder", layout="wide")

st.title("🧠 AI Persona Builder")
st.markdown("Fill out the form below to generate a custom persona profile.")

with st.form("persona_form"):
    st.header("📋 Demographics")
    age_range = st.text_input("Age Range", placeholder="e.g. 30–50")
    gender = st.text_input("Gender", placeholder="e.g. Predominantly Male")
    location = st.text_input("Location", placeholder="e.g. Urban areas")
    education = st.text_input("Education Level")
    occupation = st.text_input("Occupation / Industry")

    st.header("💭 Psychographics")
    income = st.text_input("Income Level", placeholder="$80,000+")
    interests = st.text_area("Interests and Hobbies")
    values = st.text_area("Values and Beliefs")
    goals = st.text_area("Goals and Aspirations")
    pain_points = st.text_area("Pain Points and Challenges")

    st.header("📂 Resonate Taxonomy Inputs (placeholder)")
    vertical = st.selectbox("Select a vertical", ["Automotive", "Retail", "Travel", "Healthcare", "Tech"])
    traits = st.multiselect("Select Traits", ["In-Market", "Eco-Conscious", "Luxury Buyer", "Budget-Conscious"])

    submitted = st.form_submit_button("🔍 Build Persona")

if submitted:
    st.success("Persona submitted! (next: process inputs and generate persona PDF)")
    st.write("Demographics:")
    st.write(f"- Age Range: {age_range}")
    st.write(f"- Gender: {gender}")
    st.write(f"- Location: {location}")
    st.write(f"- Education: {education}")
    st.write(f"- Occupation: {occupation}")

    st.write("Psychographics:")
    st.write(f"- Income: {income}")
    st.write(f"- Interests: {interests}")
    st.write(f"- Values: {values}")
    st.write(f"- Goals: {goals}")
    st.write(f"- Pain Points: {pain_points}")

    st.write("Resonate Layer:")
    st.write(f"- Vertical: {vertical}")
    st.write(f"- Traits: {traits}")
