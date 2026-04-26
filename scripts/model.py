# scripts/list_models.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv("gemKey")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Configure Gemini
genai.configure(api_key=api_key)

print("Available Gemini Models:\n")

try:
    for model in genai.list_models():
        # Only show models that support text generation
        if "generateContent" in model.supported_generation_methods:
            print(f"- {model.name}")

except Exception as e:
    print("Error fetching models:", e)