from pydrive2.auth import GoogleAuth
import json

# Setup GoogleAuth
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # This will open a browser to log in

# Save credentials to JSON
creds = json.loads(gauth.credentials.to_json())

# Print as string for Streamlit secrets.toml
print("\n--- Paste the following in your .streamlit/secrets.toml ---\n")
print("[google]")
print(f'CREDENTIALS = """{json.dumps(gauth.client_config)}"""')
print(f'TOKEN = """{json.dumps(creds)}"""')
