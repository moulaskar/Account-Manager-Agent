import streamlit as st
import requests
import random

API_BASE = "http://localhost:8000"

st.title("🤖 Brightspeed Chatbot")

# --- User and Session ID Management ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(random.randint(1000, 9999))

if "session_id" not in st.session_state:
    with st.spinner("Initializing session..."):
        try:
            res = requests.post(
                f"{API_BASE}/session", json={"user_id": st.session_state.user_id}
            )
            res.raise_for_status()
            st.session_state.session_id = res.json()["session_id"]
        except Exception as e:
            st.error(f"Failed to create session: {e}")
            st.stop()

# --- Chat History ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Display Chat ---
for entry in st.session_state.chat_history:
    with st.chat_message(entry["sender"]):
        st.markdown(entry["message"])

# --- User Input ---
if user_input := st.chat_input("Type your message..."):
    # Append user message to history
    st.session_state.chat_history.append({"sender": "user", "message": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        res = requests.post(
            f"{API_BASE}/chat",
            json={
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "message": user_input
            }
        )
        res.raise_for_status()
        reply = res.json().get("response", "No response")

    except Exception as e:
        reply = f"Error: {e}"

    st.session_state.chat_history.append({"sender": "assistant", "message": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)