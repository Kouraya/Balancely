# ============================================================
#  Balancely — Persönliche Finanzverwaltung  v4
# ============================================================

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib
import datetime
import re
import smtplib
import random
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

# ============================================================
#  Hilfsfunktionen
# ============================================================

def make_hashes(text): return hashlib.sha256(str.encode(text)).hexdigest()

def check_password_strength(pw):
    if len(pw) < 6: return False, "Mindestens 6 Zeichen erforderlich."
    if not re.search(r"[a-z]", pw): return False, "Mindestens ein Kleinbuchstabe erforderlich."
    if not re.search(r"[A-Z]", pw): return False, "Mindestens ein Großbuchstabe erforderlich."
    return True, ""

def is_valid_email(e): return bool(re.match(r"[^@]+@[^@]+\.[^@]+", e))
def generate_code(): return str(random.randint(100000, 999999))
def is_verified(v):
    try: return float(v) >= 1.0
    except: return str(v).strip().lower() in ('true','1','yes')

def format_timestamp(ts_str, datum_str):
    now = datetime.datetime.now(); today = now.date()
    try:
        ts = datetime.datetime.strptime(str(ts_str).strip(), "%Y-%m-%d %H:%M")
        uhr = ts.strftime("%H:%M")
        if ts.date() == today: return f"heute {uhr}"
        if ts.date() == today - datetime.timedelta(days=1): return f"gestern {uhr}"
        return ts.strftime("%d.%m.%Y %H:%M")
    except:
        try:
            d = datetime.date.fromisoformat(str(datum_str))
            if d == today: return "heute"
            if d == today - datetime.timedelta(days=1): return "gestern"
            return d.strftime("%d.%m.%Y")
        except: return str(datum_str)

def find_row_mask(df, row):
    return (
        (df['user'] == row['user']) &
        (df['datum'].astype(str) == str(row['datum'])) &
        (pd.to_numeric(df['betrag'], errors='coerce') == pd.to_numeric(row['betrag'], errors='coerce')) &
        (df['kategorie'] == row['kategorie']) &
        (~df['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0']))
    )

def send_email(to_email, subject, html_content):
    try:
        sender = st.secrets["email"]["sender"]; password = st.secrets["email"]["password"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject; msg["From"] = f"Balancely ⚖️ <{sender}>"; msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password); s.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email-Fehler: {e}"); return False

def email_html(text, code):
    return f"""<html><body style="font-family:sans-serif;background:#020617;color:#f1f5f9;padding:40px;">
    <div style="max-width:480px;margin:auto;background:#0f172a;border-radius:16px;padding:40px;border:1px solid #1e293b;">
        <h2 style="color:#38bdf8;">Balancely ⚖️</h2><p>{text}</p>
        <div style="margin:24px 0;padding:20px;background:#1e293b;border-radius:12px;text-align:center;
                    font-size:36px;font-weight:800;letter-spacing:8px;color:#38bdf8;">{code}</div>
        <p style="color:#94a3b8;font-size:13px;">Dieser Code ist 10 Minuten gültig.<br>
        Falls du diese Anfrage nicht gestellt hast, ignoriere diese Email.</p>
    </div></body></html>"""

# ============================================================
#  Konstanten
# ============================================================

DEFAULT_CATS = {
    "Einnahme": ["💼 Gehalt","🎁 Bonus","🛒 Verkauf","📈 Investitionen","🏠 Miete (Einnahme)"],
    "Ausgabe":  ["🍔 Essen","🏠 Miete","🎮 Freizeit","🚗 Transport","🛍️ Shopping",
                 "💊 Gesundheit","📚 Bildung","⚡ Strom & Gas"],
    "Depot":    ["📦 ETF","📊 Aktien","🪙 Krypto","🏦 Tagesgeld","💎 Sonstiges"],
}

THEMES = {
    'Ocean Blue':    {'primary':'#38bdf8','bg1':'#070d1a','bg2':'#080e1c','bg3':'#050b16',
                      'grad1':'rgba(56,189,248,0.06)','grad2':'rgba(99,102,241,0.05)',
                      'accent':'#0ea5e9','accent2':'#2563eb'},
    'Emerald Green': {'primary':'#34d399','bg1':'#061510','bg2':'#071812','bg3':'#051110',
                      'grad1':'rgba(52,211,153,0.07)','grad2':'rgba(16,185,129,0.05)',
                      'accent':'#10b981','accent2':'#059669'},
    'Deep Purple':   {'primary':'#a78bfa','bg1':'#0d0a1a','bg2':'#100c1e','bg3':'#08061a',
                      'grad1':'rgba(167,139,250,0.07)','grad2':'rgba(139,92,246,0.05)',
                      'accent':'#8b5cf6','accent2':'#7c3aed'},
}

CURRENCY_SYMBOLS = {'EUR':'€','CHF':'CHF','USD':'$','GBP':'£','JPY':'¥','SEK':'kr','NOK':'kr','DKK':'kr'}
TOPF_PALETTE     = ["#38bdf8","#4ade80","#a78bfa","#fb923c","#f472b6","#34d399","#facc15","#60a5fa"]
PALETTE_AUS      = ["#ff0000","#ff5232","#ff7b5a","#ff9e81","#ffbfaa","#ffdfd4","#dc2626","#b91c1c","#991b1b","#7f1d1d"]
PALETTE_EIN      = ["#008000","#469536","#6eaa5e","#93bf85","#b7d5ac","#dbead5","#2d7a2d","#4a9e4a","#5cb85c","#80c780"]
PALETTE_DEP      = ["#0000ff","#1e0bd0","#2510a3","#241178","#1f104f","#19092e","#2563eb","#1d4ed8","#1e40af","#1e3a8a"]
TYPE_COLORS      = {'Einnahme':'#4ade80','Depot':'#38bdf8','Spartopf':'#a78bfa'}

# ============================================================
#  Session State Init
# ============================================================

_DEFAULTS = {
    'logged_in':False,'user_name':"",'auth_mode':'login','t_type':'Ausgabe',
    'pending_user':{},'verify_code':"",'verify_expiry':None,
    'reset_email':"",'reset_code':"",'reset_expiry':None,
    'edit_idx':None,'show_new_cat':False,'new_cat_typ':'Ausgabe','_last_menu':"",
    'edit_cat_data':None,'delete_cat_data':None,
    'dash_month_offset':0,'dash_selected_aus':None,'dash_selected_ein':None,
    'dash_selected_cat':None,'dash_selected_typ':None,'dash_selected_color':None,
    'analysen_zeitraum':'Monatlich','analysen_month_offset':0,
    'heatmap_month_offset':0,
    'topf_edit_data':None,'topf_delete_id':None,'topf_delete_name':None,
    'settings_tab':'Profil',
    'email_verify_code':"",'email_verify_expiry':None,'email_verify_new':"",
    'theme':'Ocean Blue',
    'confirm_reset':False,'confirm_delete_account':False,
    'tx_page':0,'tx_search':"",
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

conn = st.connection("gsheets", type=GSheetsConnection)

# ============================================================
#  GSheet Cache
# ============================================================

def _gs_read(ws):
    k = f"_gs_cache_{ws}"
    if k not in st.session_state:
        st.session_state[k] = conn.read(worksheet=ws, ttl=0)
    return st.session_state[k].copy()

def _gs_update(ws, df):
    conn.update(worksheet=ws, data=df)
    st.session_state[f"_gs_cache_{ws}"] = df.copy()

def _gs_invalidate(*wss):
    for ws in wss: st.session_state.pop(f"_gs_cache_{ws}", None)

# ============================================================
#  Daten-Hilfsfunktionen
# ============================================================

def load_custom_cats(user, typ):
    try:
        df = _gs_read("categories")
        if df.empty or 'user' not in df.columns: return []
        return df[(df['user']==user)&(df['typ']==typ)]['kategorie'].tolist()
    except: return []

def save_custom_cat(user, typ, kategorie):
    try: df = _gs_read("categories")
    except: df = pd.DataFrame(columns=['user','typ','kategorie'])
    _gs_update("categories", pd.concat([df, pd.DataFrame([{'user':user,'typ':typ,'kategorie':kategorie}])], ignore_index=True))

def delete_custom_cat(user, typ, kategorie):
    try:
        df = _gs_read("categories")
        _gs_update("categories", df[~((df['user']==user)&(df['typ']==typ)&(df['kategorie']==kategorie))])
    except: pass

def update_custom_cat(user, typ, old_label, new_label):
    try:
        df = _gs_read("categories")
        df.loc[(df['user']==user)&(df['typ']==typ)&(df['kategorie']==old_label),'kategorie'] = new_label
        _gs_update("categories", df)
    except: pass

def load_goal(user):
    try:
        df = _gs_read("goals")
        if df.empty or 'user' not in df.columns: return 0.0
        row = df[df['user']==user]
        return float(row.iloc[-1].get('sparziel',0) or 0) if not row.empty else 0.0
    except: return 0.0

def save_goal(user, goal):
    try: df = _gs_read("goals")
    except: df = pd.DataFrame(columns=['user','sparziel'])
    if 'user' not in df.columns: df = pd.DataFrame(columns=['user','sparziel'])
    mask = df['user']==user
    if mask.any(): df.loc[mask,'sparziel'] = goal
    else: df = pd.concat([df, pd.DataFrame([{'user':user,'sparziel':goal}])], ignore_index=True)
    _gs_update("goals", df)

def load_user_settings(user):
    try:
        df = _gs_read("settings")
        if df.empty or 'user' not in df.columns: return {}
        row = df[df['user']==user]
        if row.empty: return {}
        r = row.iloc[-1]
        return {'budget':float(r.get('budget',0) or 0),'currency':str(r.get('currency','EUR') or 'EUR'),
                'avatar_url':str(r.get('avatar_url','') or ''),'theme':str(r.get('theme','Ocean Blue') or 'Ocean Blue'),
                'last_username_change':str(r.get('last_username_change','') or '')}
    except: return {}

def save_user_settings(user, **kwargs):
    try: df = _gs_read("settings")
    except: df = pd.DataFrame(columns=['user','budget','currency','avatar_url','theme'])
    if 'user' not in df.columns: df = pd.DataFrame(columns=['user','budget','currency','avatar_url','theme'])
    mask = df['user']==user
    if mask.any():
        for k,v in kwargs.items(): df.loc[mask,k] = v
    else:
        row_data = {'user':user,'budget':0,'currency':'EUR','avatar_url':'','theme':'Ocean Blue'}
        row_data.update(kwargs)
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
    _gs_update("settings", df)

# ── Daueraufträge ────────────────────────────────────────────

def load_dauerauftraege(user):
    try:
        df = _gs_read("dauerauftraege")
        if df.empty or 'user' not in df.columns: return []
        result = []
        for _, r in df[df['user']==user].iterrows():
            if str(r.get('deleted','')).strip().lower() in ('true','1','1.0'): continue
            result.append({'id':str(r.get('id','')),'name':str(r.get('name','')),'betrag':float(r.get('betrag',0) or 0),
                           'typ':str(r.get('typ','Ausgabe')),'kategorie':str(r.get('kategorie','')),'aktiv':str(r.get('aktiv','True'))})
        return result
    except: return []

def save_dauerauftrag(user, name, betrag, typ, kategorie):
    try: df = _gs_read("dauerauftraege")
    except: df = pd.DataFrame(columns=['user','id','name','betrag','typ','kategorie','aktiv','deleted'])
    new_id = f"{user}_{int(time.time())}"
    new_row = pd.DataFrame([{'user':user,'id':new_id,'name':name,'betrag':betrag,'typ':typ,'kategorie':kategorie,'aktiv':'True','deleted':''}])
    _gs_update("dauerauftraege", pd.concat([df, new_row], ignore_index=True))

def delete_dauerauftrag(user, da_id):
    try:
        df = _gs_read("dauerauftraege")
        df.loc[(df['user']==user)&(df['id']==da_id),'deleted'] = 'True'
        _gs_update("dauerauftraege", df)
    except: pass

def apply_dauerauftraege(user):
    try:
        das = load_dauerauftraege(user)
        if not das: return 0
        today = datetime.date.today()
        target_date = today.replace(day=1)
        df_t = _gs_read("transactions")
        booked = 0
        for da in das:
            if da['aktiv'] != 'True': continue
            already = df_t[
                (df_t['user']==user) &
                (df_t['notiz']==f"⚙️ Dauerauftrag: {da['name']}") &
                (df_t['datum'].astype(str).str.startswith(target_date.strftime('%Y-%m')))
            ] if not df_t.empty and 'user' in df_t.columns else pd.DataFrame()
            if not already.empty: continue
            betrag_save = da['betrag'] if da['typ'] in ('Einnahme','Depot') else -da['betrag']
            new_row = pd.DataFrame([{
                'user':user,'datum':str(target_date),
                'timestamp':datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                'typ':da['typ'],'kategorie':da['kategorie'],'betrag':betrag_save,
                'notiz':f"⚙️ Dauerauftrag: {da['name']}",'deleted':''
            }])
            df_t = pd.concat([df_t, new_row], ignore_index=True)
            booked += 1
        if booked > 0: _gs_update("transactions", df_t)
        return booked
    except: return 0

# ── Spartöpfe ────────────────────────────────────────────────

def load_toepfe(user):
    try:
        df = _gs_read("toepfe")
        if df.empty or 'user' not in df.columns: return []
        result = []
        for _, r in df[df['user']==user].iterrows():
            if str(r.get('deleted','')).strip().lower() in ('true','1','1.0'): continue
            result.append({'id':str(r.get('id','')),'name':str(r.get('name','')),'ziel':float(r.get('ziel',0) or 0),
                           'gespart':float(r.get('gespart',0) or 0),'emoji':str(r.get('emoji','🪣')),'farbe':str(r.get('farbe','#38bdf8'))})
        return result
    except: return []

def save_topf(user, name, ziel, emoji):
    try: df = _gs_read("toepfe")
    except: df = pd.DataFrame(columns=['user','id','name','ziel','gespart','emoji','farbe','deleted'])
    cnt = len(df[df['user']==user]) if not df.empty and 'user' in df.columns else 0
    new_row = pd.DataFrame([{'user':user,'id':f"{user}_{int(time.time())}","name":name,'ziel':ziel,'gespart':0,
                              'emoji':emoji,'farbe':TOPF_PALETTE[cnt%len(TOPF_PALETTE)],'deleted':''}])
    _gs_update("toepfe", pd.concat([df, new_row], ignore_index=True))

def update_topf_gespart(user, topf_id, topf_name, delta):
    try:
        df = _gs_read("toepfe"); mask = (df['user']==user)&(df['id']==topf_id)
        if mask.any():
            df.loc[mask,'gespart'] = max(0, float(df.loc[mask,'gespart'].values[0] or 0)+delta)
            _gs_update("toepfe", df)
    except: pass
    try:
        df_t = _gs_read("transactions")
        new_row = pd.DataFrame([{"user":user,"datum":str(datetime.date.today()),
            "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"typ":"Spartopf",
            "kategorie":f"🪣 {topf_name}","betrag":(-1 if delta>0 else 1)*abs(delta),
            "notiz":f"{'↓' if delta>0 else '↑'} {topf_name}",'deleted':''}])
        _gs_update("transactions", pd.concat([df_t, new_row], ignore_index=True))
    except: pass

def delete_topf(user, topf_id):
    try:
        df = _gs_read("toepfe")
        df.loc[(df['user']==user)&(df['id']==topf_id),'deleted'] = 'True'
        _gs_update("toepfe", df)
    except: pass

def update_topf_meta(user, topf_id, name, ziel, emoji):
    try:
        df = _gs_read("toepfe"); mask = (df['user']==user)&(df['id']==topf_id)
        if mask.any():
            df.loc[mask,['name','ziel','emoji']] = [name, ziel, emoji]
            _gs_update("toepfe", df)
    except: pass

# ============================================================
#  CSS + Theme
# ============================================================

st.markdown("""
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
    box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04) !important;
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
""", unsafe_allow_html=True)

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
    sub = (f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin:2px 0 20px 0;'>{subtitle}</p>"
           if subtitle else "<div style='margin-bottom:20px;'></div>")
    st.markdown(f"<p style='font-family:DM Mono,monospace;color:#475569;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 4px 0;'>{title}</p>{sub}", unsafe_allow_html=True)

# ============================================================
#  Dialoge
# ============================================================

@st.dialog("➕ Neue Kategorie")
def new_category_dialog():
    typ = st.session_state.get('new_cat_typ','Ausgabe')
    st.markdown(f"<p style='color:#64748b;font-size:13px;margin-bottom:20px;font-family:DM Sans,sans-serif;'>Für Typ: <span style='color:#38bdf8;font-weight:500;'>{typ}</span></p>", unsafe_allow_html=True)
    nc1, nc2 = st.columns([1,3])
    with nc1: new_emoji = st.text_input("Emoji", placeholder="🎵", max_chars=4)
    with nc2: new_name  = st.text_input("Name", placeholder="z.B. Musik")
    nc_typ = st.selectbox("Typ", ["Ausgabe","Einnahme","Depot"], index=["Ausgabe","Einnahme","Depot"].index(typ) if typ in ["Ausgabe","Einnahme","Depot"] else 0)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip(): st.error("Bitte einen Namen eingeben.")
            else:
                label = f"{new_emoji.strip()} {new_name.strip()}" if new_emoji.strip() else new_name.strip()
                existing = load_custom_cats(st.session_state['user_name'], nc_typ) + DEFAULT_CATS.get(nc_typ,[])
                if label in existing: st.error("Kategorie existiert bereits.")
                else:
                    save_custom_cat(st.session_state['user_name'], nc_typ, label)
                    st.session_state['show_new_cat'] = False; st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['show_new_cat'] = False; st.rerun()

@st.dialog("✏️ Kategorie bearbeiten")
def edit_category_dialog():
    data = st.session_state.get('edit_cat_data')
    if not data: st.rerun(); return
    old_label, typ, user = data['old_label'], data['typ'], data['user']
    parts = old_label.split(' ',1)
    init_emoji = parts[0] if len(parts)==2 and len(parts[0])<=4 else ''
    init_name  = parts[1] if len(parts)==2 and len(parts[0])<=4 else old_label
    nc1, nc2 = st.columns([1,3])
    with nc1: new_emoji = st.text_input("Emoji", value=init_emoji, max_chars=4)
    with nc2: new_name  = st.text_input("Name", value=init_name)
    new_typ = st.selectbox("Typ", ["Ausgabe","Einnahme","Depot"], index=["Ausgabe","Einnahme","Depot"].index(typ) if typ in ["Ausgabe","Einnahme","Depot"] else 0)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Speichern", use_container_width=True, type="primary"):
            if not new_name.strip(): st.error("Bitte einen Namen eingeben.")
            else:
                new_label = f"{new_emoji.strip()} {new_name.strip()}" if new_emoji.strip() else new_name.strip()
                existing  = load_custom_cats(user, new_typ) + DEFAULT_CATS.get(new_typ,[])
                if new_label != old_label and new_label in existing: st.error("Kategorie existiert bereits.")
                else:
                    if new_typ != typ: delete_custom_cat(user, typ, old_label); save_custom_cat(user, new_typ, new_label)
                    else: update_custom_cat(user, typ, old_label, new_label)
                    st.session_state['edit_cat_data'] = None; st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['edit_cat_data'] = None; st.rerun()

@st.dialog("Kategorie löschen")
def confirm_delete_cat():
    data = st.session_state.get('delete_cat_data')
    if not data: st.rerun(); return
    st.markdown(f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:8px;'>Kategorie wirklich löschen?</p><p style='color:#64748b;font-size:14px;'>{data['label']}</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Löschen", use_container_width=True, type="primary"):
            delete_custom_cat(data['user'], data['typ'], data['label'])
            st.session_state['delete_cat_data'] = None; st.rerun()
    with c2:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state['delete_cat_data'] = None; st.rerun()

@st.dialog("Eintrag löschen")
def confirm_delete(row_data):
    st.markdown(f"<p style='color:#e2e8f0;font-size:15px;margin-bottom:6px;'>Eintrag wirklich löschen?</p><p style='color:#475569;font-size:13px;'>{row_data['datum']} · {row_data['betrag_anzeige']} · {row_data['kategorie']}</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Löschen", use_container_width=True, type="primary"):
            df_all = _gs_read("transactions")
            if 'deleted' not in df_all.columns: df_all['deleted'] = ''
            mask = (
                (df_all['user']==row_data['user']) & (df_all['datum'].astype(str)==str(row_data['datum'])) &
                (pd.to_numeric(df_all['betrag'],errors='coerce')==pd.to_numeric(row_data['betrag'],errors='coerce')) &
                (df_all['kategorie']==row_data['kategorie']) &
                (~df_all['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0']))
            )
            idx = df_all[mask].index
            if len(idx)>0:
                df_all.loc[idx[0],'deleted'] = 'True'; _gs_update("transactions", df_all)
                st.session_state['edit_idx'] = None; st.rerun()
            else: st.error("Eintrag nicht gefunden.")
    with c2:
        if st.button("Abbrechen", use_container_width=True): st.rerun()

# ============================================================
#  APP — Eingeloggt
# ============================================================

if st.session_state['logged_in']:
    _theme_name    = st.session_state.get('theme','Ocean Blue')
    _t             = THEMES.get(_theme_name, THEMES['Ocean Blue'])
    _user_settings = load_user_settings(st.session_state['user_name'])
    _currency_sym  = CURRENCY_SYMBOLS.get(_user_settings.get('currency','EUR'),'€')

    inject_theme(_t)

    if _user_settings.get('theme') and _user_settings['theme'] != st.session_state.get('theme'):
        st.session_state['theme'] = _user_settings['theme']

    if datetime.date.today().day == 1:
        booked = apply_dauerauftraege(st.session_state['user_name'])
        if booked > 0:
            _gs_invalidate("transactions")
            st.toast(f"✅ {booked} Dauerauftrag/-aufträge gebucht", icon="⚙️")

    # ── Sidebar ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f"<div style='padding:8px 0 16px 0;'><span style='font-family:DM Sans,sans-serif;font-size:20px;font-weight:600;color:#e2e8f0;letter-spacing:-0.5px;'>Balancely</span>"
            f"<span style='color:{_t['primary']};font-size:20px;'> ⚖️</span></div>", unsafe_allow_html=True)

        _avatar = _user_settings.get('avatar_url','')
        _initials = st.session_state['user_name'][:2].upper()
        if _avatar and _avatar.startswith('http'):
            avatar_html = f"<img src='{_avatar}' style='width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid {_t['primary']}40;'>"
        else:
            avatar_html = f"<div style='width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,{_t['accent']},{_t['accent2']});display:flex;align-items:center;justify-content:center;font-family:DM Sans,sans-serif;font-size:13px;font-weight:600;color:#fff;flex-shrink:0;'>{_initials}</div>"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:20px;'>{avatar_html}"
            f"<div><div style='font-family:DM Sans,sans-serif;font-size:13px;color:#e2e8f0;font-weight:500;'>{st.session_state['user_name']}</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>{_user_settings.get('currency','EUR')} · {_theme_name}</div></div></div>",
            unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        menu = st.radio("Navigation", ["📈 Dashboard","💸 Transaktionen","📂 Analysen","🪣 Spartöpfe","⚙️ Einstellungen"], label_visibility="collapsed")
        st.markdown("<div style='height:28vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout ➜", use_container_width=True, type="secondary"):
            for k in [k for k in st.session_state if k.startswith("_gs_cache_")]: del st.session_state[k]
            st.session_state['logged_in'] = False; st.rerun()

    if not st.session_state.pop('_dialog_just_opened', False):
        st.session_state['show_new_cat'] = False
        st.session_state['edit_cat_data'] = None
        st.session_state['delete_cat_data'] = None

    if menu != st.session_state.get('_last_menu', menu):
        st.session_state['edit_idx'] = None
    st.session_state['_last_menu'] = menu

    # ============================================================
    #  DASHBOARD
    # ============================================================
    if menu == "📈 Dashboard":
        import plotly.graph_objects as go

        now = datetime.datetime.now()
        st.markdown(
            f"<div style='margin-bottom:36px;margin-top:16px;'>"
            f"<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>Deine Übersicht, {st.session_state['user_name']}! ⚖️</h1>"
            f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>Monatliche Finanzübersicht</p></div>", unsafe_allow_html=True)

        offset  = st.session_state.get('dash_month_offset',0)
        m_total = now.year*12 + (now.month-1) + offset
        t_year, t_month_idx = divmod(m_total,12); t_month = t_month_idx+1
        monat_label = datetime.date(t_year, t_month, 1).strftime("%B %Y")

        nav1, nav2, nav3 = st.columns([1,5,1])
        with nav1:
            if st.button("‹", use_container_width=True, key="dash_prev"):
                st.session_state['dash_month_offset'] -= 1
                st.session_state.update({'dash_selected_cat':None,'dash_selected_typ':None,'dash_selected_color':None}); st.rerun()
        with nav2:
            st.markdown(f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:14px;font-weight:500;color:#64748b;padding:6px 0;'>{monat_label}</div>", unsafe_allow_html=True)
        with nav3:
            if st.button("›", use_container_width=True, key="dash_next", disabled=(offset>=0)):
                st.session_state['dash_month_offset'] += 1
                st.session_state.update({'dash_selected_cat':None,'dash_selected_typ':None,'dash_selected_color':None}); st.rerun()

        try:
            df_t = _gs_read("transactions")
            if "user" not in df_t.columns:
                st.info("Noch keine Daten vorhanden.")
            else:
                alle = df_t[df_t["user"]==st.session_state["user_name"]].copy()
                if "deleted" in alle.columns:
                    alle = alle[~alle["deleted"].astype(str).str.strip().str.lower().isin(["true","1","1.0"])]
                alle["datum_dt"] = pd.to_datetime(alle["datum"], errors="coerce")
                monat_df = alle[(alle["datum_dt"].dt.year==t_year)&(alle["datum_dt"].dt.month==t_month)].copy()

                if monat_df.empty:
                    st.markdown(f"<div style='text-align:center;padding:60px 20px;color:#334155;font-family:DM Sans,sans-serif;font-size:15px;'>Keine Buchungen im {monat_label}</div>", unsafe_allow_html=True)
                else:
                    monat_df["betrag_num"] = pd.to_numeric(monat_df["betrag"], errors="coerce")
                    alle["betrag_num"]     = pd.to_numeric(alle["betrag"], errors="coerce")

                    ein           = monat_df[monat_df["typ"]=="Einnahme"]["betrag_num"].sum()
                    aus           = monat_df[monat_df["typ"]=="Ausgabe"]["betrag_num"].abs().sum()
                    dep_monat     = monat_df[monat_df["typ"]=="Depot"]["betrag_num"].abs().sum()
                    sp_netto      = monat_df[monat_df["typ"]=="Spartopf"]["betrag_num"].sum()
                    bank          = ein - aus - dep_monat + sp_netto
                    dep_gesamt    = alle[alle["typ"]=="Depot"]["betrag_num"].abs().sum()
                    topf_gesamt   = sum(t['gespart'] for t in load_toepfe(st.session_state["user_name"]))
                    networth      = bank + dep_gesamt + topf_gesamt

                    bank_color = "#e2e8f0" if bank>=0 else "#f87171"
                    nw_color   = "#4ade80" if networth>=0 else "#f87171"
                    bank_str   = f"{bank:,.2f} {_currency_sym}" if bank>=0 else f"-{abs(bank):,.2f} {_currency_sym}"
                    nw_str     = f"{networth:,.2f} {_currency_sym}" if networth>=0 else f"-{abs(networth):,.2f} {_currency_sym}"

                    if offset==0:
                        _budget = _user_settings.get('budget',0)
                        if _budget>0:
                            _bpct = min(aus/_budget*100,100)
                            _bcol = "#4ade80" if _bpct<60 else ("#facc15" if _bpct<85 else "#f87171")
                            _bem  = "🟢" if _bpct<60 else ("🟡" if _bpct<85 else "🔴")
                            st.markdown(
                                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:14px 18px;margin-bottom:16px;'>"
                                f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;'>"
                                f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{_bem} Monats-Budget</span>"
                                f"<span style='font-family:DM Mono,monospace;color:{_bcol};font-size:13px;font-weight:600;'>{aus:,.2f} / {_budget:,.2f} {_currency_sym} · {_bpct:.0f}%</span>"
                                f"</div><div style='background:rgba(30,41,59,0.8);border-radius:99px;height:6px;overflow:hidden;'>"
                                f"<div style='width:{_bpct:.0f}%;height:100%;background:{_bcol};border-radius:99px;'></div></div></div>", unsafe_allow_html=True)

                    if offset==0:
                        _goal = load_goal(st.session_state["user_name"])
                        _sp_einz = abs(monat_df[(monat_df["typ"]=="Spartopf")&(monat_df["betrag_num"]<0)]["betrag_num"].sum())
                        if _goal>0:
                            _effektiv = bank + _sp_einz
                            if _effektiv < _goal:
                                _fehl = _goal - _effektiv
                                st.markdown(
                                    f"<div style='background:linear-gradient(135deg,rgba(251,113,133,0.08),rgba(239,68,68,0.05));border:1px solid rgba(248,113,113,0.25);border-left:3px solid #f87171;border-radius:14px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px;'>"
                                    f"<span style='font-size:22px;'>⚠️</span><div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#fca5a5;font-weight:600;font-size:14px;margin-bottom:2px;'>Du liegst {_fehl:,.2f} {_currency_sym} unter deinem Sparziel</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;'>Ziel: {_goal:,.2f} {_currency_sym} · Gespart: {_effektiv:,.2f} {_currency_sym}</div>"
                                    f"</div></div>", unsafe_allow_html=True)
                            else:
                                _ueber = _effektiv - _goal
                                st.markdown(
                                    f"<div style='background:linear-gradient(135deg,rgba(74,222,128,0.05),rgba(34,197,94,0.03));border:1px solid rgba(74,222,128,0.2);border-left:3px solid #4ade80;border-radius:14px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px;'>"
                                    f"<span style='font-size:22px;'>✅</span><div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#86efac;font-weight:600;font-size:14px;margin-bottom:2px;'>Sparziel erreicht! +{_ueber:,.2f} {_currency_sym} Puffer</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;'>Gespart: {_effektiv:,.2f} {_currency_sym}</div>"
                                    f"</div></div>", unsafe_allow_html=True)

                    _sp_einz2 = abs(monat_df[(monat_df["typ"]=="Spartopf")&(monat_df["betrag_num"]<0)]["betrag_num"].sum())
                    dep_html = (f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(56,189,248,0.15);border-radius:16px;padding:20px 22px;'>"
                                f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Depot</div>"
                                f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:24px;font-weight:600;'>{dep_monat:,.2f} {_currency_sym}</div></div>") if dep_monat>0 else ""
                    topf_html = (f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(167,139,250,0.2);border-radius:16px;padding:20px 22px;'>"
                                 f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#7c3aed;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Spartöpfe</div>"
                                 f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
                                 f"<div style='font-family:DM Sans,sans-serif;color:#a78bfa;font-size:24px;font-weight:600;'>{_sp_einz2:,.2f} {_currency_sym}</div></div>") if _sp_einz2>0 else ""

                    st.markdown(
                        f"<div style='display:flex;gap:14px;margin:0 0 12px 0;flex-wrap:wrap;'>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Bankkontostand</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{bank_color};font-size:24px;font-weight:600;'>{bank_str}</div></div>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(56,189,248,0.12);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamtvermögen</div>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>Bank + Depot + Töpfe</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{nw_color};font-size:24px;font-weight:600;'>{nw_str}</div></div></div>"
                        f"<div style='display:flex;gap:14px;margin:0 0 28px 0;flex-wrap:wrap;'>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Einnahmen</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:24px;font-weight:600;'>+{ein:,.2f} {_currency_sym}</div></div>"
                        f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Ausgaben</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#f87171;font-size:24px;font-weight:600;'>-{aus:,.2f} {_currency_sym}</div></div>"
                        + dep_html + topf_html + "</div>", unsafe_allow_html=True)

                    ausg_df = monat_df[monat_df["typ"]=="Ausgabe"].copy(); ausg_df["betrag_num"] = ausg_df["betrag_num"].abs()
                    ein_df  = monat_df[monat_df["typ"]=="Einnahme"].copy()
                    dep_df  = monat_df[monat_df["typ"]=="Depot"].copy(); dep_df["betrag_num"] = pd.to_numeric(dep_df["betrag_num"],errors="coerce").abs()
                    ausg_grp = ausg_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num",ascending=False)
                    ein_grp  = ein_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num",ascending=False)
                    dep_grp  = dep_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num",ascending=False)

                    all_cats,all_vals,all_colors,all_types = [],[],[],[]
                    for i,(_,row) in enumerate(ein_grp.iterrows()):
                        all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_EIN[i%len(PALETTE_EIN)]); all_types.append("Einnahme")
                    for i,(_,row) in enumerate(ausg_grp.iterrows()):
                        all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_AUS[i%len(PALETTE_AUS)]); all_types.append("Ausgabe")
                    for i,(_,row) in enumerate(dep_grp.iterrows()):
                        all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
                        all_colors.append(PALETTE_DEP[i%len(PALETTE_DEP)]); all_types.append("Depot")

                    fig = go.Figure(go.Pie(
                        labels=all_cats, values=all_vals, hole=0.62,
                        marker=dict(colors=all_colors, line=dict(color="rgba(5,10,20,0.8)",width=2)),
                        textinfo="none", hoverinfo="none", direction="clockwise", sort=False, rotation=90))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                        margin=dict(t=20,b=20,l=20,r=20), height=380, autosize=True,
                        annotations=[
                            dict(text="BANK", x=0.5, y=0.62, showarrow=False, font=dict(size=10,color="#334155",family="DM Mono, monospace"), xref="paper", yref="paper"),
                            dict(text=f"<b>{bank_str}</b>", x=0.5, y=0.50, showarrow=False, font=dict(size=22,color=bank_color,family="DM Sans, sans-serif"), xref="paper", yref="paper"),
                            dict(text=f"+{ein:,.0f}  /  -{aus:,.0f} {_currency_sym}", x=0.5, y=0.38, showarrow=False, font=dict(size=11,color="#334155",family="DM Sans, sans-serif"), xref="paper", yref="paper"),
                        ])

                    chart_col, legend_col = st.columns([2,2])
                    with chart_col:
                        st.plotly_chart(fig, use_container_width=True, key="donut_combined")
                    with legend_col:
                        sel_cat   = st.session_state.get('dash_selected_cat')
                        sel_typ   = st.session_state.get('dash_selected_typ')
                        sel_color = st.session_state.get('dash_selected_color')
                        if sel_cat and sel_typ:
                            src_df = {"Ausgabe":ausg_df,"Einnahme":ein_df,"Depot":dep_df}.get(sel_typ, ausg_df)
                            detail = src_df[src_df["kategorie"]==sel_cat]
                            total_d = detail["betrag_num"].sum()
                            sign   = "−" if sel_typ=="Ausgabe" else "+"
                            rows_html = "".join(
                                f"<div style='display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);'>"
                                f"<div style='display:flex;align-items:center;gap:10px;'>"
                                f"<span style='font-family:DM Mono,monospace;color:#64748b;font-size:12px;'>{tr['datum_dt'].strftime('%d.%m.')}</span>"
                                + (f"<span style='color:#94a3b8;font-size:13px;'>{str(tr.get('notiz',''))}</span>" if str(tr.get('notiz','')).lower() not in ('nan','') else "")
                                + f"</div><span style='color:{sel_color};font-weight:600;font-size:13px;font-family:DM Mono,monospace;'>{sign}{tr['betrag_num']:,.2f} {_currency_sym}</span></div>"
                                for _,tr in detail.sort_values("datum_dt",ascending=False).iterrows())
                            if st.button("← Alle Kategorien", key="dash_back_btn"):
                                st.session_state.update({'dash_selected_cat':None,'dash_selected_typ':None,'dash_selected_color':None}); st.rerun()
                            st.markdown(
                                f"<div style='background:linear-gradient(145deg,rgba(13,23,41,0.95),rgba(10,16,30,0.98));border:1px solid {sel_color}30;border-top:2px solid {sel_color};border-radius:14px;padding:18px 20px;margin-top:10px;'>"
                                f"<div style='font-family:DM Mono,monospace;color:{sel_color};font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>{sel_typ}</div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-weight:600;font-size:16px;margin-bottom:4px;'>{sel_cat}</div>"
                                f"<div style='font-family:DM Mono,monospace;color:{sel_color};font-size:22px;font-weight:500;margin-bottom:18px;'>{sign}{total_d:,.2f} {_currency_sym}</div>"
                                f"{rows_html}</div>", unsafe_allow_html=True)
                        else:
                            TYP_CONFIG = {"Einnahme":("EINNAHMEN","#2b961f","+"),"Ausgabe":("AUSGABEN","#ff5232","−"),"Depot":("DEPOT","#2510a3","")}
                            available_types = list(dict.fromkeys(all_types))
                            if st.session_state.get('dash_legend_tab') not in available_types:
                                st.session_state['dash_legend_tab'] = available_types[0] if available_types else "Ausgabe"
                            active_tab_dash = st.session_state['dash_legend_tab']
                            tab_cols = st.columns(len(available_types))
                            for i,typ in enumerate(available_types):
                                lbl,_,_ = TYP_CONFIG.get(typ,(typ.upper(),"#64748b",""))
                                with tab_cols[i]:
                                    if st.button(lbl, key=f"dash_tab_{typ}", use_container_width=True, type="primary" if typ==active_tab_dash else "secondary"):
                                        st.session_state['dash_legend_tab'] = typ; st.rerun()
                            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                            _,color_active,sign_active = TYP_CONFIG.get(active_tab_dash,(active_tab_dash,"#64748b",""))
                            total_sum = sum(all_vals) if sum(all_vals)>0 else 1
                            for cat,val,color,typ in zip(all_cats,all_vals,all_colors,all_types):
                                if typ!=active_tab_dash: continue
                                col_legend, col_btn = st.columns([10,1])
                                with col_legend:
                                    st.markdown(
                                        f"<div style='display:flex;align-items:center;justify-content:space-between;padding:7px 8px;border-radius:8px;'>"
                                        f"<div style='display:flex;align-items:center;gap:10px;min-width:0;'>"
                                        f"<div style='width:7px;height:7px;border-radius:50%;background:{color};flex-shrink:0;'></div>"
                                        f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{cat}</span></div>"
                                        f"<div style='display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;'>"
                                        f"<span style='font-family:DM Mono,monospace;color:{color};font-weight:500;font-size:12px;'>{sign_active}{val:,.2f} {_currency_sym}</span>"
                                        f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>{val/total_sum*100:.0f}%</span>"
                                        f"</div></div>", unsafe_allow_html=True)
                                with col_btn:
                                    if st.button("›", key=f"legend_btn_{cat}_{typ}"):
                                        st.session_state.update({'dash_selected_cat':cat,'dash_selected_typ':typ,'dash_selected_color':color}); st.rerun()
        except Exception as e:
            st.warning(f"Verbindung wird hergestellt... ({e})")

    # ============================================================
    #  TRANSAKTIONEN
    # ============================================================
    elif menu == "💸 Transaktionen":
        user_name = st.session_state['user_name']
        t_type    = st.session_state['t_type']

        st.markdown(
            "<div style='margin-bottom:36px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>Buchungen &amp; Verlauf 🧾</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>Buchungen erfassen &amp; verwalten</p></div>",
            unsafe_allow_html=True)

        if st.session_state.get('show_new_cat'):    new_category_dialog()
        if st.session_state.get('edit_cat_data'):   edit_category_dialog()
        if st.session_state.get('delete_cat_data'): confirm_delete_cat()

        tabs = st.tabs(["💸 Neue Buchung", "⚙️ Daueraufträge"])

        with tabs[0]:
            all_cats = DEFAULT_CATS[t_type] + load_custom_cats(user_name, t_type)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Typ</p>", unsafe_allow_html=True)
            ta, te, td, _ = st.columns([1,1,1,2])
            for label,val,col in [("↗ Ausgabe","Ausgabe",ta),("↙ Einnahme","Einnahme",te),("📦 Depot","Depot",td)]:
                with col:
                    if st.button(label+(" ✓" if t_type==val else ""), key=f"btn_{val.lower()}", use_container_width=True, type="primary" if t_type==val else "secondary"):
                        st.session_state['t_type'] = val; st.session_state['tx_page'] = 0; st.rerun()

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.form("t_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    t_amount = st.number_input(f"Betrag in {_currency_sym}", min_value=0.01, step=0.01, format="%.2f")
                    t_date   = st.date_input("Datum", datetime.date.today())
                with col2:
                    st.markdown("<div style='font-family:DM Sans,sans-serif;font-size:14px;color:#e2e8f0;margin-bottom:4px;'>Kategorie</div>", unsafe_allow_html=True)
                    t_cat  = st.selectbox("Kategorie", all_cats, label_visibility="collapsed")
                    t_note = st.text_input("Notiz (optional)", placeholder="z.B. Supermarkt, Tankstelle...")
                if st.form_submit_button("Speichern", use_container_width=True):
                    betrag_save = t_amount if t_type in ("Depot","Einnahme") else -t_amount
                    new_row = pd.DataFrame([{"user":user_name,"datum":str(t_date),
                        "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "typ":t_type,"kategorie":t_cat,"betrag":betrag_save,"notiz":t_note,"deleted":""}])
                    _gs_update("transactions", pd.concat([_gs_read("transactions"), new_row], ignore_index=True))
                    st.session_state['tx_page'] = 0
                    st.success(f"✅ {t_type} über {t_amount:.2f} {_currency_sym} gespeichert!")
                    st.balloons()

            cat_btn_col, manage_col = st.columns([1,1])
            with cat_btn_col:
                if st.button("+ Neue Kategorie", use_container_width=True, type="secondary"):
                    st.session_state.update({'show_new_cat':True,'new_cat_typ':t_type,'_dialog_just_opened':True}); st.rerun()
            custom_cats = load_custom_cats(user_name, t_type)
            if custom_cats:
                with manage_col:
                    with st.expander(f"Eigene {t_type}-Kategorien"):
                        for cat in custom_cats:
                            cc1, cc2 = st.columns([5,1])
                            cc1.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:14px;'>{cat}</span>", unsafe_allow_html=True)
                            with cc2:
                                with st.popover("⋯", use_container_width=True):
                                    if st.button("✏️ Bearbeiten", key=f"editcat_{cat}", use_container_width=True):
                                        st.session_state.update({'edit_cat_data':{'user':user_name,'typ':t_type,'old_label':cat},'_dialog_just_opened':True}); st.rerun()
                                    if st.button("🗑️ Löschen", key=f"delcat_{cat}", use_container_width=True):
                                        st.session_state.update({'delete_cat_data':{'user':user_name,'typ':t_type,'label':cat},'_dialog_just_opened':True}); st.rerun()

            st.markdown("<div style='height:8px'></div><div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin:20px 0 10px 0;'>Meine Buchungen</div>", unsafe_allow_html=True)

            search_col, _ = st.columns([2,3])
            with search_col:
                search_val = st.text_input("🔍 Suchen...", value=st.session_state.get('tx_search',''), placeholder="Kategorie, Notiz, Betrag...", label_visibility="collapsed", key="tx_search_input")
                if search_val != st.session_state.get('tx_search',''):
                    st.session_state['tx_search'] = search_val; st.session_state['tx_page'] = 0; st.rerun()

            try:
                df_t = _gs_read("transactions")
                if 'user' not in df_t.columns:
                    st.info("Noch keine Buchungen vorhanden.")
                else:
                    del_mask = (~df_t['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0']) if 'deleted' in df_t.columns else pd.Series([True]*len(df_t),index=df_t.index))
                    user_df  = df_t[(df_t['user']==user_name)&del_mask].copy()
                    if user_df.empty:
                        st.info("Noch keine Buchungen vorhanden.")
                    else:
                        def betrag_anzeige(row, sym=_currency_sym):
                            x = pd.to_numeric(row['betrag'], errors='coerce')
                            if row.get('typ')=='Depot':    return f"📦 {abs(x):.2f} {sym}"
                            if row.get('typ')=='Spartopf': return f"🪣 {abs(x):.2f} {sym}" if x<0 else f"🪣 +{abs(x):.2f} {sym}"
                            return f"+{x:.2f} {sym}" if x>0 else f"{x:.2f} {sym}"

                        user_df['betrag_anzeige'] = user_df.apply(betrag_anzeige, axis=1)
                        sort_col = 'timestamp' if 'timestamp' in user_df.columns else 'datum'
                        user_df  = user_df.sort_values(sort_col, ascending=False)

                        search_q = st.session_state.get('tx_search','').strip().lower()
                        if search_q:
                            import re as _re
                            _pat = _re.escape(search_q)
                            betrag_match = user_df['betrag_anzeige'].str.lower().str.contains(
                                r'(?<!\d)' + _pat + r'(?!\d)', na=False, regex=True)
                            mask_s = (
                                user_df['kategorie'].str.lower().str.contains(search_q, na=False) |
                                user_df['notiz'].astype(str).str.lower().str.contains(search_q, na=False) |
                                betrag_match |
                                user_df['typ'].str.lower().str.contains(search_q, na=False)
                            )
                            user_df = user_df[mask_s]

                        PAGE_SIZE = 10
                        total     = len(user_df)
                        page      = st.session_state.get('tx_page', 0)
                        max_page  = max(0, (total-1)//PAGE_SIZE)
                        page      = min(page, max_page)
                        st.session_state['tx_page'] = page
                        start     = page * PAGE_SIZE
                        page_df   = user_df.iloc[start:start+PAGE_SIZE]

                        if page_df.empty:
                            st.info("Keine Buchungen gefunden.")
                        else:
                            for orig_idx, row in page_df.iterrows():
                                notiz     = str(row.get('notiz','')); notiz = '' if notiz.lower()=='nan' else notiz
                                betrag_num = pd.to_numeric(row['betrag'], errors='coerce')
                                farbe      = TYPE_COLORS.get(row['typ'],'#f87171')
                                zeit_label = format_timestamp(row.get('timestamp',''), row.get('datum',''))

                                c1,c2,c3,c4,c5 = st.columns([2.5,2,2.5,3,1])
                                c1.markdown(f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:12px;line-height:2.4;display:block;'>{zeit_label}</span>", unsafe_allow_html=True)
                                c2.markdown(f"<span style='font-family:DM Mono,monospace;color:{farbe};font-weight:500;font-size:13px;line-height:2.4;display:block;'>{row['betrag_anzeige']}</span>", unsafe_allow_html=True)
                                c3.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;line-height:2.4;display:block;'>{row['kategorie']}</span>", unsafe_allow_html=True)
                                c4.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#334155;font-size:13px;line-height:2.4;display:block;'>{notiz}</span>", unsafe_allow_html=True)
                                with c5:
                                    with st.popover("⋯", use_container_width=True):
                                        if st.button("✏️ Bearbeiten", key=f"edit_btn_{orig_idx}", use_container_width=True):
                                            st.session_state['edit_idx'] = None if st.session_state['edit_idx']==orig_idx else orig_idx
                                            st.session_state['show_new_cat'] = False; st.rerun()
                                        if st.button("🗑️ Löschen", key=f"del_btn_{orig_idx}", use_container_width=True):
                                            confirm_delete({"user":row['user'],"datum":row['datum'],"betrag":row['betrag'],"betrag_anzeige":row['betrag_anzeige'],"kategorie":row['kategorie']})

                                if st.session_state['edit_idx'] == orig_idx:
                                    with st.form(key=f"edit_form_{orig_idx}"):
                                        st.markdown("<p style='font-family:DM Sans,sans-serif;color:#38bdf8;font-weight:500;font-size:14px;margin-bottom:12px;'>Eintrag bearbeiten</p>", unsafe_allow_html=True)
                                        ec1, ec2 = st.columns(2)
                                        with ec1:
                                            e_betrag = st.number_input(f"Betrag in {_currency_sym}", value=abs(float(betrag_num)), min_value=0.01, step=0.01, format="%.2f")
                                            e_datum  = st.date_input("Datum", value=datetime.date.fromisoformat(str(row['datum'])))
                                        with ec2:
                                            e_typ = st.selectbox("Typ", ["Einnahme","Ausgabe","Depot"], index=["Einnahme","Ausgabe","Depot"].index(row['typ']) if row['typ'] in ["Einnahme","Ausgabe","Depot"] else 1)
                                            e_all_cats = DEFAULT_CATS[e_typ] + load_custom_cats(user_name, e_typ)
                                            e_cat = st.selectbox("Kategorie", e_all_cats, index=e_all_cats.index(row['kategorie']) if row['kategorie'] in e_all_cats else 0)
                                        e_notiz = st.text_input("Notiz (optional)", value=notiz)
                                        cs, cc = st.columns(2)
                                        with cs: saved     = st.form_submit_button("Speichern", use_container_width=True, type="primary")
                                        with cc: cancelled = st.form_submit_button("Abbrechen", use_container_width=True)
                                        if saved:
                                            df_all = _gs_read("transactions")
                                            if 'deleted' not in df_all.columns: df_all['deleted'] = ''
                                            match_idx = df_all[find_row_mask(df_all, row)].index
                                            if len(match_idx)>0:
                                                neuer_betrag = e_betrag if e_typ=="Einnahme" else -e_betrag
                                                df_all.loc[match_idx[0],['datum','typ','kategorie','betrag','notiz']] = [str(e_datum),e_typ,e_cat,neuer_betrag,e_notiz]
                                                _gs_update("transactions", df_all)
                                                st.session_state['edit_idx'] = None; st.success("✅ Gespeichert!"); st.rerun()
                                            else: st.error("❌ Eintrag nicht gefunden.")
                                        if cancelled: st.session_state['edit_idx'] = None; st.rerun()

                        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                        p1,p2,p3 = st.columns([1,4,1])
                        with p1:
                            if st.button("‹ Neuer", use_container_width=True, disabled=(page<=0)):
                                st.session_state['tx_page'] = page-1; st.rerun()
                        with p2:
                            st.markdown(f"<div style='text-align:center;font-family:DM Mono,monospace;color:#334155;font-size:12px;padding:8px 0;'>Seite {page+1} von {max_page+1} · {total} Einträge</div>", unsafe_allow_html=True)
                        with p3:
                            if st.button("Älter ›", use_container_width=True, disabled=(page>=max_page)):
                                st.session_state['tx_page'] = page+1; st.rerun()
            except Exception as e:
                st.warning(f"Fehler beim Laden: {e}")

        with tabs[1]:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            das = load_dauerauftraege(user_name)

            if das:
                st.markdown("<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Aktive Daueraufträge</div>", unsafe_allow_html=True)
                for da in das:
                    betrag_num_da = da['betrag']
                    farbe_da = '#4ade80' if da['typ']=='Einnahme' else ('#38bdf8' if da['typ']=='Depot' else '#f87171')
                    sign_da  = '+' if da['typ']=='Einnahme' else '-'
                    dc1,dc2,dc3,dc4,dc5 = st.columns([3,2,2,2,1])
                    dc1.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;line-height:2.4;display:block;'>⚙️ {da['name']}</span>", unsafe_allow_html=True)
                    dc2.markdown(f"<span style='font-family:DM Mono,monospace;color:{farbe_da};font-size:13px;line-height:2.4;display:block;'>{sign_da}{betrag_num_da:,.2f} {_currency_sym}</span>", unsafe_allow_html=True)
                    dc3.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:12px;line-height:2.4;display:block;'>{da['typ']}</span>", unsafe_allow_html=True)
                    dc4.markdown(f"<span style='font-family:DM Sans,sans-serif;color:#334155;font-size:12px;line-height:2.4;display:block;'>{da['kategorie']}</span>", unsafe_allow_html=True)
                    with dc5:
                        if st.button("🗑️", key=f"del_da_{da['id']}", use_container_width=True, type="secondary"):
                            delete_dauerauftrag(user_name, da['id']); st.rerun()
                st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown("<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Neuen Dauerauftrag erstellen</div>", unsafe_allow_html=True)
            st.markdown("<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:16px;'>Daueraufträge werden automatisch am 1. jedes Monats gebucht.</p>", unsafe_allow_html=True)
            with st.form("da_form", clear_on_submit=True):
                da1, da2 = st.columns(2)
                with da1:
                    da_name   = st.text_input("Name", placeholder="z.B. Miete, Netflix, Fitnessstudio")
                    da_betrag = st.number_input(f"Betrag ({_currency_sym})", min_value=0.01, step=0.01, format="%.2f")
                with da2:
                    da_typ    = st.selectbox("Typ", ["Ausgabe","Einnahme","Depot"])
                    da_all_cats = DEFAULT_CATS[da_typ] + load_custom_cats(user_name, da_typ)
                    da_kat    = st.selectbox("Kategorie", da_all_cats)
                if st.form_submit_button("Dauerauftrag erstellen", use_container_width=True, type="primary"):
                    if not da_name.strip(): st.error("Bitte einen Namen eingeben.")
                    else:
                        save_dauerauftrag(user_name, da_name.strip(), da_betrag, da_typ, da_kat)
                        st.success(f"✅ Dauerauftrag '{da_name.strip()}' erstellt!"); st.rerun()

            if not das:
                st.markdown(
                    "<div style='text-align:center;padding:30px 20px;'>"
                    "<div style='font-size:36px;margin-bottom:12px;'>⚙️</div>"
                    "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:14px;'>Noch keine Daueraufträge. Erstelle deinen ersten Dauerauftrag!</p></div>",
                    unsafe_allow_html=True)

    # ============================================================
    #  ANALYSEN
    # ============================================================
    elif menu == "📂 Analysen":
        import plotly.graph_objects as go
        import calendar

        user_name = st.session_state['user_name']
        st.markdown(
            "<div style='margin-bottom:36px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>Analysen &amp; Trends 📊</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>Kaufverhalten, Zeitraumübersicht &amp; Sparziele</p></div>",
            unsafe_allow_html=True)

        try:
            df_raw = _gs_read("transactions")
        except Exception as e:
            st.warning(f"Verbindung wird hergestellt... ({e})"); df_raw = pd.DataFrame()

        if df_raw.empty or 'user' not in df_raw.columns:
            st.info("Noch keine Buchungen vorhanden.")
        else:
            df_all = df_raw[df_raw['user']==user_name].copy()
            if 'deleted' in df_all.columns:
                df_all = df_all[~df_all['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0'])]
            df_all['datum_dt']   = pd.to_datetime(df_all['datum'], errors='coerce')
            df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce')
            df_all = df_all.dropna(subset=['datum_dt'])

            if df_all.empty:
                st.info("Noch keine Buchungen vorhanden.")
            else:
                now   = datetime.datetime.now()
                today = now.date()

                zeitraum = st.session_state['analysen_zeitraum']
                zt1, zt2, zt3, _ = st.columns([1,1,1,3])
                for (label,key),col in zip([("Wöchentlich","zt_weekly"),("Monatlich","zt_monthly"),("Jährlich","zt_yearly")],[zt1,zt2,zt3]):
                    with col:
                        if st.button(label+(" ✓" if zeitraum==label else ""), key=key, use_container_width=True, type="primary" if zeitraum==label else "secondary"):
                            st.session_state['analysen_zeitraum'] = label; st.session_state['analysen_month_offset'] = 0; st.rerun()

                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                if zeitraum == "Monatlich":
                    an_offset  = st.session_state.get('analysen_month_offset',0)
                    m_total    = now.year*12 + (now.month-1) + an_offset
                    an_year, an_mi = divmod(m_total,12); an_month = an_mi+1
                    an_label   = datetime.date(an_year, an_month, 1).strftime("%B %Y")
                    an1,an2,an3 = st.columns([1,5,1])
                    with an1:
                        if st.button("‹", key="an_prev", use_container_width=True): st.session_state['analysen_month_offset']-=1; st.rerun()
                    with an2:
                        st.markdown(f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:13px;color:#64748b;padding:6px 0;'>{an_label}</div>", unsafe_allow_html=True)
                    with an3:
                        if st.button("›", key="an_next", use_container_width=True, disabled=(an_offset>=0)): st.session_state['analysen_month_offset']+=1; st.rerun()
                    period_mask  = (df_all['datum_dt'].dt.year==an_year)&(df_all['datum_dt'].dt.month==an_month)
                    period_label = an_label
                elif zeitraum == "Wöchentlich":
                    ws = today - datetime.timedelta(days=today.weekday())
                    we = ws + datetime.timedelta(days=6)
                    period_mask  = (df_all['datum_dt'].dt.date>=ws)&(df_all['datum_dt'].dt.date<=we)
                    period_label = f"{ws.strftime('%d.%m.')} – {we.strftime('%d.%m.%Y')}"
                else:
                    period_mask  = df_all['datum_dt'].dt.year==now.year
                    period_label = str(now.year)

                period_df = df_all[period_mask].copy()
                st.markdown(f"<div style='font-family:DM Mono,monospace;color:#475569;font-size:11px;letter-spacing:1px;margin-bottom:18px;'>{period_label}</div>", unsafe_allow_html=True)

                def make_donut(grp, palette, label, sign, center_color, key_suffix):
                    if grp.empty: return
                    cats   = grp['kategorie'].tolist()
                    vals   = grp['betrag_num'].abs().tolist()
                    colors = [palette[i%len(palette)] for i in range(len(cats))]
                    total  = sum(vals) if sum(vals)>0 else 1
                    fig = go.Figure(go.Pie(
                        labels=cats, values=vals, hole=0.60,
                        marker=dict(colors=colors, line=dict(color="rgba(5,10,20,0.9)",width=2)),
                        textinfo="none", hoverinfo="none", direction="clockwise", sort=False, rotation=90))
                    fig.update_traces(hovertemplate=None)
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                        margin=dict(t=10,b=10,l=10,r=10), height=240, autosize=True, dragmode=False,
                        annotations=[dict(text=f"<b>{sign}{total:,.2f} {_currency_sym}</b>", x=0.5, y=0.5, showarrow=False,
                                          font=dict(size=15,color=center_color,family="DM Sans, sans-serif"), xref="paper", yref="paper")])
                    rows = "".join(
                        f"<div style='display:flex;align-items:center;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>"
                        f"<div style='display:flex;align-items:center;gap:8px;min-width:0;flex:1;'>"
                        f"<div style='width:7px;height:7px;border-radius:50%;background:{col};flex-shrink:0;'></div>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{cat}</span></div>"
                        f"<div style='display:flex;align-items:center;gap:6px;flex-shrink:0;margin-left:10px;'>"
                        f"<span style='font-family:DM Mono,monospace;color:{col};font-size:11px;font-weight:500;'>{sign}{val:,.2f} {_currency_sym}</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>{val/total*100:.0f}%</span></div></div>"
                        for cat,val,col in zip(cats,vals,colors))
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:18px 22px;margin-bottom:16px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>{label}</div>",
                        unsafe_allow_html=True)
                    pie_col, leg_col = st.columns([1,1])
                    with pie_col: st.plotly_chart(fig, use_container_width=True, key=f"donut_{key_suffix}_{zeitraum}_{period_label}", config={"displayModeBar":False,"staticPlot":True})
                    with leg_col: st.markdown(f"<div style='padding:4px 0;'>{rows}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                if period_df.empty:
                    st.markdown(f"<div style='text-align:center;padding:40px 20px;color:#334155;font-family:DM Sans,sans-serif;font-size:15px;'>Keine Buchungen im gewählten Zeitraum.</div>", unsafe_allow_html=True)
                else:
                    aus_p = period_df[period_df['typ']=='Ausgabe'].copy(); aus_p['betrag_num'] = aus_p['betrag_num'].abs()
                    make_donut(aus_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num',ascending=False), PALETTE_AUS, "Ausgaben","−","#f87171","aus")
                    ein_p = period_df[period_df['typ']=='Einnahme'].copy()
                    make_donut(ein_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num',ascending=False), PALETTE_EIN, "Einnahmen","+","#4ade80","ein")
                    dep_p = period_df[period_df['typ']=='Depot'].copy(); dep_p['betrag_num'] = dep_p['betrag_num'].abs()
                    make_donut(dep_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num',ascending=False), PALETTE_DEP, "Depot","","#38bdf8","dep")

                st.markdown("<hr>", unsafe_allow_html=True)

                # ── CHANGE 3: Kaufverhalten — Ø der letzten 12 Monate ──
                st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Kaufverhalten <span style=\"font-size:9px;color:#1e293b;\">(Ø letzte 12 Monate)</span></p>", unsafe_allow_html=True)
                kv_l, kv_r = st.columns(2)
                with kv_l:
                    # Filter to last 12 months for a yearly average
                    _twelve_months_ago = now - datetime.timedelta(days=365)
                    aus_all = df_all[(df_all['typ']=='Ausgabe') & (df_all['datum_dt'] >= _twelve_months_ago)].copy()
                    aus_all['betrag_num'] = aus_all['betrag_num'].abs()
                    # Calculate monthly average per category
                    _months_in_range = max(aus_all['datum_dt'].dt.to_period('M').nunique(), 1)
                    kat_grp_sum = aus_all.groupby('kategorie')['betrag_num'].sum()
                    kat_avg = (kat_grp_sum / _months_in_range).reset_index()
                    kat_grp = kat_avg.sort_values('betrag_num', ascending=True).tail(8)
                    if not kat_grp.empty:
                        REDS = ['#7f1d1d','#991b1b','#b91c1c','#dc2626','#ef4444','#f87171','#fca5a5','#fecaca']
                        fig_kat = go.Figure(go.Bar(
                            x=kat_grp['betrag_num'], y=kat_grp['kategorie'], orientation='h',
                            marker=dict(color=REDS[:len(kat_grp)], cornerradius=6),
                            # CHANGE 2: text inside bars
                            text=[f"Ø {v:,.0f} {_currency_sym}" for v in kat_grp['betrag_num']],
                            textposition='inside', insidetextanchor='middle',
                            textfont=dict(size=11,color='rgba(255,255,255,0.85)',family='DM Mono, monospace'),
                            hovertemplate=None))
                        fig_kat.update_traces(hovertemplate=None)
                        fig_kat.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            height=280, margin=dict(t=0,b=0,l=0,r=10), dragmode=False,
                            xaxis=dict(showgrid=False,showticklabels=False,showline=False,fixedrange=True),
                            yaxis=dict(tickfont=dict(size=12,color='#94a3b8',family='DM Sans, sans-serif'),showgrid=False,showline=False,fixedrange=True,automargin=True))
                        st.markdown(f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:8px;'>Top Ausgabe-Kategorien — Ø pro Monat</p>", unsafe_allow_html=True)
                        st.plotly_chart(fig_kat, use_container_width=True, key="kat_chart", config={"displayModeBar":False,"staticPlot":True})
                    else: st.info("Keine Ausgaben vorhanden.")
                with kv_r:
                    aus_all2 = df_all[(df_all['typ']=='Ausgabe') & (df_all['datum_dt'] >= _twelve_months_ago)].copy()
                    aus_all2['betrag_num'] = aus_all2['betrag_num'].abs()
                    aus_all2['wochentag'] = aus_all2['datum_dt'].dt.day_name()
                    wt_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                    wt_de    = {'Monday':'Mo','Tuesday':'Di','Wednesday':'Mi','Thursday':'Do','Friday':'Fr','Saturday':'Sa','Sunday':'So'}
                    if not aus_all2.empty:
                        heat = aus_all2.groupby('wochentag')['betrag_num'].mean().reindex(wt_order).fillna(0)
                        fig_heat = go.Figure(go.Bar(
                            x=[wt_de.get(d,d) for d in heat.index], y=heat.values,
                            marker=dict(color=heat.values,colorscale=[[0,'#1a0505'],[0.5,'#dc2626'],[1,'#ff5232']],showscale=False,cornerradius=6),
                            text=[f"{v:,.0f} {_currency_sym}" if v>0 else "" for v in heat.values],
                            textposition='inside', insidetextanchor='middle',
                            textfont=dict(size=10,color='rgba(255,255,255,0.7)',family='DM Mono, monospace'), hovertemplate=None))
                        fig_heat.update_traces(hovertemplate=None)
                        fig_heat.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            height=280, margin=dict(t=0,b=0,l=0,r=0), dragmode=False,
                            xaxis=dict(tickfont=dict(size=13,color='#94a3b8',family='DM Sans, sans-serif'),showgrid=False,showline=False,fixedrange=True),
                            yaxis=dict(showgrid=False,showticklabels=False,showline=False,fixedrange=True))
                        st.markdown("<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:8px;'>Ø Ausgaben nach Wochentag</p>", unsafe_allow_html=True)
                        st.plotly_chart(fig_heat, use_container_width=True, key="heat_chart", config={"displayModeBar":False,"staticPlot":True})

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Kalender-Heatmap</p>", unsafe_allow_html=True)
                hm_offset = st.session_state.get('heatmap_month_offset',0)
                hm_m_total = now.year*12+(now.month-1)+hm_offset
                hm_year, hm_mi = divmod(hm_m_total,12); hm_month = hm_mi+1
                hm_label = datetime.date(hm_year, hm_month, 1).strftime("%B %Y")
                hn1,hn2,hn3 = st.columns([1,5,1])
                with hn1:
                    if st.button("‹", key="hm_prev", use_container_width=True): st.session_state['heatmap_month_offset']-=1; st.rerun()
                with hn2:
                    st.markdown(f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:13px;color:#64748b;padding:6px 0;'>{hm_label}</div>", unsafe_allow_html=True)
                with hn3:
                    if st.button("›", key="hm_next", use_container_width=True, disabled=(hm_offset>=0)): st.session_state['heatmap_month_offset']+=1; st.rerun()

                hm_df = df_all[(df_all['datum_dt'].dt.year==hm_year)&(df_all['datum_dt'].dt.month==hm_month)&(df_all['typ']=='Ausgabe')].copy()
                hm_df['betrag_num'] = hm_df['betrag_num'].abs()
                tages_summen  = hm_df.groupby(hm_df['datum_dt'].dt.day)['betrag_num'].sum()
                max_val       = max(tages_summen.max() if not tages_summen.empty else 1, 1)
                days_in_month = calendar.monthrange(hm_year, hm_month)[1]
                first_weekday = calendar.monthrange(hm_year, hm_month)[0]

                header_html = "".join(f"<div style='width:42px;text-align:center;font-family:DM Mono,monospace;font-size:10px;color:#334155;padding-bottom:4px;'>{d}</div>" for d in ['Mo','Di','Mi','Do','Fr','Sa','So'])
                cal_cells = "<div style='width:42px;height:42px;'></div>" * first_weekday
                for day in range(1, days_in_month+1):
                    val = tages_summen.get(day,0); intensity = val/max_val if max_val>0 else 0
                    is_today = (hm_year==now.year and hm_month==now.month and day==now.day)
                    if val==0: bg,text_color = "rgba(15,23,42,0.6)","#1e293b"
                    else:
                        r,g,b = int(20+intensity*235),int(5+(1-intensity)*30),int(5+(1-intensity)*10)
                        bg = f"rgba({r},{g},{b},0.85)"; text_color = "#ffffff" if intensity>0.3 else "#94a3b8"
                    border = "2px solid #38bdf8" if is_today else "1px solid rgba(148,163,184,0.06)"
                    cal_cells += (f"<div title='{day}. {hm_label}: {val:.2f} {_currency_sym}' style='width:42px;height:42px;border-radius:8px;background:{bg};border:{border};display:flex;flex-direction:column;align-items:center;justify-content:center;'>"
                                  f"<span style='font-family:DM Mono,monospace;font-size:11px;color:#334155;line-height:1;'>{day}</span>"
                                  + (f"<span style='font-family:DM Mono,monospace;font-size:8px;color:{text_color};line-height:1;margin-top:2px;'>{val:.0f}{_currency_sym}</span>" if val>0 else "")
                                  + "</div>")
                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:14px;'>Ausgaben pro Tag — hellere Felder = höhere Ausgaben</div>"
                    f"<div style='display:flex;gap:6px;margin-bottom:6px;'>{header_html}</div>"
                    f"<div style='display:flex;flex-wrap:wrap;gap:6px;'>{cal_cells}</div>"
                    f"<div style='display:flex;align-items:center;gap:8px;margin-top:14px;'>"
                    f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>0 {_currency_sym}</span>"
                    f"<div style='height:6px;flex:1;max-width:120px;border-radius:3px;background:linear-gradient(to right,rgba(15,23,42,0.6),#ff0000);'></div>"
                    f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#64748b;'>{max_val:.0f} {_currency_sym}</span></div></div>",
                    unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Monatsende-Prognose</p>", unsafe_allow_html=True)
                curr_month_df = df_all[(df_all['datum_dt'].dt.year==now.year)&(df_all['datum_dt'].dt.month==now.month)].copy()
                today_day     = now.day
                days_in_cur   = calendar.monthrange(now.year, now.month)[1]
                days_left     = days_in_cur - today_day
                curr_ein      = curr_month_df[curr_month_df['typ']=='Einnahme']['betrag_num'].sum()
                curr_aus      = curr_month_df[curr_month_df['typ']=='Ausgabe']['betrag_num'].abs().sum()
                curr_dep      = curr_month_df[curr_month_df['typ']=='Depot']['betrag_num'].sum()
                curr_sp_netto = curr_month_df[curr_month_df['typ']=='Spartopf']['betrag_num'].sum()
                daily_rate    = curr_aus/today_day if today_day>0 else 0
                fc_aus_total  = daily_rate*days_in_cur
                fc_remaining  = daily_rate*days_left
                fc_bank       = curr_ein - fc_aus_total - curr_dep + curr_sp_netto
                curr_bank     = curr_ein - curr_aus - curr_dep + curr_sp_netto
                fc_color  = "#4ade80" if fc_bank>=0 else "#f87171"
                fc_str    = f"+{fc_bank:,.2f} {_currency_sym}" if fc_bank>=0 else f"-{abs(fc_bank):,.2f} {_currency_sym}"
                curr_color= "#4ade80" if curr_bank>=0 else "#f87171"
                curr_str  = f"+{curr_bank:,.2f} {_currency_sym}" if curr_bank>=0 else f"-{abs(curr_bank):,.2f} {_currency_sym}"
                month_pct     = today_day/days_in_cur*100

                fc_col_l, fc_col_r = st.columns(2)
                with fc_col_l:
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;'>Prognose für {now.strftime('%B %Y')}</div>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Monatsverlauf</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#64748b;font-size:12px;'>Tag {today_day}/{days_in_cur}</span></div>"
                        f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:5px;margin-bottom:16px;'>"
                        f"<div style='width:{month_pct:.0f}%;height:100%;background:#475569;border-radius:99px;'></div></div>"
                        f"<div style='display:flex;flex-direction:column;gap:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ø Tagesausgaben</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>{daily_rate:,.2f} {_currency_sym}/Tag</span></div>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Noch {days_left} Tage → ca.</span>"
                        f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{fc_remaining:,.2f} {_currency_sym}</span></div>"
                        f"<div style='border-top:1px solid rgba(148,163,184,0.08);padding-top:10px;display:flex;justify-content:space-between;align-items:baseline;'>"
                        f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;font-weight:500;'>Prognose Monatsende</span>"
                        f"<span style='font-family:DM Mono,monospace;color:{fc_color};font-size:18px;font-weight:600;'>{fc_str}</span>"
                        f"</div></div></div>", unsafe_allow_html=True)
                with fc_col_r:
                    goal_fc = load_goal(user_name)
                    goal_html = ""
                    if goal_fc>0:
                        diff_goal = fc_bank - goal_fc; on_track = fc_bank >= goal_fc
                        _g_bg    = "rgba(74,222,128,0.06)"  if on_track else "rgba(248,113,113,0.06)"
                        _g_bor   = "rgba(74,222,128,0.15)"  if on_track else "rgba(248,113,113,0.15)"
                        _g_icon  = "✅" if on_track else "⚠️"
                        _g_col   = "#4ade80" if on_track else "#fca5a5"
                        _g_lbl   = "Sparziel erreichbar!" if on_track else "Sparziel in Gefahr"
                        _g_pre   = "Puffer: +" if diff_goal >= 0 else "Fehlbetrag: "
                        goal_html = (
                            f"<div style='margin-top:12px;padding:10px 14px;border-radius:10px;"
                            f"background:{_g_bg};border:1px solid {_g_bor};display:flex;align-items:center;gap:10px;'>"
                            f"<span style='font-size:16px;'>{_g_icon}</span>"
                            f"<div><div style='font-family:DM Sans,sans-serif;color:{_g_col};font-size:13px;font-weight:500;'>{_g_lbl}</div>"
                            f"<div style='font-family:DM Mono,monospace;color:#475569;font-size:11px;'>{_g_pre}{abs(diff_goal):,.2f} {_currency_sym}</div></div></div>")
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;'>Jetzt vs. Prognose</div>"
                        f"<div style='display:flex;gap:12px;'>"
                        f"<div style='flex:1;background:rgba(10,16,30,0.5);border-radius:12px;padding:14px;border:1px solid rgba(148,163,184,0.06);text-align:center;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;'>Aktuell</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{curr_color};font-size:20px;font-weight:600;'>{curr_str}</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;margin-top:4px;'>Tag {today_day}</div></div>"
                        f"<div style='display:flex;align-items:center;color:#334155;font-size:18px;'>→</div>"
                        f"<div style='flex:1;background:rgba(10,16,30,0.5);border-radius:12px;padding:14px;border:1px solid rgba(148,163,184,0.06);text-align:center;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;'>Prognose</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{fc_color};font-size:20px;font-weight:600;'>{fc_str}</div>"
                        f"<div style='font-family:DM Mono,monospace;color:#334155;font-size:10px;margin-top:4px;'>Tag {days_in_cur}</div></div></div>"
                        f"{goal_html}</div>", unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Spar-Potenzial</p>", unsafe_allow_html=True)
                hist_df = df_all[~((df_all['datum_dt'].dt.year==now.year)&(df_all['datum_dt'].dt.month==now.month))&(df_all['typ']=='Ausgabe')].copy()
                hist_df['betrag_num'] = hist_df['betrag_num'].abs()
                hist_df = hist_df[hist_df['datum_dt'] >= now - datetime.timedelta(days=90)]

                if not hist_df.empty and not curr_month_df.empty:
                    hist_months  = max(hist_df['datum_dt'].dt.to_period('M').nunique(),1)
                    avg_per_kat  = hist_df.groupby('kategorie')['betrag_num'].sum() / hist_months
                    curr_aus_df  = curr_month_df[curr_month_df['typ']=='Ausgabe'].copy(); curr_aus_df['betrag_num'] = curr_aus_df['betrag_num'].abs()
                    curr_per_kat = curr_aus_df.groupby('kategorie')['betrag_num'].sum()
                    potenzial_rows = sorted([
                        {'kategorie':kat,'aktuell':curr_per_kat.get(kat,0),'durchschn':avg_per_kat.get(kat,0),
                         'diff_pct':(curr_per_kat.get(kat,0)-avg_per_kat.get(kat,0))/avg_per_kat.get(kat,0)*100,
                         'diff_eur':curr_per_kat.get(kat,0)-avg_per_kat.get(kat,0)}
                        for kat in curr_per_kat.index
                        if avg_per_kat.get(kat,0)>0 and curr_per_kat.get(kat,0)>avg_per_kat.get(kat,0)*1.1
                    ], key=lambda x: x['diff_eur'], reverse=True)

                    if potenzial_rows:
                        total_potenzial = sum(r['diff_eur'] for r in potenzial_rows)
                        st.markdown(
                            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;margin-bottom:12px;'>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:14px;margin-bottom:16px;'>Diesen Monat hast du in <b style='color:#e2e8f0;'>{len(potenzial_rows)} Kategorien</b> mehr ausgegeben als im Durchschnitt. Spar-Potenzial: <span style='color:#4ade80;font-weight:600;'>{total_potenzial:,.2f} {_currency_sym}</span></div>",
                            unsafe_allow_html=True)
                        for r in potenzial_rows:
                            bar_pct = min(r['diff_pct'],200)/200*100
                            st.markdown(
                                f"<div style='margin-bottom:14px;'>"
                                f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;'>"
                                f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{r['kategorie']}</span>"
                                f"<div style='display:flex;gap:14px;'>"
                                f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>{r['aktuell']:,.2f} {_currency_sym}</span>"
                                f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>Ø {r['durchschn']:,.2f} {_currency_sym}</span>"
                                f"<span style='font-family:DM Mono,monospace;color:#facc15;font-size:12px;font-weight:600;'>+{r['diff_pct']:.0f}%</span>"
                                f"</div></div>"
                                f"<div style='background:rgba(30,41,59,0.6);border-radius:99px;height:4px;'>"
                                f"<div style='width:{bar_pct:.0f}%;height:100%;border-radius:99px;background:linear-gradient(to right,#facc15,#f87171);'></div></div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:4px;'>Da könntest du ca. <span style='color:#4ade80;font-weight:500;'>{r['diff_eur']:,.2f} {_currency_sym}</span> sparen</div></div>",
                                unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(74,222,128,0.12);border-left:3px solid #4ade80;border-radius:16px;padding:18px 22px;'>"
                            "<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:14px;font-weight:500;'>🎉 Alles im grünen Bereich!</div>"
                            "<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-top:6px;'>Deine Ausgaben liegen diesen Monat im normalen Rahmen.</div></div>",
                            unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color:#334155;font-family:DM Sans,sans-serif;font-size:14px;padding:16px;'>Zu wenig Daten für Vergleich.</div>", unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Sparziel</p>", unsafe_allow_html=True)
                current_goal = load_goal(user_name)
                df_month = df_all[(df_all['datum_dt'].dt.year==now.year)&(df_all['datum_dt'].dt.month==now.month)].copy()
                df_month['betrag_num'] = pd.to_numeric(df_month['betrag'], errors='coerce')
                monat_ein        = df_month[df_month['typ']=='Einnahme']['betrag_num'].sum()
                monat_aus        = df_month[df_month['typ']=='Ausgabe']['betrag_num'].abs().sum()
                monat_dep        = df_month[df_month['typ']=='Depot']['betrag_num'].abs().sum()
                monat_sp_einzahl = abs(df_month[(df_month['typ']=='Spartopf')&(df_month['betrag_num']<0)]['betrag_num'].sum())
                monat_sp_netto   = df_month[df_month['typ']=='Spartopf']['betrag_num'].sum()
                bank_aktuell     = monat_ein - monat_aus - monat_dep + monat_sp_netto
                # CHANGE 1: Depot zählt als "gespart" (wie Spartopf-Einzahlungen)
                akt_spar         = bank_aktuell + monat_sp_einzahl + abs(monat_dep)

                sg_col_l, sg_col_r = st.columns([1,1])
                with sg_col_l:
                    with st.form("sparziel_form"):
                        goal_input = st.number_input(f"Monatliches Sparziel ({_currency_sym})", min_value=0.0, value=float(current_goal), step=50.0, format="%.2f")
                        if st.form_submit_button("Sparziel speichern", use_container_width=True, type="primary"):
                            save_goal(user_name, goal_input); st.success("✅ Sparziel gespeichert!"); st.rerun()
                    spar_color = '#4ade80' if akt_spar>=0 else '#f87171'
                    spar_str   = f"{akt_spar:,.2f} {_currency_sym}" if akt_spar>=0 else f"-{abs(akt_spar):,.2f} {_currency_sym}"
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.8),rgba(10,16,30,0.9));border:1px solid rgba(148,163,184,0.06);border-radius:12px;padding:16px 18px;margin-top:10px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;'>{now.strftime('%B %Y')}</div>"
                        f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Einnahmen</div><div style='font-family:DM Mono,monospace;color:#4ade80;font-size:12px;'>+{monat_ein:,.2f} {_currency_sym}</div></div>"
                        f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ausgaben</div><div style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{monat_aus:,.2f} {_currency_sym}</div></div>"
                        + (f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Depot</div><div style='font-family:DM Mono,monospace;color:#38bdf8;font-size:12px;'>📦 {abs(monat_dep):,.2f} {_currency_sym}</div></div>" if monat_dep!=0 else "")
                        + (f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Spartöpfe</div><div style='font-family:DM Mono,monospace;color:#a78bfa;font-size:12px;'>🪣 {monat_sp_einzahl:,.2f} {_currency_sym}</div></div>" if monat_sp_einzahl>0 else "")
                        + f"<div style='border-top:1px solid rgba(148,163,184,0.08);margin-top:8px;padding-top:8px;display:flex;justify-content:space-between;'>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:12px;font-weight:500;'>Gespart (inkl. Töpfe &amp; Depot)</div>"
                        f"<div style='font-family:DM Mono,monospace;color:{spar_color};font-size:13px;font-weight:600;'>{spar_str}</div></div></div>",
                        unsafe_allow_html=True)
                with sg_col_r:
                    if current_goal>0:
                        fehlbetrag  = current_goal - akt_spar; erreicht = akt_spar >= current_goal
                        pct_display = max(0, min(akt_spar/current_goal*100,100))
                        bar_color   = '#4ade80' if erreicht else ('#facc15' if pct_display>=60 else '#f87171')
                        spar_color2 = '#4ade80' if akt_spar>=0 else '#f87171'
                        spar_str2   = f"{akt_spar:,.2f} {_currency_sym}" if akt_spar>=0 else f"-{abs(akt_spar):,.2f} {_currency_sym}"
                        st.markdown(
                            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;'>"
                            f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;'>Fortschritt</span>"
                            f"<span style='font-family:DM Mono,monospace;font-size:13px;color:{bar_color};font-weight:600;'>{pct_display:.0f}%</span></div>"
                            f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:6px;overflow:hidden;margin-bottom:16px;'>"
                            f"<div style='height:100%;width:{pct_display}%;background:{bar_color};border-radius:99px;'></div></div>"
                            f"<div style='display:flex;justify-content:space-between;'>"
                            f"<div><div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;'>Aktuell gespart</div>"
                            f"<div style='font-family:DM Sans,sans-serif;color:{spar_color2};font-size:18px;font-weight:600;'>{spar_str2}</div></div>"
                            f"<div style='text-align:right;'><div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;'>Ziel</div>"
                            f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:18px;font-weight:600;'>{current_goal:,.2f} {_currency_sym}</div></div></div></div>",
                            unsafe_allow_html=True)
                        if not erreicht and fehlbetrag>0:
                            aus_monat = df_month[df_month['typ']=='Ausgabe'].copy(); aus_monat['betrag_num'] = aus_monat['betrag_num'].abs()
                            kat_monat = aus_monat.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num',ascending=False)
                            if not kat_monat.empty:
                                remaining = fehlbetrag; rows_html = ""
                                for _,kr in kat_monat.iterrows():
                                    if remaining<=0: break
                                    cut = min(kr['betrag_num'],remaining)
                                    rows_html += (f"<div style='display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>"
                                                  f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{kr['kategorie']}</span>"
                                                  f"<div><span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>−{cut:,.2f} {_currency_sym}</span>"
                                                  f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;margin-left:8px;'>({cut/kr['betrag_num']*100:.0f}%)</span></div></div>")
                                    remaining -= cut
                                st.markdown(
                                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(248,113,113,0.1);border-left:3px solid #f87171;border-radius:16px;padding:18px 20px;margin-top:12px;'>"
                                    f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#ef4444;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Noch {fehlbetrag:,.2f} {_currency_sym} bis zum Ziel</div>"
                                    f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>Diese Kategorien könntest du reduzieren:</div>"
                                    f"{rows_html}</div>", unsafe_allow_html=True)
                        elif erreicht:
                            st.markdown(
                                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(74,222,128,0.15);border-left:3px solid #4ade80;border-radius:16px;padding:18px 20px;margin-top:12px;'>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:14px;font-weight:500;'>🎉 Sparziel diesen Monat erreicht!</div>"
                                f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-top:6px;'>Du hast {akt_spar-current_goal:,.2f} {_currency_sym} mehr gespart als geplant.</div></div>",
                                unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:12px;padding:20px 22px;color:#334155;font-family:DM Sans,sans-serif;font-size:14px;'>Trage links ein Sparziel ein, um Empfehlungen zu erhalten.</div>", unsafe_allow_html=True)

    # ============================================================
    #  SPARTÖPFE
    # ============================================================
    elif menu == "🪣 Spartöpfe":
        user_name = st.session_state['user_name']
        st.markdown(
            "<div style='margin-bottom:36px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;margin:0 0 6px 0;letter-spacing:-1px;'>Spartöpfe 🪣</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>Virtuelle Töpfe für deine Sparziele</p></div>",
            unsafe_allow_html=True)

        toepfe = load_toepfe(user_name)
        if toepfe:
            total_gespart = sum(t['gespart'] for t in toepfe)
            total_ziel    = sum(t['ziel'] for t in toepfe if t['ziel']>0)
            st.markdown(
                f"<div style='display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;'>"
                f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(56,189,248,0.12);border-radius:14px;padding:16px 18px;'>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt gespart</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:22px;font-weight:600;'>{total_gespart:,.2f} {_currency_sym}</div></div>"
                f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
                f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Anzahl Töpfe</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:22px;font-weight:600;'>{len(toepfe)}</div></div>"
                + (f"<div style='flex:1;min-width:140px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:16px 18px;'>"
                   f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamt-Ziel</div>"
                   f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:22px;font-weight:600;'>{total_ziel:,.2f} {_currency_sym}</div></div>" if total_ziel>0 else "")
                + "</div>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            for i, topf in enumerate(toepfe):
                col    = col_a if i%2==0 else col_b
                farbe  = topf.get('farbe','#38bdf8'); gespart = topf['gespart']; ziel = topf['ziel']
                emoji  = topf.get('emoji','🪣'); topf_id = topf['id']
                with col:
                    if ziel>0:
                        pct = min(gespart/ziel*100,100)
                        ziel_html = (f"<div style='display:flex;justify-content:space-between;margin-bottom:6px;margin-top:10px;'>"
                                     f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>{gespart:,.2f} / {ziel:,.2f} {_currency_sym}</span>"
                                     f"<span style='font-family:DM Mono,monospace;color:{farbe};font-size:10px;font-weight:600;'>{pct:.0f}%</span></div>"
                                     f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:5px;overflow:hidden;'>"
                                     f"<div style='width:{pct:.0f}%;height:100%;background:{farbe};border-radius:99px;'></div></div>")
                        badge_html = (f"<span style='background:rgba(74,222,128,0.1);color:#4ade80;font-family:DM Mono,monospace;font-size:9px;padding:2px 8px;border-radius:99px;border:1px solid rgba(74,222,128,0.2);'>✓ ERREICHT</span>" if pct>=100 else f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>noch {ziel-gespart:,.2f} {_currency_sym} fehlen</span>")
                    else:
                        ziel_html = ""; badge_html = f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:10px;'>kein Ziel gesetzt</span>"

                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));border:1px solid {farbe}20;border-top:2px solid {farbe};border-radius:16px;padding:18px 20px;margin-bottom:14px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                        f"<div><div style='font-size:22px;margin-bottom:4px;'>{emoji}</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-weight:600;font-size:16px;'>{topf['name']}</div></div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:{farbe};font-size:22px;font-weight:600;'>{gespart:,.2f} {_currency_sym}</div></div>"
                        f"{ziel_html}<div style='margin-top:10px;'>{badge_html}</div></div>", unsafe_allow_html=True)

                    with st.expander(f"💰 Ein/Auszahlen — {topf['name']}"):
                        tz1, tz2 = st.columns(2)
                        with tz1:
                            einzahl_val = st.number_input(f"Einzahlen ({_currency_sym})", min_value=0.01, step=1.0, format="%.2f", key=f"einzahl_{topf_id}")
                            if st.button("+ Einzahlen", key=f"do_einzahl_{topf_id}", use_container_width=True, type="primary"):
                                update_topf_gespart(user_name, topf_id, topf['name'], einzahl_val); st.rerun()
                        with tz2:
                            auszahl_val = st.number_input(f"Auszahlen ({_currency_sym})", min_value=0.01, step=1.0, format="%.2f", key=f"auszahl_{topf_id}")
                            if st.button("− Auszahlen", key=f"do_auszahl_{topf_id}", use_container_width=True, type="secondary"):
                                update_topf_gespart(user_name, topf_id, topf['name'], -auszahl_val); st.rerun()

                    te1, te2 = st.columns(2)
                    with te1:
                        if st.button("✏️", key=f"edit_topf_{topf_id}", use_container_width=True, type="secondary"):
                            st.session_state['topf_edit_data'] = topf; st.session_state['_dialog_just_opened'] = True; st.rerun()
                    with te2:
                        if st.button("🗑️", key=f"del_topf_{topf_id}", use_container_width=True, type="secondary"):
                            st.session_state['topf_delete_id'] = topf_id; st.session_state['topf_delete_name'] = topf['name']
                            st.session_state['_dialog_just_opened'] = True; st.rerun()
        else:
            st.markdown(
                "<div style='text-align:center;padding:60px 20px;'>"
                "<div style='font-size:48px;margin-bottom:16px;'>🪣</div>"
                "<p style='font-family:DM Sans,sans-serif;color:#334155;font-size:15px;'>Noch keine Spartöpfe. Erstelle deinen ersten Topf!</p></div>",
                unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;'>Neuen Topf erstellen</p>", unsafe_allow_html=True)
        with st.form("neuer_topf_form", clear_on_submit=True):
            nt1, nt2, nt3 = st.columns([1,3,2])
            with nt1: nt_emoji = st.text_input("Emoji", placeholder="✈️", max_chars=4)
            with nt2: nt_name  = st.text_input("Name", placeholder="z.B. Urlaub, Neues Auto, Laptop...")
            with nt3: nt_ziel  = st.number_input(f"Sparziel ({_currency_sym}, optional)", min_value=0.0, step=50.0, format="%.2f", value=0.0)
            if st.form_submit_button("Topf erstellen", use_container_width=True, type="primary"):
                if not nt_name.strip(): st.error("Bitte einen Namen eingeben.")
                else:
                    save_topf(user=user_name, name=nt_name.strip(), ziel=nt_ziel, emoji=nt_emoji.strip() if nt_emoji.strip() else "🪣")
                    st.success(f"✅ Topf '{nt_name.strip()}' erstellt!"); st.rerun()

        if st.session_state.get('topf_edit_data'):
            @st.dialog("✏️ Topf bearbeiten")
            def topf_edit_dialog():
                t = st.session_state['topf_edit_data']
                e1, e2 = st.columns([1,3])
                with e1: new_emoji = st.text_input("Emoji", value=t['emoji'], max_chars=4)
                with e2: new_name  = st.text_input("Name", value=t['name'])
                new_ziel = st.number_input(f"Sparziel ({_currency_sym})", min_value=0.0, value=float(t['ziel']), step=50.0, format="%.2f")
                cs, cc = st.columns(2)
                with cs:
                    if st.button("Speichern", use_container_width=True, type="primary"):
                        update_topf_meta(user_name, t['id'], new_name.strip() or t['name'], new_ziel, new_emoji.strip() or t['emoji'])
                        st.session_state['topf_edit_data'] = None; st.rerun()
                with cc:
                    if st.button("Abbrechen", use_container_width=True):
                        st.session_state['topf_edit_data'] = None; st.rerun()
            topf_edit_dialog()

        if st.session_state.get('topf_delete_id'):
            @st.dialog("Topf löschen")
            def topf_delete_dialog():
                name = st.session_state.get('topf_delete_name','')
                st.markdown(f"<p style='color:#e2e8f0;font-size:15px;'>Topf <b>'{name}'</b> wirklich löschen?</p>", unsafe_allow_html=True)
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Löschen", use_container_width=True, type="primary"):
                        delete_topf(user_name, st.session_state['topf_delete_id'])
                        st.session_state['topf_delete_id'] = None; st.session_state['topf_delete_name'] = None; st.rerun()
                with d2:
                    if st.button("Abbrechen", use_container_width=True):
                        st.session_state['topf_delete_id'] = None; st.session_state['topf_delete_name'] = None; st.rerun()
            topf_delete_dialog()

    # ============================================================
    #  EINSTELLUNGEN
    # ============================================================
    elif menu == "⚙️ Einstellungen":
        user_name = st.session_state['user_name']
        st.markdown(
            "<div style='margin-bottom:28px;margin-top:16px;'>"
            "<h1 style='font-family:DM Sans,sans-serif;font-size:36px;font-weight:700;color:#e2e8f0;margin:0 0 4px 0;letter-spacing:-1px;'>Einstellungen ⚙️</h1>"
            "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:14px;margin:0;'>Profil, Finanzen, Design und Konto</p></div>",
            unsafe_allow_html=True)

        SETTINGS_TABS = [("👤","Profil"),("💰","Finanzen"),("🎨","Design"),("🔐","Sicherheit"),("📦","Daten")]
        active_tab    = st.session_state.get('settings_tab','Profil')
        tab_cols = st.columns(len(SETTINGS_TABS))
        for i,(icon,label) in enumerate(SETTINGS_TABS):
            with tab_cols[i]:
                if st.button(f"{icon} {label}", key=f"stab_{label}", use_container_width=True, type="primary" if active_tab==label else "secondary"):
                    st.session_state['settings_tab'] = label; st.rerun()
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        if active_tab == "Profil":
            col_main, col_preview = st.columns([2,1])
            with col_main:
                section_header("Profilbild", "URL zu einem öffentlich zugänglichen Bild")
                with st.form("avatar_form"):
                    new_avatar = st.text_input("Bild-URL", value=_user_settings.get('avatar_url',''), placeholder="https://beispiel.de/foto.jpg")
                    if st.form_submit_button("Profilbild speichern", use_container_width=True, type="primary"):
                        save_user_settings(user_name, avatar_url=new_avatar.strip()); st.success("✅ Profilbild gespeichert!"); st.rerun()
            with col_preview:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                _av = _user_settings.get('avatar_url','')
                if _av and _av.startswith('http'):
                    st.markdown(f"<div style='text-align:center;'><img src='{_av}' style='width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid {_t['primary']}60;'><p style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:8px;'>Aktuelles Profilbild</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center;'><div style='width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,{_t['accent']},{_t['accent2']});display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:600;color:#fff;margin:0 auto;'>{user_name[:2].upper()}</div><p style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:8px;'>Initialen-Avatar</p></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            section_header("Benutzername ändern", "Kann nur alle 30 Tage geändert werden")
            try:
                df_u_name = _gs_read("users"); idx_un = df_u_name[df_u_name['username']==user_name].index
                last_change_raw = str(df_u_name.loc[idx_un[0],'username_changed_at']) if (not idx_un.empty and 'username_changed_at' in df_u_name.columns) else ''
                last_change = None
                try: last_change = datetime.date.fromisoformat(last_change_raw.strip()) if last_change_raw.strip() not in ('','nan','None') else None
                except: pass
                days_since = (datetime.date.today() - last_change).days if last_change else 999
                can_change = days_since >= 30
                days_left  = max(0, 30 - days_since)
                primary_color = _t['primary']
                st.markdown(f"<div style='background:rgba(10,16,30,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:10px;padding:12px 16px;display:inline-block;margin-bottom:12px;'><span style='font-family:DM Mono,monospace;color:{primary_color};font-size:15px;font-weight:500;'>@{user_name}</span></div>", unsafe_allow_html=True)
                if not can_change:
                    st.markdown(f"<div style='background:rgba(250,204,21,0.06);border:1px solid rgba(250,204,21,0.15);border-radius:10px;padding:10px 14px;'><span style='font-family:DM Sans,sans-serif;color:#fbbf24;font-size:13px;'>⏳ Nächste Änderung möglich in <b>{days_left}</b> Tag{'en' if days_left!=1 else ''}.</span></div>", unsafe_allow_html=True)
                else:
                    with st.form("username_change_form"):
                        new_uname = st.text_input("Neuer Benutzername", placeholder="Mindestens 3 Zeichen, keine Leerzeichen")
                        if st.form_submit_button("Benutzername ändern", use_container_width=True, type="primary"):
                            new_uname = new_uname.strip()
                            if len(new_uname) < 3: st.error("❌ Mindestens 3 Zeichen erforderlich.")
                            elif ' ' in new_uname: st.error("❌ Keine Leerzeichen erlaubt.")
                            elif new_uname == user_name: st.error("❌ Das ist bereits dein Benutzername.")
                            elif not df_u_name[df_u_name['username']==new_uname].empty: st.error("❌ Benutzername bereits vergeben.")
                            else:
                                df_u_name.loc[idx_un[0],'username'] = new_uname
                                if 'username_changed_at' not in df_u_name.columns: df_u_name['username_changed_at'] = ''
                                df_u_name.loc[idx_un[0],'username_changed_at'] = str(datetime.date.today())
                                _gs_update("users", df_u_name)
                                for ws,col in [("transactions","user"),("toepfe","user"),("goals","user"),("settings","user"),("dauerauftraege","user")]:
                                    try:
                                        df_ws = _gs_read(ws)
                                        if col in df_ws.columns:
                                            df_ws.loc[df_ws[col]==user_name, col] = new_uname; _gs_update(ws, df_ws)
                                    except: pass
                                for k in [k for k in st.session_state if k.startswith("_gs_cache_")]: del st.session_state[k]
                                st.session_state['user_name'] = new_uname
                                st.success(f"✅ Benutzername geändert zu @{new_uname}!"); st.rerun()
            except Exception as e: st.error(f"Fehler: {e}")

        elif active_tab == "Finanzen":
            col_l, col_r = st.columns(2)
            with col_l:
                section_header("Monatliches Budget-Limit")
                with st.form("budget_form"):
                    new_budget = st.number_input(f"Budget ({_currency_sym})", min_value=0.0, value=float(_user_settings.get('budget',0.0)), step=50.0, format="%.2f")
                    if st.form_submit_button("Budget speichern", use_container_width=True, type="primary"):
                        save_user_settings(user_name, budget=new_budget); st.success("✅ Budget-Limit gespeichert!"); st.rerun()
            with col_r:
                section_header("Währung")
                with st.form("currency_form"):
                    curr_options = list(CURRENCY_SYMBOLS.keys())
                    curr_current = _user_settings.get('currency','EUR')
                    curr_idx     = curr_options.index(curr_current) if curr_current in curr_options else 0
                    curr_labels  = [f"{sym} ({CURRENCY_SYMBOLS[sym]})" for sym in curr_options]
                    new_curr_lbl = st.selectbox("Währung wählen", curr_labels, index=curr_idx)
                    new_currency = curr_options[curr_labels.index(new_curr_lbl)]
                    if st.form_submit_button("Währung speichern", use_container_width=True, type="primary"):
                        save_user_settings(user_name, currency=new_currency); _gs_invalidate("settings")
                        st.success(f"✅ Währung auf {new_currency} gesetzt!"); st.rerun()

        elif active_tab == "Design":
            section_header("Farbschema")
            theme_cols = st.columns(3)
            theme_icons = {"Ocean Blue":"🌊","Emerald Green":"🌿","Deep Purple":"🔮"}
            theme_descs = {"Ocean Blue":"Dunkles Marineblau mit Sky-Akzenten","Emerald Green":"Tiefes Waldgrün mit Smaragd-Akzenten","Deep Purple":"Samtiges Dunkelviolett mit Amethyst-Akzenten"}
            for i,tname in enumerate(THEMES.keys()):
                t_data = THEMES[tname]; is_active = (_theme_name==tname)
                with theme_cols[i]:
                    _tc_bor = t_data['primary']+'ff' if is_active else t_data['primary']+'30'
                    _tc_sha = f"box-shadow:0 0 20px {t_data['primary']}30;" if is_active else ""
                    _tc_badge = f"<div style='margin-top:8px;font-family:DM Mono,monospace;color:{t_data['primary']};font-size:9px;letter-spacing:1.5px;'>✓ AKTIV</div>" if is_active else ""
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,{t_data['bg1']},{t_data['bg2']});border:2px solid {_tc_bor};border-radius:14px;padding:16px;margin-bottom:10px;text-align:center;{_tc_sha}'>"
                        f"<div style='font-size:24px;margin-bottom:8px;'>{theme_icons[tname]}</div>"
                        f"<div style='display:flex;justify-content:center;gap:6px;margin-bottom:10px;'>"
                        f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['primary']};'></div>"
                        f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['accent']};'></div>"
                        f"<div style='width:16px;height:16px;border-radius:50%;background:{t_data['accent2']};'></div></div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:13px;font-weight:600;margin-bottom:4px;'>{tname}</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:11px;'>{theme_descs[tname]}</div>"
                        f"{_tc_badge}</div>", unsafe_allow_html=True)
                    if st.button("Auswählen" if not is_active else "✓ Aktiv", key=f"theme_btn_{tname}", use_container_width=True, type="primary" if is_active else "secondary", disabled=is_active):
                        st.session_state['theme'] = tname; save_user_settings(user_name, theme=tname); st.rerun()

        elif active_tab == "Sicherheit":
            col_l, col_r = st.columns(2)
            with col_l:
                section_header("Passwort ändern")
                with st.form("pw_form"):
                    pw_alt = st.text_input("Aktuelles Passwort", type="password")
                    pw_neu = st.text_input("Neues Passwort", type="password")
                    pw_neu2= st.text_input("Neues Passwort wiederholen", type="password")
                    if st.form_submit_button("Passwort ändern", use_container_width=True, type="primary"):
                        df_u = _gs_read("users"); idx = df_u[df_u['username']==user_name].index
                        if idx.empty: st.error("❌ Benutzer nicht gefunden.")
                        elif make_hashes(pw_alt) != str(df_u.loc[idx[0],'password']): st.error("❌ Aktuelles Passwort ist falsch.")
                        elif pw_neu == pw_alt: st.error("❌ Das neue Passwort darf nicht dem alten entsprechen.")
                        else:
                            ok, msg = check_password_strength(pw_neu)
                            if not ok: st.error(f"❌ {msg}")
                            elif pw_neu != pw_neu2: st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                            else:
                                df_u.loc[idx[0],'password'] = make_hashes(pw_neu); _gs_update("users", df_u)
                                st.success("✅ Passwort erfolgreich geändert!")
            with col_r:
                section_header("E-Mail-Adresse ändern")
                try:
                    df_u_em = _gs_read("users"); idx_em = df_u_em[df_u_em['username']==user_name].index
                    curr_email = str(df_u_em.loc[idx_em[0],'email']) if not idx_em.empty else "–"
                except: curr_email = "–"
                st.markdown(f"<div style='background:rgba(10,16,30,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:10px;padding:10px 14px;margin-bottom:14px;'><span style='font-family:DM Mono,monospace;color:#475569;font-size:11px;'>Aktuell: </span><span style='font-family:DM Mono,monospace;color:{_t['primary']};font-size:12px;'>{curr_email}</span></div>", unsafe_allow_html=True)
                if not st.session_state.get('email_verify_code'):
                    with st.form("email_change_form"):
                        new_email_input = st.text_input("Neue E-Mail-Adresse", placeholder="neu@beispiel.de")
                        if st.form_submit_button("Code senden", use_container_width=True, type="primary"):
                            if not is_valid_email(new_email_input.strip()): st.error("❌ Bitte gib eine gültige E-Mail ein.")
                            elif new_email_input.strip().lower() == curr_email.lower(): st.error("❌ Das ist bereits deine E-Mail-Adresse.")
                            else:
                                code = generate_code(); expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                                if send_email(new_email_input.strip().lower(), "Balancely – E-Mail-Adresse bestätigen", email_html("Dein Code zum Ändern der E-Mail-Adresse lautet:", code)):
                                    st.session_state.update({'email_verify_code':code,'email_verify_expiry':expiry,'email_verify_new':new_email_input.strip().lower()}); st.rerun()
                                else: st.error("❌ E-Mail konnte nicht gesendet werden.")
                else:
                    st.markdown(f"<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>Code gesendet an <span style='color:{_t['primary']};'>{st.session_state['email_verify_new']}</span></p>", unsafe_allow_html=True)
                    with st.form("email_verify_form"):
                        code_in = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                        cv1, cv2 = st.columns(2)
                        with cv1: confirm = st.form_submit_button("Bestätigen", use_container_width=True, type="primary")
                        with cv2: cancel  = st.form_submit_button("Abbrechen",  use_container_width=True)
                        if confirm:
                            if st.session_state['email_verify_expiry'] and datetime.datetime.now() > st.session_state['email_verify_expiry']:
                                st.error("⏰ Code abgelaufen."); st.session_state['email_verify_code'] = ""; st.rerun()
                            elif code_in.strip() != st.session_state['email_verify_code']: st.error("❌ Falscher Code.")
                            else:
                                df_u2 = _gs_read("users"); idx2 = df_u2[df_u2['username']==user_name].index
                                if not idx2.empty:
                                    df_u2.loc[idx2[0],'email'] = st.session_state['email_verify_new']; _gs_update("users", df_u2)
                                st.session_state.update({'email_verify_code':"",'email_verify_expiry':None,'email_verify_new':""})
                                st.success("✅ E-Mail-Adresse erfolgreich geändert!"); st.rerun()
                        if cancel:
                            st.session_state.update({'email_verify_code':"",'email_verify_new':""}); st.rerun()

        elif active_tab == "Daten":

            section_header("Excel-Export")
            try:
                import io
                df_export = _gs_read("transactions")
                if 'user' in df_export.columns:
                    df_export = df_export[df_export['user']==user_name]
                    if 'deleted' in df_export.columns:
                        df_export = df_export[~df_export['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0'])]
                    df_export = df_export.drop(columns=['deleted','user'], errors='ignore')
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Transaktionen')
                excel_bytes = buffer.getvalue()
                st.markdown(f"<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>{len(df_export)} Transaktionen bereit</p>", unsafe_allow_html=True)
                _, dl_col, _ = st.columns([1, 2, 1])
                with dl_col:
                    st.download_button(
                        label="⬇️ Transaktionen exportieren (Excel)",
                        data=excel_bytes,
                        file_name=f"balancely_{user_name}_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True, type="primary")
            except Exception as e:
                st.error(f"Export fehlgeschlagen: {e}")

            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

            section_header("Daten zurücksetzen")
            if not st.session_state['confirm_reset']:
                _, rst_col, _ = st.columns([1, 2, 1])
                with rst_col:
                    if st.button("🔄 Alle Transaktionen löschen", use_container_width=True, type="secondary"):
                        st.session_state['confirm_reset'] = True; st.rerun()
            else:
                st.markdown(
                    "<div style='background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.2);border-radius:10px;padding:14px;margin-bottom:10px;'>"
                    "<p style='font-family:DM Sans,sans-serif;color:#fca5a5;font-size:14px;font-weight:500;margin:0 0 4px 0;'>⚠️ Wirklich alle Transaktionen löschen?</p>"
                    "<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin:0;'>Diese Aktion kann nicht rückgängig gemacht werden.</p></div>",
                    unsafe_allow_html=True)
                _, rc1, rc2, _ = st.columns([1, 1, 1, 1])
                with rc1:
                    if st.button("Ja, löschen", use_container_width=True, type="primary"):
                        try:
                            df_all_t = _gs_read("transactions")
                            if 'deleted' not in df_all_t.columns: df_all_t['deleted'] = ''
                            df_all_t.loc[df_all_t['user']==user_name,'deleted'] = 'True'
                            _gs_update("transactions", df_all_t)
                            st.session_state['confirm_reset'] = False; st.success("✅ Alle Transaktionen gelöscht."); st.rerun()
                        except Exception as e: st.error(f"Fehler: {e}")
                with rc2:
                    if st.button("Abbrechen", use_container_width=True):
                        st.session_state['confirm_reset'] = False; st.rerun()

            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

            section_header("Account löschen")
            if not st.session_state['confirm_delete_account']:
                _, del_col, _ = st.columns([1, 2, 1])
                with del_col:
                    if st.button("🗑️ Account und alle Daten löschen", use_container_width=True, type="secondary"):
                        st.session_state['confirm_delete_account'] = True; st.rerun()
            else:
                st.markdown(
                    "<div style='background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.25);border-left:3px solid #f87171;border-radius:10px;padding:14px;margin-bottom:10px;'>"
                    "<p style='font-family:DM Sans,sans-serif;color:#fca5a5;font-size:14px;font-weight:600;margin:0 0 4px 0;'>🔴 Account unwiderruflich löschen?</p>"
                    "<p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin:0;'>Alle Transaktionen, Spartöpfe, Sparziele und Einstellungen werden gelöscht.</p></div>",
                    unsafe_allow_html=True)
                _, da1, da2, _ = st.columns([1, 1, 1, 1])
                with da1:
                    if st.button("Ja, Account löschen", use_container_width=True, type="primary"):
                        try:
                            for ws,col_name in [("transactions","user"),("toepfe","user")]:
                                df_ws = _gs_read(ws)
                                if 'deleted' not in df_ws.columns: df_ws['deleted'] = ''
                                df_ws.loc[df_ws[col_name]==user_name,'deleted'] = 'True'; _gs_update(ws, df_ws)
                            for ws in ["goals","settings"]:
                                df_ws = _gs_read(ws); _gs_update(ws, df_ws[df_ws['user']!=user_name])
                            df_u3 = _gs_read("users")
                            if 'deleted' not in df_u3.columns: df_u3['deleted'] = ''
                            df_u3.loc[df_u3['username']==user_name,'deleted'] = 'True'; _gs_update("users", df_u3)
                            for k in [k for k in st.session_state if k.startswith("_gs_cache_")]: del st.session_state[k]
                            st.session_state.update({'logged_in':False,'user_name':"",'confirm_delete_account':False}); st.rerun()
                        except Exception as e: st.error(f"Fehler beim Löschen: {e}")
                with da2:
                    if st.button("Abbrechen", use_container_width=True, key="cancel_del_acc"):
                        st.session_state['confirm_delete_account'] = False; st.rerun()

# ============================================================
#  AUTH
# ============================================================

else:
    st.markdown("<div style='height:10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Balancely</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Verwalte deine Finanzen mit Klarheit</p>", unsafe_allow_html=True)

    _, center_col, _ = st.columns([1,1.2,1])
    with center_col:
        mode = st.session_state['auth_mode']

        if mode == 'login':
            with st.form("login_form"):
                st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>Anmelden</h3>", unsafe_allow_html=True)
                u_in = st.text_input("Username", placeholder="Benutzername")
                p_in = st.text_input("Passwort", type="password")
                if st.form_submit_button("Anmelden", use_container_width=True):
                    time.sleep(1)
                    df_u = _gs_read("users"); matching = df_u[df_u['username']==u_in]
                    user_row = matching.iloc[[-1]] if not matching.empty else matching
                    if not user_row.empty and make_hashes(p_in) == str(user_row.iloc[0]['password']):
                        if not is_verified(user_row.iloc[0].get('verified','True')):
                            st.error("❌ Bitte verifiziere zuerst deine E-Mail-Adresse.")
                        else:
                            st.session_state.update({'logged_in':True,'user_name':u_in}); st.rerun()
                    else: st.error("❌ Login ungültig.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Konto erstellen", use_container_width=True):
                    st.session_state['auth_mode'] = 'signup'; st.rerun()
            with col2:
                if st.button("Passwort vergessen?", use_container_width=True, type="secondary"):
                    st.session_state['auth_mode'] = 'forgot'; st.rerun()

        elif mode == 'signup':
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-family:DM Sans,sans-serif;font-weight:600;font-size:22px;letter-spacing:-0.5px;margin-bottom:24px;'>Registrierung</h3>", unsafe_allow_html=True)
                s_name  = st.text_input("Name", placeholder="Max Mustermann")
                s_user  = st.text_input("Username", placeholder="max123")
                s_email = st.text_input("E-Mail", placeholder="max@beispiel.de")
                s_pass  = st.text_input("Passwort", type="password")
                c_pass  = st.text_input("Passwort wiederholen", type="password")
                if st.form_submit_button("Konto erstellen", use_container_width=True):
                    if not all([s_name,s_user,s_email,s_pass]): st.error("❌ Bitte fülle alle Felder aus!")
                    elif len(s_name.strip().split())<2: st.error("❌ Bitte gib deinen vollständigen Vor- und Nachnamen an.")
                    elif not is_valid_email(s_email): st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        ok, msg = check_password_strength(s_pass)
                        if not ok: st.error(f"❌ {msg}")
                        elif s_pass != c_pass: st.error("❌ Die Passwörter stimmen nicht überein.")
                        else:
                            df_u = _gs_read("users")
                            if s_user in df_u['username'].values: st.error("⚠️ Dieser Username ist bereits vergeben.")
                            elif s_email.strip().lower() in df_u['email'].values: st.error("⚠️ Diese E-Mail ist bereits registriert.")
                            else:
                                code = generate_code(); expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                                if send_email(s_email.strip().lower(), "Balancely – E-Mail verifizieren", email_html("Willkommen bei Balancely! Dein Verifizierungscode lautet:", code)):
                                    st.session_state.update({
                                        'pending_user':{"name":make_hashes(s_name.strip()),"username":s_user,"email":s_email.strip().lower(),"password":make_hashes(s_pass)},
                                        'verify_code':code,'verify_expiry':expiry,'auth_mode':'verify_email'})
                                    st.rerun()
                                else: st.error("❌ E-Mail konnte nicht gesendet werden.")
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'; st.rerun()

        elif mode == 'verify_email':
            pending_email = st.session_state['pending_user'].get('email','')
            with st.form("verify_form"):
                st.markdown(f"<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>E-Mail verifizieren</h3><p style='text-align:center;color:#475569;font-size:14px;margin-bottom:20px;'>Code gesendet an <span style='color:#38bdf8;'>{pending_email}</span></p>", unsafe_allow_html=True)
                code_input = st.text_input("Code eingeben", placeholder="123456", max_chars=6)
                if st.form_submit_button("Bestätigen", use_container_width=True):
                    if st.session_state['verify_expiry'] and datetime.datetime.now() > st.session_state['verify_expiry']:
                        st.error("⏰ Code abgelaufen."); st.session_state['auth_mode'] = 'signup'; st.rerun()
                    elif code_input.strip() != st.session_state['verify_code']: st.error("❌ Falscher Code.")
                    else:
                        df_u = _gs_read("users")
                        new_u = pd.DataFrame([{**st.session_state['pending_user'],"verified":"True","token":"","token_expiry":""}])
                        _gs_update("users", pd.concat([df_u, new_u], ignore_index=True))
                        st.session_state.update({'pending_user':{},'verify_code':"",'verify_expiry':None,'auth_mode':'login'})
                        st.success("✅ E-Mail verifiziert! Du kannst dich jetzt einloggen.")
            if st.button("Zum Login", use_container_width=True, type="primary"):
                st.session_state['auth_mode'] = 'login'; st.rerun()

        elif mode == 'forgot':
            with st.form("forgot_form"):
                st.markdown("<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>Passwort vergessen</h3>", unsafe_allow_html=True)
                forgot_email = st.text_input("E-Mail", placeholder="deine@email.de")
                if st.form_submit_button("Code senden", use_container_width=True):
                    if not is_valid_email(forgot_email): st.error("❌ Bitte gib eine gültige E-Mail-Adresse ein.")
                    else:
                        df_u = _gs_read("users"); idx = df_u[df_u['email']==forgot_email.strip().lower()].index
                        if idx.empty:
                            st.success("✅ Falls diese E-Mail registriert ist, wurde ein Code gesendet.")
                        else:
                            code = generate_code(); expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            if send_email(forgot_email.strip().lower(), "Balancely – Passwort zurücksetzen", email_html("Dein Code zum Zurücksetzen des Passworts lautet:", code)):
                                st.session_state.update({'reset_email':forgot_email.strip().lower(),'reset_code':code,'reset_expiry':expiry,'auth_mode':'reset_password'}); st.rerun()
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'; st.rerun()

        elif mode == 'reset_password':
            with st.form("reset_form"):
                st.markdown(f"<h3 style='text-align:center;color:#e2e8f0;font-size:22px;font-weight:600;margin-bottom:12px;'>Passwort zurücksetzen</h3><p style='text-align:center;color:#475569;font-size:14px;margin-bottom:20px;'>Code gesendet an <span style='color:#38bdf8;'>{st.session_state['reset_email']}</span></p>", unsafe_allow_html=True)
                code_input = st.text_input("6-stelliger Code", placeholder="123456", max_chars=6)
                pw_neu  = st.text_input("Neues Passwort", type="password")
                pw_neu2 = st.text_input("Passwort wiederholen", type="password")
                if st.form_submit_button("Passwort speichern", use_container_width=True):
                    if st.session_state['reset_expiry'] and datetime.datetime.now() > st.session_state['reset_expiry']:
                        st.error("⏰ Code abgelaufen."); st.session_state['auth_mode'] = 'forgot'; st.rerun()
                    elif code_input.strip() != st.session_state['reset_code']: st.error("❌ Falscher Code.")
                    else:
                        ok, msg = check_password_strength(pw_neu)
                        if not ok: st.error(f"❌ {msg}")
                        elif pw_neu != pw_neu2: st.error("❌ Die neuen Passwörter stimmen nicht überein.")
                        else:
                            df_u = _gs_read("users"); idx = df_u[df_u['email']==st.session_state['reset_email']].index
                            if not idx.empty:
                                df_u.loc[idx[0],'password'] = make_hashes(pw_neu); _gs_update("users", df_u)
                                st.session_state.update({'reset_email':"",'reset_code':"",'reset_expiry':None,'auth_mode':'login'})
                                st.success("✅ Passwort geändert! Du kannst dich jetzt einloggen."); st.rerun()
            if st.button("Zurück zum Login", use_container_width=True):
                st.session_state['auth_mode'] = 'login'; st.rerun()

