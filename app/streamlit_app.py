import streamlit as st
import sqlite3
import pandas as pd
import os
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

# Load transcription data
st.write("Fetching transcription data from the database...")
try:
    # Fetch unique requests
    unique_requests = get_unique_requests()
    if not unique_requests.empty:
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
                        <div style="text-align: left; padding: 10px; margin: 5px; background-color: #f0f0f5; border-radius: 10px; max-width: 70%;">
                            <b>Customer:</b> {row['transcript']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif row["channel_index"] == 1:
                        st.markdown(f"""
                        <div style="text-align: right; padding: 10px; margin: 5px; background-color: #e0ffe0; border-radius: 10px; max-width: 70%; margin-left: auto;">
                            <b>Agent:</b> {row['transcript']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.write("No conversation found for the selected Request ID.")
    else:
        st.write("No transcription data found in the database.")
except Exception as e:
    st.error(f"An error occurred while fetching transcription data: {e}")
