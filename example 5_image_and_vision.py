"""
Example 5 - Image Creation and Vision with GPT
Demonstrates AI-powered image generation using GPT for prompt enhancement and DALL-E for creation
"""

import openai
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GPTImageCreator:
    """
    AI-powered image creation system using GPT for prompt enhancement and DALL-E for generation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GPT Image Creator
        
        Args:
            api_key: Optional API key. If not provided, will load from environment
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Image generation settings
        self.default_size = "1024x1024"
        self.default_quality = "standard"
        self.default_style = "vivid"
    
    def enhance_prompt_with_gpt(self, user_input: str, style: str = "artistic") -> str:
        """
        Use GPT to enhance a simple user input into a detailed image prompt
        
        Args:
            user_input: Simple description from user
            style: Style preference (artistic, photographic, cartoon, etc.)
            
        Returns:
            Enhanced prompt optimized for DALL-E
        """
        try:
            system_prompt = f"""You are an expert at creating detailed, vivid image prompts for AI image generation.
            Transform the user's simple description into a rich, detailed prompt that will create a stunning {style} image.
            
            Guidelines:
            - Add specific visual details (colors, lighting, composition)
            - Include artistic style elements
            - Mention mood and atmosphere
            - Keep it under 400 characters
            - Make it creative but coherent
            - Focus on visual elements that translate well to images"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this image idea: {user_input}"}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error enhancing prompt: {e}")
            return user_input  # Fallback to original input
    
    def generate_image(self, prompt: str, size: str = None, quality: str = None) -> Dict[str, Any]:
        """
        Generate image using DALL-E with the provided prompt
        
        Args:
            prompt: Image description prompt
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Image quality (standard, hd)
            
        Returns:
            Dictionary with image data and metadata
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size or self.default_size,
                quality=quality or self.default_quality,
                style=self.default_style,
                n=1
            )
            
            return {
                "success": True,
                "image_url": response.data[0].url,
                "revised_prompt": response.data[0].revised_prompt,
                "original_prompt": prompt,
                "size": size or self.default_size,
                "quality": quality or self.default_quality
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_prompt": prompt
            }
    
    def create_image_from_input(self, user_input: str, style: str = "artistic", 
                               enhance_prompt: bool = True) -> Dict[str, Any]:
        """
        Complete pipeline: enhance prompt with GPT and generate image
        
        Args:
            user_input: User's simple description
            style: Visual style preference
            enhance_prompt: Whether to use GPT to enhance the prompt
            
        Returns:
            Complete result with enhanced prompt and image data
        """
        print(f"🎨 Processing your request: '{user_input}'")
        
        # Enhance prompt with GPT if requested
        if enhance_prompt:
            print("🤖 Enhancing prompt with GPT...")
            enhanced_prompt = self.enhance_prompt_with_gpt(user_input, style)
            print(f"✨ Enhanced prompt: {enhanced_prompt}")
        else:
            enhanced_prompt = user_input
        
        # Generate image
        print("🖼️ Generating image with DALL-E...")
        result = self.generate_image(enhanced_prompt)
        
        # Add enhancement info to result
        result["user_input"] = user_input
        result["enhanced_prompt"] = enhanced_prompt
        result["prompt_enhanced"] = enhance_prompt
        result["style"] = style
        
        return result
    
    def suggest_image_ideas(self, theme: str) -> List[str]:
        """
        Use GPT to suggest creative image ideas based on a theme
        
        Args:
            theme: General theme or topic
            
        Returns:
            List of creative image suggestions
        """
        try:
            system_prompt = """You are a creative AI that suggests unique and interesting image ideas.
            Generate 5 creative, specific image concepts based on the given theme.
            Make each suggestion vivid and imaginative but feasible to create."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Suggest 5 creative image ideas for the theme: {theme}"}
                ],
                max_tokens=300,
                temperature=0.9
            )
            
            # Parse suggestions (assuming they're numbered or listed)
            suggestions = response.choices[0].message.content.strip().split('\n')
            return [s.strip() for s in suggestions if s.strip()]
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return [f"A creative interpretation of {theme}"]


class ImageCreationInterface:
    """
    Interactive interface for image creation
    """
    
    def __init__(self):
        """Initialize the interface"""
        self.creator = GPTImageCreator()
        print("🎨 GPT-Powered Image Creation System")
        print("=" * 50)
    
    def interactive_image_creation(self):
        """Interactive image creation session"""
        print("\n🖼️ Interactive Image Creation Mode")
        print("-" * 40)
        print("Type your image ideas (type 'quit' to exit, 'help' for options)")
        
        while True:
            try:
                user_input = input("\n🎨 Describe the image you want: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower().startswith('suggest '):
                    theme = user_input[8:].strip()
                    self.show_suggestions(theme)
                    continue
                
                if user_input:
                    # Ask for style preference
                    print("\n🎭 Choose a style:")
                    print("1. Artistic/Painterly")
                    print("2. Photographic/Realistic") 
                    print("3. Cartoon/Illustration")
                    print("4. Abstract/Modern")
                    print("5. Fantasy/Surreal")
                    
                    style_choice = input("Enter choice (1-5) or press Enter for artistic: ").strip()
                    style_map = {
                        "1": "artistic",
                        "2": "photographic", 
                        "3": "cartoon",
                        "4": "abstract",
                        "5": "fantasy"
                    }
                    style = style_map.get(style_choice, "artistic")
                    
                    # Ask about prompt enhancement
                    enhance = input("\nEnhance prompt with GPT? (y/n, default=y): ").strip().lower()
                    use_enhancement = enhance != 'n'
                    
                    # Create image
                    result = self.creator.create_image_from_input(
                        user_input, 
                        style=style, 
                        enhance_prompt=use_enhancement
                    )
                    
                    self.display_result(result)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def show_help(self):
        """Display help information"""
        print("\n📖 Help - Available Commands:")
        print("-" * 30)
        print("• Type any image description to create an image")
        print("• 'suggest [theme]' - Get AI suggestions for a theme")
        print("• 'help' - Show this help")
        print("• 'quit' - Exit the program")
        print("\n💡 Tips:")
        print("• Be descriptive but concise")
        print("• Mention colors, mood, style preferences")
        print("• Try themes like: nature, sci-fi, fantasy, abstract")
    
    def show_suggestions(self, theme: str):
        """Show AI-generated suggestions for a theme"""
        print(f"\n💡 AI Suggestions for '{theme}':")
        print("-" * 30)
        suggestions = self.creator.suggest_image_ideas(theme)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    
    def display_result(self, result: Dict[str, Any]):
        """Display image creation result"""
        print("\n" + "=" * 50)
        if result["success"]:
            print("✅ Image created successfully!")
            print(f"🔗 Image URL: {result['image_url']}")
            if result["prompt_enhanced"]:
                print(f"🤖 Original input: {result['user_input']}")
                print(f"✨ Enhanced prompt: {result['enhanced_prompt']}")
            print(f"🎨 DALL-E's interpretation: {result['revised_prompt']}")
            print(f"📐 Size: {result['size']} | Quality: {result['quality']}")
            
            # Offer to view
            action = input("\nWould you like to (v)iew in browser or (c)ontinue? ").lower()
            if action == 'v':
                import webbrowser
                webbrowser.open(result['image_url'])
        else:
            print("❌ Image creation failed!")
            print(f"Error: {result['error']}")
    
    def demo_preset_images(self):
        """Demonstrate with preset examples"""
        print("\n🎬 Preset Image Demonstrations")
        print("-" * 40)
        
        examples = [
            ("A cozy reading nook", "artistic"),
            ("Futuristic city at sunset", "photographic"),
            ("Cute robot gardening", "cartoon")
        ]
        
        for description, style in examples:
            print(f"\n🎨 Creating: '{description}' ({style} style)")
            result = self.creator.create_image_from_input(description, style=style)
            if result["success"]:
                print(f"✅ Created! URL: {result['image_url']}")
            else:
                print(f"❌ Failed: {result['error']}")


# Function to be called from main.py
def run_example5():
    """
    Main function to run Example 5 demonstrations
    This function will be called from main.py
    """
    try:
        interface = ImageCreationInterface()
        
        print("\n🎯 Choose an option:")
        print("1. Interactive image creation")
        print("2. Preset demonstrations")
        
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == "1":
            interface.interactive_image_creation()
        elif choice == "2":
            interface.demo_preset_images()
        else:
            print("Running interactive mode by default...")
            interface.interactive_image_creation()
            
        return True
    except Exception as e:
        print(f"❌ Example 5 failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run directly if this file is executed
    run_example5()

