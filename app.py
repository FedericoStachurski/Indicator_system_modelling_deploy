'''
Useful commands to run this app:
python3  -m venv streamlitEnv
source streamlitEnv/bin/activate
pip3 install -r requirements.txt
python3 -m streamlit run app.py
git status
git commit -m "Add simple Streamlit app with slider"
'''
import streamlit as st

st.title("Indicator system modelling: Proof of Concept")

# Create slider
number = st.slider("Select a value", min_value=0, max_value=100, value=50)

# Show the selected value
st.write(f"You selected: {number}")

# Do something with the value — e.g. square it
st.write(f"The square of {number} is {number ** 2}")