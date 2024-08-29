import requests

# Define the URL for the login endpoint
url = 'http://127.0.0.1:5000/api/v1/login'

# Define the payload with username and password
payload = {
    'email': 'chris_moltesanti@gmail.com',
    'password': 'moltesanti123'
}

# Send a POST request to the login endpoint
response = requests.post(url, json=payload)

# Check the response status code
if response.status_code == 200:
    print("Login Successful")
    # Extract the access token from the response
    access_token = response.json().get('access_token')
    with open('token.txt', 'w') as f:
        f.write(access_token)
    print(f"Account:{payload['email']} \n Access Token: {access_token}")
else:
    print(f"Login Failed: {response.status_code}")
    print("Response Content:", response.text)  # Print raw response content
    try:
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        print("Response is not in JSON format")

