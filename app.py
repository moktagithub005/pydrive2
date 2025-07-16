import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import os
import tempfile
from io import BytesIO

# MUST BE FIRST: Set page config
st.set_page_config(page_title="Apple Image Uploader", page_icon="🍎")

# Step 1: Load SERVICE_ACCOUNT from secrets
try:
    service_account_info = json.loads(st.secrets["google"]["SERVICE_ACCOUNT"])
except Exception as e:
    st.error(f"❌ Error loading service account from secrets: {e}")
    st.stop()

# Step 2: Save it to a temporary service_account.json file
try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(service_account_info, f)
        service_account_path = f.name
except Exception as e:
    st.error(f"❌ Error creating service account file: {e}")
    st.stop()

# Step 3: Create proper settings.yaml content for service account
settings_content = f"""
client_config_backend: service
client_config:
  client_id: {service_account_info.get('client_id', '')}
  client_secret: {service_account_info.get('client_secret', '')}

save_credentials: True
save_credentials_backend: file
save_credentials_file: credentials.json

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive.file
  - https://www.googleapis.com/auth/drive.install

service_config:
  client_service_email: {service_account_info.get('client_email', '')}
  client_user_email: {service_account_info.get('client_email', '')}
  client_pkcs12_file_path: {service_account_path}
  client_json_file_path: {service_account_path}
"""

# Write settings.yaml
try:
    with open("settings.yaml", "w") as f:
        f.write(settings_content)
except Exception as e:
    st.error(f"❌ Error creating settings.yaml: {e}")
    st.stop()

# Step 4: Authenticate with PyDrive2
try:
    gauth = GoogleAuth(settings_file="settings.yaml")
    gauth.ServiceAuth()  # Use ServiceAuth() instead of Authorize() for service accounts
    drive = GoogleDrive(gauth)
    st.success("✅ Authenticated with Google Drive successfully!")
except Exception as e:
    st.error(f"❌ Authentication failed: {e}")
    st.error("Please check your service account credentials in Streamlit secrets.")
    st.stop()

# Your Google Drive folder ID for 'apple_dataset'
FOLDER_ID = "1bHPAGisgocVuTXT6BLWycQFIncCA_x4W"  # Replace with your actual folder ID
st.title("🍎 Apple Image Uploader for AI Dataset (IARI Delhi सहयोग)")

st.markdown("""
📢 **Help us build India's largest AI-based Apple Variety Dataset!**

**भारत का सबसे बड़ा एआई आधारित सेब डेटासेट बनाने में हमारी मदद करें!**

🧠 This technology will help farmers assess **color, ripeness, and damage** of apples.

📞 संपर्क: 7876471141
📧 ईमेल: unisole.empower@gmail.com
""")

st.markdown("---")

with st.form("upload_form"):
    st.subheader("📷 Choose Image Source / छवि स्रोत चुनें")
    source = st.radio(
        "Select one / एक विकल्प चुनें:",
        ["📁 Upload from device / डिवाइस से अपलोड करें", "📸 Use camera / कैमरा से लें"]
    )

    if source == "📁 Upload from device / डिवाइस से अपलोड करें":
        uploaded_file = st.file_uploader("Upload apple image / सेब की तस्वीर अपलोड करें", type=["jpg", "jpeg", "png"])
    else:
        uploaded_file = st.camera_input("Take a picture / एक तस्वीर लें")

    st.markdown("---")
    st.subheader("🍏 Apple Metadata / सेब की जानकारी")

    col1, col2 = st.columns(2)
    with col1:
        quality = st.selectbox("Quality / गुणवत्ता", ["High / उच्च", "Medium / मध्यम", "Low / कम"])
        size = st.selectbox("Size / आकार", ["Small / छोटा", "Medium / मध्यम", "Large / बड़ा"])
    with col2:
        ripeness = st.selectbox("Ripeness / पकने की स्थिति", ["Unripe / कच्चा", "Semi-ripe / अधपका", "Ripe / पका हुआ"])

    submitted = st.form_submit_button("📤 Upload / अपलोड करें")

# Upload to Drive
if submitted and uploaded_file:
    try:
        st.image(uploaded_file, caption="📸 Preview / पूर्वावलोकन", use_column_width=True)

        # Compose filename from metadata
        file_name = f"{quality}_{size}_{ripeness}_{uploaded_file.name if hasattr(uploaded_file, 'name') else 'captured_image.jpg'}"

        # Create file in Drive
        file_drive = drive.CreateFile({
            'title': file_name,
            'parents': [{'id': FOLDER_ID}]
        })
        
        # Set content from uploaded file bytes
        file_drive.SetContentFile(BytesIO(uploaded_file.getvalue()))
        file_drive.Upload()

        st.success("✅ File uploaded successfully! / फ़ाइल सफलतापूर्वक अपलोड हो गई!")
        st.info("🎉 धन्यवाद! यह तस्वीर हमारे AI मॉडल के लिए संग्रहित कर ली गई है।\nThank you! Your image has been saved for our AI model.")
        
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        st.error("Please try again or contact support.")

# Cleanup temporary files
try:
    if os.path.exists(service_account_path):
        os.unlink(service_account_path)
    if os.path.exists("settings.yaml"):
        os.unlink("settings.yaml")
except:
    pass