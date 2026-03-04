"""
OpenAI Tutorial - Main Application
Object-oriented implementation demonstrating basic OpenAI SDK usage
"""

import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from example1 import run_example1

class OpenAIClient:
    """
    A wrapper class for OpenAI API operations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client
        
        Args:
            api_key: Optional API key. If not provided, will load from environment
        """
        # Load environment variables
        load_dotenv()
        
        # Set API key
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Default model settings
        self.default_model = "gpt-4o-mini"
        self.default_max_tokens = 150
        self.default_temperature = 0.7
    
    def chat_completion(
        self,
        message: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a chat completion using OpenAI's chat models
        
        Args:
            message: The user message to send
            model: The model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0-1)
            system_prompt: Optional system prompt for context
            
        Returns:
            The generated response text
        """
        try:
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """
        Generate embeddings for the given text
        
        Args:
            text: The text to generate embeddings for
            model: The embedding model to use
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return []
    
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> List[str]:
        """
        Generate images using DALL-E
        
        Args:
            prompt: Description of the image to generate
            size: Image size (256x256, 512x512, 1024x1024)
            quality: Image quality (standard, hd)
            n: Number of images to generate
            
        Returns:
            List of image URLs
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=n
            )
            
            return [image.url for image in response.data]
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return []


class OpenAITutorial:
    """
    Main tutorial class demonstrating various OpenAI capabilities
    """
    
    def __init__(self):
        """Initialize the tutorial with OpenAI client"""
        self.ai_client = OpenAIClient()
        print("OpenAI Tutorial initialized successfully!")
        print("-" * 50)
    
    def demo_chat_completion(self):
        """Demonstrate basic chat completion"""
        print("\n🤖 Chat Completion Demo")
        print("-" * 30)
        
        # Simple conversation
        response = self.ai_client.chat_completion("Hello! Tell me a fun fact about Python programming.")
        print(f"AI Response: {response}")
        
        # With system prompt
        system_prompt = "You are a helpful coding assistant. Keep responses concise and practical."
        response = self.ai_client.chat_completion(
            "How do I create a virtual environment in Python?",
            system_prompt=system_prompt
        )
        print(f"\nAI Response (with system prompt): {response}")
    
    def demo_embeddings(self):
        """Demonstrate text embeddings"""
        print("\n📊 Text Embeddings Demo")
        print("-" * 30)
        
        text = "OpenAI provides powerful AI models for developers"
        embeddings = self.ai_client.generate_embeddings(text)
        
        if embeddings:
            print(f"Text: {text}")
            print(f"Embedding vector length: {len(embeddings)}")
            print(f"First 5 values: {embeddings[:5]}")
        else:
            print("Failed to generate embeddings")
    
    def demo_image_generation(self):
        """Demonstrate image generation"""
        print("\n🎨 Image Generation Demo")
        print("-" * 30)
        
        prompt = "A serene mountain landscape with a crystal clear lake, digital art style"
        print(f"Generating image with prompt: {prompt}")
        
        image_urls = self.ai_client.generate_image(prompt)
        
        if image_urls:
            print(f"Generated {len(image_urls)} image(s):")
            for i, url in enumerate(image_urls, 1):
                print(f"Image {i}: {url}")
        else:
            print("Failed to generate image")
    
    def interactive_chat(self):
        """Interactive chat session with the AI"""
        print("\n💬 Interactive Chat Mode")
        print("-" * 30)
        print("Type your messages (type 'quit' to exit):")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if user_input:
                    response = self.ai_client.chat_completion(user_input)
                    print(f"AI: {response}")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def run_all_demos(self):
        """Run all demonstration functions"""
        try:
            # self.demo_chat_completion()
            # self.demo_embeddings()
            # self.demo_image_generation()
            
            # Ask user if they want to try interactive chat
            # print("\n" + "=" * 50)
            # choice = input("Would you like to try interactive chat? (y/n): ").lower()
            # if choice in ['y', 'yes']:
            #     self.interactive_chat()
            
            # Ask user if they want to run Example 1
            print("\n" + "=" * 50)
            example_choice = input("Would you like to run Example 1 (Bedtime Story Demo)? (y/n): ").lower()
            if example_choice in ['y', 'yes']:
                print("\n")
                run_example1()
                
        except Exception as e:
            print(f"Error running demos: {str(e)}")
            print("Make sure your OpenAI API key is set correctly in the .env file")


def main():
    """Main entry point"""
    print("🚀 Welcome to OpenAI Tutorial!")
    print("=" * 50)
    
    try:
        # Create tutorial instance
        tutorial = OpenAITutorial()
        
        # Run all demonstrations
        tutorial.run_all_demos()
        
    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        print("Please check your .env file and ensure OPENAI_API_KEY is set")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()