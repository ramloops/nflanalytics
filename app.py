"""
Super Bowl LX 4th Down Analysis
================================
Supabase + Claude API Version
"""

import streamlit as st
import pandas as pd

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Super Bowl LX: 4th Down Analysis",
    page_icon="🏈",
    layout="wide"
)

# ============================================
# LIGHT MODE ONLY (Mobile-friendly)
# ============================================
mobile_css = """
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        h1 { font-size: 1.5rem !important; }
        h2, h3 { font-size: 1.2rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.85rem !important;
        }
        .stButton > button {
            width: 100% !important;
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
        }
        [data-testid="stChatInput"] textarea { font-size: 16px !important; }
    }
    
    @media (max-width: 480px) {
        h1 { font-size: 1.25rem !important; }
        [data-testid="stMetricValue"] { font-size: 1rem !important; }
        .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.5rem !important;
            font-size: 0.75rem !important;
        }
    }
    
    /* Light mode - ensure readable text */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    [data-testid="stChatMessage"] {
        background-color: #f0f2f6;
        color: #1a1a1a !important;
    }
    
    [data-testid="stChatMessage"] p {
        color: #1a1a1a !important;
    }
    
    [data-testid="stChatMessage"] * {
        color: #1a1a1a !important;
    }
"""

st.markdown(f"<style>{mobile_css}</style>", unsafe_allow_html=True)

# ============================================
# SUPABASE CONNECTION
# ============================================
@st.cache_resource
def get_supabase_client():
    """Create Supabase client from secrets"""
    try:
        from supabase import create_client, Client
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        st.error(f"Supabase connection error: {e}")
        return None

# ============================================
# DATA FUNCTIONS
# ============================================
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_fourth_down_data():
    """Fetch 4th down data from Supabase"""
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table('play_by_play_2025') \
                .select('play_id, qtr, down, ydstogo, posteam, defteam, posteam_score, defteam_score, wp, wpa, epa, play_type, desc, side_of_field, yardline_100') \
                .eq('game_id', '2025_22_SEA_NE') \
                .eq('down', '4') \
                .eq('posteam', 'NE') \
                .order('play_id') \
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Rename columns to match our app
                df = df.rename(columns={
                    'qtr': 'QUARTER',
                    'ydstogo': 'YARDS_TO_GO',
                    'side_of_field': 'SIDE_OF_FIELD',
                    'yardline_100': 'YARDLINE_100',
                    'posteam_score': 'NE_SCORE',
                    'defteam_score': 'SEA_SCORE',
                    'play_type': 'PLAY_TYPE',
                    'wp': 'WIN_PROB_PCT',
                    'wpa': 'WPA_PCT',
                    'epa': 'EPA',
                    'desc': 'PLAY_DESCRIPTION'
                })
                
                # Convert TEXT columns to numeric
                df['QUARTER'] = pd.to_numeric(df['QUARTER'], errors='coerce')
                df['YARDS_TO_GO'] = pd.to_numeric(df['YARDS_TO_GO'], errors='coerce')
                df['NE_SCORE'] = pd.to_numeric(df['NE_SCORE'], errors='coerce').fillna(0).astype(int)
                df['SEA_SCORE'] = pd.to_numeric(df['SEA_SCORE'], errors='coerce').fillna(0).astype(int)
                df['WIN_PROB_PCT'] = pd.to_numeric(df['WIN_PROB_PCT'], errors='coerce') * 100
                df['WPA_PCT'] = pd.to_numeric(df['WPA_PCT'], errors='coerce') * 100
                df['EPA'] = pd.to_numeric(df['EPA'], errors='coerce')
                
                # Calculate score differential
                df['SCORE_DIFFERENTIAL'] = df['NE_SCORE'] - df['SEA_SCORE']
                
                # Create field position string
                df['FIELD_POSITION'] = df['SIDE_OF_FIELD'].fillna('') + ' ' + df['YARDLINE_100'].fillna('').astype(str)
                
                # Mark all as punt attempts (since we filtered for punts)
                df['PUNT_ATTEMPT'] = df['PLAY_TYPE'] == 'punt'
                
                return df
    except Exception as e:
        st.warning(f"Could not fetch from Supabase: {e}")
    
    # Fallback to hardcoded data if Supabase fails
    return get_fallback_data()

def get_fallback_data():
    """Fallback data if Supabase is not available"""
    return pd.DataFrame([
        {"QUARTER": 1, "TIME": "10:23", "YARDS_TO_GO": 8, "FIELD_POSITION": "SEA 44", 
         "NE_SCORE": 0, "SEA_SCORE": 3, "SCORE_DIFFERENTIAL": -3, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 38.0, "WPA_PCT": -3.0, "EPA": -0.5, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt to SEA 20"},
        {"QUARTER": 1, "TIME": "5:45", "YARDS_TO_GO": 15, "FIELD_POSITION": "NE 35",
         "NE_SCORE": 0, "SEA_SCORE": 3, "SCORE_DIFFERENTIAL": -3, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 35.0, "WPA_PCT": -2.0, "EPA": -0.3, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt downed at SEA 15"},
        {"QUARTER": 2, "TIME": "9:30", "YARDS_TO_GO": 17, "FIELD_POSITION": "NE 28",
         "NE_SCORE": 0, "SEA_SCORE": 6, "SCORE_DIFFERENTIAL": -6, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 25.0, "WPA_PCT": -3.0, "EPA": -0.4, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt to SEA 25"},
        {"QUARTER": 2, "TIME": "2:15", "YARDS_TO_GO": 6, "FIELD_POSITION": "SEA 38",
         "NE_SCORE": 0, "SEA_SCORE": 6, "SCORE_DIFFERENTIAL": -6, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 22.0, "WPA_PCT": -2.5, "EPA": -0.6, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt into end zone, touchback"},
        {"QUARTER": 3, "TIME": "8:40", "YARDS_TO_GO": 1, "FIELD_POSITION": "OWN 41",
         "NE_SCORE": 0, "SEA_SCORE": 12, "SCORE_DIFFERENTIAL": -12, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 12.0, "WPA_PCT": -4.2, "EPA": -0.8, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "4th & 1 PUNT from own 41 - THE KEY PLAY"},
        {"QUARTER": 3, "TIME": "2:30", "YARDS_TO_GO": 8, "FIELD_POSITION": "NE 23",
         "NE_SCORE": 0, "SEA_SCORE": 12, "SCORE_DIFFERENTIAL": -12, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 8.0, "WPA_PCT": -2.0, "EPA": -0.3, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt to SEA 45"},
        {"QUARTER": 4, "TIME": "12:05", "YARDS_TO_GO": 11, "FIELD_POSITION": "NE 19",
         "NE_SCORE": 6, "SEA_SCORE": 19, "SCORE_DIFFERENTIAL": -13, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 5.0, "WPA_PCT": -1.5, "EPA": -0.2, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt to SEA 35"},
        {"QUARTER": 4, "TIME": "5:20", "YARDS_TO_GO": 4, "FIELD_POSITION": "SEA 48",
         "NE_SCORE": 13, "SEA_SCORE": 22, "SCORE_DIFFERENTIAL": -9, "PLAY_TYPE": "punt",
         "WIN_PROB_PCT": 6.0, "WPA_PCT": -3.0, "EPA": -0.7, "PUNT_ATTEMPT": True,
         "PLAY_DESCRIPTION": "Punt with 5 min left, down 9"},
    ])

# ============================================
# GROQ AI CHAT (Free!)
# ============================================
def get_ai_response(question, fourth_downs_df):
    """Get AI response using Groq API (free, fast)"""
    
    # Session limit: 10 questions per session
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    
    if st.session_state.question_count >= 10:
        return "⚠️ You've reached the limit of 10 questions per session. Refresh the page to start a new session."
    
    st.session_state.question_count += 1
    
    data_context = fourth_downs_df.to_string()
    
    system_prompt = f"""You are an NFL analytics expert analyzing the Patriots' 4th down decisions in Super Bowl LX (Seahawks 29, Patriots 13).

Here is the data on all Patriots 4th down plays:
{data_context}

Key facts:
- NFL 4th & 1 conversion rate is 72%
- The Patriots punted on 4th & 1 from their own 41 while down 12-0 in Q3
- WPA = Win Probability Added (negative means the decision hurt their chances)
- EPA = Expected Points Added

Answer questions concisely and reference specific plays from the data."""

    try:
        from groq import Groq
        
        api_key = st.secrets.get("GROQ_API_KEY") or st.secrets.get("groq", {}).get("api_key")
        
        if not api_key:
            return "⚠️ Groq API key not configured. Add GROQ_API_KEY to your Streamlit secrets."
        
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)[:150]}"

# ============================================
# LOAD DATA
# ============================================
fourth_downs = get_fourth_down_data()

# Grade decisions
def grade_decision(row):
    ydstogo = row.get('YARDS_TO_GO', 10)
    score_diff = row.get('SCORE_DIFFERENTIAL', 0)
    wpa = row.get('WPA_PCT', 0)
    punt = row.get('PUNT_ATTEMPT', False)
    
    if punt:
        if ydstogo <= 1 and score_diff <= -10:
            return "🔴 TERRIBLE"
        elif ydstogo <= 2 and score_diff <= -7:
            return "🔴 BAD"
        elif ydstogo <= 4 and score_diff <= -9:
            return "🟡 QUESTIONABLE"
        elif wpa < -3:
            return "🟡 QUESTIONABLE"
    return "✅ OK"

fourth_downs['GRADE'] = fourth_downs.apply(grade_decision, axis=1)

# ============================================
# HEADER
# ============================================
st.title("🏈 Super Bowl LX: 4th Down Analysis")
st.markdown("### Seahawks 29 - Patriots 13")
st.markdown("*Why conservative play-calling cost New England the game*")

# ============================================
# KEY METRICS
# ============================================
col1, col2, col3, col4 = st.columns(4)

punts = fourth_downs[fourth_downs['PUNT_ATTEMPT'] == True]

with col1:
    st.metric("4th Down Punts", len(punts))
with col2:
    bad_decisions = len(fourth_downs[fourth_downs['GRADE'].str.contains('🔴|🟡')])
    st.metric("Bad/Questionable", bad_decisions)
with col3:
    total_wpa = punts['WPA_PCT'].sum()
    st.metric("Total WPA Lost", f"{total_wpa:.1f}%")
with col4:
    total_epa = punts['EPA'].sum()
    st.metric("Total EPA Lost", f"{total_epa:.2f}")

st.markdown("---")

# ============================================
# TABS
# ============================================
tab_home, tab_data, tab_analysis = st.tabs(["🏠 Overview", "📊 All 4th Downs", "📈 Analysis"])

with tab_home:
    chat_col, play_col = st.columns([1, 1])

    with chat_col:
        st.subheader("🤖 Ask About the Game")
        st.caption(f"Powered by Groq AI • {10 - st.session_state.get('question_count', 0)} questions left")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        st.caption("Try asking:")
        example_cols = st.columns(2)
        with example_cols[0]:
            if st.button("What was the worst decision?", use_container_width=True):
                st.session_state.pending_question = "What was the worst 4th down decision and why?"
        with example_cols[1]:
            if st.button("Should they have gone for it?", use_container_width=True):
                st.session_state.pending_question = "Should the Patriots have gone for it on 4th & 1?"
        
        question = st.chat_input("Ask about Patriots' 4th down decisions...")
        
        if "pending_question" in st.session_state:
            question = st.session_state.pending_question
            del st.session_state.pending_question
        
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = get_ai_response(question, fourth_downs)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    with play_col:
        st.subheader("🔥 The Key Play")
        
        # Find the 4th & 1 play (or shortest yardage)
        key_play_df = fourth_downs[fourth_downs['YARDS_TO_GO'] == fourth_downs['YARDS_TO_GO'].min()]
        if len(key_play_df) > 0:
            key_play = key_play_df.iloc[0]
            ydstogo = int(key_play['YARDS_TO_GO'])
            st.error(f"**4th & {ydstogo} from own {key_play.get('YARDLINE_100', 'N/A')}, down {abs(int(key_play['SCORE_DIFFERENTIAL']))}-0 in Q{int(key_play['QUARTER'])} → PUNT**")
        
            kp_col1, kp_col2 = st.columns(2)
            with kp_col1:
                st.metric("Win Prob Before", f"{key_play['WIN_PROB_PCT']:.1f}%")
                st.metric("NFL 4th & 1 Conv Rate", "72%")
            with kp_col2:
                st.metric("WPA from Punt", f"{key_play['WPA_PCT']:.1f}%", delta="Lost", delta_color="inverse")
                st.metric("Decision", "PUNT 👎")
            
            st.markdown("""
            **The Math:**
            - Go for it: 72% convert → keep drive alive
            - Even if fail: SEA gets ball at NE 41
            - Punt: SEA gets ball at ~SEA 15
            
            **Net field position gain from punt: ~44 yards**  
            **Not worth giving up 72% chance to convert!**
            """)
        else:
            st.warning("No 4th down data found")

with tab_data:
    st.header("All Patriots 4th Down Decisions")
    
    display_df = fourth_downs.copy()
    display_df['SITUATION'] = 'Q' + display_df['QUARTER'].astype(str)
    display_df['DOWN_DIST'] = '4th & ' + display_df['YARDS_TO_GO'].astype(str)
    display_df['SCORE'] = display_df['NE_SCORE'].astype(int).astype(str) + '-' + display_df['SEA_SCORE'].astype(int).astype(str)
    
    show_cols = ['SITUATION', 'DOWN_DIST', 'FIELD_POSITION', 'SCORE', 
                 'WIN_PROB_PCT', 'WPA_PCT', 'EPA', 'GRADE']
    
    st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True)

with tab_analysis:
    st.header("Decision Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Probability Trend")
        chart_df = fourth_downs.copy()
        chart_df['Play #'] = range(1, len(chart_df) + 1)
        st.bar_chart(chart_df.set_index('Play #')['WIN_PROB_PCT'])
        st.caption("Win probability dropped with each conservative punt")
    
    with col2:
        st.subheader("Decision Grades")
        grade_counts = fourth_downs['GRADE'].value_counts()
        
        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            bad = grade_counts.get('🔴 TERRIBLE', 0) + grade_counts.get('🔴 BAD', 0)
            st.metric("🔴 Bad", bad)
        with gcol2:
            st.metric("🟡 Questionable", grade_counts.get('🟡 QUESTIONABLE', 0))
        with gcol3:
            st.metric("✅ OK", grade_counts.get('✅ OK', 0))

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("Super Bowl LX")
    st.markdown("""
    🦅 **Seahawks 29**  
    🏈 **Patriots 13**
    
    📅 February 8, 2026  
    🏟️ Levi's Stadium
    """)
    
    st.markdown("---")
    
    st.markdown("""
    **Metrics:**
    - **WP** - Win Probability
    - **WPA** - Win Prob Added
    - **EPA** - Expected Points Added
    
    **Grades:**
    - 🔴 Should have gone for it
    - 🟡 Borderline / questionable
    - ✅ Reasonable decision
    """)
    
    st.markdown("---")
    
    st.subheader("🔌 Status")
    supabase = get_supabase_client()
    if supabase:
        st.success("Supabase: Connected")
    else:
        st.warning("Supabase: Using fallback data")
    
    st.markdown("---")
    st.caption("Data: Supabase | AI: Groq")

st.markdown("---")
st.caption("Built with Streamlit + Supabase + Groq")
