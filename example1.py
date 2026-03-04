import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Function to be called from main.py
def run_example1():
    """
    Main function to run Example 1 demonstrations
    This function will be called from main.py
    """
    try:
        print("🚀 Running Example 1 - GPT Advanced Demo")
        print("=" * 50)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using available model
            messages=[
                {"role": "user", "content": "Write a one-sentence bedtime story about a unicorn."}
            ]
        )
        
        print("🦄 Bedtime Story:")
        print(response.choices[0].message.content)
        print(f"\n✅ Model used: {response.model}")
        print(f"📊 Tokens used: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ Error in Example 1: {str(e)}")
        print("Make sure your OpenAI API key is set in the .env file")


if __name__ == "__main__":
    # Run directly if this file is executed
    run_example1()