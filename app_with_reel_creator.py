"""
Facebook Reel Concept Generator - COMPLETE WORKING CODE
Step 2: Generate Viral Reel Concepts from Trending Data
"""

import streamlit as st
from groq import Groq
from typing import Dict, Optional
import json

# ============================================================================
# CONFIG
# ============================================================================
st.set_page_config(page_title="Reel Concept Generator", page_icon="🎬", layout="wide")

# ============================================================================
# GROQ CLIENT SETUP
# ============================================================================
@st.cache_resource
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found in Streamlit Secrets!")
        st.stop()
    return Groq(api_key=api_key)

# ============================================================================
# CLASS: Reel Concept Generator
# ============================================================================
class ReelConceptGenerator:
    """Generate viral Facebook Reel concepts using AI"""
    
    def __init__(self, groq_client):
        self.client = groq_client
    
    def generate_concept(self, topic: str, trending_data: Dict) -> str:
        """
        Generate reel concept from trending data
        
        Args:
            topic: Reel content topic
            trending_data: Dictionary with avg_likes, avg_comments, etc
        
        Returns:
            AI-generated reel concept (Mongolian)
        """
        
        # Build prompt
        avg_likes = trending_data.get('avg_likes', 0)
        avg_comments = trending_data.get('avg_comments', 0)
        
        prompt = f"""
Create a VIRAL Facebook Reel concept based on this data:

📌 TOPIC: {topic}
📊 TRENDING METRICS:
   - Average Likes: {avg_likes:.0f}
   - Average Comments: {avg_comments:.0f}

Generate a DETAILED reel concept with:

1. 🎬 HOOK (0-3 seconds)
   - Attention-grabbing opening line
   - Why viewer must keep watching
   - Emotional trigger or curiosity gap

2. 📖 STORY/CONTENT (3-20 seconds)
   - Main message or value
   - Entertainment or education
   - Keep it engaging
   - Include specific actions/visuals

3. 🎯 CALL TO ACTION (20-28 seconds)
   - What viewer should do
   - "Like", "Comment", "Share", "Follow"
   - Make it compelling

4. 🎵 AUDIO & MUSIC
   - Trending sound recommendations
   - Music style suggestions
   - Sound effects

5. #️⃣ HASHTAGS & DESCRIPTION
   - 10-15 relevant hashtags
   - SEO-friendly description
   - Instagram/Facebook optimized

Format your answer with clear sections using emoji headers.
WRITE IN MONGOLIAN LANGUAGE.
Make it creative and viral-worthy!
        """
        
        # Call Groq API
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=1500,
            top_p=1,
            stream=False
        )
        
        return response.choices[0].message.content
    
    def optimize_concept(self, concept: str, platform: str = "facebook") -> str:
        """
        Optimize concept for maximum virality
        
        Args:
            concept: Original concept
            platform: "facebook" or "instagram"
        
        Returns:
            Optimized concept
        """
        
        prompt = f"""
Optimize this {platform} reel concept for MAXIMUM VIRALITY:

ORIGINAL CONCEPT:
{concept}

OPTIMIZATION CHECKLIST:
1. ✅ Hook Strength - Is it 100% compelling in first 1 second?
2. ✅ Pacing - Does it keep viewers watching until the end?
3. ✅ CTA Power - Is the call to action irresistible?
4. ✅ Emotional Impact - Does it trigger emotion/curiosity?
5. ✅ Shareability - Will people share this?
6. ✅ Trend Alignment - Is it aligned with current trends?

OPTIMIZE FOR:
- Shorter hooks (1-2 seconds max)
- More engaging visuals
- Stronger emotional triggers
- Better pacing
- Multiple CTA opportunities
- More shareable moments

Return the OPTIMIZED VERSION in Mongolian.
Keep the same structure but make it MORE VIRAL.
Be specific with changes you made.
        """
        
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.75,
            max_tokens=1500,
            stream=False
        )
        
        return response.choices[0].message.content
    
    def create_variations(self, concept: str, num_variations: int = 3) -> list:
        """
        Create multiple concept variations
        
        Args:
            concept: Base concept
            num_variations: How many variations to generate
        
        Returns:
            List of concept variations
        """
        
        prompt = f"""
Create {num_variations} DIFFERENT viral reel concepts based on this core idea:

BASE CONCEPT:
{concept}

Generate {num_variations} unique variations that:
1. Keep the same topic
2. Have different hooks
3. Use different storytelling approaches
4. Include different CTAs
5. Are all viral-worthy

Format each variation as:
VARIATION 1:
[concept]

VARIATION 2:
[concept]

etc.

Write in Mongolian language.
Make each one unique and compelling.
        """
        
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=2000,
            stream=False
        )
        
        # Parse variations
        result = response.choices[0].message.content
        variations = result.split(f"VARIATION")
        return [v.strip() for v in variations if v.strip()]

# ============================================================================
# STREAMLIT UI
# ============================================================================

st.title("🎬 Facebook Reel Concept Generator")
st.markdown("**AI-Powered Viral Content Creation**")

# Get Groq client
groq = get_groq_client()

# ============================================================================
# SIDEBAR: INPUT DATA
# ============================================================================
with st.sidebar:
    st.header("📊 Trending Data Input")
    
    col1, col2 = st.columns(2)
    with col1:
        avg_likes = st.number_input("Avg Likes", value=450, min_value=0)
    with col2:
        avg_comments = st.number_input("Avg Comments", value=25, min_value=0)
    
    col3, col4 = st.columns(2)
    with col3:
        total_reels = st.number_input("Total Reels", value=15, min_value=1)
    with col4:
        engagement_rate = st.number_input("Engagement %", value=3.2, min_value=0.0)
    
    trending_data = {
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "total_reels": total_reels,
        "avg_engagement_rate": engagement_rate
    }
    
    st.divider()
    st.markdown("**Or paste JSON:**")
    json_data = st.text_area("JSON trending data", height=100)
    if json_data:
        try:
            trending_data = json.loads(json_data)
            st.success("✅ JSON loaded")
        except:
            st.error("❌ Invalid JSON")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Topic input
topic = st.text_input(
    "📌 Reel Topic",
    value="Facebook Marketing",
    placeholder="Enter reel topic..."
)

st.divider()

# STEP 1: Generate Concept
st.subheader("1️⃣ Generate Concept")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎬 Generate Concept", use_container_width=True, key="gen"):
        with st.spinner("Creating viral concept..."):
            try:
                generator = ReelConceptGenerator(groq)
                concept = generator.generate_concept(topic, trending_data)
                st.session_state.concept = concept
                st.success("✅ Concept generated!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    if st.button("⚡ Optimize", use_container_width=True, key="opt"):
        if "concept" in st.session_state:
            with st.spinner("Optimizing for virality..."):
                try:
                    generator = ReelConceptGenerator(groq)
                    optimized = generator.optimize_concept(st.session_state.concept)
                    st.session_state.optimized = optimized
                    st.success("✅ Optimized!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("Generate concept first!")

with col3:
    if st.button("🎯 Variations", use_container_width=True, key="var"):
        if "concept" in st.session_state:
            with st.spinner("Creating variations..."):
                try:
                    generator = ReelConceptGenerator(groq)
                    variations = generator.create_variations(st.session_state.concept, 3)
                    st.session_state.variations = variations
                    st.success("✅ Variations created!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("Generate concept first!")

# Display Generated Concept
if "concept" in st.session_state:
    st.divider()
    st.subheader("📝 Generated Concept")
    st.markdown(st.session_state.concept)
    
    # Download button
    st.download_button(
        "📥 Download Concept",
        st.session_state.concept,
        f"reel_concept_{topic.replace(' ', '_')}.txt",
        "text/plain"
    )

# Display Optimized Concept
if "optimized" in st.session_state:
    st.divider()
    st.subheader("⚡ Optimized Concept")
    st.markdown(st.session_state.optimized)
    
    st.download_button(
        "📥 Download Optimized",
        st.session_state.optimized,
        f"reel_optimized_{topic.replace(' ', '_')}.txt",
        "text/plain"
    )

# Display Variations
if "variations" in st.session_state:
    st.divider()
    st.subheader("🎯 Concept Variations")
    
    for i, var in enumerate(st.session_state.variations, 1):
        with st.expander(f"Variation {i}"):
            st.markdown(var)

# ============================================================================
# ADVANCED OPTIONS
# ============================================================================
st.divider()
st.subheader("⚙️ Advanced Options")

with st.expander("Custom Prompt"):
    custom_prompt = st.text_area(
        "Custom AI instruction",
        height=100,
        placeholder="Enter custom prompt for concept generation..."
    )
    
    if st.button("🚀 Generate with Custom Prompt"):
        if custom_prompt:
            with st.spinner("Generating..."):
                try:
                    response = groq.chat.completions.create(
                        model="mixtral-8x7b-32768",
                        messages=[
                            {
                                "role": "user",
                                "content": f"{custom_prompt}\n\nTopic: {topic}\n\nTrending data: {trending_data}"
                            }
                        ],
                        temperature=0.8,
                        max_tokens=1500,
                        stream=False
                    )
                    custom_result = response.choices[0].message.content
                    st.markdown(custom_result)
                    st.session_state.custom_result = custom_result
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("Enter custom prompt!")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
**How to use:**
1. Enter trending metrics or paste JSON
2. Input your reel topic
3. Click "Generate Concept"
4. Optimize for virality
5. Create variations
6. Download and use!

**Features:**
- 🎬 AI concept generation
- ⚡ Viral optimization
- 🎯 Multiple variations
- 📥 Easy download
- 🇲🇳 Mongolian language
""")

st.markdown("**Powered by Groq API | Free & Fast**")
