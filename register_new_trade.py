import requests

with open('token.txt', 'r') as f:
    access_token = f.read().strip()

# Define the URL for the register_new_trade endpoint
register_url = 'http://127.0.0.1:5000/api/v1/register-trade-config'

register_data = {
    "email": "chris_moltesanti@gmail.com",
    "asset": "BTC",
    "starting_budget": 1000,
    "vendor_commission": 0.001,
    "min_transaction": 10
}

# Assuming you have obtained the access token from the login response
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.post(register_url, json=register_data, headers=headers)

if response.status_code in [200, 201]:
    print("Trade Registered Successfully")
else:
    #print(f"Registration Failed: {response.status_code} - {response.json().get('description')}")
    try:
        print("Error details:", response.json())
    except Exception as e:
        print("The following error occurred: \\n",e)
        print("Response Content:", response.text)