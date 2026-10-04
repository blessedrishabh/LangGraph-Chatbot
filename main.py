import langchain
import os
from langgraph.graph import StateGraph, START, END, add_messages
from typing import TypedDict, Annotated
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage
import sqlite3

connection = sqlite3.connect("chatbot.db", check_same_thread=False)
memory = SqliteSaver(connection)

load_dotenv()
model = ChatGroq(model="openai/gpt-oss-20b")
class ChatBot(TypedDict):
    messages: Annotated[list, add_messages]


def query(state):
    message = state["messages"]
    prompt = SystemMessage("You are an AI Assistant, Answer the user query in a straight-forward fashion, query")
    full_conversation = [prompt]+message
    response = model.invoke(full_conversation)
    return {"messages": [response]}

state = StateGraph(ChatBot)

state.add_node("query", query)

state.add_edge(START, "query")
state.add_edge("query", END)

graph = state.compile(checkpointer=memory)

def retreive_all_threads():
    seen = set()
    all_threads = []
    
    for threads in memory.list(None):
        thread_id = threads.config["configurable"]["thread_id"]
        # Keep track of unique threads while preserving order
        if thread_id not in seen:
            seen.add(thread_id)
            all_threads.append(thread_id)

    # Reverse it so the list goes from oldest -> newest
    all_threads.reverse()
    
    return all_threads

