import openai
import os
from dotenv import load_dotenv
import json
import time

# go to https://platform.openai.com/, login, go to chat create chat with two variable values customer_name and product, save prompt as reusable prompt, 
# get prompt id and version and use below code to call it
# Load environment variables


load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# Using instruction in the response creation
response = client.responses.create(
    model="gpt-5-nano",
    prompt={
        
        "id": "pmpt_6910f04c950c81958959d0ea0f6b6264082e272395b6571a",
        "version": "2",
        "variables": {
            "customer_name": "Quazi Heider",
            "product": "Noise-Cancelling Headphones"
        }
    }
)
print(response.output_text)
