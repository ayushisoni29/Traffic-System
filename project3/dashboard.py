import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

st.title("🚦 Smart Traffic Dashboard")

mode = st.radio("Select Mode", ["Automatic", "Manual"])

if mode == "Manual":
    lanes = ["North", "South", "East", "West"]
    for lane in lanes:
        signal = st.selectbox(f"{lane} Lane Signal", ["Red", "Yellow", "Green"], key=lane)
        if st.button(f"Update {lane}"):
            requests.post(f"{API_URL}/update_signal", json={"lane": lane, "signal": signal})
            st.success(f"{lane} updated to {signal}")
else:
    if st.button("Switch to Auto"):
        requests.post(f"{API_URL}/switch_auto")
        st.success("Switched to Automatic Mode ✅")

# Real-time state view
if st.button("Refresh State"):
    state = requests.get(f"{API_URL}/get_state").json()
    st.json(state)
