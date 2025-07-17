from database import get_user_api_keys

# Replace with your user_id (usually 1 for the first user)
user_id = 1

api_keys = get_user_api_keys(user_id)
if not api_keys:
    print("No API keys found for user_id:", user_id)
else:
    for key in api_keys:
        print(f"API Key: {key['api_key']}")
        print(f"Name: {key['name']}")
        print(f"Created: {key['created_at']}")
        print(f"Last used: {key['last_used']}")
        print("-" * 40)