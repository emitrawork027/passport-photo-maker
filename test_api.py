import requests

api_key = 'wur8bps17aG47SXUxygcPura'

# Test 1: Check API account status
print("Testing API key...")
response = requests.get(
    'https://api.remove.bg/v1.0/account',
    headers={'X-Api-Key': api_key}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Test 2: Try to remove background (if you have test.jpg)
if response.status_code == 200:
    print("\n\nAPI key is valid! Testing background removal...")
    try:
        with open('test.jpg', 'rb') as image_file:
            response2 = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': 'auto'},
                headers={'X-Api-Key': api_key}
            )
            print(f"Removal Status: {response2.status_code}")
            if response2.status_code == 200:
                print("SUCCESS! Background removal working!")
                with open('output.png', 'wb') as out:
                    out.write(response2.content)
                print("Saved as output.png")
            else:
                print(f"Error: {response2.text}")
    except FileNotFoundError:
        print("test.jpg not found. Create one to test removal.")
