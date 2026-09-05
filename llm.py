from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Initialize client (will automatically use GEMINI_API_KEY from .env)
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words"
)

print(response.text)