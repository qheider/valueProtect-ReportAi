from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client with API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Using instruction in the response creation
response = client.responses.create(
    model="gpt-5-nano",
    reasoning={"effort": "low"},
    instructions="Talk like a pirate.",
    input="Are semicolons optional in JavaScript?",
)
print(response.output_text)

#put instruction inside input array as Developer role and user question as User role
response = client.responses.create(
    model="gpt-5-nano",
    reasoning={"effort": "low"},
    input=[
 {
            "role": "developer",
            "content": "Talk like a pirate."
        },
{"role": "user", 
 "content": "Are semicolons optional in JavaScript?"}

    ]
)   
print(response.output_text)
