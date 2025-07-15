import streamlit as st
import json
import os
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from PIL import Image
import uuid
from datetime import datetime
import base64
import tempfile

# ✅ Page config must come FIRST
st.set_page_config(
    page_title="Apple Image Collector - TEAM UNISOLE", 
    layout="centered",
    page_icon="🍎"
)

# Enhanced Google Drive authentication with better error handling
@st.cache_resource
def connect_drive():
    try:
        # Get credentials from Streamlit secrets
        credentials_json = st.secrets["google"]["CREDENTIALS"]
        
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(credentials_json)
            credentials_file = f.name
        
        # Initialize GoogleAuth
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile(credentials_file)
        
        # Configure OAuth settings
        gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
        gauth.settings['get_refresh_token'] = True
        
        # Method 1: Try using saved credentials (if TOKEN exists in secrets)
        if "TOKEN" in st.secrets["google"]:
            try:
                token_json = st.secrets["google"]["TOKEN"]
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(token_json)
                    token_file = f.name
                
                gauth.LoadCredentialsFile(token_file)
                
                # Check if credentials are valid
                if gauth.credentials and not gauth.access_token_expired:
                    gauth.Authorize()
                    # Clean up
                    os.unlink(credentials_file)
                    os.unlink(token_file)
                    return GoogleDrive(gauth)
                elif gauth.credentials and gauth.access_token_expired:
                    # Try to refresh
                    gauth.Refresh()
                    gauth.Authorize()
                    # Clean up
                    os.unlink(credentials_file)
                    os.unlink(token_file)
                    return GoogleDrive(gauth)
                    
            except Exception as token_error:
                st.warning(f"⚠️ Saved token failed: {str(token_error)}")
                # Continue to Method 2
        
        # Method 2: Use service account approach (if SERVICE_ACCOUNT exists)
        if "SERVICE_ACCOUNT" in st.secrets["google"]:
            try:
                service_account_json = st.secrets["google"]["SERVICE_ACCOUNT"]
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(service_account_json)
                    service_account_file = f.name
                
                gauth.settings['service_config'] = {
                    'client_service_email': json.loads(service_account_json)['client_email'],
                    'client_service_key_file': service_account_file,
                    'client_pkl_file': None,
                    'client_secrets_file': None
                }
                
                gauth.ServiceAuth()
                # Clean up
                os.unlink(credentials_file)
                os.unlink(service_account_file)
                return GoogleDrive(gauth)
                
            except Exception as service_error:
                st.warning(f"⚠️ Service account failed: {str(service_error)}")
        
        # Method 3: Manual authorization flow (for local development)
        st.error("❌ Authentication failed. Please follow the setup instructions below.")
        return None
        
    except KeyError as e:
        st.error(f"❌ Missing Streamlit secret: {str(e)}")
        st.info("""
        **Setup Instructions:**
        
        **Option 1: OAuth Token (Recommended for development)**
        1. Run the authentication script locally
        2. Add both CREDENTIALS and TOKEN to Streamlit secrets
        
        **Option 2: Service Account (Recommended for production)**
        1. Create a service account in Google Cloud Console
        2. Download the service account key JSON
        3. Add SERVICE_ACCOUNT to Streamlit secrets
        4. Share your Google Drive folder with the service account email
        """)
        return None
    except Exception as e:
        st.error(f"❌ Google Drive connection failed: {str(e)}")
        return None

# Function to find or create the apple_dataset folder
def get_or_create_folder(drive, folder_name="apple_dataset"):
    """
    Find existing folder or create new one in Google Drive
    Returns folder ID
    """
    try:
        # Search for existing folder
        file_list = drive.ListFile({
            'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        }).GetList()
        
        if file_list:
            # Folder exists, return its ID
            folder_id = file_list[0]['id']
            return folder_id
        else:
            # Create new folder
            folder_metadata = {
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive.CreateFile(folder_metadata)
            folder.Upload()
            folder_id = folder['id']
            return folder_id
            
    except Exception as e:
        st.error(f"❌ Error with folder operations: {str(e)}")
        return None

# Initialize drive connection
drive = connect_drive()

# --- Header Section ---
st.title("🍎 Apple Dataset Collector")
st.markdown("### **TEAM UNISOLE** - Incubated at IARI (Indian Agricultural Research Institute)")
st.markdown("📞 **Contact:** 7876471141 | 📧 **Email:** team.unisole@gmail.com")

# --- Mission Statement ---
st.markdown("""
---
### 🎯 Our Mission / हमारा मिशन

**English:** We are building India's largest open dataset of apple varieties to develop AI-powered tools for farmers. As an IARI-incubated startup, we're creating technology that helps farmers:
- Identify apple varieties instantly using photos
- Get better market prices through accurate variety classification
- Improve crop management with AI insights
- Access expert agricultural knowledge

**हिंदी:** हम भारत का सबसे बड़ा सेब किस्मों का डेटासेट बना रहे हैं ताकि किसानों के लिए AI-आधारित उपकरण विकसित कर सकें। IARI से इनक्यूबेटेड स्टार्टअप के रूप में, हम ऐसी तकनीक बना रहे हैं जो किसानों की मदद करती है:
- तस्वीरों से सेब की किस्मों की तुरंत पहचान करना
- सटीक किस्म वर्गीकरण के माध्यम से बेहतर बाजार मूल्य पाना
- AI अंतर्दृष्टि के साथ फसल प्रबंधन में सुधार
- विशेषज्ञ कृषि ज्ञान तक पहुंच

**🔬 Research Impact:** Your contribution will directly help build AI models that benefit the entire farming community.
---
""")

# Check if drive is connected
if drive is None:
    st.error("❌ Google Drive connection failed. Please check your setup.")
    
    # Show setup instructions
    st.markdown("### 🔧 Setup Instructions")
    
    tab1, tab2, tab3 = st.tabs(["🔑 OAuth Setup", "🛠️ Service Account Setup", "🆘 Troubleshooting"])
    
    with tab1:
        st.markdown("""
        **OAuth Token Setup (For Development):**
        
        1. **Run this authentication script locally:**
        ```python
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
        import json
        
        # Create GoogleAuth instance
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile("credentials.json")
        gauth.settings['oauth_scope'] = ["https://www.googleapis.com/auth/drive"]
        gauth.settings['get_refresh_token'] = True
        
        # Authenticate (opens browser)
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("token.json")
        
        # Test connection
        drive = GoogleDrive(gauth)
        print("✅ Success!")
        
        # Show token content
        with open("token.json", "r") as f:
            print("Copy this to Streamlit secrets:")
            print(f.read())
        ```
        
        2. **Add to Streamlit secrets:**
        ```toml
        [google]
        CREDENTIALS = '{"installed":{"client_id":"...","client_secret":"..."}}'
        TOKEN = '{"access_token":"...","refresh_token":"..."}'
        ```
        """)
    
    with tab2:
        st.markdown("""
        **Service Account Setup (For Production):**
        
        1. **Create Service Account:**
           - Go to Google Cloud Console
           - Create a new service account
           - Download the JSON key file
        
        2. **Share Google Drive folder:**
           - Share your Google Drive folder with the service account email
           - Give it "Editor" permissions
        
        3. **Add to Streamlit secrets:**
        ```toml
        [google]
        SERVICE_ACCOUNT = '{"type":"service_account","project_id":"...","private_key":"..."}'
        ```
        """)
    
    with tab3:
        st.markdown("""
        **Common Issues & Solutions:**
        
        **Issue:** "Token has been expired or revoked"
        **Solution:** 
        - Generate a completely new token
        - Make sure you're using the correct Google account
        - Check that your OAuth consent screen is properly configured
        
        **Issue:** "invalid_grant"
        **Solution:**
        - Your token might be from a different environment
        - Regenerate the token on the same machine/environment
        - Ensure the time on your machine is correct
        
        **Issue:** "Access denied"
        **Solution:**
        - Check Google Drive API is enabled
        - Verify OAuth scopes include drive access
        - Ensure the Google account has proper permissions
        """)
    
    st.stop()

# Display folder information
st.info(f"""
📁 **Storage Location:** All images will be saved to the 'apple_dataset' folder in Google Drive.
🔗 **Access:** Log in to `unisole.empower@gmail.com` → My Drive → apple_dataset folder
""")

# --- Image Capture/Upload Section ---
st.subheader("📸 Share Your Apple Images / अपनी सेब की तस्वीरें साझा करें")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📷 कैमरा / Camera", "📁 Single Upload / एक फाइल", "📁 Multiple Upload / कई फाइलें"])

uploaded_images = []
rotation_angles = []

# Rotation utility function
def rotate_image(image_data, angle):
    """Rotate image by specified angle"""
    try:
        image = Image.open(image_data)
        if angle != 0:
            rotated = image.rotate(-angle, expand=True)
        else:
            rotated = image
        
        # Convert to RGB if necessary
        if rotated.mode != 'RGB':
            rotated = rotated.convert('RGB')
        
        byte_arr = io.BytesIO()
        rotated.save(byte_arr, format='JPEG', quality=90)
        byte_arr.seek(0)
        return byte_arr
    except Exception as e:
        st.error(f"Error rotating image: {str(e)}")
        return None

# Tab 1: Camera Input
with tab1:
    st.markdown("📱 **Tip:** Ensure good lighting and clear focus for best results")
    camera_image = st.camera_input("📸 Take a photo of an apple / सेब की तस्वीर लें")
    
    if camera_image:
        rotation_angle = st.slider(
            "🔄 Rotate Image if needed / यदि आवश्यक हो तो छवि घुमाएं", 
            0, 360, 0, step=90, 
            key="camera_rotation"
        )
        
        img_bytes = rotate_image(camera_image, rotation_angle)
        if img_bytes:
            uploaded_images = [img_bytes]
            rotation_angles = [rotation_angle]
            st.image(img_bytes, caption="📷 Your Image / आपकी तस्वीर", width=300)

# Tab 2: Single File Upload
with tab2:
    st.markdown("📁 **Supported formats:** JPG, JPEG, PNG")
    file_upload = st.file_uploader(
        "📁 Upload apple image / सेब की तस्वीर अपलोड करें", 
        type=["jpg", "jpeg", "png"]
    )
    
    if file_upload:
        rotation_angle = st.slider(
            "🔄 Rotate Image if needed / यदि आवश्यक हो तो छवि घुमाएं", 
            0, 360, 0, step=90, 
            key="upload_rotation"
        )
        
        img_bytes = rotate_image(file_upload, rotation_angle)
        if img_bytes:
            uploaded_images = [img_bytes]
            rotation_angles = [rotation_angle]
            st.image(img_bytes, caption="🖼️ Your Image / आपकी तस्वीर", width=300)

# Tab 3: Multiple File Upload
with tab3:
    st.markdown("""
    📁 **Multiple Images Upload / कई तस्वीरें अपलोड करें**
    
    **English:** Upload multiple images of different apples to make a bigger contribution to our dataset! 
    You can select multiple files at once by holding Ctrl (Windows) or Cmd (Mac) while clicking.
    
    **हिंदी:** अलग-अलग सेबों की कई तस्वीरें अपलोड करें और हमारे डेटासेट में बड़ा योगदान दें! 
    आप Ctrl (Windows) या Cmd (Mac) दबाकर एक साथ कई फाइलें चुन सकते हैं।
    """)
    
    st.markdown("**Supported formats:** JPG, JPEG, PNG")
    
    multiple_files = st.file_uploader(
        "📁 Select multiple apple images / कई सेब की तस्वीरें चुनें",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Hold Ctrl/Cmd while clicking to select multiple files"
    )
    
    if multiple_files:
        st.success(f"✅ {len(multiple_files)} images selected / {len(multiple_files)} तस्वीरें चुनी गईं")
        
        uploaded_images = []
        rotation_angles = []
        
        # Process each uploaded file
        for i, file in enumerate(multiple_files):
            st.markdown(f"**Image {i+1}: {file.name}**")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                rotation_angle = st.slider(
                    f"🔄 Rotate Image {i+1}",
                    0, 360, 0, step=90,
                    key=f"multi_rotation_{i}"
                )
                rotation_angles.append(rotation_angle)
            
            with col2:
                img_bytes = rotate_image(file, rotation_angle)
                if img_bytes:
                    uploaded_images.append(img_bytes)
                    st.image(img_bytes, caption=f"Image {i+1}: {file.name}", width=200)
                else:
                    st.error(f"Failed to process image {i+1}")
        
        if len(uploaded_images) != len(multiple_files):
            st.error("❌ Some images failed to process. Please try again.")
            uploaded_images = []

# --- Metadata Collection ---
if uploaded_images:
    st.subheader("📋 Image Information / तस्वीर की जानकारी")
    
    # Show different UI based on single vs multiple images
    if len(uploaded_images) == 1:
        st.markdown("**Single Image Metadata / एकल तस्वीर की जानकारी**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            variety = st.text_input(
                "🍏 Apple Variety / सेब की किस्म*", 
                placeholder="e.g., Red Delicious, Fuji, Gala",
                help="Enter the specific variety name if known"
            )
            
            size = st.selectbox(
                "📏 Apple Size / सेब का आकार",
                ["Small/छोटा", "Medium/मध्यम", "Large/बड़ा", "Extra Large/अतिरिक्त बड़ा"]
            )
        
        with col2:
            location = st.text_input(
                "📍 Location / स्थान", 
                placeholder="e.g., Shimla, Kashmir, Uttarakhand",
                help="State or region where the apple was grown"
            )
            
            ripeness = st.selectbox(
                "🍎 Ripeness / पकने की स्थिति",
                ["Unripe/कच्चा", "Ripe/पका हुआ", "Overripe/अधिक पका"]
            )
        
        # Additional information
        st.markdown("**Optional Details / वैकल्पिक विवरण**")
        
        col3, col4 = st.columns(2)
        with col3:
            season = st.selectbox(
                "🗓️ Harvest Season / फसल का मौसम",
                ["Spring/वसंत", "Summer/गर्मी", "Autumn/शरद", "Winter/सर्दी", "Not Sure/पता नहीं"]
            )
        
        with col4:
            quality = st.selectbox(
                "⭐ Quality Grade / गुणवत्ता ग्रेड",
                ["Excellent/उत्कृष्ट", "Good/अच्छा", "Average/औसत", "Poor/खराब"]
            )
        
        additional_notes = st.text_area(
            "📝 Additional Notes / अतिरिक्त टिप्पणियां",
            placeholder="Any other observations about the apple...",
            height=100
        )
        
        # Store metadata for single image
        all_metadata = [{
            'variety': variety,
            'location': location,
            'size': size,
            'ripeness': ripeness,
            'season': season,
            'quality': quality,
            'notes': additional_notes
        }]
        
    else:
        st.markdown(f"**Multiple Images Metadata / कई तस्वीरों की जानकारी ({len(uploaded_images)} images)**")
        
        # Common metadata for all images
        st.markdown("**Common Information for All Images / सभी तस्वीरों के लिए सामान्य जानकारी**")
        
        col1, col2 = st.columns(2)
        with col1:
            common_location = st.text_input(
                "📍 Common Location / सामान्य स्थान", 
                placeholder="e.g., Shimla, Kashmir, Uttarakhand",
                help="State or region where all apples were grown"
            )
            common_season = st.selectbox(
                "🗓️ Common Harvest Season / सामान्य फसल का मौसम",
                ["Spring/वसंत", "Summer/गर्मी", "Autumn/शरद", "Winter/सर्दी", "Not Sure/पता नहीं"]
            )
        
        with col2:
            common_quality = st.selectbox(
                "⭐ Common Quality Grade / सामान्य गुणवत्ता ग्रेड",
                ["Excellent/उत्कृष्ट", "Good/अच्छा", "Average/औसत", "Poor/खराब"]
            )
        
        common_notes = st.text_area(
            "📝 Common Notes / सामान्य टिप्पणियां",
            placeholder="Any common observations about all apples...",
            height=80
        )
        
        st.markdown("---")
        st.markdown("**Individual Image Details / व्यक्तिगत तस्वीर विवरण**")
        
        all_metadata = []
        
        # Individual metadata for each image
        for i in range(len(uploaded_images)):
            with st.expander(f"🍎 Image {i+1} Details / तस्वीर {i+1} विवरण"):
                col1, col2 = st.columns(2)
                
                with col1:
                    variety = st.text_input(
                        "🍏 Apple Variety / सेब की किस्म*",
                        placeholder="e.g., Red Delicious, Fuji, Gala",
                        key=f"variety_{i}"
                    )
                    
                    size = st.selectbox(
                        "📏 Apple Size / सेब का आकार",
                        ["Small/छोटा", "Medium/मध्यम", "Large/बड़ा", "Extra Large/अतिरिक्त बड़ा"],
                        key=f"size_{i}"
                    )
                
                with col2:
                    ripeness = st.selectbox(
                        "🍎 Ripeness / पकने की स्थिति",
                        ["Unripe/कच्चा", "Ripe/पका हुआ", "Overripe/अधिक पका"],
                        key=f"ripeness_{i}"
                    )
                    
                    individual_notes = st.text_input(
                        "📝 Specific Notes / विशिष्ट टिप्पणियां",
                        placeholder="Specific observations for this apple...",
                        key=f"notes_{i}"
                    )
                
                # Combine common and individual metadata
                metadata = {
                    'variety': variety,
                    'location': common_location,
                    'size': size,
                    'ripeness': ripeness,
                    'season': common_season,
                    'quality': common_quality,
                    'notes': f"{common_notes} | {individual_notes}" if individual_notes else common_notes
                }
                all_metadata.append(metadata)

    # --- Submit Section ---
    st.markdown("---")
    
    # Validation
    missing_varieties = []
    for i, metadata in enumerate(all_metadata):
        if not metadata['variety'].strip():
            missing_varieties.append(i+1)
    
    if missing_varieties:
        st.error(f"❌ Please enter apple variety for image(s): {', '.join(map(str, missing_varieties))} / कृपया तस्वीर संख्या {', '.join(map(str, missing_varieties))} के लिए सेब की किस्म दर्ज करें")
    
    if st.button("🚀 Upload to Dataset / डेटासेट में अपलोड करें", type="primary", use_container_width=True):
        if missing_varieties:
            st.error("❌ Please fill in all required fields before uploading.")
        else:
            try:
                with st.spinner(f"⏳ Uploading {len(uploaded_images)} image(s) to apple_dataset folder... / apple_dataset फोल्डर में {len(uploaded_images)} तस्वीर(ों) को अपलोड हो रहा है..."):
                    
                    # Get or create the apple_dataset folder
                    folder_id = get_or_create_folder(drive, "apple_dataset")
                    if folder_id is None:
                        st.error("❌ Failed to access or create the apple_dataset folder.")
                        st.stop()
                    
                    uploaded_files = []
                    failed_uploads = []
                    
                    # Upload each image
                    for i, (img_bytes, metadata) in enumerate(zip(uploaded_images, all_metadata)):
                        try:
                            # Create unique filename with metadata
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            unique_id = uuid.uuid4().hex[:8]
                            
                            # Clean variety name for filename
                            clean_variety = "".join(c for c in metadata['variety'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            
                            filename = f"apple_dataset_{timestamp}_{clean_variety}_{unique_id}_{i+1}.jpg"
                            
                            # Prepare metadata with upload info
                            full_metadata = {
                                **metadata,
                                'upload_time': datetime.now().isoformat(),
                                'contributor_type': 'farmer_app',
                                'folder': 'apple_dataset',
                                'batch_upload': len(uploaded_images) > 1,
                                'batch_size': len(uploaded_images),
                                'image_number': i + 1
                            }
                            
                            # Create file on Google Drive in the specific folder
                            file_drive = drive.CreateFile({
                                'title': filename,
                                'description': json.dumps(full_metadata, ensure_ascii=False),
                                'parents': [{'id': folder_id}]
                            })
                            
                            # Set content from uploaded image
                            img_bytes.seek(0)
                            file_drive.content = img_bytes
                            file_drive.Upload()
                            
                            uploaded_files.append({
                                'filename': filename,
                                'variety': metadata['variety'],
                                'unique_id': unique_id
                            })
                            
                        except Exception as e:
                            failed_uploads.append(f"Image {i+1}: {str(e)}")
                    
                    # Show results
                    if uploaded_files:
                        st.success(f"✅ Successfully uploaded {len(uploaded_files)} image(s) to the apple_dataset folder!")
                        st.success(f"✅ सफलतापूर्वक {len(uploaded_files)} तस्वीर(ें) apple_dataset फोल्डर में अपलोड हो गईं!")
                        st.balloons()
                        
                        # Show contribution summary
                        st.info(f"""
                        📊 **Your Contribution Summary / आपका योगदान सारांश:**
                        - Total Images Uploaded: {len(uploaded_files)}
                        - 📁 Saved to: apple_dataset folder
                        
                        **Uploaded Files:**
                        """)
                        
                        for file_info in uploaded_files:
                            st.write(f"• {file_info['variety']} - {file_info['filename']}")
                        
                        st.info("""
                        **To find your images:**
                        1. Log in to Google Drive with unisole.empower@gmail.com
                        2. Go to My Drive → apple_dataset folder
                        3. Search for your upload timestamp
                        
                        This data will help train AI models to benefit farmers across India!
                        यह डेटा भारत भर के किसानों को लाभ पहुंचाने वाले AI मॉडल को प्रशिक्षित करने में मदद करेगा!
                        """)
                    
                    if failed_uploads:
                        st.error("❌ Some uploads failed:")
                        for error in failed_uploads:
                            st.error(f"• {error}")
                    
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                st.error("Please check your internet connection and try again.")

# --- Footer ---
st.markdown("---")
st.markdown("""
### 🤝 About TEAM UNISOLE

We are a research-driven startup incubated at **IARI (Indian Agricultural Research Institute)**, India's premier agricultural research institution. Our mission is to bridge the gap between cutting-edge agricultural research and practical farming solutions using AI and machine learning.

**Our Impact Goals:**
- Build comprehensive datasets for Indian agriculture
- Develop AI tools specifically for Indian farming conditions  
- Provide free technology solutions to support farmers
- Contribute to food security and sustainable agriculture

**Contact Us:**
- 📞 Phone: 7876471141
- 📧 Email: team.unisole@gmail.com
- 🏢 Incubated at: IARI, New Delhi

*Your contribution today helps build tomorrow's farming technology!*
""")

st.markdown("---")
st.markdown("*© 2025 TEAM UNISOLE - Building the future of Indian agriculture with AI*")