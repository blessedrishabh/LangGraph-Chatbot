import streamlit as st
from main import graph, retreive_all_threads
import uuid
from langchain_core.messages import HumanMessage


# Session States
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
if "conversations" not in st.session_state:
    st.session_state["conversations"] = {}
if "db_loaded" not in st.session_state:
    existing_threads = retreive_all_threads()
    for t_id in existing_threads:
        # Fetch the state for this thread to generate a title
        state_values = graph.get_state({"configurable": {"thread_id": t_id}}).values
        messages = state_values.get("messages", [])
        
        title = "Untitled"
        # Find the first human message to use as the snippet title
        for msg in messages:
            if isinstance(msg, HumanMessage):
                title = msg.content[:25] + "..." if len(msg.content) > 25 else msg.content
                break
                
        # Add the historical thread to the sidebar dictionary
        st.session_state["conversations"][t_id] = title
    st.session_state["conversations"][st.session_state["thread_id"]] = "Untitled"
    st.session_state["db_loaded"] = True

# Utility Fuctions
def GenerateIdAndClear():
    unique_key = str(uuid.uuid4())
    st.session_state["thread_id"] = unique_key
    st.session_state["message_history"] = []
    st.session_state["conversations"][unique_key] = "Untitled"

def FormatMessages(state):
    role = ""
    temp_messages = []
    for msg in state:
        if isinstance(msg, HumanMessage):
            role = "user"
        else:
            role = "assistant"
        temp_messages.append({"user_type": role, "content":msg.content})
    return temp_messages

def FetchConversation(thread_id):
    st.session_state["thread_id"] = thread_id
    CONFIG = {"configurable":{"thread_id":thread_id}}
    # Fetch the state values
    state_values = graph.get_state(config=CONFIG).values
    
    # Safely retrieve "messages". If it doesn't exist, default to an empty list []
    state = state_values.get("messages", [])
    temp_messages = FormatMessages(state)
    st.session_state["message_history"] = temp_messages

# Side bar
with st.sidebar:
    st.title("LangGraph ChatBot")
    if st.button("New Chat"):
        GenerateIdAndClear()
    st.markdown("My Conversations")
    for thread, title in reversed(list(st.session_state["conversations"].items())):
        if st.button(title, key=thread):
            FetchConversation(thread)

# Loading Previous Messages, as every time the screen loads
for messages in st.session_state["message_history"]:
    if messages["user_type"] == "user":
        with st.chat_message("user"):
            st.markdown(messages["content"])
    
    if messages["user_type"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(messages["content"])
        

# Taking the new user Input
user_input = st.chat_input("Type Here...")

if user_input:
    # 1. Update the title if this is the first message in the thread
    if st.session_state["conversations"][st.session_state["thread_id"]] == "Untitled":
        # Grab the first 25 characters and add an ellipsis
        snippet = user_input[:25] + "..." if len(user_input) > 25 else user_input
        st.session_state["conversations"][st.session_state["thread_id"]] = snippet
    # Displaying the new user message
    with st.chat_message("user"):
        st.markdown(user_input)
    #  Making the model call
    config = {"configurable":{"thread_id":st.session_state["thread_id"]}}
    response = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    # saving the new user message
    st.session_state["message_history"].append({"user_type": "user", "content": user_input})
    # Displaying the assistant response
    ai_response = response["messages"][-1].content
    with st.chat_message("assistant"):
        st.markdown(ai_response)
    # Saving the assistant response
    st.session_state["message_history"].append({"user_type": "assistant", "content": ai_response})

    
