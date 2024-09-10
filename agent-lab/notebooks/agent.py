import os
import requests
import base64
import sys
import json



def call_openai(request):
    ENDPOINT = "https://ai-swe-cent.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    
    # Configuration
    API_KEY = "0be7aa97e2c34dfca521aa591ad8d132"
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }
    # Payload for the request
    payload = {
        "messages": [
            {
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": "You are an agent that helps people order pizza. You are open from 7 AM to 11 PM"
                }
            ]
            },
            {
             "role": "user",
             "content" : request   
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
        }
   
    # Send request
    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")
    
    json_loads = json.loads(response.text)
    print(json_loads["choices"][0]["message"]["content"])

param = input("Enter your message:")
call_openai(param)







# exit

# Handle the response as needed (e.g., print or process)
