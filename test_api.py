import os
from dotenv import load_dotenv
from google import genai

print("1. Loading .env file...")
# load_dotenv returns True if it successfully finds and loads a file
env_loaded = load_dotenv()

if not env_loaded:
    print("⚠️ WARNING: load_dotenv() did not find a .env file in this directory.")

# Grab the key explicitly
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("\n❌ ERROR: GEMINI_API_KEY is completely blank!")
    print("Check your .env file to ensure it says: GEMINI_API_KEY=your_key_here")
    print("Also, ensure your file isn't accidentally named '.env.txt'")
else:
    print(f"2. Success! API Key found (starts with {api_key[:8]}...)")
    print("3. Sending request to Gemini...")
    
    # Pass the key explicitly to the client
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='models/gemini-2.5-flash',
        contents='Say exactly: Gemini is working!'
    )
    
    print("\n=== FINAL OUTPUT ===")
    print(response.text)
    print("====================")