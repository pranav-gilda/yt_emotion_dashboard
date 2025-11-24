import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a model instance
model = genai.GenerativeModel('models/gemini-3-pro-preview')

# Generate a simple response
# for m in genai.list_models():
#     print(m.name, "supports:", m.supported_generation_methods)

# response = model.generate_content("Say hello in three different languages.")
# print(response.text)

from openai import OpenAI
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

result = client.responses.create(
    model="gpt-5.1",
    input="Find the null pointer exception: ...your code here...",
    reasoning={ "effort": "high" },
)

print(result.output_text)