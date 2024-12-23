import streamlit as st
import sqlite3
import pandas as pd
import time

# SQLite database path
DB_PATH = 'transcriptions.db'

def get_transcriptions():
    """Retrieve all transcription data from the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT request_id, transcript, channel_index, created_at
            FROM transcriptions
            ORDER BY created_at ASC
        """
        df = pd.read_sql_query(query, conn)
    return df

def get_unique_requests():
    """Retrieve unique request IDs with their earliest timestamp."""
    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT request_id, MIN(created_at) AS earliest_time
            FROM transcriptions
            GROUP BY request_id
            ORDER BY earliest_time ASC
        """
        df = pd.read_sql_query(query, conn)
    return df

# Streamlit app
st.title("Chat Viewer: Customer-Agent Conversations")

# Add a refresh button
refresh_interval = st.sidebar.slider("Set refresh interval (seconds)", 5, 60, 10)

def load_transcription_data():
    """Fetch the transcription data from the database."""
    try:
        unique_requests = get_unique_requests()
        return unique_requests
    except Exception as e:
        st.error(f"An error occurred while fetching transcription data: {e}")
        return None

# Fetch unique requests
unique_requests = load_transcription_data()

if unique_requests is not None and not unique_requests.empty:
    st.write("### Available Conversations")
    # Display request IDs as clickable options
    request_id = st.selectbox(
        "Select a Request ID to view the conversation:",
        options=unique_requests["request_id"],
        format_func=lambda x: f"{x} (Earliest: {unique_requests.loc[unique_requests['request_id'] == x, 'earliest_time'].values[0]})"
    )
    
    if request_id:
        # Fetch transcriptions for the selected request ID
        transcriptions = get_transcriptions()
        filtered_data = transcriptions[transcriptions["request_id"] == request_id]
        
        if not filtered_data.empty:
            st.write(f"### Conversation for Request ID: {request_id}")
            
            # Display the conversation in a chat-like interface
            for _, row in filtered_data.iterrows():
                if row["channel_index"] == 0:
                    st.markdown(f"""
                    <div style="text-align: left; padding: 10px; margin: 5px; background-color: #f0f0f5; border-radius: 10px; max-width: 70%; display: inline-block;">
                        <b>Customer:</b> {row['transcript']}
                    </div>
                    """, unsafe_allow_html=True)
                elif row["channel_index"] == 1:
                    st.markdown(f"""
                    <div style="text-align: right; padding: 10px; margin: 5px; background-color: #e0ffe0; border-radius: 10px; max-width: 70%; margin-left: auto; display: inline-block;">
                        <b>Agent:</b> {row['transcript']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No conversation found for the selected Request ID.")
else:
    st.write("No transcription data found in the database.")

# Auto-refresh functionality
while True:
    time.sleep(refresh_interval)
    st.rerun()
