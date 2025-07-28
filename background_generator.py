#!/usr/bin/env python3
"""
Background Generator - AI-powered Website Background Creator
Uses OpenAI's DALL-E to generate landscape website backgrounds based on company logos and context.
"""

import os
import asyncio
import json
import csv
import base64
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import pandas as pd
from dotenv import load_dotenv
import openai
from PIL import Image
import io
import requests
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

class BackgroundGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Background Generator with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Default settings
        self.image_size = "1792x1024"  # Wide landscape format for website backgrounds
        self.quality = "hd"
        self.style = "natural"  # Can be "natural" or "vivid"
        
    def analyze_logo(self, logo_path_or_url: str) -> Dict[str, str]:
        """Analyze logo to extract colors, style, and industry context using GPT-4 Vision."""
        try:
            # Check if it's a URL or local file
            if logo_path_or_url.startswith(('http://', 'https://')):
                # Download image from URL
                response = requests.get(logo_path_or_url)
                if response.status_code != 200:
                    raise ValueError(f"Failed to download logo from {logo_path_or_url}")
                image_bytes = response.content
            else:
                # Read local file
                with open(logo_path_or_url, 'rb') as f:
                    image_bytes = f.read()
            
            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Analyze logo with GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this company logo and provide insights for creating a complementary website background. Please identify:
                                
                                1. Primary colors (hex codes if possible)
                                2. Secondary colors
                                3. Design style (modern, classic, minimalist, bold, etc.)
                                4. Industry/business type (based on visual elements)
                                5. Brand personality (professional, creative, tech-focused, etc.)
                                6. Visual elements (geometric, organic, text-based, icon-based, etc.)
                                
                                Respond in JSON format with these exact keys: primary_colors, secondary_colors, design_style, industry, brand_personality, visual_elements"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            # Extract JSON from the response (in case there's extra text)
            try:
                # Find JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    logo_analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except json.JSONDecodeError:
                # Fallback: create a basic analysis
                logo_analysis = {
                    "primary_colors": ["#2E86AB", "#A23B72"],
                    "secondary_colors": ["#F18F01", "#C73E1D"],
                    "design_style": "modern",
                    "industry": "technology",
                    "brand_personality": "professional",
                    "visual_elements": "geometric"
                }
                print("⚠️ Could not parse JSON response, using fallback analysis")
            
            print(f"🎨 Logo analysis completed:")
            for key, value in logo_analysis.items():
                print(f"   {key}: {value}")
            
            return logo_analysis
            
        except Exception as e:
            print(f"❌ Error analyzing logo: {str(e)}")
            # Return default analysis
            return {
                "primary_colors": ["#2E86AB", "#A23B72"],
                "secondary_colors": ["#F18F01", "#C73E1D"],
                "design_style": "modern",
                "industry": "technology",
                "brand_personality": "professional",
                "visual_elements": "geometric"
            }
    
    def create_background_prompt(self, logo_analysis: Dict[str, str], company_name: str = "", 
                               company_description: str = "", style_preference: str = "") -> str:
        """Create a detailed prompt for DALL-E based on logo analysis and additional context."""
        
        # Base prompt structure
        prompt_parts = []
        
        # Style and composition
        prompt_parts.append("Create a stunning landscape website background image in wide format (16:9 aspect ratio)")
        
        # Incorporate logo analysis
        if logo_analysis.get("industry"):
            industry_styles = {
                "technology": "futuristic cityscape with clean lines and digital elements",
                "healthcare": "serene natural landscape with soft, calming elements",
                "finance": "modern urban skyline with geometric patterns",
                "education": "inspiring mountain or forest vista with bright, optimistic tones",
                "retail": "vibrant, energetic landscape with dynamic elements",
                "consulting": "professional, clean landscape with subtle sophistication",
                "creative": "artistic, imaginative landscape with bold visual interest",
                "manufacturing": "industrial-inspired landscape with strong, reliable elements"
            }
            industry_style = industry_styles.get(logo_analysis["industry"].lower(), "modern, professional landscape")
            prompt_parts.append(f"The scene should be a {industry_style}")
        
        # Color scheme
        if logo_analysis.get("primary_colors"):
            colors = logo_analysis["primary_colors"]
            if isinstance(colors, list):
                color_str = " and ".join(colors[:2])  # Use up to 2 primary colors
            else:
                color_str = str(colors)
            prompt_parts.append(f"incorporating color tones that complement {color_str}")
        
        # Design style
        style_descriptors = {
            "modern": "sleek, minimalist, with clean gradients",
            "classic": "timeless, elegant, with refined details",
            "minimalist": "simple, uncluttered, with subtle beauty",
            "bold": "striking, dramatic, with strong visual impact",
            "organic": "natural, flowing, with soft organic shapes",
            "geometric": "structured, precise, with geometric elements"
        }
        
        design_style = logo_analysis.get("design_style", "modern").lower()
        style_desc = style_descriptors.get(design_style, "modern and professional")
        prompt_parts.append(f"The aesthetic should be {style_desc}")
        
        # Brand personality influence
        personality_elements = {
            "professional": "sophisticated lighting and composition",
            "creative": "artistic flair and unique perspective",
            "tech-focused": "subtle tech elements or digital-inspired patterns",
            "friendly": "warm, welcoming atmosphere",
            "innovative": "forward-thinking, cutting-edge visual elements",
            "trustworthy": "stable, reliable, comforting elements"
        }
        
        personality = logo_analysis.get("brand_personality", "professional").lower()
        if personality in personality_elements:
            prompt_parts.append(f"with {personality_elements[personality]}")
        
        # Additional context
        if company_description:
            prompt_parts.append(f"The image should reflect a company that {company_description}")
        
        # Style preference override
        if style_preference:
            prompt_parts.append(f"Overall style: {style_preference}")
        
        # Technical requirements
        prompt_parts.extend([
            "The image should work well as a website hero background",
            "with good contrast areas for overlaying text",
            "professional quality, high resolution",
            "avoid any text, logos, or specific branded elements",
            "photorealistic style with excellent composition and lighting"
        ])
        
        # Join all parts
        full_prompt = ". ".join(prompt_parts) + "."
        
        print(f"🎯 Generated prompt: {full_prompt[:200]}...")
        return full_prompt
    
    def generate_background(self, prompt: str, filename: str = None) -> Tuple[str, str]:
        """Generate background image using DALL-E."""
        try:
            print(f"🎨 Generating background image...")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=self.image_size,
                quality=self.quality,
                style=self.style,
                n=1
            )
            
            # Get the image URL
            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], 'revised_prompt', prompt)
            
            print(f"✅ Background generated successfully!")
            print(f"🔗 Image URL: {image_url}")
            
            # Download and save the image if filename provided
            if filename:
                self.download_and_save_image(image_url, filename)
            
            return image_url, revised_prompt
            
        except Exception as e:
            print(f"❌ Error generating background: {str(e)}")
            raise
    
    def download_and_save_image(self, image_url: str, filename: str) -> str:
        """Download and save the generated image."""
        try:
            # Create backgrounds directory if it doesn't exist
            backgrounds_dir = "generated_backgrounds"
            if not os.path.exists(backgrounds_dir):
                os.makedirs(backgrounds_dir)
            
            # Add timestamp to filename if not already unique
            if not filename.endswith(('.png', '.jpg', '.jpeg')):
                filename += '.png'
            
            # Create full path
            filepath = os.path.join(backgrounds_dir, filename)
            
            # Download image
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"💾 Background saved to: {filepath}")
                return filepath
            else:
                raise ValueError(f"Failed to download image: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error saving image: {str(e)}")
            raise
    
    def process_single_logo(self, logo_path: str, company_name: str = "", 
                          company_description: str = "", style_preference: str = "",
                          save_image: bool = True) -> Dict[str, str]:
        """Process a single logo and generate background."""
        try:
            print(f"\n🏢 Processing: {company_name or 'Company'}")
            print(f"📁 Logo: {logo_path}")
            
            # Analyze logo
            logo_analysis = self.analyze_logo(logo_path)
            
            # Create prompt
            prompt = self.create_background_prompt(
                logo_analysis, company_name, company_description, style_preference
            )
            
            # Generate filename
            if save_image:
                safe_name = ''.join(c for c in (company_name or 'background') if c.isalnum() or c in '._-')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_name}_{timestamp}.png"
            else:
                filename = None
            
            # Generate background
            image_url, revised_prompt = self.generate_background(prompt, filename)
            
            return {
                'company_name': company_name,
                'logo_path': logo_path,
                'logo_analysis': logo_analysis,
                'original_prompt': prompt,
                'revised_prompt': revised_prompt,
                'image_url': image_url,
                'timestamp': datetime.now().isoformat(),
                'saved_file': filename if save_image else None
            }
            
        except Exception as e:
            print(f"❌ Error processing {company_name or logo_path}: {str(e)}")
            return {
                'company_name': company_name,
                'logo_path': logo_path,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_csv_batch(self, csv_path: str, save_images: bool = True) -> str:
        """Process multiple logos from a CSV file."""
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_cols = ['logo_path']
            optional_cols = ['company_name', 'company_description', 'style_preference']
            
            if 'logo_path' not in df.columns:
                raise ValueError("CSV must contain 'logo_path' column")
            
            results = []
            total = len(df)
            
            print(f"\n🚀 Processing {total} logos from {csv_path}")
            
            for idx, row in df.iterrows():
                print(f"\n--- Processing {idx + 1}/{total} ---")
                
                # Extract data from row
                logo_path = row['logo_path']
                company_name = row.get('company_name', '')
                company_description = row.get('company_description', '')
                style_preference = row.get('style_preference', '')
                
                # Process logo
                result = self.process_single_logo(
                    logo_path, company_name, company_description, 
                    style_preference, save_images
                )
                results.append(result)
            
            # Save results to CSV
            results_df = pd.DataFrame(results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"background_generation_results_{timestamp}.csv"
            results_df.to_csv(results_file, index=False)
            
            print(f"\n✅ Batch processing completed!")
            print(f"📊 Results saved to: {results_file}")
            
            return results_file
            
        except Exception as e:
            print(f"❌ Error processing CSV batch: {str(e)}")
            raise

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Generate website backgrounds based on company logos')
    parser.add_argument('--logo', '-l', type=str, help='Path or URL to company logo')
    parser.add_argument('--name', '-n', type=str, default='', help='Company name')
    parser.add_argument('--description', '-d', type=str, default='', help='Company description')
    parser.add_argument('--style', '-s', type=str, default='', help='Style preference')
    parser.add_argument('--csv', '-c', type=str, help='CSV file with multiple logos to process')
    parser.add_argument('--no-save', action='store_true', help='Do not save images locally')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (overrides environment variable)')
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = BackgroundGenerator(api_key=args.api_key)
        
        if args.csv:
            # Batch processing
            generator.process_csv_batch(args.csv, save_images=not args.no_save)
        elif args.logo:
            # Single logo processing
            result = generator.process_single_logo(
                args.logo, args.name, args.description, 
                args.style, save_image=not args.no_save
            )
            
            print(f"\n🎉 Background generation completed!")
            print(f"🔗 Image URL: {result.get('image_url', 'N/A')}")
            if result.get('saved_file'):
                print(f"💾 Saved as: {result['saved_file']}")
        else:
            print("❌ Please provide either --logo for single processing or --csv for batch processing")
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())