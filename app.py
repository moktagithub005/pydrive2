import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import os

# Load secrets from Streamlit secrets
creds = json.loads(st.secrets["google"]["CREDENTIALS"])
token = json.loads(st.secrets["google"]["TOKEN"])

# Save the secrets to files
with open("credentials.json", "w") as f:
    json.dump(creds, f)
with open("token.json", "w") as f:
    json.dump(token, f)

# Authenticate with PyDrive2
gauth = GoogleAuth()
gauth.LoadCredentialsFile("token.json")
if not gauth.credentials or gauth.credentials.invalid:
    gauth.LoadClientConfigFile("credentials.json")
    gauth.Authorize()
    gauth.SaveCredentialsFile("token.json")

drive = GoogleDrive(gauth)

# Streamlit UI
st.title("🍎 Apple Image Uploader to Google Drive")

uploaded_file = st.file_uploader("Upload an image of an apple", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Preview", use_column_width=True)
    file_drive = drive.CreateFile({'title': uploaded_file.name})
    file_drive.SetContentString(uploaded_file.getvalue().decode("ISO-8859-1"))
    file_drive.Upload()
    st.success("✅ File uploaded to Google Drive successfully!")
