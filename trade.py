import requests
import datetime


# Define the URL for the trade_action endpoint
trade_url = 'http://127.0.0.1:5000/api/v1/trade'

start_time = datetime.datetime.now()

# Your existing code here


# Define the query parameters
params = {
    "asset": "BTC",
    "email": "chris_moltesanti@gmail.com"
}

# Assuming you have obtained the access token from login response
with open('token.txt', 'r') as f:
    access_token = f.read().strip()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json" 
}

# Send the GET request to the trade_action endpoint

response = requests.get(trade_url, params=params, headers=headers)

# Check the response status code
if response.status_code == 200:
    # Parse the JSON response
    trade_data = response.json()
    print("Trade Action Successful")
    print("Asset:", trade_data["asset"])
    print("Price:", trade_data["price"])
    print("Action:", trade_data["action"])
    print("Volume:", trade_data["volume"])
    print("key:", trade_data["key"])
else:
    print(f"Trade Action Failed: {response.status_code}")
    try:
        error_details = response.json()
        print("Error details:", error_details)
    except ValueError:
        print("Response is not in JSON format")
        print("Raw response text:", response.text)
    
end_time = datetime.datetime.now()
execution_time = end_time - start_time
print("Execution Time:", execution_time)