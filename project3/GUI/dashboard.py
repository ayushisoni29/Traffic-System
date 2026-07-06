import streamlit as st
import requests

st.title("🚦 Smart Traffic Dashboard")

if st.button("Get Signal Status"):
    res = requests.get("http://127.0.0.1:5000/status").json()
    st.json(res)

choice = st.selectbox("Change Signal", ["N", "S", "E", "W"])
if st.button("Change"):
    res = requests.get(f"http://127.0.0.1:5000/change/{choice}").json()
    st.success(f"Changed to {res['signal']}")
