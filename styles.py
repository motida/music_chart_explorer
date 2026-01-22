import streamlit as st


def apply_retro_style():
    """
    Applies a retro CRT monitor style to the Streamlit app.
    """
    st.markdown(
        """
        <style>
        /* Import Retro Font (VT323) */
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        /* Main App Background - CRT Black */
        .stApp {
            background-color: #050505;
            color: #33ff00; /* Bright green text */
            font-family: 'VT323', monospace;
        }

        /* Scanline Effect Overlay 
           Creates a subtle visual effect resembling a CRT monitor's scanlines.
        */
        .stApp::before {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                        linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none; /* Allows clicks to pass through the overlay */
        }

        /* Headers with Neon Glow */
        h1, h2, h3 {
            color: #33ff00 !important; /* Green */
            font-family: 'VT323', monospace !important;
            text-transform: uppercase;
            text-shadow: 2px 2px #005500; /* Dark green shadow for depth */
            letter-spacing: 2px;
        }
        
        h1 {
            border-bottom: 2px dashed #33ff00;
            padding-bottom: 10px;
        }

        /* Sidebar in Terminal Gray */
        [data-testid="stSidebar"] {
            background-color: #0a0a0a !important;
            border-right: 2px solid #33ff00;
        }
        
        [data-testid="stSidebar"] * {
            font-family: 'VT323', monospace !important;
            color: #33ff00 !important;
        }

        /* Retro Action Button */
        div.stButton > button:first-child {
            background-color: #000000 !important;
            color: #33ff00 !important;
            border: 2px solid #33ff00 !important;
            border-radius: 0px !important; /* Sharp corners */
            padding: 0.5rem 1rem !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.5rem !important;
            text-transform: uppercase;
            box-shadow: 4px 4px 0px #005500 !important; /* 3D effect */
            transition: all 0.1s;
            width: 100%;
        }

        div.stButton > button:hover {
            transform: translate(2px, 2px); /* "Pushed in" effect */
            box-shadow: 2px 2px 0px #005500 !important;
            background-color: #33ff00 !important;
            color: #000000 !important; /* Invert colors on hover */
        }
        
        /* Inputs - Console Style */
        .stTextInput>div>div>input {
            background-color: #000000 !important;
            color: #33ff00 !important;
            border: 2px solid #33ff00 !important;
            border-radius: 0px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.2rem;
        }
        
        .stTextInput>div>div>input::placeholder {
            color: #007700 !important;
            opacity: 0.7;
        }
        
        /* Glow effect on focus */
        .stTextInput>div>div>input:focus {
            box-shadow: 0 0 15px #33ff00 !important;
            border-color: #33ff00 !important;
        }

        /* Selectbox */
        .stSelectbox>div>div {
             background-color: #000000 !important;
             color: #33ff00 !important;
             border: 2px solid #33ff00 !important;
             border-radius: 0px !important;
             font-family: 'VT323', monospace !important;
        }

        /* Dataframes - Green Borders */
        .stDataFrame {
            border: 1px dashed #33ff00;
            font-family: 'VT323', monospace !important;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #33ff00 !important;
            font-family: 'VT323', monospace !important;
            text-shadow: 0px 0px 10px #005500;
        }
        
        [data-testid="stMetricLabel"] {
            color: #00cc00 !important;
            font-family: 'VT323', monospace !important;
        }
        
        /* Images */
        img {
            border: 1px solid #33ff00;
            box-shadow: 4px 4px 0px #005500;
            opacity: 0.9;
        }
        
        /* Alerts */
        .stAlert {
            background-color: #050505;
            color: #33ff00;
            border: 1px solid #33ff00;
            font-family: 'VT323', monospace !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
