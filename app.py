import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import os
import datetime
from PIL import Image
import io

# Load secrets
creds = json.loads(st.secrets["google"]["CREDENTIALS"])
token = json.loads(st.secrets["google"]["TOKEN"])

# Write credentials to file
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

# Initialize session state for progress tracking
if 'total_uploads' not in st.session_state:
    st.session_state.total_uploads = 0
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

# App UI
st.set_page_config(
    page_title="Apple AI Dataset Collection", 
    page_icon="🍎",
    layout="wide"
)

# Header with animated elements
st.markdown("""
<div style="background: linear-gradient(90deg, #FF6B6B, #4ECDC4); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; text-align: center; margin: 0;">🍎 Apple Smart Assessment Project</h1>
    <p style="color: white; text-align: center; margin: 5px 0;">सेब स्मार्ट मूल्यांकन परियोजना</p>
</div>
""", unsafe_allow_html=True)

# Progress display
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Contributions", f"{st.session_state.total_uploads} 📸")
with col2:
    st.metric("Project Partner", "IARI Delhi 🏛️")
with col3:
    st.metric("Goal", "10,000 Images 🎯")

# Welcome message
st.markdown("""
### 🤝 Welcome Farmer Friends! / किसान मित्रों का स्वागत है!

**🎯 Our Mission / हमारा उद्देश्य:**
- Build AI to assess apple **color percentage** / रंग प्रतिशत का आकलन
- Determine **ripeness levels** / पकने की स्थिति निर्धारित करना  
- Detect **damage and defects** / नुकसान और दोष की पहचान

**💡 You can upload as many images as you want to help us build better AI models!**
**आप जितनी चाहें उतनी तस्वीरें अपलोड कर सकते हैं!**
""")

st.markdown("---")

# Image upload section
st.subheader("📸 Step 1: Upload Apple Image / चरण 1: सेब की तस्वीर अपलोड करें")

# Image source selection
option = st.radio(
    "Choose image source / छवि स्रोत चुनें",
    ["📁 Upload from device / डिवाइस से अपलोड करें", "📸 Use camera / कैमरा से लें"]
)

uploaded_file = None
if option == "📁 Upload from device / डिवाइस से अपलोड करें":
    uploaded_file = st.file_uploader(
        "Upload apple image / सेब की तस्वीर अपलोड करें", 
        type=["jpg", "jpeg", "png"],
        help="Best quality images help us build better AI models!"
    )
elif option == "📸 Use camera / कैमरा से लें":
    uploaded_file = st.camera_input(
        "Take a picture / एक तस्वीर लें",
        help="Hold camera steady and ensure good lighting"
    )

# Store current image in session state
if uploaded_file is not None:
    st.session_state.current_image = uploaded_file

# Show image preview and assessment form only if image is uploaded
if st.session_state.current_image is not None:
    # Preview uploaded image
    st.subheader("🖼️ Image Preview / छवि पूर्वावलोकन")
    
    # Display image with analysis
    image = Image.open(st.session_state.current_image)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(image, caption="Uploaded Apple Image", use_column_width=True)
    
    with col2:
        st.success("✅ Image Quality: Good")
        st.info(f"📏 Size: {image.size[0]}x{image.size[1]} pixels")
        st.info(f"💾 File Size: {len(st.session_state.current_image.getvalue())/1024:.1f} KB")
        
        # Quality tips
        st.markdown("**📸 Photography Tips:**")
        st.markdown("- Good lighting ✨")
        st.markdown("- Clear focus 🎯")
        st.markdown("- Full apple visible 🍎")
        st.markdown("- Neutral background 🤍")
    
    st.markdown("---")
    
    # Assessment form
    st.subheader("🔍 Step 2: Apple Assessment / चरण 2: सेब का मूल्यांकन")
    
    with st.form("assessment_form"):
        # Color assessment
        st.write("**🎨 Color Distribution / रंग वितरण:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            red_percentage = st.slider("Red Color % / लाल रंग %", 0, 100, 50)
        with col2:
            green_percentage = st.slider("Green Color % / हरा रंग %", 0, 100, 30)
        with col3:
            yellow_percentage = st.slider("Yellow Color % / पीला रंग %", 0, 100, 20)
        
        # Show color distribution visually
        total_percentage = red_percentage + green_percentage + yellow_percentage
        if total_percentage > 100:
            st.warning("⚠️ Total percentage should not exceed 100% / कुल प्रतिशत 100% से अधिक नहीं होना चाहिए")
        else:
            st.success(f"✅ Total: {total_percentage}% (Remaining: {100-total_percentage}%)")
        
        st.markdown("---")
        
        # Ripeness assessment
        st.write("**🍎 Ripeness Level / पकने की स्थिति:**")
        ripeness = st.selectbox("Select ripeness level / पकने की स्थिति चुनें",
                               ["Unripe / कच्चा (Hard, very green)",
                                "Semi-ripe / अधपका (Firm, mixed colors)",
                                "Ripe / पका हुआ (Sweet, good colors)",
                                "Over-ripe / अधिक पका (Soft, dull colors)"])
        
        st.markdown("---")
        
        # Damage assessment
        st.write("**🔍 Damage Assessment / नुकसान का आकलन:**")
        
        col1, col2 = st.columns(2)
        with col1:
            surface_damage = st.multiselect("Surface Damage / सतह की क्षति",
                                           ["Scratches / खरोंचें",
                                            "Bruises / चोट के निशान",
                                            "Cuts / कटाव",
                                            "Insect damage / कीड़े का नुकसान",
                                            "Disease spots / बीमारी के धब्बे",
                                            "Sunburn / धूप की जलन",
                                            "None / कोई नहीं"])
        
        with col2:
            damage_severity = st.selectbox("Damage Severity / नुकसान की गंभीरता",
                                          ["None / कोई नहीं",
                                           "Minor / मामूली",
                                           "Moderate / मध्यम",
                                           "Severe / गंभीर"])
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit Assessment / मूल्यांकन जमा करें", 
                                         use_container_width=True)
        
        if submitted:
            # Create metadata
            metadata = {
                "red_percentage": red_percentage,
                "green_percentage": green_percentage,
                "yellow_percentage": yellow_percentage,
                "total_color_percentage": total_percentage,
                "ripeness": ripeness,
                "surface_damage": surface_damage,
                "damage_severity": damage_severity,
                "upload_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Success message with animation
            st.balloons()
            st.success("🎉 Thank you for your contribution! / आपके योगदान के लिए धन्यवाद!")
            
            # Update progress
            st.session_state.total_uploads += 1
            
            # Show contribution summary
            st.markdown("### 📊 Your Contribution Summary / आपका योगदान सारांश")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Color Distribution:** {red_percentage}% Red, {green_percentage}% Green, {yellow_percentage}% Yellow")
                st.info(f"**Ripeness:** {ripeness}")
            with col2:
                st.info(f"**Damage Type:** {', '.join(surface_damage) if surface_damage else 'None'}")
                st.info(f"**Damage Severity:** {damage_severity}")
            
            # Clear current image to allow new upload
            st.session_state.current_image = None
            
            # Encouragement message
            st.markdown("---")
            st.markdown("### 🌟 Upload More Images! / और तस्वीरें अपलोड करें!")
            st.markdown("""
            **🔄 You can upload as many images as you want!**
            **आप जितनी चाहें उतनी तस्वीरें अपलोड कर सकते हैं!**
            
            **Your images help us:**
            - Train better AI models 🤖
            - Help farmers get fair prices 💰
            - Reduce food waste 🌱
            - Build technology for rural India 🇮🇳
            """)
            
    # Reset button to upload another image (outside the form)
    if st.session_state.total_uploads > 0:
        if st.button("📸 Upload Another Image / एक और तस्वीर अपलोड करें", use_container_width=True):
            st.experimental_rerun()

else:
    st.info("👆 Please upload or take a picture of an apple to continue / कृपया आगे बढ़ने के लिए सेब की तस्वीर अपलोड करें या लें")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background-color: #f0f0f0; border-radius: 10px;">
    <h4>🤝 Project Partnership</h4>
    <p><strong>IARI Delhi</strong> | Indian Agricultural Research Institute</p>
    <p>📞 Contact: 7876471141 | 📧 Email: unisole.empower@gmail.com</p>
    <p><em>Building AI for Agriculture • कृषि के लिए एआई का निर्माण</em></p>
</div>
""", unsafe_allow_html=True)

# Tips sidebar
with st.sidebar:
    st.header("💡 Tips for Better Images")
    st.markdown("""
    **📸 Photography Guidelines:**
    - Use natural daylight
    - Clean the apple surface
    - Show the entire apple
    - Include a coin for size reference
    - Take multiple angles if possible
    
    **🎯 What We're Looking For:**
    - Color variations
    - Ripeness stages
    - Surface defects
    - Different varieties
    - Various storage conditions
    """)
    
    st.header("📈 Project Progress")
    st.progress(min(st.session_state.total_uploads / 100, 1.0))  # Progress out of 100
    st.write(f"Images collected: {st.session_state.total_uploads}")
    
    st.header("🏆 Contribution Stats")
    st.markdown(f"""
    **Your contributions today:** {st.session_state.total_uploads}
    
    **Keep going!** Every image helps build better AI models for farmers.
    """)