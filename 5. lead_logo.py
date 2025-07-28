
#!/usr/bin/env python3
"""
Logo Finder - AI-powered Logo Detection and Validation Tool
Uses web scraping to find potential logo images and GPT-4o Vision to validate them.
"""

import os
import asyncio
import json
import csv
import base64
import argparse
import re
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from urllib.parse import urljoin, urlparse
import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page
import openai
from PIL import Image
import io

# Load environment variables
load_dotenv()

class LogoFinder:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Logo Finder with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Screenshot and image settings
        self.screenshot_width = 1920
        self.screenshot_height = 1080
        self.timeout = 30000  # 30 seconds
        self.max_image_size = 20 * 1024 * 1024  # 20MB limit for OpenAI API
        
        # Logo detection selectors and patterns
        self.logo_selectors = [
            'img[alt*="logo" i]',
            'img[src*="logo" i]',
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            '.logo img',
            '#logo img',
            'header img',
            '.header img',
            '.navbar img',
            '.nav img',
            '.brand img',
            '.brand-logo img',
            '.site-logo img',
            '.company-logo img',
            '[class*="brand"] img',
            '[class*="logo"] img',
            'img[alt*="brand" i]',
            'img[src*="brand" i]'
        ]
        
        # Common logo file patterns
        self.logo_patterns = [
            r'logo',
            r'brand',
            r'header',
            r'nav',
            r'company',
            r'site'
        ]
    
    async def find_logo_candidates(self, url: str, browser: Browser) -> List[Dict[str, str]]:
        """Find potential logo images on a webpage."""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            page = await browser.new_page()
            await page.set_viewport_size({"width": self.screenshot_width, "height": self.screenshot_height})
            
            print(f"🔍 Searching for logos on {url}")
            
            # Navigate to the page
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            logo_candidates = []
            
            # Try each selector to find potential logos
            for selector in self.logo_selectors:
                try:
                    images = await page.query_selector_all(selector)
                    for img in images:
                        try:
                            # Get image attributes
                            src = await img.get_attribute('src')
                            alt = await img.get_attribute('alt') or ''
                            class_name = await img.get_attribute('class') or ''
                            img_id = await img.get_attribute('id') or ''
                            
                            if src:
                                # Convert relative URLs to absolute
                                absolute_src = urljoin(url, src)
                                
                                # Get image dimensions to filter out very small images
                                bounding_box = await img.bounding_box()
                                width = bounding_box['width'] if bounding_box else 0
                                height = bounding_box['height'] if bounding_box else 0
                                
                                # Filter out very small images (likely not logos)
                                if width >= 50 and height >= 20:
                                    logo_candidates.append({
                                        'src': absolute_src,
                                        'alt': alt,
                                        'class': class_name,
                                        'id': img_id,
                                        'width': width,
                                        'height': height,
                                        'selector': selector,
                                        'position': await self._get_image_position(img)
                                    })
                        except Exception as e:
                            continue  # Skip this image if there's an error
                            
                except Exception as e:
                    continue  # Skip this selector if there's an error
            
            # Remove duplicates based on src URL
            seen_urls = set()
            unique_candidates = []
            for candidate in logo_candidates:
                if candidate['src'] not in seen_urls:
                    seen_urls.add(candidate['src'])
                    unique_candidates.append(candidate)
            
            # Sort by likelihood (header position, size, logo-related keywords)
            unique_candidates.sort(key=self._score_logo_candidate, reverse=True)
            
            await page.close()
            
            print(f"📋 Found {len(unique_candidates)} logo candidates")
            return unique_candidates[:10]  # Return top 10 candidates
            
        except Exception as e:
            print(f"❌ Error finding logos on {url}: {str(e)}")
            return []
    
    async def _get_image_position(self, img_element) -> Dict[str, float]:
        """Get the position of an image element on the page."""
        try:
            bounding_box = await img_element.bounding_box()
            if bounding_box:
                return {
                    'x': bounding_box['x'],
                    'y': bounding_box['y'],
                    'width': bounding_box['width'],
                    'height': bounding_box['height']
                }
        except:
            pass
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    
    def _score_logo_candidate(self, candidate: Dict[str, str]) -> float:
        """Score a logo candidate based on various factors."""
        score = 0.0
        
        # Position scoring (higher scores for top of page)
        y_position = candidate['position']['y']
        if y_position < 150:  # Very top of page
            score += 3.0
        elif y_position < 300:  # Still in header area
            score += 2.0
        elif y_position < 600:  # Upper portion
            score += 1.0
        
        # Size scoring (reasonable logo sizes)
        width = candidate['width']
        height = candidate['height']
        
        # Prefer moderate sizes (not too small, not too large)
        if 100 <= width <= 400 and 50 <= height <= 200:
            score += 2.0
        elif 50 <= width <= 600 and 20 <= height <= 300:
            score += 1.0
        
        # Keyword scoring
        text_to_check = f"{candidate['alt']} {candidate['class']} {candidate['id']} {candidate['src']}".lower()
        
        for pattern in self.logo_patterns:
            if pattern in text_to_check:
                score += 1.5
        
        # Bonus for specific logo-related terms
        if 'logo' in text_to_check:
            score += 2.0
        if 'brand' in text_to_check:
            score += 1.5
        if any(term in text_to_check for term in ['header', 'nav', 'brand']):
            score += 1.0
        
        return score
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """Download an image from a URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check file size
            if len(response.content) > self.max_image_size:
                print(f"⚠️ Image too large: {len(response.content)} bytes")
                return None
                
            return response.content
            
        except Exception as e:
            print(f"❌ Error downloading image {image_url}: {str(e)}")
            return None
    
    def encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def validate_logo_with_ai(self, image_bytes: bytes, website_url: str, website_name: str = "") -> Dict[str, any]:
        """Use OpenAI Vision API to validate if an image is a website logo."""
        try:
            base64_image = self.encode_image(image_bytes)
            
            # Create the prompt
            prompt = f"""
            Please analyze this image and determine if it is the logo for the website: {website_url}
            
            Website/Business name hint: {website_name}
            
            Consider the following criteria:
            1. Does this appear to be a logo or brand mark?
            2. Does it contain text, symbols, or graphics that would identify a business?
            3. Is it professionally designed and suitable as a brand identifier?
            4. Does it appear to be the main logo (not a social media icon, advertisement, or decoration)?
            5. Is the image quality and resolution appropriate for a logo?
            
            Respond with a JSON object containing:
            - "is_logo": boolean (true if this is likely the website's logo)
            - "confidence": integer from 0-100 (how confident you are)
            - "reasoning": string (1-2 sentences explaining your decision)
            - "logo_type": string ("text", "symbol", "combination", "wordmark", or "other")
            - "has_business_name": boolean (does the logo contain readable business name)
            - "quality": string ("high", "medium", "low") based on image quality and professionalism
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
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
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: create a basic response if JSON parsing fails
                result = {
                    "is_logo": False,
                    "confidence": 0,
                    "reasoning": "Could not parse AI response",
                    "logo_type": "other",
                    "has_business_name": False,
                    "quality": "unknown"
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Error validating logo with AI: {str(e)}")
            return {
                "is_logo": False,
                "confidence": 0,
                "reasoning": f"API error: {str(e)}",
                "logo_type": "other",
                "has_business_name": False,
                "quality": "unknown"
            }
    
    async def process_website(self, url: str, website_name: str, browser: Browser) -> Dict[str, any]:
        """Process a website to find and validate its logo."""
        print(f"\n🏢 Processing website: {url}")
        
        result = {
            "url": url,
            "website_name": website_name,
            "logo_found": False,
            "logo_url": "",
            "logo_confidence": 0,
            "logo_reasoning": "",
            "logo_type": "",
            "has_business_name": False,
            "logo_quality": "",
            "candidates_found": 0,
            "error": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Find logo candidates
            candidates = await self.find_logo_candidates(url, browser)
            result["candidates_found"] = len(candidates)
            
            if not candidates:
                result["error"] = "No logo candidates found"
                return result
            
            # Test each candidate until we find a valid logo
            for i, candidate in enumerate(candidates):
                print(f"📸 Testing candidate {i+1}/{len(candidates)}: {candidate['src']}")
                
                # Download the image
                image_bytes = self.download_image(candidate['src'])
                if not image_bytes:
                    continue
                
                # Validate with AI
                validation = self.validate_logo_with_ai(image_bytes, url, website_name)
                
                if validation.get("is_logo", False) and validation.get("confidence", 0) >= 70:
                    result.update({
                        "logo_found": True,
                        "logo_url": candidate['src'],
                        "logo_confidence": validation.get("confidence", 0),
                        "logo_reasoning": validation.get("reasoning", ""),
                        "logo_type": validation.get("logo_type", ""),
                        "has_business_name": validation.get("has_business_name", False),
                        "logo_quality": validation.get("quality", ""),
                    })
                    
                    print(f"✅ Logo found! Confidence: {validation.get('confidence', 0)}%")
                    break
                else:
                    print(f"❌ Not a logo (confidence: {validation.get('confidence', 0)}%)")
                
                # Add delay between API calls
                await asyncio.sleep(1)
            
            if not result["logo_found"]:
                result["error"] = "No valid logos found among candidates"
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error processing {url}: {str(e)}")
        
        return result
    
    async def process_csv_file(self, csv_file: str, output_file: str = None) -> List[Dict[str, any]]:
        """Process websites from a CSV file and find their logos."""
        if not output_file:
            output_file = csv_file.replace('.csv', '_logos.csv')
        
        print(f"📂 Reading websites from {csv_file}")
        
        # Read the CSV file
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
            return []
        
        # Determine which columns contain URL and name
        url_column = None
        name_column = None
        
        for col in df.columns:
            if col.lower() in ['url', 'website', 'website_url', 'site']:
                url_column = col
            elif col.lower() in ['name', 'restaurant_name', 'business_name', 'company_name', 'title']:
                name_column = col
        
        if not url_column:
            print("❌ No URL column found in CSV file")
            return []
        
        urls = df[url_column].dropna().tolist()
        names = df[name_column].tolist() if name_column else [''] * len(urls)
        
        print(f"📊 Found {len(urls)} websites to process")
        
        results = []
        
        # Process websites with browser automation
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                for i, (url, name) in enumerate(zip(urls, names)):
                    print(f"\n📍 Processing {i+1}/{len(urls)}")
                    
                    result = await self.process_website(url, name, browser)
                    results.append(result)
                    
                    # Save intermediate results every 10 websites
                    if (i + 1) % 10 == 0:
                        self.save_results_to_csv(results, output_file)
                        print(f"💾 Intermediate save: {i+1} websites processed")
                    
                    # Add delay between websites
                    await asyncio.sleep(2)
                    
            finally:
                await browser.close()
        
        # Save final results
        self.save_results_to_csv(results, output_file)
        print(f"✅ Logo finding complete! Results saved to {output_file}")
        
        return results
    
    def save_results_to_csv(self, results: List[Dict[str, any]], output_file: str):
        """Save results to CSV file."""
        try:
            # Define column order
            columns = [
                "url", "website_name", "logo_found", "logo_url", "logo_confidence",
                "logo_reasoning", "logo_type", "has_business_name", "logo_quality",
                "candidates_found", "error", "timestamp"
            ]
            
            # Create DataFrame
            df = pd.DataFrame(results, columns=columns)
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def print_summary(self, results: List[Dict[str, any]]):
        """Print a summary of the logo finding results."""
        total = len(results)
        found = sum(1 for r in results if r.get("logo_found", False))
        high_confidence = sum(1 for r in results if r.get("logo_confidence", 0) >= 90)
        has_business_name = sum(1 for r in results if r.get("has_business_name", False))
        
        print(f"\n📊 LOGO FINDING SUMMARY")
        print(f"{'='*50}")
        print(f"Total websites processed: {total}")
        print(f"Logos found: {found} ({found/total*100:.1f}%)" if total > 0 else "Logos found: 0")
        print(f"High confidence logos (90%+): {high_confidence}")
        print(f"Logos with business name: {has_business_name}")
        
        # Quality breakdown
        quality_counts = {}
        for result in results:
            if result.get("logo_found", False):
                quality = result.get("logo_quality", "unknown")
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        if quality_counts:
            print(f"\nLogo quality breakdown:")
            for quality, count in sorted(quality_counts.items()):
                print(f"  {quality.title()}: {count}")

async def main():
    """Main function to run the logo finder."""
    parser = argparse.ArgumentParser(description="Find and validate website logos using AI")
    parser.add_argument("--csv", "-c", help="CSV file containing websites to process")
    parser.add_argument("--url", "-u", help="Single URL to process")
    parser.add_argument("--name", "-n", help="Website/business name (when using --url)")
    parser.add_argument("--output", "-o", help="Output CSV file path")
    
    args = parser.parse_args()
    
    # Initialize logo finder
    try:
        logo_finder = LogoFinder()
    except ValueError as e:
        print(f"❌ {str(e)}")
        return
    
    if args.csv:
        # Process CSV file
        results = await logo_finder.process_csv_file(args.csv, args.output)
        logo_finder.print_summary(results)
        
    elif args.url:
        # Process single URL
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                result = await logo_finder.process_website(args.url, args.name or "", browser)
                print(f"\n📊 Results:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            finally:
                await browser.close()
    else:
        # Process default file if it exists
        default_files = [
            "lead_lists/Bishops_Stortford_restaurants_qualified.csv",
            "lead_lists/Bishops_Stortford_restaurants_filtered.csv",
            "lead_lists/Bishops_Stortford_restaurants.csv"
        ]
        
        csv_file = None
        for file_path in default_files:
            if os.path.exists(file_path):
                csv_file = file_path
                break
        
        if csv_file:
            print(f"📂 Using default file: {csv_file}")
            results = await logo_finder.process_csv_file(csv_file)
            logo_finder.print_summary(results)
        else:
            print("❌ No CSV file specified and no default files found.")
            print("Use --csv to specify a file or --url for a single website.")
            print("Example: python 5. lead_logo.py --csv lead_lists/restaurants.csv")

if __name__ == "__main__":
    asyncio.run(main())

