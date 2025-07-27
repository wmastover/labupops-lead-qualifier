#!/usr/bin/env python3
"""
Lead Qualifier - AI-powered Website Audit Tool
Uses GPT-4o Vision to analyze website screenshots and determine if they appear outdated.
"""

import os
import asyncio
import json
import csv
import base64
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page
import openai
from PIL import Image
import io

# Load environment variables
load_dotenv()

class LeadQualifier:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Lead Qualifier with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Screenshot settings
        self.screenshot_width = 1920
        self.screenshot_height = 1080
        self.timeout = 30000  # 30 seconds
        
    async def take_screenshot(self, url: str, browser: Browser, save_debug: bool = True) -> Optional[bytes]:
        """Take a full-page screenshot of the website."""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            page = await browser.new_page()
            await page.set_viewport_size({"width": self.screenshot_width, "height": self.screenshot_height})
            
            print(f"📸 Taking screenshot of {url}")
            
            # Navigate to the page with timeout
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait a bit more for dynamic content
            await page.wait_for_timeout(2000)
            
            # Take full page screenshot
            screenshot = await page.screenshot(full_page=True, type='png')
            
            # Save screenshot for debugging if requested
            if save_debug:
                try:
                    # Create screenshots directory if it doesn't exist
                    screenshots_dir = "screenshots"
                    if not os.path.exists(screenshots_dir):
                        os.makedirs(screenshots_dir)
                    
                    # Create a safe filename from the URL
                    safe_filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
                    # Limit filename length and remove invalid characters
                    safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c in '._-')[:100]
                    screenshot_path = os.path.join(screenshots_dir, f"{safe_filename}.png")
                    
                    # Save the screenshot
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot)
                    
                    print(f"💾 Screenshot saved to: {screenshot_path}")
                
                except Exception as e:
                    print(f"⚠️ Could not save screenshot: {e}")
            
            await page.close()
            return screenshot
            
        except Exception as e:
            print(f"❌ Error taking screenshot of {url}: {str(e)}")
            return None
    
    def encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def analyze_website_design(self, screenshot_bytes: bytes) -> Dict[str, any]:
        """Send screenshot to GPT-4o Vision for analysis using function calling."""
        try:
            # Encode image
            base64_image = self.encode_image(screenshot_bytes)
            
            print("🧠 Analyzing website design with GPT-4o...")
            
            # Define the function schema for website analysis
            website_analysis_function = {
                "type": "function",
                "function": {
                    "name": "analyze_website_design",
                    "description": "Analyze a website screenshot to determine if the design looks modern or outdated",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "judgment": {
                                "type": "string",
                                "enum": ["Modern", "Outdated", "Unclear"],
                                "description": "Whether the website design appears modern, outdated, or unclear"
                            },
                            "reason": {
                                "type": "string",
                                "description": "1-2 sentence explanation of the assessment"
                            },
                            "confidence": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Confidence level of the assessment (0-100)"
                            }
                        },
                        "required": ["judgment", "reason", "confidence"]
                    }
                }
            }
            
            # Prepare the prompt
            system_prompt = """You are an expert web designer and developer with extensive experience in modern web design trends and UX principles."""
            
            user_prompt = """
            Analyze this website screenshot to determine if the design looks modern or outdated.

            Consider these factors:
            - Layout design (responsive vs fixed-width, grid systems)
            - Typography (modern fonts vs default system fonts)
            - Color schemes and visual hierarchy
            - Navigation patterns and UI elements
            - Overall visual sophistication and current design trends
            - Mobile-first design principles
            - White space usage and content density

            Use the analyze_website_design function to provide your assessment.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                tools=[website_analysis_function],
                tool_choice={"type": "function", "function": {"name": "analyze_website_design"}},
                max_tokens=300,
                temperature=0.1
            )
            
            # Extract the function call result
            if response.choices[0].message.tool_calls:
                function_call = response.choices[0].message.tool_calls[0]
                if function_call.function.name == "analyze_website_design":
                    # Parse the function arguments
                    result = json.loads(function_call.function.arguments)
                    return result
                else:
                    print(f"⚠️ Unexpected function called: {function_call.function.name}")
                    return {
                        "judgment": "Unclear",
                        "reason": "Unexpected function response",
                        "confidence": 0
                    }
            else:
                print("⚠️ No function call in response")
                return {
                    "judgment": "Unclear",
                    "reason": "No function call received",
                    "confidence": 0
                }
                
        except Exception as e:
            print(f"❌ Error analyzing website: {str(e)}")
            return {
                "judgment": "Unclear",
                "reason": f"Analysis error: {str(e)}",
                "confidence": 0
            }
    
    async def process_url(self, url: str, browser: Browser, save_debug: bool = True) -> Dict[str, any]:
        """Process a single URL: take screenshot and analyze."""
        result = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "judgment": "Unclear",
            "reason": "Processing failed",
            "confidence": 0,
            "screenshot_taken": False
        }
        
        try:
            # Take screenshot
            screenshot = await self.take_screenshot(url, browser, save_debug)
            
            if screenshot:
                result["screenshot_taken"] = True
                
                # Analyze with GPT-4o
                analysis = self.analyze_website_design(screenshot)
                
                # Update result with analysis
                result.update({
                    "judgment": analysis.get("judgment", "Unclear"),
                    "reason": analysis.get("reason", "Analysis failed"),
                    "confidence": analysis.get("confidence", 0)
                })
                
                print(f"✅ {url}: {result['judgment']} (confidence: {result['confidence']}%)")
                print(f"   Reason: {result['reason']}")
            else:
                result["reason"] = "Failed to take screenshot"
                print(f"❌ {url}: Failed to take screenshot")
                
        except Exception as e:
            result["reason"] = f"Processing error: {str(e)}"
            print(f"❌ {url}: {str(e)}")
        
        return result
    
    async def process_urls(self, urls: List[str], output_file: str = None) -> List[Dict[str, any]]:
        """Process multiple URLs and return results."""
        results = []
        
        print(f"🚀 Starting analysis of {len(urls)} websites...")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            try:
                # Process URLs sequentially to avoid overwhelming the API
                for i, url in enumerate(urls, 1):
                    print(f"\n[{i}/{len(urls)}] Processing: {url}")
                    
                    result = await self.process_url(url, browser)
                    results.append(result)
                    
                    # Small delay between requests
                    if i < len(urls):
                        await asyncio.sleep(1)
                
            finally:
                await browser.close()
        
        # Save results if output file specified
        if output_file:
            self.save_results(results, output_file)
        
        return results
    
    def save_results(self, results: List[Dict[str, any]], filename: str):
        """Save results to CSV file."""
        try:
            # Convert to DataFrame for easy CSV export
            df = pd.DataFrame(results)
            
            # Reorder columns for better readability
            column_order = ['url', 'judgment', 'confidence', 'reason', 'screenshot_taken', 'timestamp']
            df = df.reindex(columns=column_order)
            
            df.to_csv(filename, index=False)
            print(f"💾 Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def load_urls_from_csv(self, filename: str, url_column: str = 'website') -> List[str]:
        """Load URLs from a CSV file."""
        try:
            df = pd.read_csv(filename)
            if url_column not in df.columns:
                raise ValueError(f"Column '{url_column}' not found in CSV file. Available columns: {list(df.columns)}")
            
            # Filter out empty/NaN websites and clean them
            urls = df[url_column].dropna().tolist()
            # Remove empty strings
            urls = [url.strip() for url in urls if url.strip()]
            
            print(f"📋 Loaded {len(urls)} valid website URLs from {filename}")
            print(f"📊 Total restaurants in file: {len(df)}")
            print(f"📊 Restaurants with websites: {len(urls)}")
            
            return urls
            
        except Exception as e:
            print(f"❌ Error loading URLs from CSV: {str(e)}")
            return []

    def load_restaurants_with_websites(self, filename: str) -> List[Dict[str, str]]:
        """Load restaurant data with websites for enhanced reporting."""
        try:
            df = pd.read_csv(filename)
            
            # Filter to only restaurants with websites
            restaurants_with_websites = df[df['website'].notna() & (df['website'] != '')].copy()
            
            # Convert to list of dictionaries for easier handling
            restaurants = []
            for _, row in restaurants_with_websites.iterrows():
                restaurants.append({
                    'name': row.get('name', 'Unknown'),
                    'website': row.get('website', '').strip(),
                    'address': row.get('address', 'Unknown'),
                    'rating': row.get('rating', 'N/A'),
                    'phone_number': row.get('phone_number', 'N/A')
                })
            
            print(f"📋 Loaded {len(restaurants)} restaurants with websites")
            return restaurants
            
        except Exception as e:
            print(f"❌ Error loading restaurant data: {str(e)}")
            return []

    async def process_restaurants(self, restaurants: List[Dict[str, str]], output_file: str = None, save_debug: bool = True) -> List[Dict[str, any]]:
        """Process restaurants with website analysis."""
        results = []
        
        print(f"🚀 Starting website analysis of {len(restaurants)} restaurants...")
        
        if save_debug:
            print("📸 Debug mode: Screenshots will be saved to 'screenshots/' folder")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            try:
                # Process URLs sequentially to avoid overwhelming the API
                for i, restaurant in enumerate(restaurants, 1):
                    url = restaurant['website']
                    name = restaurant['name']
                    
                    print(f"\n[{i}/{len(restaurants)}] Processing: {name}")
                    print(f"   Website: {url}")
                    
                    result = await self.process_url(url, browser, save_debug)
                    
                    # Add restaurant info to result
                    result.update({
                        'restaurant_name': name,
                        'address': restaurant.get('address', 'Unknown'),
                        'rating': restaurant.get('rating', 'N/A'),
                        'phone_number': restaurant.get('phone_number', 'N/A')
                    })
                    
                    results.append(result)
                    
                    # Small delay between requests
                    if i < len(restaurants):
                        await asyncio.sleep(2)  # Slightly longer delay to be respectful
                
            finally:
                await browser.close()
        
        # Save results if output file specified
        if output_file:
            self.save_enhanced_results(results, output_file)
        
        return results

    def save_enhanced_results(self, results: List[Dict[str, any]], filename: str):
        """Save enhanced results with restaurant info to CSV file."""
        try:
            # Convert to DataFrame for easy CSV export
            df = pd.DataFrame(results)
            
            # Reorder columns for better readability
            column_order = [
                'restaurant_name', 'url', 'judgment', 'confidence', 'reason', 
                'address', 'rating', 'phone_number', 'screenshot_taken', 'timestamp'
            ]
            
            # Only include columns that exist
            available_columns = [col for col in column_order if col in df.columns]
            df = df.reindex(columns=available_columns)
            
            df.to_csv(filename, index=False)
            print(f"💾 Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")

def main():
    """Main function to run the lead qualifier."""
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Lead Qualifier - AI Website Audit Tool')
    parser.add_argument('input_file', help='Input CSV file containing filtered restaurant leads')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--no-screenshots', action='store_true', help='Disable screenshot saving (screenshots saved by default)')
    
    args = parser.parse_args()
    
    # Handle screenshot saving logic (enabled by default, disabled with --no-screenshots)
    save_debug = not args.no_screenshots

    # Initialize qualifier
    try:
        qualifier = LeadQualifier(api_key=args.api_key)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    print("🔍 Lead Qualifier - AI Website Audit Tool")
    print("=" * 50)
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        return
    
    # Generate output filename by replacing "filtered" with "qualified"
    output_file = args.input_file
    if "_filtered" in output_file:
        output_file = output_file.replace("_filtered", "_qualified")
    else:
        # If "filtered" not found, add "_qualified" before the extension
        base_name, ext = os.path.splitext(output_file)
        output_file = f"{base_name}_qualified{ext}"
    
    print(f"📋 Input file: {args.input_file}")
    print(f"💾 Output file: {output_file}")
    
    # Load restaurants with websites
    restaurants = qualifier.load_restaurants_with_websites(args.input_file)
    
    if not restaurants:
        print("❌ No restaurants with websites found")
        return
    
    # Process restaurants
    try:
        results = asyncio.run(qualifier.process_restaurants(restaurants, output_file, save_debug))
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 WEBSITE AUDIT SUMMARY")
        print("=" * 50)
        
        modern_count = sum(1 for r in results if r['judgment'] == 'Modern')
        outdated_count = sum(1 for r in results if r['judgment'] == 'Outdated')
        unclear_count = sum(1 for r in results if r['judgment'] == 'Unclear')
        
        print(f"Modern websites: {modern_count}")
        print(f"Outdated websites: {outdated_count}")
        print(f"Unclear/Failed: {unclear_count}")
        print(f"Total processed: {len(results)}")
        
        if results:
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            print(f"Average confidence: {avg_confidence:.1f}%")
            
            # Show some examples of outdated websites (potential leads)
            outdated_sites = [r for r in results if r['judgment'] == 'Outdated']
            if outdated_sites:
                print(f"\n🎯 POTENTIAL LEADS (Outdated Websites):")
                for site in outdated_sites[:5]:  # Show top 5
                    print(f"   • {site['restaurant_name']} - {site['url']}")
                    print(f"     Confidence: {site['confidence']}% | {site['reason']}")
                
                if len(outdated_sites) > 5:
                    print(f"   ... and {len(outdated_sites) - 5} more potential leads")
        
        print(f"\n✅ Analysis complete! Results saved to: {output_file}")
        
        if save_debug:
            print(f"📸 Screenshots saved to: screenshots/ folder")
        
    except Exception as e:
        print(f"❌ Error running qualifier: {str(e)}")

if __name__ == "__main__":
    main() 