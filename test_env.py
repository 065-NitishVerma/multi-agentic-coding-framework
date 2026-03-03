import os
from dotenv import load_dotenv

load_dotenv()
print("API KEY LOADED:", bool(os.getenv("OPENAI_API_KEY")))