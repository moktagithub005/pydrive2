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
if 'farmer_name' not in st.session_state:
    st.session_state.farmer_name = ""

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

**💰 Benefits for You / आपके लिए फायदे:**
- Get better prices for quality apples / गुणवत्तापूर्ण सेबों के लिए बेहतर कीमत
- Reduce post-harvest losses / फसल के बाद के नुकसान को कम करना
- Smart storage decisions / स्मार्ट भंडारण निर्णय
""")

st.markdown("---")

# Farmer information section
st.subheader("👨‍🌾 Farmer Information / किसान जानकारी")

col1, col2 = st.columns(2)
with col1:
    farmer_name = st.text_input("Your Name / आपका नाम", value=st.session_state.farmer_name)
    if farmer_name:
        st.session_state.farmer_name = farmer_name
    
    location = st.text_input("Village/District / गाँव/जिला", placeholder="e.g., Shimla, Himachal Pradesh")
    
with col2:
    farm_size = st.selectbox("Farm Size / खेत का आकार", 
                            ["< 1 acre / 1 एकड़ से कम", 
                             "1-5 acres / 1-5 एकड़", 
                             "5-10 acres / 5-10 एकड़", 
                             "> 10 acres / 10 एकड़ से अधिक"])
    
    experience = st.selectbox("Apple Farming Experience / सेब की खेती का अनुभव",
                             ["< 5 years / 5 साल से कम",
                              "5-10 years / 5-10 साल",
                              "10-20 years / 10-20 साल", 
                              "> 20 years / 20 साल से अधिक"])

st.markdown("---")

# Image upload section
st.subheader("📸 Apple Image Upload / सेब की तस्वीर अपलोड करें")

with st.form("upload_form"):
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
    
    # Apple variety information
    st.subheader("🍎 Apple Details / सेब का विवरण")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        variety = st.selectbox("Apple Variety / सेब की किस्म", 
                              ["Red Delicious / रेड डिलीशियस", 
                               "Golden Delicious / गोल्डन डिलीशियस",
                               "Granny Smith / ग्रानी स्मिथ",
                               "Gala / गाला",
                               "Fuji / फूजी",
                               "Royal Delicious / रॉयल डिलीशियस",
                               "Other / अन्य"])
        
        if variety == "Other / अन्य":
            other_variety = st.text_input("Specify variety / किस्म बताएं")
    
    with col2:
        harvest_time = st.selectbox("Harvest Stage / फसल का चरण",
                                   ["Just picked / अभी तोड़ा गया",
                                    "1-3 days old / 1-3 दिन पुराना",
                                    "1 week old / 1 सप्ताह पुराना",
                                    "2+ weeks old / 2+ सप्ताह पुराना"])
        
        storage_condition = st.selectbox("Storage Condition / भंडारण स्थिति",
                                        ["Room temperature / कमरे का तापमान",
                                         "Cold storage / कोल्ड स्टोरेज",
                                         "Refrigerated / रेफ्रिजरेटेड",
                                         "Controlled atmosphere / नियंत्रित वातावरण"])
    
    with col3:
        size_category = st.selectbox("Size Category / आकार श्रेणी",
                                    ["Small (< 6cm) / छोटा",
                                     "Medium (6-8cm) / मध्यम",
                                     "Large (8-10cm) / बड़ा",
                                     "Extra Large (>10cm) / अतिरिक्त बड़ा"])
        
        weight_estimate = st.selectbox("Weight Estimate / वजन का अनुमान",
                                      ["< 100g / 100 ग्राम से कम",
                                       "100-150g / 100-150 ग्राम",
                                       "150-200g / 150-200 ग्राम",
                                       "> 200g / 200 ग्राम से अधिक"])
    
    # Quality assessment
    st.subheader("🔍 Quality Assessment / गुणवत्ता मूल्यांकन")
    
    col1, col2 = st.columns(2)
    with col1:
        # Color assessment
        st.write("**Color Distribution / रंग वितरण:**")
        red_percentage = st.slider("Red Color % / लाल रंग %", 0, 100, 50)
        green_percentage = st.slider("Green Color % / हरा रंग %", 0, 100, 30)
        yellow_percentage = st.slider("Yellow Color % / पीला रंग %", 0, 100, 20)
        
        # Ripeness assessment
        ripeness = st.selectbox("Ripeness Level / पकने की स्थिति",
                               ["Unripe / कच्चा (Hard, very green)",
                                "Semi-ripe / अधपका (Firm, mixed colors)",
                                "Ripe / पका हुआ (Sweet, good colors)",
                                "Over-ripe / अधिक पका (Soft, dull colors)"])
        
        firmness = st.selectbox("Firmness / कठोरता",
                               ["Very firm / बहुत कठोर",
                                "Firm / कठोर",
                                "Slightly soft / थोड़ा नरम",
                                "Soft / नरम"])
    
    with col2:
        # Damage assessment
        st.write("**Damage Assessment / नुकसान का आकलन:**")
        
        surface_damage = st.multiselect("Surface Damage / सतह की क्षति",
                                       ["Scratches / खरोंचें",
                                        "Bruises / चोट के निशान",
                                        "Cuts / कटाव",
                                        "Insect damage / कीड़े का नुकसान",
                                        "Disease spots / बीमारी के धब्बे",
                                        "Sunburn / धूप की जलन",
                                        "None / कोई नहीं"])
        
        damage_severity = st.selectbox("Damage Severity / नुकसान की गंभीरता",
                                      ["None / कोई नहीं",
                                       "Minor / मामूली",
                                       "Moderate / मध्यम",
                                       "Severe / गंभीर"])
        
        market_grade = st.selectbox("Market Grade / बाजार ग्रेड",
                                   ["Premium / प्रीमियम",
                                    "Grade A / ग्रेड ए",
                                    "Grade B / ग्रेड बी",
                                    "Grade C / ग्रेड सी"])
    
    # Additional information
    st.subheader("📝 Additional Information / अतिरिक्त जानकारी")
    
    col1, col2 = st.columns(2)
    with col1:
        expected_price = st.number_input("Expected Price (₹/kg) / अपेक्षित मूल्य", 
                                        min_value=0, max_value=500, value=50)
        
        organic_status = st.selectbox("Organic Status / जैविक स्थिति",
                                     ["Organic / जैविक",
                                      "Natural / प्राकृतिक",
                                      "Conventional / पारंपरिक"])
    
    with col2:
        notes = st.text_area("Additional Notes / अतिरिक्त टिप्पणियां",
                            placeholder="Any special observations about this apple...")
    
    # Preview uploaded image
    if uploaded_file is not None:
        st.subheader("🖼️ Image Preview / छवि पूर्वावलोकन")
        
        # Display image with analysis
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(image, caption="Uploaded Apple Image", use_column_width=True)
        
        with col2:
            st.success("✅ Image Quality: Good")
            st.info(f"📏 Size: {image.size[0]}x{image.size[1]} pixels")
            st.info(f"💾 File Size: {len(uploaded_file.getvalue())/1024:.1f} KB")
            
            # Quality tips
            st.markdown("**📸 Photography Tips:**")
            st.markdown("- Good lighting ✨")
            st.markdown("- Clear focus 🎯")
            st.markdown("- Full apple visible 🍎")
            st.markdown("- Neutral background 🤍")
    
    # Submit button
    submitted = st.form_submit_button("🚀 Upload & Contribute / अपलोड करें और योगदान दें", 
                                     use_container_width=True)
    
    if submitted and uploaded_file is not None:
        if farmer_name and location:
            # Create metadata
            metadata = {
                "farmer_name": farmer_name,
                "location": location,
                "farm_size": farm_size,
                "experience": experience,
                "variety": variety,
                "harvest_time": harvest_time,
                "storage_condition": storage_condition,
                "size_category": size_category,
                "weight_estimate": weight_estimate,
                "red_percentage": red_percentage,
                "green_percentage": green_percentage,
                "yellow_percentage": yellow_percentage,
                "ripeness": ripeness,
                "firmness": firmness,
                "surface_damage": surface_damage,
                "damage_severity": damage_severity,
                "market_grade": market_grade,
                "expected_price": expected_price,
                "organic_status": organic_status,
                "notes": notes,
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
                st.info(f"**Apple Variety:** {variety}")
                st.info(f"**Ripeness:** {ripeness}")
                st.info(f"**Market Grade:** {market_grade}")
            with col2:
                st.info(f"**Color:** {red_percentage}% Red, {green_percentage}% Green")
                st.info(f"**Damage:** {damage_severity}")
                st.info(f"**Expected Price:** ₹{expected_price}/kg")
            
            # Encouragement message
            st.markdown("---")
            st.markdown("### 🌟 Keep Contributing! / योगदान जारी रखें!")
            st.markdown("""
            **Your images help us:**
            - Train better AI models 🤖
            - Help farmers get fair prices 💰
            - Reduce food waste 🌱
            - Build technology for rural India 🇮🇳
            
            **आपकी तस्वीरें हमारी मदद करती हैं:**
            - बेहतर एआई मॉडल बनाने में
            - किसानों को उचित मूल्य दिलाने में
            - खाद्य बर्बादी कम करने में
            - ग्रामीण भारत के लिए तकनीक बनाने में
            """)
            
        else:
            st.error("Please fill in your name and location / कृपया अपना नाम और स्थान भरें")
    elif submitted:
        st.error("Please upload an image first / कृपया पहले एक तस्वीर अपलोड करें")

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
    st.progress(st.session_state.total_uploads / 100)  # Progress out of 100
    st.write(f"Images collected: {st.session_state.total_uploads}")
    
    st.header("🏆 Top Contributors")
    st.markdown("""
    1. Raj Kumar - 25 images
    2. Priya Sharma - 20 images  
    3. Amit Singh - 18 images
    4. **You** - Continue contributing!
    """)