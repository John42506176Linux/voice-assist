import streamlit as st

# Create a Streamlit connection object
conn = st.connection('transcriptions_db', type='sql')

# Initialize database schema if needed
with conn.session as s:
    s.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            request_id TEXT,
            transcript TEXT,
            channel_index INTEGER,
            created_at TIMESTAMP
        )
    """)
    s.commit()

def get_transcriptions(request_id=None):
    """Retrieve transcription data from the SQLite database."""
    if request_id:
        return conn.query(
            """
            SELECT request_id, transcript, channel_index, created_at
            FROM transcriptions
            WHERE request_id = ?
            ORDER BY created_at ASC
            """,
            params=[request_id]
        )
    return conn.query(
        """
        SELECT request_id, transcript, channel_index, created_at
        FROM transcriptions
        ORDER BY created_at ASC
        """
    )

def get_unique_requests():
    """Retrieve unique request IDs with their earliest timestamp."""
    return conn.query(
        """
        SELECT request_id, MIN(created_at) AS earliest_time
        FROM transcriptions
        GROUP BY request_id
        ORDER BY earliest_time ASC
        """
    )

# Streamlit app
st.title("Chat Viewer: Customer-Agent Conversations")

# Add a refresh button
refresh_interval = st.sidebar.slider("Set refresh interval (seconds)", 1, 10, 2)

# Use st.cache_data to cache the unique requests data, but with a short TTL
@st.cache_data(ttl=refresh_interval)
def load_unique_requests():
    """Fetch the unique request IDs from the database."""
    try:
        return get_unique_requests()
    except Exception as e:
        st.error(f"An error occurred while fetching transcription data: {e}")
        return None

# Fetch unique requests
unique_requests = load_unique_requests()

if unique_requests is not None and not unique_requests.empty:
    st.write("### Available Conversations")
    # Display request IDs as clickable options
    request_id = st.selectbox(
        "Select a Request ID to view the conversation:",
        options=unique_requests["request_id"],
        format_func=lambda x: f"{x} (Earliest: {unique_requests.loc[unique_requests['request_id'] == x, 'earliest_time'].values[0]})"
    )
    
    if request_id:
        # Use st.cache_resource to cache the conversation data
        @st.cache_resource(ttl=refresh_interval)
        def load_conversation(request_id):
            """Fetch the conversation for the given request ID."""
            try:
                return get_transcriptions(request_id)
            except Exception as e:
                st.error(f"An error occurred while fetching transcription data: {e}")
                return None

        # Fetch conversation
        filtered_data = load_conversation(request_id)

        if filtered_data is not None and not filtered_data.empty:
            st.write(f"### Conversation for Request ID: {request_id}")
            
            # Display the conversation in a chat-like interface
            for _, row in filtered_data.iterrows():
                if row["channel_index"] == 0:
                    st.markdown(f"""
                    <div style="text-align: left; padding: 10px; margin: 5px; background-color: #f0f0f5; border-radius: 10px; max-width: 70%; display: inline-block;">
                        <b>Customer:</b> {row['transcript']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: right; padding: 10px; margin: 5px; background-color: #e0ffe0; border-radius: 10px; max-width: 70%; margin-left: auto; display: inline-block;">
                        <b>Agent:</b> {row['transcript']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No conversation found for the selected Request ID.")
else:
    st.write("No transcription data found in the database.")