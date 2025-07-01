from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()

# Force the OAuth flow to re-consent and request a refresh token
gauth.LoadClientConfigFile("credentials.json")
gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
gauth.settings['get_refresh_token'] = True
gauth.LocalWebserverAuth()

gauth.SaveCredentialsFile("token.json")
drive = GoogleDrive(gauth)
