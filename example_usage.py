#!/usr/bin/env python3
"""
Example usage of the Background Generator
This script demonstrates how to use the BackgroundGenerator class programmatically.
"""

import sys
import os

# Add the current directory to the Python path so we can import our module
sys.path.append(os.path.dirname(__file__))

from background_generator import BackgroundGenerator

def example_single_logo():
    """Example: Generate background for a single logo."""
    print("🚀 Example: Single Logo Processing")
    print("=" * 50)
    
    try:
        # Initialize the generator
        generator = BackgroundGenerator()
        
        # Process a single logo (using a public logo URL)
        result = generator.process_single_logo(
            logo_path="https://logo.clearbit.com/apple.com",
            company_name="Apple",
            company_description="designs and manufactures innovative consumer electronics",
            style_preference="modern and minimalist",
            save_image=True
        )
        
        print("\n✅ Result:")
        print(f"   Image URL: {result.get('image_url', 'N/A')}")
        print(f"   Saved File: {result.get('saved_file', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_batch_processing():
    """Example: Process multiple logos from CSV."""
    print("\n🚀 Example: Batch Processing")
    print("=" * 50)
    
    try:
        # Initialize the generator
        generator = BackgroundGenerator()
        
        # Process logos from the sample CSV
        results_file = generator.process_csv_batch("sample_logos.csv", save_images=True)
        
        print(f"\n✅ Batch processing completed!")
        print(f"   Results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_logo_analysis_only():
    """Example: Just analyze a logo without generating background."""
    print("\n🚀 Example: Logo Analysis Only")
    print("=" * 50)
    
    try:
        # Initialize the generator
        generator = BackgroundGenerator()
        
        # Analyze a logo
        analysis = generator.analyze_logo("https://logo.clearbit.com/spotify.com")
        
        print("\n🎨 Logo Analysis Results:")
        for key, value in analysis.items():
            print(f"   {key}: {value}")
        
        # Create a prompt based on the analysis
        prompt = generator.create_background_prompt(
            analysis, 
            company_name="Spotify",
            company_description="music streaming platform",
            style_preference="vibrant and energetic"
        )
        
        print(f"\n📝 Generated Prompt:")
        print(f"   {prompt}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all examples."""
    print("🎨 Background Generator Examples")
    print("=" * 60)
    print("Make sure you have set your OPENAI_API_KEY environment variable!")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key and try again.")
        return
    
    # Run examples
    try:
        # Example 1: Logo analysis only (no image generation)
        example_logo_analysis_only()
        
        # Example 2: Single logo processing (uncomment to run)
        # example_single_logo()
        
        # Example 3: Batch processing (uncomment to run)
        # example_batch_processing()
        
        print("\n🎉 Examples completed!")
        print("\nTo run the full examples (with image generation), uncomment the lines in main() function.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()