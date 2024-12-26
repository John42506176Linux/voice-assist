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
            ORDER BY created_at DESC
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
            ORDER BY earliest_time DESC
        """
        df = pd.read_sql_query(query, conn)
    return df

# Initialize session state for tracking the last refresh time
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Streamlit app
st.title("Chat Viewer: Customer-Agent Conversations")

# Add refresh interval selector to sidebar
refresh_interval = st.sidebar.slider("Set refresh interval (seconds)", 0.1, 10.0, 0.5)

# Add manual refresh button
if st.sidebar.button("Refresh Now"):
    st.session_state.last_refresh = time.time()

def load_transcription_data():
    """Fetch the transcription data from the database."""
    try:
        unique_requests = get_unique_requests()
        return unique_requests
    except Exception as e:
        st.error(f"An error occurred while fetching transcription data: {e}")
        return None

# Check if it's time to refresh
current_time = time.time()
if current_time - st.session_state.last_refresh >= refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()

# Fetch unique requests
unique_requests = load_transcription_data()

if unique_requests is not None and not unique_requests.empty:
    st.write("### Available Conversations")
    
    # Display request IDs as clickable options with conversation ID
    request_id = st.selectbox(
        "Select a Request ID to view the conversation:",
        options=unique_requests["request_id"],
        format_func=lambda x: f"Conversation ID: {x} (Started: {unique_requests.loc[unique_requests['request_id'] == x, 'earliest_time'].values[0]})"
    )
    
    if request_id:
        # Fetch transcriptions for the selected request ID
        transcriptions = get_transcriptions()
        filtered_data = transcriptions[transcriptions["request_id"] == request_id].sort_values('created_at', ascending=False)
        
        if not filtered_data.empty:
            st.write(f"### Conversation ID: {request_id}")
            
            # Display the conversation in a chat-like interface
            for _, row in filtered_data.iterrows():
                if row["channel_index"] == 0:  # Customer message
                    st.markdown(f"""
                    <div style="margin: 5px 50% 5px 0;">
                        <div style="background-color: #f0f0f5; border-radius: 10px; padding: 10px; color: black;">
                            <b>Customer:</b> {row['transcript']}
                            <br><small>{row['created_at']}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif row["channel_index"] == 1:  # Agent message
                    st.markdown(f"""
                    <div style="margin: 5px 0 5px 50%; text-align: right;">
                        <div style="background-color: #e0ffe0; border-radius: 10px; padding: 10px; color: black;">
                            <b>Agent:</b> {row['transcript']}
                            <br><small>{row['created_at']}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No conversation found for the selected Request ID.")

else:
    st.write("No transcription data found in the database.")

# Display last refresh time
st.sidebar.write(f"Last refreshed: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_refresh))}")