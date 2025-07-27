
import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import tempfile
import os
import json

# Set page title and icon
st.set_page_config(page_title="Apple Image Uploader", page_icon="🍎")

# Session state setup
if 'drive' not in st.session_state:
    st.session_state.drive = None
    st.session_state.auth_success = False

def authenticate_google_drive():
    """Authenticate using Service Account (works for all users)"""
    try:
        # Parse service account JSON from secrets
        service_account_info = json.loads(st.secrets["google"]["SERVICE_ACCOUNT"])
        
        # Create a temporary file with service account credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(service_account_info, tmp_file)
            service_account_file = tmp_file.name

        # Setup GoogleAuth with service account
        gauth = GoogleAuth()
        gauth.settings = {
            'client_config_backend': 'service',
            'service_config': {
                'client_json_file_path': service_account_file,
                'client_user_email': service_account_info['client_email']
            },
            'oauth_scope': ['https://www.googleapis.com/auth/drive']
        }
        gauth.ServiceAuth()
        
        # Clean up temporary file
        if os.path.exists(service_account_file):
            os.unlink(service_account_file)
            
        drive = GoogleDrive(gauth)
        return drive, True, "✅ Google Drive authenticated with Service Account!"

    except Exception as e:
        return None, False, f"❌ Service Account Authentication Failed: {str(e)}"

# Run auth
if not st.session_state.auth_success:
    with st.spinner("🔐 Authenticating with Google Drive..."):
        drive, success, message = authenticate_google_drive()

        if success:
            st.session_state.drive = drive
            st.session_state.auth_success = True
            st.success(message)
        else:
            st.error(message)
            st.stop()

# Your Google Drive folder ID (replace this with your own folder inside Drive)
FOLDER_ID = "1bHPAGisgocVuTXT6BLWycQFIncCA_x4W"  # 'apple_dataset'

# App Header
st.title("🍎 Apple Image Uploader for AI Dataset (IARI Delhi सहयोग)")

st.markdown("""
📢 **Help us build India's largest AI-based Apple Variety Dataset!**  
**भारत का सबसे बड़ा एआई आधारित सेब डेटासेट बनाने में हमारी मदद करें!**

🧠 This technology will help farmers assess **color, ripeness, and damage** of apples.

📞 संपर्क: 7876471141  
📧 ईमेल: unisole.empower@gmail.com
""")
st.markdown("---")

# Upload form
if st.session_state.auth_success:
    with st.form("upload_form"):
        st.subheader("📷 Choose Image Source / छवि स्रोत चुनें")
        source = st.radio(
            "Select one / एक विकल्प चुनें:",
            ["📁 Upload from device / डिवाइस से अपलोड करें", "📸 Use camera / कैमरा से लें"]
        )

        if source == "📁 Upload from device / डिवाइस से अपलोड करें":
            uploaded_files = st.file_uploader("Upload apple images / सेब की तस्वीरें अपलोड करें", 
                                             type=["jpg", "jpeg", "png"], 
                                             accept_multiple_files=True)
        else:
            uploaded_file = st.camera_input("Take a picture / एक तस्वीर लें")
            uploaded_files = [uploaded_file] if uploaded_file else []

        st.markdown("---")
        st.subheader("🍏 Apple Metadata / सेब की जानकारी")

        col1, col2 = st.columns(2)
        with col1:
            quality = st.selectbox("Quality / गुणवत्ता", ["High / उच्च", "Medium / मध्यम", "Low / कम"])
            size = st.selectbox("Size / आकार", ["Small / छोटा", "Medium / मध्यम", "Large / बड़ा"])
        with col2:
            ripeness = st.selectbox("Ripeness / पकने की स्थिति", ["Unripe / कच्चा", "Semi-ripe / अधपका", "Ripe / पका हुआ"])

        submitted = st.form_submit_button("📤 Upload / अपलोड करें")

    if submitted and uploaded_files:
        try:
            # Show preview of all images
            if len(uploaded_files) > 1:
                st.subheader(f"📸 Preview ({len(uploaded_files)} images) / पूर्वावलोकन")
                cols = st.columns(min(3, len(uploaded_files)))  # Max 3 columns
                for idx, file in enumerate(uploaded_files[:6]):  # Show max 6 previews
                    with cols[idx % 3]:
                        st.image(file, caption=f"Image {idx+1}", use_container_width=True)
                if len(uploaded_files) > 6:
                    st.info(f"... and {len(uploaded_files) - 6} more images")
            else:
                st.image(uploaded_files[0], caption="📸 Preview / पूर्वावलोकन", use_container_width=True)

            # Upload progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            total_files = len(uploaded_files)
            
            for idx, file in enumerate(uploaded_files):
                # Update progress
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)
                status_text.text(f"⬆️ Uploading {idx + 1}/{total_files}: {file.name if hasattr(file, 'name') else f'captured_image_{idx+1}.jpg'}")

                try:
                    file_name = f"{quality}_{size}_{ripeness}_{file.name if hasattr(file, 'name') else f'captured_image_{idx+1}.jpg'}"

                    file_drive = st.session_state.drive.CreateFile({
                        'title': file_name,
                        'parents': [{'id': FOLDER_ID}]
                    })

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(file.getvalue())
                        tmp_file_path = tmp_file.name

                    file_drive.SetContentFile(tmp_file_path)
                    file_drive.Upload()

                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                    
                    success_count += 1

                except Exception as e:
                    st.error(f"❌ Failed to upload {file.name if hasattr(file, 'name') else f'image_{idx+1}'}: {str(e)}")

            # Final status
            progress_bar.progress(1.0)
            status_text.text("✅ Upload completed!")
            
            if success_count == total_files:
                st.success(f"✅ All {success_count} files uploaded successfully!")
            elif success_count > 0:
                st.warning(f"⚠️ {success_count}/{total_files} files uploaded successfully!")
            else:
                st.error("❌ No files were uploaded successfully!")
                
            if success_count > 0:
                st.info("🎉 धन्यवाद! ये तस्वीरें हमारे AI मॉडल के लिए संग्रहित कर ली गई हैं।")

        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
else:
    st.warning("⚠️ Google Drive authentication required.")