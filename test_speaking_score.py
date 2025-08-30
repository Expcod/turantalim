#!/usr/bin/env python3
"""
Test script to verify speaking test score calculation and API response.
"""

import requests
import json

# Test the API endpoint
def test_speaking_score():
    # Test the specific test result ID mentioned in the user's request
    test_result_id = 195
    url = f"https://api.turantalim.uz/multilevel/test-result/{test_result_id}/"
    
    print(f"Testing API endpoint: {url}")
    
    try:
        # Note: This would require authentication in a real scenario
        # For now, we'll just test the endpoint structure
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("API Response:")
            print(json.dumps(data, indent=2))
            
            # Check if percentage field contains the correct score
            percentage = data.get('percentage', 0)
            print(f"\nPercentage field value: {percentage}")
            
            if percentage > 0:
                print("✅ SUCCESS: Percentage field contains a non-zero score")
            else:
                print("❌ ISSUE: Percentage field is still 0")
                
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

if __name__ == "__main__":
    test_speaking_score()
