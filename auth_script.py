from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()

# Tell PyDrive2 where to find your client_secrets.json
gauth.LoadClientConfigFile("credentials.json")

# Start local server to authenticate
gauth.LocalWebserverAuth()

# Save credentials to avoid logging in next time
gauth.SaveCredentialsFile("token.json")

print("✅ Authentication successful. token.json saved.")
