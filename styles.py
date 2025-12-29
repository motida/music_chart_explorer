import streamlit as st


def apply_retro_style():
    st.markdown(
        """
        <style>
        /* Retro Terminal/Arcade Theme */
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {
            background-color: #0a0a0a;
            color: #00ff41;
            font-family: 'VT323', monospace;
        }

        /* Scanline Effect */
        .stApp::before {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                        linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
        }

        /* Titles and Headers */
        h1, h2, h3 {
            color: #ff00ff !important;
            text-shadow: 3px 3px #00ffff;
            font-family: 'VT323', monospace !important;
            text-transform: uppercase;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #111 !important;
            border-right: 2px solid #00ff41;
        }

        /* Buttons */
        .stButton>button {
            border: 2px solid #00ff41 !important;
            background-color: #000 !important;
            color: #00ff41 !important;
            border-radius: 0px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.5rem !important;
            transition: 0.3s;
        }

        .stButton>button:hover {
            background-color: #00ff41 !important;
            color: #000 !important;
            box-shadow: 0 0 15px #00ff41;
        }

        /* Dataframe & Tables */
        .stDataFrame {
            border: 1px solid #00ff41;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #00ffff !important;
            font-size: 2.5rem !important;
        }

        /* Blinking Cursor Animation */
        @keyframes blink-shadow {
            0% { box-shadow: 0 0 0 #00ff41; }
            50% { box-shadow: 0 0 10px #00ff41; }
            100% { box-shadow: 0 0 0 #00ff41; }
        }

        /* Inputs */
        input {
            background-color: #111 !important;
            color: #00ff41 !important;
            border: 1px solid #00ff41 !important;
            caret-color: #00ff41 !important;
        }

        input:focus {
            animation: blink-shadow 2s infinite;
            outline: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
