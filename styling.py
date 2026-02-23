import streamlit as st


def scroll_to_top():
    st.components.v1.html(
        "<script>"
        "window.parent.document.querySelectorAll('[data-testid=\"stMain\"]').forEach(el => el.scrollTo(0,0));"
        "window.parent.document.querySelectorAll('.main').forEach(el => el.scrollTo(0,0));"
        "window.parent.scrollTo(0,0);"
        "</script>",
        height=0,
    )


BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] { font-family: 'DM Sans', sans-serif !important; }
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 80% 50% at 20% -10%, rgba(56,189,248,0.06) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 80% 110%, rgba(99,102,241,0.05) 0%, transparent 55%),
                linear-gradient(160deg, #070d1a 0%, #080e1c 40%, #050b16 100%) !important;
    min-height: 100vh;
}
h1, h2, h3, h4 { font-family: 'DM Sans', sans-serif !important; letter-spacing: -0.5px; }
[data-testid="stMain"] .block-container { padding-top: 2rem !important; max-width: 1200px !important; }
.main-title {
    text-align: center; color: #f8fafc; font-size: clamp(48px, 8vw, 72px);
    font-weight: 700; letter-spacing: -3px; margin-bottom: 0; line-height: 1;
    background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 50%, #64748b 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sub-title { text-align: center; color: #475569; font-size: 15px; font-weight: 400; letter-spacing: 0.3px; margin-bottom: 48px; margin-top: 8px; }
[data-testid="stForm"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(10,16,32,0.95) 100%) !important;
    backdrop-filter: blur(20px) !important; padding: 40px !important;
    border-radius: 20px !important; border: 1px solid rgba(148,163,184,0.08) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04) !important;
}
div[data-testid="stTextInputRootElement"] { background-color: transparent !important; }
div[data-baseweb="input"], div[data-baseweb="base-input"] {
    background-color: rgba(15,23,42,0.6) !important; border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important; transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    padding-right: 0 !important; gap: 0 !important; box-shadow: none !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within {
    background-color: rgba(15,23,42,0.8) !important; border-color: rgba(56,189,248,0.5) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}
input { padding-left: 15px !important; color: #e2e8f0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; }
input::placeholder { color: #334155 !important; }
div[data-testid="stDateInput"] > div {
    background-color: rgba(15,23,42,0.6) !important; border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important; box-shadow: none !important; min-height: 42px !important; overflow: hidden !important;
}
div[data-baseweb="select"] > div:first-child {
    background-color: rgba(15,23,42,0.6) !important; border: 1px solid rgba(148,163,184,0.1) !important;
    border-radius: 10px !important; box-shadow: none !important;
}
div[data-baseweb="select"] > div:first-child:focus-within {
    border-color: rgba(56,189,248,0.5) !important; box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}
button[kind="primaryFormSubmit"], button[kind="secondaryFormSubmit"] {
    height: 48px !important; border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; letter-spacing: 0.2px !important; transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d1a 0%, #060b18 100%) !important;
    border-right: 1px solid rgba(148,163,184,0.07) !important;
}
[data-testid="stSidebar"] .stMarkdown p { font-family: 'DM Sans', sans-serif !important; color: #475569 !important; font-size: 13px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
    border: 1px solid transparent !important; border-radius: 10px !important; padding: 9px 14px !important;
    margin-bottom: 3px !important; color: #475569 !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important; font-weight: 400 !important; transition: all 0.15s ease !important; letter-spacing: 0.1px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
    border-color: rgba(56,189,248,0.15) !important; color: #94a3b8 !important; background: rgba(56,189,248,0.04) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
    border-color: rgba(56,189,248,0.25) !important; background: rgba(56,189,248,0.08) !important; color: #e2e8f0 !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
button[data-testid="stNumberInputStepDown"], button[data-testid="stNumberInputStepUp"] { display: none !important; }
div[data-baseweb="input"] > div:not(:has(input)):not(:has(button)):not(:has(svg)) { display: none !important; }
[data-testid="InputInstructions"], [data-testid="stInputInstructions"],
div[class*="InputInstructions"], div[class*="stInputInstructions"] {
    display: none !important; visibility: hidden !important; height: 0 !important; overflow: hidden !important; position: absolute !important;
}
button, [data-testid="stPopover"] button, div[data-baseweb="select"], div[data-baseweb="select"] *,
div[data-testid="stDateInput"], [data-testid="stSelectbox"] * { cursor: pointer !important; }
div[data-testid="stDialog"] > div, div[role="dialog"] {
    position: fixed !important; top: 50% !important; left: 50% !important;
    transform: translate(-50%, -50%) !important; margin: 0 !important; max-height: 90vh !important; overflow-y: auto !important;
    background: linear-gradient(145deg, #0d1729, #0a1020) !important;
    border: 1px solid rgba(148,163,184,0.1) !important; border-radius: 18px !important; box-shadow: 0 40px 80px rgba(0,0,0,0.6) !important;
}
div[data-testid="stDialog"] { display: flex !important; align-items: center !important; justify-content: center !important; }
hr { border-color: rgba(148,163,184,0.08) !important; margin: 24px 0 !important; }
[data-testid="stMarkdownContainer"] h3 { font-size: 15px !important; font-weight: 600 !important; color: #64748b !important; letter-spacing: 0.5px !important; text-transform: uppercase !important; }
[data-testid="stAlert"] { border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; }
[data-testid="stExpander"] { border: 1px solid rgba(148,163,184,0.08) !important; border-radius: 12px !important; background: rgba(10,16,32,0.5) !important; }
</style>
"""


def inject_base_css():
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def inject_theme(t):
    st.markdown(f"""<style>
    [data-testid="stAppViewContainer"] {{
        background: radial-gradient(ellipse 80% 50% at 20% -10%, {t['grad1']} 0%, transparent 60%),
                    radial-gradient(ellipse 60% 40% at 80% 110%, {t['grad2']} 0%, transparent 55%),
                    linear-gradient(160deg, {t['bg1']} 0%, {t['bg2']} 40%, {t['bg3']} 100%) !important;
    }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, {t['bg1']} 0%, {t['bg3']} 100%) !important; }}
    button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="baseButton-primary"],
    div[data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['accent2']}) !important; border: none !important;
        color: #ffffff !important; box-shadow: 0 4px 15px {t['primary']}40 !important; transition: all 0.2s ease !important;
    }}
    button[kind="secondary"], [data-testid="baseButton-secondary"] {{
        background: rgba(255,255,255,0.04) !important; border: 1px solid {t['primary']}30 !important;
        color: {t['primary']} !important; transition: all 0.2s ease !important;
    }}
    [data-testid="stDownloadButton"] > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['accent2']}) !important;
        border: none !important; color: #ffffff !important; box-shadow: 0 4px 15px {t['primary']}40 !important;
    }}
    </style>""", unsafe_allow_html=True)


def section_header(title, subtitle=""):
    sub = (
        f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin:2px 0 20px 0;'>{subtitle}</p>"
        if subtitle else "<div style='margin-bottom:20px;'></div>"
    )
    st.markdown(
        f"<p style='font-family:DM Mono,monospace;color:#475569;font-size:10px;font-weight:500;"
        f"letter-spacing:1.5px;text-transform:uppercase;margin:0 0 4px 0;'>{title}</p>{sub}",
        unsafe_allow_html=True,
    )
