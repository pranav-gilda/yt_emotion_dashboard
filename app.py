import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a model instance
model = genai.GenerativeModel('models/gemini-2.5-flash')

# Generate a simple response
# for m in genai.list_models():
#     print(m.name, "supports:", m.supported_generation_methods)

response = model.generate_content("Say hello in three different languages.")
print(response.text)
