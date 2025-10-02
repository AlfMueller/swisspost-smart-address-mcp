#!/usr/bin/env python3
"""
Test für n8n Webhook
"""

import requests
import json

def test_webhook():
    """Test n8n Webhook"""
    try:
        # Test data for webhook
        data = {
            "company": "Beispiel AG",
            "firstname": "Max",
            "lastname": "Mustermann",
            "street": "Musterstrasse 123",
            "city": "Musterstadt",
            "postcode": "8001"
        }
        
        print("Testing n8n Webhook...")
        print(f"URL: https://your-n8n-instance.com/webhook/swisspost-validate")
        print(f"Data: {json.dumps(data, indent=2)}")
        print("-" * 50)
        
        response = requests.post(
            "https://your-n8n-instance.com/webhook/swisspost-validate",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Webhook Success!")
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print("✅ Webhook Success (non-JSON response)!")
                print(f"Response Text: {response.text}")
        else:
            print(f"❌ Webhook Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook Test Error: {e}")

def test_webhook_with_different_address():
    """Test webhook with different address"""
    try:
        # Test with Bahnhofstrasse (known to work)
        data = {
            "company": "Test AG",
            "firstname": "Max",
            "lastname": "Mustermann",
            "street": "Bahnhofstrasse 1",
            "city": "Zürich",
            "postcode": "8001"
        }
        
        print("\n" + "=" * 50)
        print("Testing with Bahnhofstrasse (known working address)...")
        print(f"Data: {json.dumps(data, indent=2)}")
        print("-" * 50)
        
        response = requests.post(
            "https://your-n8n-instance.com/webhook/swisspost-validate",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Webhook Success!")
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print("✅ Webhook Success (non-JSON response)!")
                print(f"Response Text: {response.text}")
        else:
            print(f"❌ Webhook Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Webhook Test Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing n8n Webhook Integration...")
    print("=" * 60)
    
    test_webhook()
    test_webhook_with_different_address()
    
    print("\n" + "=" * 60)
    print("🏁 Webhook test completed!")
