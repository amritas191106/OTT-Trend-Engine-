"""
Centralized LLM client. 
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Requires GOOGLE_API_KEY in your environment / .env file
# Get a free key at https://aistudio.google.com/apikey
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    max_output_tokens=4096,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)
