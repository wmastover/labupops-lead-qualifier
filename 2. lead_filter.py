#!/usr/bin/env python3
"""
Lead List Filter using OpenAI
Filters restaurant lead lists to remove chain restaurants and keep only small local businesses.
"""

import csv
import os
import sys
import argparse
import json
from typing import List, Dict, Optional
import pandas as pd
from openai import OpenAI

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class LeadListFilter:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Lead List Filter with OpenAI API key."""
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.client = OpenAI(api_key=api_key)
    
    def create_filter_prompt(self, restaurants_data: List[Dict]) -> str:
        """
        Create a prompt for OpenAI to filter restaurants.
        
        Args:
            restaurants_data: List of restaurant dictionaries from CSV
        
        Returns:
            Formatted prompt string
        """
        # Convert restaurants to a more readable format for the AI
        restaurants_text = ""
        for i, restaurant in enumerate(restaurants_data, 1):
            restaurants_text += f"{i}. {restaurant.get('name', 'N/A')} - {restaurant.get('address', 'N/A')}\n"
        
        prompt = f"""
I have a list of restaurants and takeaways from a local area. I need to identify which ones are DEFINITELY large chains vs local independent businesses.

IMPORTANT: Only mark a business for removal if you are CERTAIN it's a major chain. When in doubt, keep it.

DEFINITELY REMOVE (only if you're 100% certain):
- Well-known fast food chains: McDonald's, KFC, Subway, Burger King, Domino's, Pizza Hut, Papa John's
- Major coffee chains: Starbucks, Costa Coffee, Caffè Nero
- Large restaurant chains: Pizza Express, Prezzo, Nando's, TGI Fridays, Harvester
- Pub chains: Wetherspoon, Greene King, Stonegate pubs
- Gas station food: Shell, BP, Tesco Express, Sainsbury's Local
- Major supermarket cafes/delis

ALWAYS KEEP (err on side of caution):
- Any name that could be local/independent
- Ethnic restaurants (even if chain-sounding names)
- Names you're not 100% sure about
- Local-sounding names
- Independent pubs, cafes, takeaways

Here is the list:

{restaurants_text}

Please respond with a JSON object containing two arrays:
{{
  "remove": [list of numbers for businesses you're CERTAIN are major chains],
  "keep": [list of numbers for businesses that should be kept - local/independent or uncertain]
}}

Be conservative - only put numbers in "remove" if you're absolutely certain it's a major chain.
"""
        return prompt
    
    def filter_restaurants_batch(self, restaurants_data: List[Dict], batch_size: int = 20) -> List[Dict]:
        """
        Filter restaurants using OpenAI in batches.
        
        Args:
            restaurants_data: List of restaurant dictionaries
            batch_size: Number of restaurants to process at once
        
        Returns:
            Filtered list of restaurants
        """
        filtered_restaurants = []
        
        # Process in batches to avoid token limits
        for i in range(0, len(restaurants_data), batch_size):
            batch = restaurants_data[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}: restaurants {i+1} to {min(i+batch_size, len(restaurants_data))}")
            
            try:
                prompt = self.create_filter_prompt(batch)
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # Using the cost-effective model
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying major chain restaurants vs local independent restaurants. You are conservative and only mark businesses for removal when you're absolutely certain they are major chains. You must respond with a valid JSON object only - do not use markdown formatting or code blocks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent results
                    max_tokens=800
                )
                
                # Parse the response
                response_text = response.choices[0].message.content.strip()
                print(f"AI Response: {response_text}")
                
                # Try to parse JSON response
                try:
                    # Handle markdown code blocks if present
                    json_text = response_text
                    if response_text.startswith('```json'):
                        # Extract JSON from markdown code block
                        lines = response_text.split('\n')
                        json_lines = []
                        in_json = False
                        for line in lines:
                            if line.strip() == '```json':
                                in_json = True
                                continue
                            elif line.strip() == '```' and in_json:
                                break
                            elif in_json:
                                json_lines.append(line)
                        json_text = '\n'.join(json_lines)
                    elif response_text.startswith('```'):
                        # Handle generic code blocks
                        json_text = response_text.strip('`').strip()
                    
                    result = json.loads(json_text)
                    if isinstance(result, dict) and 'remove' in result and 'keep' in result:
                        remove_indices = result.get('remove', [])
                        keep_indices = result.get('keep', [])
                        
                        print(f"  AI suggests removing: {len(remove_indices)} businesses")
                        print(f"  AI suggests keeping: {len(keep_indices)} businesses")
                        
                        # Show what's being removed for transparency
                        if remove_indices:
                            print("  Removing (chains):")
                            for idx in remove_indices:
                                if 1 <= idx <= len(batch):
                                    print(f"    - {batch[idx - 1].get('name', 'N/A')}")
                        
                        # Add kept restaurants to filtered list
                        for idx in keep_indices:
                            if 1 <= idx <= len(batch):
                                filtered_restaurants.append(batch[idx - 1])
                            else:
                                print(f"Warning: Invalid keep index {idx} for batch of size {len(batch)}")
                                
                        # If a restaurant wasn't mentioned in either list, keep it (be conservative)
                        all_mentioned = set(remove_indices + keep_indices)
                        for idx in range(1, len(batch) + 1):
                            if idx not in all_mentioned:
                                print(f"  Warning: Restaurant {idx} not categorized, keeping by default: {batch[idx - 1].get('name', 'N/A')}")
                                filtered_restaurants.append(batch[idx - 1])
                                
                    else:
                        print(f"Warning: Expected dict with 'remove' and 'keep' keys but got {type(result)}")
                        # If parsing fails, keep all restaurants (be conservative)
                        filtered_restaurants.extend(batch)
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse JSON response: {e}")
                    print(f"Raw response: {response_text}")
                    # If parsing fails, keep all restaurants (be conservative)
                    filtered_restaurants.extend(batch)
                    
            except Exception as e:
                print(f"Error processing batch: {e}")
                # In case of error, include all restaurants from this batch
                filtered_restaurants.extend(batch)
        
        return filtered_restaurants
    
    def filter_csv(self, input_file: str, output_file: str = None) -> str:
        """
        Filter a CSV file of restaurants.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
        
        Returns:
            Path to output file
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if output_file is None:
            # Generate output filename
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_filtered.csv"
        
        print(f"Reading restaurants from: {input_file}")
        
        # Read CSV file
        df = pd.read_csv(input_file)
        restaurants_data = df.to_dict('records')
        
        print(f"Found {len(restaurants_data)} restaurants to filter")
        
        # Filter restaurants using OpenAI
        filtered_restaurants = self.filter_restaurants_batch(restaurants_data)
        
        print(f"Filtered down to {len(filtered_restaurants)} local restaurants")
        
        # Save filtered results
        if filtered_restaurants:
            filtered_df = pd.DataFrame(filtered_restaurants)
            filtered_df.to_csv(output_file, index=False)
            print(f"Filtered results saved to: {output_file}")
        else:
            print("Warning: No restaurants passed the filter")
            # Create empty file
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                if restaurants_data:
                    writer.writerow(restaurants_data[0].keys())
        
        return output_file
    
    def show_filtered_summary(self, original_file: str, filtered_file: str):
        """Show a summary of what was filtered out."""
        original_df = pd.read_csv(original_file)
        filtered_df = pd.read_csv(filtered_file)
        
        print(f"\n=== FILTERING SUMMARY ===")
        print(f"Original restaurants: {len(original_df)}")
        print(f"Filtered restaurants: {len(filtered_df)}")
        print(f"Removed: {len(original_df) - len(filtered_df)}")
        print(f"Kept: {len(filtered_df)/len(original_df)*100:.1f}%")
        
        # Show some examples of what was removed
        filtered_names = set(filtered_df['name'].tolist())
        removed_names = [name for name in original_df['name'].tolist() if name not in filtered_names]
        
        if removed_names:
            print(f"\nExamples of restaurants removed:")
            for name in removed_names[:10]:  # Show first 10
                print(f"  - {name}")
            if len(removed_names) > 10:
                print(f"  ... and {len(removed_names) - 10} more")


def main():
    parser = argparse.ArgumentParser(description='Filter restaurant lead lists using OpenAI')
    parser.add_argument('input_file', help='Input CSV file containing restaurant leads')
    parser.add_argument('-o', '--output', help='Output CSV file (default: input_filtered.csv)')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--show-summary', action='store_true', help='Show filtering summary')
    
    args = parser.parse_args()
    
    try:
        # Initialize filter
        filter_tool = LeadListFilter(api_key=args.api_key)
        
        # Filter the CSV
        output_file = filter_tool.filter_csv(args.input_file, args.output)
        
        # Show summary if requested
        if args.show_summary:
            filter_tool.show_filtered_summary(args.input_file, output_file)
        
        print(f"\n✅ Filtering complete! Check {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 