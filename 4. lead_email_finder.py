#!/usr/bin/env python3
"""
Lead Contact Finder - Step 4
Uses browser-use to automatically find email contact information for restaurants with outdated websites.
Collects: emails and contact form links.
"""

import asyncio
import pandas as pd
import json
import argparse
import re
from datetime import datetime
from pathlib import Path
from browser_use import Agent, BrowserSession, BrowserProfile, Controller, ActionResult
from browser_use.llm import ChatOpenAI
from browser_use.browser.types import Page
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ContactInfo(BaseModel):
    """Structured model for restaurant contact information"""
    email: Optional[str] = Field(default=None, description="Primary contact email address")
    contact_form_url: Optional[str] = Field(default=None, description="URL to contact/get-in-touch form if available")
    additional_emails: list[str] = Field(default_factory=list, description="Any additional email addresses found")
    notes: Optional[str] = Field(default=None, description="Any additional notes about contact methods")

# Create controller and register custom action
controller = Controller()

@controller.action('Extract complete contact information from restaurant website', param_model=ContactInfo)
async def extract_contact_info(params: ContactInfo, page: Page) -> ActionResult:
    """
    Custom action for the agent to return structured contact information
    
    The agent should call this function to provide all found contact details
    in a structured format rather than free text.
    """
    # Convert the contact info to a structured result
    contact_data = {
        'email': params.email,
        'contact_form_url': params.contact_form_url,
        'additional_emails': params.additional_emails,
        'notes': params.notes,
        'page_url': page.url
    }
    
    # Create summary for the LLM
    summary_parts = []
    if params.email:
        summary_parts.append(f"Email: {params.email}")
    if params.contact_form_url:
        summary_parts.append(f"Contact form: {params.contact_form_url}")
    
    summary = "Contact information extracted: " + ", ".join(summary_parts) if summary_parts else "No contact information found"
    
    return ActionResult(
        extracted_content=summary,
        include_in_memory=True,
        additional_data=contact_data  # Store structured data
    )

class EmailFinderAgent:
    def __init__(self, csv_file_path: str, output_file_path: str = None):
        """
        Initialize the Email Finder Agent
        
        Args:
            csv_file_path: Path to the CSV file with restaurant data
            output_file_path: Path to save results (optional)
        """
        self.csv_file_path = csv_file_path
        
        # Generate output file name based on input CSV if not provided
        if output_file_path:
            self.output_file_path = output_file_path
        else:
            # Extract base name and create contact version
            csv_path = Path(csv_file_path)
            base_name = csv_path.stem.replace('_qualified', '').replace('_filtered', '')
            self.output_file_path = f"lead_lists/{base_name}_contacts.csv"
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(model="gpt-4o")
        
        # Configure browser for stability
        self.browser_profile = BrowserProfile(
            headless=True,  # Run headless to avoid conflicts
            viewport={"width": 1280, "height": 720},  # Stable viewport size
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        
        # Results storage
        self.results = []
        
    def load_outdated_restaurants(self):
        """Load restaurants with outdated websites from CSV"""
        try:
            df = pd.read_csv(self.csv_file_path)
            # Filter for outdated restaurants
            outdated_df = df[df['judgment'].str.lower() == 'outdated'].copy()
            print(f"Found {len(outdated_df)} restaurants with outdated websites")
            return outdated_df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return pd.DataFrame()
    
    async def find_contact_info_for_restaurant(self, restaurant_data):
        """
        Use browser agent to find complete contact information for a specific restaurant
        
        Args:
            restaurant_data: Series with restaurant information
            
        Returns:
            dict: Result with all contact information
        """
        restaurant_name = restaurant_data['restaurant_name']
        url = restaurant_data['url']
        
        print(f"\n🔍 Searching for contact info: {restaurant_name}")
        print(f"URL: {url}")
        
        # Create enhanced granular task for comprehensive contact info
        task = f"""
        Visit the website {url} for {restaurant_name} and systematically find ALL their contact information using this step-by-step approach:

        **STEP 1: Homepage Email Search**
        First, carefully examine the homepage for any email addresses:
        - Look in the header navigation
        - Check the footer section thoroughly
        - Look for any "Contact" or "Email" text
        - Check for any mailto: links
        - Look in the main content area
        - Check any contact sections or boxes
        
        **STEP 2: About Page Search (if exists)**
        If there's an "About", "About Us", or "Our Story" page:
        - Navigate to that page
        - Look for owner/manager email addresses
        - Check for team contact information
        - Look for business inquiry emails
        
        **STEP 3: Contact Page Search (if exists)**
        If there's a "Contact", "Contact Us", or "Get in Touch" page:
        - Navigate to that page
        - Look for all email addresses listed
        - Check for department-specific emails
        - Look for contact forms and note their URLs
        
        **STEP 4: Additional Contact Information**
        While on these pages, also collect:
        - Phone numbers (main, reservations, takeaway)
        - Physical addresses (complete street address)
        - Contact form URLs
        
        **STEP 5: Final Sweep**
        Do a final check of any other obvious pages like:
        - "Location" or "Find Us" pages
        - "Reservations" or "Bookings" pages
        - Any footer links you haven't checked
        
        **IMPORTANT INSTRUCTIONS:**
        - Be methodical - check each page section by section
        - Don't rush - emails are often hidden in footers or small text
        - Look for text like "Email us at:", "Contact:", "Write to us:"
        - Check both visible text and any links (mailto: links)
        - When you find contact information, immediately note it down
        
        **WHEN COMPLETE:** You MUST call the 'extract_contact_info' function with ALL the details you found:
        - email: The primary/best email address found
        - phone: The primary phone number
        - address: The complete physical address
        - contact_form_url: Full URL to any contact form
        - additional_emails: List of any other emails found
        - additional_phones: List of any other phone numbers found
        - notes: Which pages you found information on and any other relevant details
        
        Do not just describe what you found - you must call the extract_contact_info function with the structured data!
        """
        
        try:
            # Create browser session with configured profile
            browser_session = BrowserSession(
                browser_profile=self.browser_profile
            )
            
            # Create and run the agent with our custom controller
            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=browser_session,
                controller=controller,  # Use our custom controller
                use_vision=True,
            )
            
            # Run the agent and get history
            history = await agent.run()
            
            # Extract structured contact info from the custom action
            contact_info = self.extract_structured_contact_info(history)
            
            result_data = {
                'restaurant_name': restaurant_name,
                'url': url,
                'original_address': restaurant_data.get('address', ''),
                'original_phone': restaurant_data.get('phone_number', ''),
                'rating': restaurant_data.get('rating', ''),
                'judgment': restaurant_data.get('judgment', ''),
                'confidence': restaurant_data.get('confidence', ''),
                
                # Contact information found
                'email': contact_info.get('email'),
                'contact_form_url': contact_info.get('contact_form_url'),
                'additional_emails': '; '.join(contact_info.get('additional_emails', [])) if contact_info.get('additional_emails') else None,
                'contact_notes': contact_info.get('notes'),
                
                'search_timestamp': datetime.now().isoformat(),
                'search_status': 'success' if contact_info.get('email') or contact_info.get('contact_form_url') else 'no_contact_found',
                'agent_steps': len(history.model_actions()) if history else 0,
                'urls_visited': len(history.urls()) if history else 0,
            }
                
            return result_data
            
        except Exception as e:
            print(f"❌ Error processing {restaurant_name}: {e}")
            return {
                'restaurant_name': restaurant_name,
                'url': url,
                'original_address': restaurant_data.get('address', ''),
                'original_phone': restaurant_data.get('phone_number', ''),
                'rating': restaurant_data.get('rating', ''),
                'judgment': restaurant_data.get('judgment', ''),
                'confidence': restaurant_data.get('confidence', ''),
                'email': None,
                'contact_form_url': None,
                'additional_emails': None,
                'contact_notes': None,
                'search_timestamp': datetime.now().isoformat(),
                'search_status': 'error',
                'error_details': str(e),
            }
    
    def extract_structured_contact_info(self, history):
        """
        Extract structured contact information from agent history
        
        Args:
            history: Agent execution history
            
        Returns:
            dict: Structured contact information
        """
        contact_info = {}
        
        if not history:
            return contact_info
            
        # Look for our custom action results in the history
        for action in history.model_actions():
            if hasattr(action, 'result') and hasattr(action.result, 'additional_data'):
                additional_data = action.result.additional_data
                if isinstance(additional_data, dict) and 'email' in additional_data:
                    contact_info.update(additional_data)
                    break
        
        # Fallback: try to extract from final result text if custom action wasn't called
        if not contact_info:
            final_result = history.final_result() if history else ""
            contact_info = self.extract_contact_from_text(str(final_result))
        
        return contact_info
    
    def extract_contact_from_text(self, result_text):
        """
        Fallback method to extract contact info from free text
        
        Args:
            result_text: Text result from browser agent
            
        Returns:
            dict: Extracted contact information
        """
        contact_info = {}
        
        # Extract emails
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        emails = []
        for pattern in email_patterns:
            matches = re.findall(pattern, result_text)
            emails.extend(matches)
        
        if emails:
            # Filter out common non-contact emails
            excluded_patterns = ['noreply', 'no-reply', 'admin@', 'webmaster@']
            contact_emails = [email for email in emails if not any(excluded in email.lower() for excluded in excluded_patterns)]
            
            if contact_emails:
                contact_info['email'] = contact_emails[0]
                if len(contact_emails) > 1:
                    contact_info['additional_emails'] = contact_emails[1:]
            elif emails:
                contact_info['email'] = emails[0]
        
        return contact_info
    
    async def process_all_restaurants(self):
        """Process all outdated restaurants to find their contact information"""
        restaurants_df = self.load_outdated_restaurants()
        
        if restaurants_df.empty:
            print("No outdated restaurants found!")
            return
        
        print(f"🚀 Starting contact search for {len(restaurants_df)} restaurants")
        print(f"📄 Results will be saved to: {self.output_file_path}")
        
        # Process each restaurant
        for index, restaurant in restaurants_df.iterrows():
            try:
                result = await self.find_contact_info_for_restaurant(restaurant)
                self.results.append(result)
                
                # Save progress after each restaurant
                self.save_results()
                
                # Small delay to be respectful
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⚠️ Process interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                continue
        
        print(f"\n✅ Completed! Processed {len(self.results)} restaurants")
        print(f"📄 Results saved to: {self.output_file_path}")
    
    def save_results(self):
        """Save current results to CSV file"""
        if not self.results:
            return
            
        # Ensure the lead_lists directory exists
        Path(self.output_file_path).parent.mkdir(exist_ok=True)
        
        df = pd.DataFrame(self.results)
        df.to_csv(self.output_file_path, index=False)
        
        # Also save as JSON for backup
        json_file = self.output_file_path.replace('.csv', '_backup.json')
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def print_summary(self):
        """Print summary of results"""
        if not self.results:
            print("No results to summarize")
            return
        
        df = pd.DataFrame(self.results)
        
        print("\n📊 CONTACT SEARCH SUMMARY:")
        print(f"Total restaurants processed: {len(df)}")
        print(f"Emails found: {len(df[df['email'].notna()])}")
        print(f"Contact forms found: {len(df[df['contact_form_url'].notna()])}")
        print(f"No contact info found: {len(df[df['search_status'] == 'no_contact_found'])}")
        print(f"Errors: {len(df[df['search_status'] == 'error'])}")
        
        # Show successful finds
        successful = df[df['search_status'] == 'success']
        if not successful.empty:
            print("\n📧 CONTACT INFO FOUND:")
            for _, row in successful.iterrows():
                contact_parts = []
                if row['email']:
                    contact_parts.append(f"Email: {row['email']}")
                if row['contact_form_url']:
                    contact_parts.append(f"Form: {row['contact_form_url']}")
                
                print(f"  • {row['restaurant_name']}: {', '.join(contact_parts)}")


async def test_single_url():
    """Test the contact finder with a single URL"""
    print("🧪 Testing with Ruby's Indian Restaurant")
    
    # Create test data
    test_restaurant = {
        'restaurant_name': "Ruby's Indian Restaurant",
        'url': 'https://www.rubys.org.uk/',
        'address': '43-45 Hockerill Street, Bishop\'s Stortford',
        'phone_number': '01279 912 929',
        'rating': '4.5',
        'judgment': 'outdated',
        'confidence': 'high'
    }
    
    # Create a temporary agent (no CSV needed)
    contact_finder = EmailFinderAgent("dummy.csv", "test_contacts.csv")
    
    # Test the contact finding
    result = await contact_finder.find_contact_info_for_restaurant(pd.Series(test_restaurant))
    
    print("\n📊 TEST RESULT:")
    print(f"Restaurant: {result['restaurant_name']}")
    print(f"URL: {result['url']}")
    print(f"Email: {result['email']}")
    print(f"Contact Form: {result['contact_form_url']}")
    print(f"Status: {result['search_status']}")
    print(f"Agent steps: {result['agent_steps']}")
    
    return result

async def main():
    """Main function to run the contact finder"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Find contact information for restaurants with outdated websites')
    parser.add_argument('--test', action='store_true',
                       help='Test with Ruby\'s restaurant only')
    parser.add_argument('csv_file', nargs='?', 
                       default='lead_lists/Bishops_Stortford_restaurants_qualified.csv',
                       help='Path to the CSV file with restaurant data')
    parser.add_argument('--output', '-o', 
                       help='Output CSV file path (auto-generated if not specified)')
    
    args = parser.parse_args()
    
    # Check if we're running a test
    if args.test:
        await test_single_url()
        return
    
    csv_file = args.csv_file
    
    # Check if CSV file exists
    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        print("Please make sure the file exists or run the previous steps first:")
        print("1. 1. lead_scraper.py")
        print("2. 2. lead_filter.py") 
        print("3. 3. lead_qualifier.py")
        print(f"\nUsage: python3.11 '4. lead_email_finder.py' [csv_file] [--test]")
        return
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("❌ OpenAI API key not set!")
        print("Please set your OPENAI_API_KEY in the .env file")
        print("Get your API key from: https://platform.openai.com/api-keys")
        return
    
    # Create and run contact finder
    print("🤖 Lead Contact Finder - Step 4")
    print("=" * 50)
    print(f"📄 Input CSV: {csv_file}")
    
    contact_finder = EmailFinderAgent(
        csv_file, 
        output_file_path=args.output
    )
    
    try:
        await contact_finder.process_all_restaurants()
        contact_finder.print_summary()
        
        print(f"\n🎉 Contact search complete!")
        print(f"📄 Output file: {contact_finder.output_file_path}")
        print(f"📄 Backup file: {contact_finder.output_file_path.replace('.csv', '_backup.json')}")
        
    except Exception as e:
        print(f"❌ Error running contact finder: {e}")
        print("Make sure you have installed all dependencies with Python 3.11:")
        print("python3.11 -m pip install browser-use pandas python-dotenv openai")
        print("python3.11 -m playwright install")


if __name__ == "__main__":
    asyncio.run(main())
