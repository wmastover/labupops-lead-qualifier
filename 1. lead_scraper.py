#!/usr/bin/env python3
"""
Google Places API Fetcher
Fetches places from Google Places API based on a town name and exports to CSV.
"""

import csv
import os
import sys
import argparse
from typing import List, Dict, Optional
import googlemaps
from datetime import datetime
import time

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class PlacesFetcher:
    def __init__(self, api_key: str):
        """Initialize the Places Fetcher with Google Maps API key."""
        self.gmaps = googlemaps.Client(key=api_key)
    
    def search_places(self, town_name: str, place_type: Optional[str] = None, 
                     radius: int = 2000) -> List[Dict]:
        """
        Search for places in a given town.
        
        Args:
            town_name: Name of the town to search in
            place_type: Type of place to search for (default: searches for restaurants and takeaways)
            radius: Search radius in meters (default: 2km)
        
        Returns:
            List of place dictionaries
        """
        try:
            # First, geocode the town to get coordinates
            geocode_result = self.gmaps.geocode(town_name)
            if not geocode_result:
                raise ValueError(f"Could not find location for town: {town_name}")
            
            location = geocode_result[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            print(f"Found coordinates for {town_name}: {lat}, {lng}")
            
            all_places = []
            
            # If no specific type provided, search for restaurants and takeaways
            if place_type is None:
                # Search for multiple food-related types
                food_types = ['restaurant', 'meal_takeaway',]
                for food_type in food_types:
                    print(f"Searching for {food_type}...")
                    places_result = self.gmaps.places_nearby(
                        location=(lat, lng),
                        radius=radius,
                        type=food_type
                    )
                    
                    places = places_result.get('results', [])
                    print(f"Found {len(places)} {food_type} places")
                    
                    # Get additional pages if available
                    while 'next_page_token' in places_result:
                        time.sleep(2)  # Required delay for next page token
                        places_result = self.gmaps.places_nearby(
                            page_token=places_result['next_page_token']
                        )
                        places.extend(places_result.get('results', []))
                    
                    all_places.extend(places)
                
                # Remove duplicates based on place_id
                unique_places = {}
                for place in all_places:
                    place_id = place.get('place_id')
                    if place_id and place_id not in unique_places:
                        unique_places[place_id] = place
                
                places = list(unique_places.values())
                print(f"Total unique food establishments found: {len(places)}")
                
            else:
                # Search for the specified type
                places_result = self.gmaps.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type
                )
                
                places = places_result.get('results', [])
                print(f"Found {len(places)} places")
                
                # Get additional pages if available
                while 'next_page_token' in places_result:
                    time.sleep(2)  # Required delay for next page token
                    places_result = self.gmaps.places_nearby(
                        page_token=places_result['next_page_token']
                    )
                    places.extend(places_result.get('results', []))
                    print(f"Total places found: {len(places)}")
            
            return places
            
        except Exception as e:
            print(f"Error searching for places: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get detailed information for a specific place."""
        try:
            details = self.gmaps.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'formatted_phone_number', 
                       'website', 'rating', 'user_ratings_total', 'business_status',
                       'opening_hours', 'price_level', 'type']
            )
            return details.get('result', {})
        except Exception as e:
            print(f"Error getting place details for {place_id}: {e}")
            return {}
    
    def export_to_csv(self, places: List[Dict], filename: str, 
                     include_details: bool = False):
        """
        Export places data to CSV file.
        
        Args:
            places: List of place dictionaries
            filename: Output CSV filename
            include_details: Whether to fetch detailed info for each place
        """
        if not places:
            print("No places to export")
            return
        
        # Define CSV headers
        headers = [
            'name', 'place_id', 'address', 'latitude', 'longitude',
            'rating', 'user_ratings_total', 'price_level', 'types',
            'business_status', 'phone_number', 'website', 'opening_hours'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for i, place in enumerate(places, 1):
                print(f"Processing place {i}/{len(places)}: {place.get('name', 'Unknown')}")
                
                # Basic information
                row = {
                    'name': place.get('name', ''),
                    'place_id': place.get('place_id', ''),
                    'address': place.get('vicinity', ''),
                    'latitude': place.get('geometry', {}).get('location', {}).get('lat', ''),
                    'longitude': place.get('geometry', {}).get('location', {}).get('lng', ''),
                    'rating': place.get('rating', ''),
                    'user_ratings_total': place.get('user_ratings_total', ''),
                    'price_level': place.get('price_level', ''),
                    'types': ', '.join(place.get('types', [])),
                    'business_status': place.get('business_status', ''),
                    'phone_number': place.get('formatted_phone_number', ''),
                    'website': place.get('website', ''),
                    'opening_hours': ''
                }
                
                # Always try to get phone and website if missing, or if details requested
                if place.get('place_id') and (include_details or not row['phone_number'] or not row['website']):
                    details = self.get_place_details(place['place_id'])
                    if details:
                        # Use better address if available
                        if details.get('formatted_address'):
                            row['address'] = details.get('formatted_address')
                        # Use phone from details if not already available
                        if details.get('formatted_phone_number') and not row['phone_number']:
                            row['phone_number'] = details.get('formatted_phone_number')
                        # Use website from details if not already available
                        if details.get('website') and not row['website']:
                            row['website'] = details.get('website')
                        # Only get opening hours if details requested
                        if include_details:
                            row['opening_hours'] = self._format_opening_hours(
                                details.get('opening_hours', {})
                            )
                        time.sleep(0.1)  # Small delay for details requests
                
                writer.writerow(row)
        
        print(f"Successfully exported {len(places)} places to {filename}")
    
    def _format_opening_hours(self, opening_hours: Dict) -> str:
        """Format opening hours for CSV output."""
        if not opening_hours or 'weekday_text' not in opening_hours:
            return ''
        return '; '.join(opening_hours['weekday_text'])


def main():
    parser = argparse.ArgumentParser(
        description='Fetch restaurants and takeaways from Google Places API and export to CSV'
    )
    parser.add_argument('town_name', help='Name of the town to search in')
    parser.add_argument('--api-key', help='Google Maps API key (or set GOOGLE_MAPS_API_KEY env var)')
    parser.add_argument('--output', '-o', default='places.csv', help='Output CSV filename')
    parser.add_argument('--type', help='Type of place to search for (default: restaurants and takeaways). Options: restaurant, meal_takeaway, food, etc.')
    parser.add_argument('--radius', type=int, default=2000, 
                       help='Search radius in meters (default: 2000 = 2km)')
    parser.add_argument('--details', action='store_true', 
                       help='Fetch detailed information for each place (slower)')
    
    args = parser.parse_args()
    
    # Get API key from multiple possible sources
    api_key = (args.api_key or 
               os.getenv('GOOGLE_MAPS_API_KEY') or 
               os.getenv('GOOGLE_API_KEY'))
    
    if not api_key:
        print("Error: Google Maps API key is required.")
        print("Either:")
        print("  - Pass --api-key argument")
        print("  - Set GOOGLE_MAPS_API_KEY environment variable")
        print("  - Set GOOGLE_API_KEY in .env file")
        print("Get your API key from: https://console.cloud.google.com/apis/credentials")
        sys.exit(1)
    
    # Create fetcher instance
    fetcher = PlacesFetcher(api_key)
    
    # Set up output directory and filename
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lead_lists_dir = os.path.join(script_dir, 'lead_lists')
    
    # Create lead_lists directory if it doesn't exist
    os.makedirs(lead_lists_dir, exist_ok=True)
    
    # Set filename based on town name if not specified
    if args.output == 'places.csv':
        clean_town_name = args.town_name.replace(" ", "_").replace(",", "").replace(".", "")
        args.output = os.path.join(lead_lists_dir, f'{clean_town_name}_restaurants.csv')
    
    print(f"Searching for food establishments in: {args.town_name}")
    if args.type:
        print(f"Place type: {args.type}")
    else:
        print("Place types: restaurants, takeaways, and food establishments")
    print(f"Search radius: {args.radius}m ({args.radius/1000}km)")
    print(f"Output file: {args.output}")
    print(f"Include details: {args.details}")
    print("-" * 50)
    
    # Search for places
    places = fetcher.search_places(
        town_name=args.town_name,
        place_type=args.type,
        radius=args.radius
    )
    
    if places:
        # Export to CSV
        fetcher.export_to_csv(places, args.output, include_details=args.details)
        print(f"\nSuccess! {len(places)} food establishments exported to {args.output}")
    else:
        print("No places found or error occurred.")
        sys.exit(1)


if __name__ == '__main__':
    main() 