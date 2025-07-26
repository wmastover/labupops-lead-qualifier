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
        
    async def take_screenshot(self, url: str, browser: Browser) -> Optional[bytes]:
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
            
            await page.close()
            return screenshot
            
        except Exception as e:
            print(f"❌ Error taking screenshot of {url}: {str(e)}")
            return None
    
    def encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def analyze_website_design(self, screenshot_bytes: bytes) -> Dict[str, any]:
        """Send screenshot to GPT-4o Vision for analysis."""
        try:
            # Encode image
            base64_image = self.encode_image(screenshot_bytes)
            
            print("🧠 Analyzing website design with GPT-4o...")
            
            # Prepare the prompt
            system_prompt = """You are an expert web designer and developer with extensive experience in modern web design trends and UX principles."""
            
            user_prompt = """
            Here's a screenshot of a website. Based on its visual design, layout, typography, color scheme, and overall aesthetic, determine if it looks outdated or modern.

            Consider these factors:
            - Layout design (responsive vs fixed-width, grid systems)
            - Typography (modern fonts vs default system fonts)
            - Color schemes and visual hierarchy
            - Navigation patterns and UI elements
            - Overall visual sophistication and current design trends
            - Mobile-first design principles
            - White space usage and content density

            Respond ONLY in valid JSON format with exactly these fields:
            {
                "judgment": "Modern" or "Outdated" or "Unclear",
                "reason": "1-2 sentence explanation of your assessment",
                "confidence": <integer from 0 to 100>
            }
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
                max_tokens=300,
                temperature=0.1
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract information manually
                print(f"⚠️ Failed to parse JSON response: {response_text}")
                return {
                    "judgment": "Unclear",
                    "reason": "Failed to parse AI response",
                    "confidence": 0
                }
                
        except Exception as e:
            print(f"❌ Error analyzing website: {str(e)}")
            return {
                "judgment": "Unclear",
                "reason": f"Analysis error: {str(e)}",
                "confidence": 0
            }
    
    async def process_url(self, url: str, browser: Browser) -> Dict[str, any]:
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
            screenshot = await self.take_screenshot(url, browser)
            
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
    
    def load_urls_from_csv(self, filename: str, url_column: str = 'url') -> List[str]:
        """Load URLs from a CSV file."""
        try:
            df = pd.read_csv(filename)
            if url_column not in df.columns:
                raise ValueError(f"Column '{url_column}' not found in CSV file")
            
            urls = df[url_column].dropna().tolist()
            print(f"📋 Loaded {len(urls)} URLs from {filename}")
            return urls
            
        except Exception as e:
            print(f"❌ Error loading URLs from CSV: {str(e)}")
            return []

def main():
    """Main function to run the lead qualifier."""
    
    # Example usage
    qualifier = LeadQualifier()
    
    # Sample URLs for testing
    sample_urls = [
        "example.com",
        "old-site.com",
        "modern-startup.com"
    ]
    
    print("🔍 Lead Qualifier - AI Website Audit Tool")
    print("=" * 50)
    
    # Check if there's a URLs file to process
    urls_file = "2. Lead qualifier/sample_urls.csv"
    if os.path.exists(urls_file):
        print(f"📋 Found URLs file: {urls_file}")
        urls = qualifier.load_urls_from_csv(urls_file)
    else:
        print("📋 Using sample URLs for demonstration")
        urls = sample_urls
    
    if not urls:
        print("❌ No URLs to process")
        return
    
    # Process URLs
    try:
        results = asyncio.run(qualifier.process_urls(urls, "2. Lead qualifier/audit_results.csv"))
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 AUDIT SUMMARY")
        print("=" * 50)
        
        modern_count = sum(1 for r in results if r['judgment'] == 'Modern')
        outdated_count = sum(1 for r in results if r['judgment'] == 'Outdated')
        unclear_count = sum(1 for r in results if r['judgment'] == 'Unclear')
        
        print(f"Modern websites: {modern_count}")
        print(f"Outdated websites: {outdated_count}")
        print(f"Unclear/Failed: {unclear_count}")
        print(f"Total processed: {len(results)}")
        
        avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
        print(f"Average confidence: {avg_confidence:.1f}%")
        
    except Exception as e:
        print(f"❌ Error running qualifier: {str(e)}")

if __name__ == "__main__":
    main() 