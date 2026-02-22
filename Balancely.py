# ============================================================
#  Balancely — Persönliche Finanzverwaltung  v5
# ============================================================
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import hashlib, datetime, re, smtplib, random, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Balancely", page_icon="⚖️", layout="wide")

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
        msg["Subject"] = subject; msg["From"] = "Balancely ⚖️ <" + sender + ">"; msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password); s.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email-Fehler: {e}"); return False

def email_html(text, code_val):
    return (
        '<html><body style="font-family:sans-serif;background:#020617;color:#f1f5f9;padding:40px;">'
        '<div style="max-width:480px;margin:auto;background:#0f172a;border-radius:16px;padding:40px;border:1px solid #1e293b;">'
        '<h2 style="color:#38bdf8;">Balancely ⚖️</h2><p>' + text + '</p>'
        '<div style="margin:24px 0;padding:20px;background:#1e293b;border-radius:12px;text-align:center;'
        'font-size:36px;font-weight:800;letter-spacing:8px;color:#38bdf8;">' + code_val + '</div>'
        '<p style="color:#94a3b8;font-size:13px;">Dieser Code ist 10 Minuten gültig.</p>'
        '</div></body></html>')

DEFAULT_CATS = {
    "Einnahme": ["💼 Gehalt","🎁 Bonus","🛒 Verkauf","📈 Investitionen","🏠 Miete (Einnahme)"],
    "Ausgabe":  ["🍔 Essen","🏠 Miete","🎮 Freizeit","🚗 Transport","🛍️ Shopping","💊 Gesundheit","📚 Bildung","⚡ Strom & Gas"],
    "Depot":    ["📦 ETF","📊 Aktien","🪙 Krypto","🏦 Tagesgeld","💎 Sonstiges"],
}
THEMES = {
    'Ocean Blue':    {'primary':'#38bdf8','bg1':'#070d1a','bg2':'#080e1c','bg3':'#050b16','grad1':'rgba(56,189,248,0.06)','grad2':'rgba(99,102,241,0.05)','accent':'#0ea5e9','accent2':'#2563eb'},
    'Emerald Green': {'primary':'#34d399','bg1':'#061510','bg2':'#071812','bg3':'#051110','grad1':'rgba(52,211,153,0.07)','grad2':'rgba(16,185,129,0.05)','accent':'#10b981','accent2':'#059669'},
    'Deep Purple':   {'primary':'#a78bfa','bg1':'#0d0a1a','bg2':'#100c1e','bg3':'#08061a','grad1':'rgba(167,139,250,0.07)','grad2':'rgba(139,92,246,0.05)','accent':'#8b5cf6','accent2':'#7c3aed'},
}
CURRENCY_SYMBOLS = {'EUR':'€','CHF':'CHF','USD':'$','GBP':'£','JPY':'¥','SEK':'kr','NOK':'kr','DKK':'kr'}
TOPF_PALETTE = ["#38bdf8","#4ade80","#a78bfa","#fb923c","#f472b6","#34d399","#facc15","#60a5fa"]
PALETTE_AUS  = ["#ff0000","#ff5232","#ff7b5a","#ff9e81","#ffbfaa","#ffdfd4","#dc2626","#b91c1c","#991b1b","#7f1d1d"]
PALETTE_EIN  = ["#008000","#469536","#6eaa5e","#93bf85","#b7d5ac","#dbead5","#2d7a2d","#4a9e4a","#5cb85c","#80c780"]
PALETTE_DEP  = ["#0000ff","#1e0bd0","#2510a3","#241178","#1f104f","#19092e","#2563eb","#1d4ed8","#1e40af","#1e3a8a"]
TYPE_COLORS  = {'Einnahme':'#4ade80','Depot':'#38bdf8','Spartopf':'#a78bfa'}

_DEFAULTS = {
    'logged_in':False,'user_name':"",'auth_mode':'login','t_type':'Ausgabe',
    'pending_user':{},'verify_code':"",'verify_expiry':None,
    'reset_email':"",'reset_code':"",'reset_expiry':None,
    'edit_idx':None,'show_new_cat':False,'new_cat_typ':'Ausgabe','_last_menu':"",
    'edit_cat_data':None,'delete_cat_data':None,
    'dash_month_offset':0,'dash_selected_aus':None,'dash_selected_ein':None,
    'dash_selected_cat':None,'dash_selected_typ':None,'dash_selected_color':None,
    'analysen_zeitraum':'Monatlich','analysen_month_offset':0,
    'heatmap_month_offset':0,'topf_edit_data':None,'topf_delete_id':None,'topf_delete_name':None,
    'settings_tab':'Profil','email_verify_code':"",'email_verify_expiry':None,'email_verify_new':"",
    'theme':'Ocean Blue','confirm_reset':False,'confirm_delete_account':False,
    'tx_page':0,'tx_search':"",
    'show_walkthrough':False,'walkthrough_step':0,
    'show_onboarding_prefs':False,
    'onboarding_selected_theme':'Ocean Blue','onboarding_selected_curr_idx':0,
    'is_first_login':False,
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

conn = st.connection("gsheets", type=GSheetsConnection)

# GSheet Cache
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
def check_first_login(user):
    try:
        df = _gs_read("settings")
        if df.empty or 'user' not in df.columns: return True
        return df[df['user']==user].empty
    except: return True
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
        today = datetime.date.today(); target_date = today.replace(day=1)
        df_t = _gs_read("transactions"); booked = 0
        for da in das:
            if da['aktiv'] != 'True': continue
            already = df_t[(df_t['user']==user)&(df_t['notiz']==f"⚙️ Dauerauftrag: {da['name']}")&(df_t['datum'].astype(str).str.startswith(target_date.strftime('%Y-%m')))] if not df_t.empty and 'user' in df_t.columns else pd.DataFrame()
            if not already.empty: continue
            betrag_save = da['betrag'] if da['typ'] in ('Einnahme','Depot') else -da['betrag']
            new_row = pd.DataFrame([{'user':user,'datum':str(target_date),'timestamp':datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),'typ':da['typ'],'kategorie':da['kategorie'],'betrag':betrag_save,'notiz':f"⚙️ Dauerauftrag: {da['name']}",'deleted':''}])
            df_t = pd.concat([df_t, new_row], ignore_index=True); booked += 1
        if booked > 0: _gs_update("transactions", df_t)
        return booked
    except: return 0
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
    new_row = pd.DataFrame([{'user':user,'id':f"{user}_{int(time.time())}","name":name,'ziel':ziel,'gespart':0,'emoji':emoji,'farbe':TOPF_PALETTE[cnt%len(TOPF_PALETTE)],'deleted':''}])
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
        new_row = pd.DataFrame([{"user":user,"datum":str(datetime.date.today()),"timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"typ":"Spartopf","kategorie":f"🪣 {topf_name}","betrag":(-1 if delta>0 else 1)*abs(delta),"notiz":f"{'↓' if delta>0 else '↑'} {topf_name}",'deleted':''}])
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

# ── WALKTHROUGH DATA ─────────────────────────────────────────
WALKTHROUGH_STEPS = [
    {"icon":"🏠","title":"Dashboard","desc":"Dein persönlicher Überblick – Kontostand, Monatsbilanz und die letzten Transaktionen auf einen Blick.","tip":"💡 Nutze die Monatsnavigation, um frühere Monate zu vergleichen."},
    {"icon":"💸","title":"Transaktionen","desc":"Erfasse alle Einnahmen, Ausgaben und Depot-Käufe. Mit Daueraufträgen automatisierst du wiederkehrende Buchungen.","tip":"💡 Suchfunktion und Filter helfen dir, Buchungen schnell zu finden."},
    {"icon":"📊","title":"Analysen","desc":"Visualisiere deine Ausgaben mit interaktiven Charts, einer Heatmap und behalte dein Sparziel im Blick.","tip":"💡 Hellere Felder in der Heatmap = höhere Ausgaben an diesem Tag."},
    {"icon":"🪣","title":"Spartöpfe","desc":"Spare gezielt für bestimmte Ziele – Urlaub, neues Laptop, Notfallreserve. Jeder Topf zeigt deinen Fortschritt.","tip":"💡 Einzahlungen werden automatisch als Transaktion erfasst."},
    {"icon":"⚙️","title":"Einstellungen","desc":"Passe Theme, Währung, Budget und dein Profil an. Du kannst auch Kategorien verwalten.","tip":"💡 Mit dem monatlichen Budget bekommst du Warnungen, wenn du es überschreitest."},
]

@st.dialog("🗺️ App-Tour", width="large")
def walkthrough_dialog():
    step = st.session_state.walkthrough_step
    total = len(WALKTHROUGH_STEPS)
    s = WALKTHROUGH_STEPS[step]
    pri = THEMES.get(st.session_state.get('theme','Ocean Blue'),THEMES['Ocean Blue'])['primary']
    st.markdown(f'''
    <div style="text-align:center;padding:20px 0 10px;">
        <div style="font-size:56px;margin-bottom:12px;">{s["icon"]}</div>
        <h2 style="font-size:24px;font-weight:800;margin:0 0 8px;">{s["title"]}</h2>
        <p style="color:#94a3b8;max-width:420px;margin:0 auto 16px;line-height:1.6;">{s["desc"]}</p>
        <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px 20px;display:inline-block;margin-bottom:20px;">
            <span style="color:{pri};font-size:14px;">{s["tip"]}</span>
        </div>
    </div>''', unsafe_allow_html=True)
    # Progress dots
    dots_html = '<div style="text-align:center;margin-bottom:24px;">'
    for i in range(total):
        color = pri if i==step else '#334155'
        dots_html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin:0 4px;"></span>'
    dots_html += f'<p style="color:#64748b;font-size:13px;margin-top:8px;">{step+1} / {total}</p></div>'
    st.markdown(dots_html, unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("Überspringen", use_container_width=True):
            st.session_state.show_walkthrough = False; st.rerun()
    with c2:
        if step < total-1:
            if st.button("Weiter →", use_container_width=True, type="primary"):
                st.session_state.walkthrough_step += 1; st.rerun()
        else:
            if st.button("✅ Los geht's!", use_container_width=True, type="primary"):
                st.session_state.show_walkthrough = False; st.rerun()

@st.dialog("👋 Willkommen bei Balancely!", width="large")
def onboarding_prefs_dialog():
    pri = THEMES.get(st.session_state.get('theme','Ocean Blue'),THEMES['Ocean Blue'])['primary']
    st.markdown(f'<p style="color:#94a3b8;margin-bottom:24px;">Bevor es losgeht – richte kurz deine Vorlieben ein.</p>', unsafe_allow_html=True)
    # Theme selection
    st.markdown("**🎨 Wähle dein Theme:**")
    theme_cols = st.columns(3)
    theme_names = list(THEMES.keys())
    theme_icons = {'Ocean Blue':'🌊','Emerald Green':'🌿','Deep Purple':'🔮'}
    for i, (tc, tname) in enumerate(zip(theme_cols, theme_names)):
        with tc:
            th = THEMES[tname]
            selected = st.session_state.onboarding_selected_theme == tname
            border = f"2px solid {th['primary']}" if selected else "2px solid #1e293b"
            if st.button(f"{theme_icons.get(tname,'🎨')} {tname}", key=f"ob_theme_{tname}", use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state.onboarding_selected_theme = tname; st.rerun()
            st.markdown(f'<div style="height:6px;border-radius:3px;background:{th["primary"]};margin-top:4px;"></div>', unsafe_allow_html=True)
    st.markdown("<br>**💱 Wähle deine Währung:**")
    curr_list = list(CURRENCY_SYMBOLS.keys())
    curr_idx = st.selectbox("", curr_list, index=st.session_state.onboarding_selected_curr_idx, label_visibility="collapsed",
                             format_func=lambda c: f"{c} ({CURRENCY_SYMBOLS[c]})", key="ob_curr_select")
    st.session_state.onboarding_selected_curr_idx = curr_list.index(curr_idx)
    st.markdown("<br>")
    if st.button("✅ Einstellungen speichern & Tour starten", use_container_width=True, type="primary"):
        user = st.session_state.user_name
        chosen_theme = st.session_state.onboarding_selected_theme
        chosen_curr = curr_list[st.session_state.onboarding_selected_curr_idx]
        save_user_settings(user, theme=chosen_theme, currency=chosen_curr)
        st.session_state.theme = chosen_theme
        st.session_state.show_onboarding_prefs = False
        st.session_state.show_walkthrough = True
        st.session_state.walkthrough_step = 0
        st.rerun()

# ── THEME INJECTION ──────────────────────────────────────────
def inject_theme(theme_name):
    t = THEMES.get(theme_name, THEMES['Ocean Blue'])
    pri = t['primary']; bg1 = t['bg1']; bg2 = t['bg2']; bg3 = t['bg3']
    grad1 = t['grad1']; grad2 = t['grad2']; accent = t['accent']; accent2 = t['accent2']
    css = f"""<style>
:root{{--pri:{pri};--bg1:{bg1};--bg2:{bg2};--bg3:{bg3};
      --grad1:{grad1};--grad2:{grad2};--accent:{accent};--accent2:{accent2};}}
[data-testid="stAppViewContainer"]{{background-color:{bg1}!important;}}
[data-testid="stSidebar"]{{background-color:{bg2}!important;border-right:1px solid #1e293b;}}
[data-testid="stMain"] .block-container{{background:transparent!important;padding-top:1.5rem;}}
.stButton>button{{background:linear-gradient(135deg,{pri},{accent2});color:#fff;border:none;
    border-radius:12px;font-weight:600;transition:all .2s;}}
.stButton>button:hover{{opacity:.9;transform:translateY(-1px);box-shadow:0 4px 15px rgba(0,0,0,.4);}}
.stButton>button[kind="secondary"]{{background:#1e293b;color:#cbd5e1;}}
[data-testid="stMetricValue"]{{font-size:2rem!important;font-weight:800!important;}}
.stTextInput>div>input,.stSelectbox>div>div,.stNumberInput>div>input{{background:#0f172a!important;
    color:#f1f5f9!important;border:1px solid #334155!important;border-radius:10px!important;}}
h1,h2,h3{{color:#f1f5f9!important;}} p,label{{color:#cbd5e1;}}
::-webkit-scrollbar{{width:6px;}} ::-webkit-scrollbar-track{{background:#0f172a;}}
::-webkit-scrollbar-thumb{{background:#334155;border-radius:3px;}}
.stAlert{{border-radius:12px!important;}}
</style>"""
    st.markdown(css, unsafe_allow_html=True)

def section_header(icon, title, subtitle=""):
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']; acc2 = t['accent2']
    sub_html = f'<p style="color:#64748b;font-size:14px;margin:4px 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
<div style="padding:20px 0 16px;border-bottom:1px solid #1e293b;margin-bottom:24px;">
    <h1 style="font-size:26px;font-weight:800;margin:0;color:#f1f5f9;">
        <span style="background:linear-gradient(135deg,{pri},{acc2});-webkit-background-clip:text;
            -webkit-text-fill-color:transparent;">{icon} {title}</span>
    </h1>{sub_html}
</div>""", unsafe_allow_html=True)

# ── CRUD DIALOGS ─────────────────────────────────────────────
@st.dialog("✏️ Transaktion bearbeiten", width="large")
def edit_transaction_dialog(row):
    user = st.session_state.user_name
    settings = load_user_settings(user)
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    all_cats = DEFAULT_CATS.copy()
    for typ in ('Einnahme','Ausgabe','Depot'):
        custom = load_custom_cats(user, typ)
        all_cats[typ] = all_cats.get(typ,[]) + [c for c in custom if c not in all_cats.get(typ,[])]
    typ_val = str(row.get('typ','Ausgabe'))
    datum_str = str(row.get('datum','')).strip()
    betrag_num = abs(float(str(row.get('betrag',0)).replace(',','.')))
    notiz_val = str(row.get('notiz',''))
    c1,c2 = st.columns(2)
    with c1:
        typ_new = st.selectbox("Typ", ['Einnahme','Ausgabe','Depot'], index=['Einnahme','Ausgabe','Depot'].index(typ_val) if typ_val in ['Einnahme','Ausgabe','Depot'] else 1)
    with c2:
        cats = all_cats.get(typ_new, [])
        cat_val = str(row.get('kategorie',''))
        cat_idx = cats.index(cat_val) if cat_val in cats else 0
        cat_new = st.selectbox("Kategorie", cats, index=cat_idx)
    c3,c4 = st.columns(2)
    with c3:
        try: datum_obj = datetime.date.fromisoformat(datum_str)
        except: datum_obj = datetime.date.today()
        datum_new = st.date_input("Datum", value=datum_obj)
    with c4:
        betrag_new = st.number_input(f"Betrag ({sym})", min_value=0.01, value=betrag_num, step=0.01)
    notiz_new = st.text_input("Notiz (optional)", value=notiz_val)
    ca, cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.edit_idx = None; st.rerun()
    with cb:
        if st.button("💾 Speichern", use_container_width=True, type="primary"):
            df = _gs_read("transactions")
            mask = find_row_mask(df, row)
            if mask.any():
                idx = df[mask].index[0]
                betrag_save = betrag_new if typ_new in ('Einnahme','Depot') else -betrag_new
                df.at[idx,'typ'] = typ_new; df.at[idx,'kategorie'] = cat_new
                df.at[idx,'datum'] = str(datum_new); df.at[idx,'betrag'] = betrag_save
                df.at[idx,'notiz'] = notiz_new
                _gs_update("transactions", df)
            st.session_state.edit_idx = None; st.rerun()

@st.dialog("🗑️ Transaktion löschen")
def delete_transaction_dialog(row):
    sym = CURRENCY_SYMBOLS.get(load_user_settings(st.session_state.user_name).get('currency','EUR'),'€')
    st.warning(f"Wirklich löschen? {row.get('typ','')} · {row.get('kategorie','')} · {abs(float(str(row.get('betrag',0)).replace(',','.')))} {sym}")
    ca, cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True): st.rerun()
    with cb:
        if st.button("🗑️ Löschen", use_container_width=True, type="primary"):
            df = _gs_read("transactions")
            mask = find_row_mask(df, row)
            if mask.any(): df.loc[mask,'deleted'] = 'True'; _gs_update("transactions", df)
            st.rerun()

@st.dialog("➕ Neue Kategorie")
def add_cat_dialog():
    user = st.session_state.user_name
    typ = st.selectbox("Typ", ['Einnahme','Ausgabe','Depot'])
    st.session_state.new_cat_typ = typ
    emoji = st.text_input("Emoji", "💡", max_chars=2)
    name = st.text_input("Name")
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.show_new_cat = False; st.rerun()
    with cb:
        if st.button("➕ Hinzufügen", use_container_width=True, type="primary"):
            if name.strip():
                label = f"{emoji} {name.strip()}"
                save_custom_cat(user, typ, label)
                st.session_state.show_new_cat = False; st.rerun()
            else: st.error("Bitte Namen eingeben.")

@st.dialog("✏️ Kategorie bearbeiten")
def edit_cat_dialog(cat_data):
    user = st.session_state.user_name
    old_label = cat_data['kategorie']; typ = cat_data['typ']
    parts = old_label.split(" ", 1)
    old_emoji = parts[0] if len(parts)>1 else "💡"
    old_name = parts[1] if len(parts)>1 else old_label
    new_emoji = st.text_input("Emoji", old_emoji, max_chars=2)
    new_name = st.text_input("Name", old_name)
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.edit_cat_data = None; st.rerun()
    with cb:
        if st.button("💾 Speichern", use_container_width=True, type="primary"):
            new_label = f"{new_emoji} {new_name.strip()}"
            update_custom_cat(user, typ, old_label, new_label)
            st.session_state.edit_cat_data = None; st.rerun()

@st.dialog("🗑️ Kategorie löschen")
def delete_cat_dialog(cat_data):
    st.warning(f"Kategorie '{cat_data['kategorie']}' löschen?")
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.delete_cat_data = None; st.rerun()
    with cb:
        if st.button("🗑️ Löschen", use_container_width=True, type="primary"):
            delete_custom_cat(st.session_state.user_name, cat_data['typ'], cat_data['kategorie'])
            st.session_state.delete_cat_data = None; st.rerun()

@st.dialog("✏️ Sparziel bearbeiten")
def edit_goal_dialog(current_goal):
    user = st.session_state.user_name
    sym = CURRENCY_SYMBOLS.get(load_user_settings(user).get('currency','EUR'),'€')
    new_goal = st.number_input(f"Monatliches Sparziel ({sym})", min_value=0.0, value=float(current_goal), step=50.0)
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True): st.rerun()
    with cb:
        if st.button("💾 Speichern", use_container_width=True, type="primary"):
            save_goal(user, new_goal); st.rerun()

@st.dialog("➕ Neuer Dauerauftrag")
def add_dauerauftrag_dialog():
    user = st.session_state.user_name
    all_cats = DEFAULT_CATS.copy()
    for typ in ('Einnahme','Ausgabe','Depot'):
        custom = load_custom_cats(user, typ)
        all_cats[typ] = all_cats.get(typ,[]) + [c for c in custom if c not in all_cats.get(typ,[])]
    sym = CURRENCY_SYMBOLS.get(load_user_settings(user).get('currency','EUR'),'€')
    name = st.text_input("Name des Dauerauftrags")
    c1,c2 = st.columns(2)
    with c1: typ = st.selectbox("Typ", ['Einnahme','Ausgabe','Depot'])
    with c2: kat = st.selectbox("Kategorie", all_cats.get(typ,[]))
    betrag = st.number_input(f"Betrag ({sym})", min_value=0.01, step=1.0)
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True): st.rerun()
    with cb:
        if st.button("✅ Speichern", use_container_width=True, type="primary"):
            if name.strip(): save_dauerauftrag(user, name, betrag, typ, kat); st.rerun()
            else: st.error("Bitte Namen eingeben.")

@st.dialog("➕ Neuer Spartopf")
def add_topf_dialog():
    name = st.text_input("Name")
    c1,c2 = st.columns(2)
    with c1: emoji = st.text_input("Emoji", "🪣", max_chars=2)
    with c2: ziel = st.number_input("Sparziel (€)", min_value=1.0, step=50.0)
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True): st.rerun()
    with cb:
        if st.button("✅ Erstellen", use_container_width=True, type="primary"):
            if name.strip(): save_topf(st.session_state.user_name, name, ziel, emoji); st.rerun()
            else: st.error("Bitte Namen eingeben.")

@st.dialog("✏️ Spartopf bearbeiten")
def edit_topf_dialog(topf):
    new_name = st.text_input("Name", topf['name'])
    c1,c2 = st.columns(2)
    with c1: new_emoji = st.text_input("Emoji", topf['emoji'], max_chars=2)
    with c2: new_ziel = st.number_input("Sparziel", min_value=1.0, value=float(topf['ziel']), step=50.0)
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.topf_edit_data = None; st.rerun()
    with cb:
        if st.button("💾 Speichern", use_container_width=True, type="primary"):
            if new_name.strip():
                update_topf_meta(st.session_state.user_name, topf['id'], new_name, new_ziel, new_emoji)
                st.session_state.topf_edit_data = None; st.rerun()

@st.dialog("🗑️ Spartopf löschen")
def delete_topf_dialog(topf_id, topf_name):
    st.warning(f"Spartopf '{topf_name}' wirklich löschen?")
    ca,cb = st.columns(2)
    with ca:
        if st.button("Abbrechen", use_container_width=True):
            st.session_state.topf_delete_id = None; st.rerun()
    with cb:
        if st.button("🗑️ Löschen", use_container_width=True, type="primary"):
            delete_topf(st.session_state.user_name, topf_id)
            st.session_state.topf_delete_id = None; st.session_state.topf_delete_name = None; st.rerun()

# ── AUTH PAGES ───────────────────────────────────────────────
def show_login():
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']; acc2 = t['accent2']
    st.markdown(f"""
<div style="text-align:center;padding:60px 20px 40px;">
    <div style="font-size:64px;margin-bottom:16px;">⚖️</div>
    <h1 style="font-size:38px;font-weight:900;background:linear-gradient(135deg,{pri},{acc2});
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;">Balancely</h1>
    <p style="color:#64748b;font-size:16px;">Deine persönliche Finanzverwaltung</p>
</div>""", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        mode = st.session_state.auth_mode
        tab_login, tab_reg = st.tabs(["🔐 Anmelden","📝 Registrieren"])
        with tab_login:
            u = st.text_input("Benutzername", key="li_user")
            p = st.text_input("Passwort", type="password", key="li_pass")
            if st.button("🔐 Anmelden", use_container_width=True, type="primary", key="li_btn"):
                try:
                    df = _gs_read("users")
                    match = df[(df['username']==u)&(df['password']==make_hashes(p))]
                    if match.empty: st.error("Falscher Benutzername oder Passwort.")
                    else:
                        row = match.iloc[-1]
                        if not is_verified(row.get('verified',0)):
                            st.error("Bitte zuerst E-Mail bestätigen."); st.stop()
                        st.session_state.logged_in = True; st.session_state.user_name = u
                        settings = load_user_settings(u)
                        if settings.get('theme'): st.session_state.theme = settings['theme']
                        # Check first login
                        if check_first_login(u):
                            st.session_state.is_first_login = True
                            st.session_state.show_onboarding_prefs = True
                        _gs_invalidate("transactions"); st.rerun()
                except Exception as e: st.error(f"Fehler: {e}")
            st.markdown("---")
            st.markdown("**Passwort vergessen?**")
            re_email = st.text_input("Deine E-Mail-Adresse", key="re_email_inp")
            if st.button("📧 Code senden", use_container_width=True, key="re_send"):
                if not is_valid_email(re_email): st.error("Ungültige E-Mail.")
                else:
                    try:
                        df = _gs_read("users"); row = df[df['email']==re_email]
                        if row.empty: st.error("E-Mail nicht gefunden.")
                        else:
                            code = generate_code()
                            expiry = (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
                            st.session_state.reset_email = re_email
                            st.session_state.reset_code = make_hashes(code)
                            st.session_state.reset_expiry = expiry
                            if send_email(re_email,"🔑 Balancely Passwort-Reset", email_html("Dein Reset-Code:", code)):
                                st.success("Code gesendet! Prüfe dein Postfach.")
                    except Exception as e: st.error(f"Fehler: {e}")
            if st.session_state.reset_email:
                code_inp = st.text_input("Reset-Code eingeben", key="re_code_inp")
                new_pw = st.text_input("Neues Passwort", type="password", key="re_new_pw")
                if st.button("🔑 Passwort zurücksetzen", use_container_width=True, key="re_confirm"):
                    if datetime.datetime.now().isoformat() > st.session_state.reset_expiry:
                        st.error("Code abgelaufen.")
                    elif make_hashes(code_inp) != st.session_state.reset_code:
                        st.error("Falscher Code.")
                    else:
                        ok, msg = check_password_strength(new_pw)
                        if not ok: st.error(msg)
                        else:
                            try:
                                df = _gs_read("users")
                                df.loc[df['email']==st.session_state.reset_email,'password'] = make_hashes(new_pw)
                                _gs_update("users", df)
                                st.success("Passwort geändert!"); st.session_state.reset_email = ""; st.rerun()
                            except Exception as e: st.error(f"Fehler: {e}")
        with tab_reg:
            ru = st.text_input("Benutzername", key="reg_user")
            re_mail = st.text_input("E-Mail", key="reg_email")
            rp = st.text_input("Passwort", type="password", key="reg_pass")
            rp2 = st.text_input("Passwort wiederholen", type="password", key="reg_pass2")
            if st.button("📝 Registrieren", use_container_width=True, type="primary", key="reg_btn"):
                if not ru.strip(): st.error("Benutzername erforderlich.")
                elif not is_valid_email(re_mail): st.error("Ungültige E-Mail.")
                elif rp != rp2: st.error("Passwörter stimmen nicht überein.")
                else:
                    ok, msg = check_password_strength(rp)
                    if not ok: st.error(msg)
                    else:
                        try:
                            df = _gs_read("users")
                            if not df.empty and 'username' in df.columns and ru in df['username'].values:
                                st.error("Benutzername bereits vergeben.")
                            else:
                                code = generate_code()
                                expiry = (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
                                st.session_state.pending_user = {'username':ru,'email':re_mail,'password':make_hashes(rp),'verified':0}
                                st.session_state.verify_code = make_hashes(code)
                                st.session_state.verify_expiry = expiry
                                if send_email(re_mail,"✅ Balancely E-Mail bestätigen", email_html("Dein Bestätigungs-Code:", code)):
                                    st.session_state.auth_mode = 'verify'; st.success("Code gesendet!"); st.rerun()
                        except Exception as e: st.error(f"Fehler: {e}")
    if st.session_state.auth_mode == 'verify' and st.session_state.pending_user:
        col2 = st.columns([1,2,1])[1]
        with col2:
            st.info(f"Code an {st.session_state.pending_user.get('email','')} gesendet.")
            code_in = st.text_input("Bestätigungs-Code", key="verify_code_inp")
            if st.button("✅ Bestätigen", use_container_width=True, type="primary"):
                if datetime.datetime.now().isoformat() > st.session_state.verify_expiry:
                    st.error("Code abgelaufen.")
                elif make_hashes(code_in) != st.session_state.verify_code:
                    st.error("Falscher Code.")
                else:
                    try:
                        df = _gs_read("users")
                        new_user = {**st.session_state.pending_user, 'verified':1}
                        _gs_update("users", pd.concat([df, pd.DataFrame([new_user])], ignore_index=True))
                        st.session_state.auth_mode = 'login'; st.session_state.pending_user = {}
                        st.success("Account bestätigt! Bitte anmelden."); st.rerun()
                    except Exception as e: st.error(f"Fehler: {e}")

# ── DASHBOARD ────────────────────────────────────────────────
def show_dashboard(user, df_all, settings):
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']; acc2 = t['accent2']
    section_header("🏠","Dashboard","Dein finanzieller Überblick")

    offset = st.session_state.dash_month_offset
    now = datetime.date.today()
    target = (now.replace(day=1) + datetime.timedelta(days=32*(-offset))).replace(day=1) if offset else now.replace(day=1)
    month_label = target.strftime("%B %Y") if offset else "Aktueller Monat"

    col_nav = st.columns([1,3,1])
    with col_nav[0]:
        if st.button("◀ Vorheriger", use_container_width=True): st.session_state.dash_month_offset += 1; st.rerun()
    with col_nav[1]:
        st.markdown(f'<div style="text-align:center;padding:8px;color:#94a3b8;font-weight:600;">{month_label}</div>', unsafe_allow_html=True)
    with col_nav[2]:
        if offset > 0:
            if st.button("Nächster ▶", use_container_width=True): st.session_state.dash_month_offset -= 1; st.rerun()

    if df_all.empty or 'datum' not in df_all.columns:
        st.info("Noch keine Transaktionen vorhanden."); return

    df_all = df_all.copy()
    df_all['datum_dt'] = pd.to_datetime(df_all['datum'], errors='coerce')
    df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce').fillna(0)
    df_month = df_all[(df_all['datum_dt'].dt.year==target.year)&(df_all['datum_dt'].dt.month==target.month)]

    ein_m = df_month[df_month['typ']=='Einnahme']['betrag_num'].sum()
    aus_m = abs(df_month[df_month['typ']=='Ausgabe']['betrag_num'].sum())
    dep_m = df_month[df_month['typ']=='Depot']['betrag_num'].sum()
    sp_m  = df_month[df_month['typ']=='Spartopf']['betrag_num'].sum()
    bal_m = ein_m - aus_m - abs(dep_m) - abs(sp_m)
    budget = float(settings.get('budget',0) or 0)

    m1,m2,m3,m4 = st.columns(4)
    def metric_card(col, icon, label, value, color, delta=None):
        delta_html = f'<p style="font-size:12px;color:{"#4ade80" if delta>=0 else "#f87171"};margin:2px 0 0;">{("+" if delta>=0 else "")}{delta:.2f} {sym}</p>' if delta is not None else ""
        col.markdown(f'''<div style="background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:20px;text-align:center;">
            <div style="font-size:28px;">{icon}</div>
            <p style="color:#64748b;font-size:12px;margin:4px 0;">{label}</p>
            <h2 style="font-size:22px;font-weight:800;color:{color};margin:4px 0;">{value}</h2>
            {delta_html}</div>''', unsafe_allow_html=True)
    metric_card(m1,"💰","Einnahmen",f"{ein_m:,.2f} {sym}","#4ade80")
    metric_card(m2,"💸","Ausgaben",f"{aus_m:,.2f} {sym}","#f87171")
    metric_card(m3,"📈","Depot",f"{abs(dep_m):,.2f} {sym}","#38bdf8")
    metric_card(m4,"⚖️","Bilanz",f"{bal_m:,.2f} {sym}",pri)
    
    if budget > 0:
        pct = min(aus_m / budget, 1.0)
        bar_color = "#f87171" if pct > 0.9 else "#fb923c" if pct > 0.7 else "#4ade80"
        st.markdown(f'''<div style="margin-top:16px;background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:#94a3b8;font-size:13px;">📊 Budget {month_label}</span>
                <span style="color:#f1f5f9;font-size:13px;font-weight:600;">{aus_m:.2f} / {budget:.2f} {sym}</span>
            </div>
            <div style="background:#1e293b;border-radius:6px;height:8px;">
                <div style="width:{pct*100:.1f}%;background:{bar_color};border-radius:6px;height:8px;transition:width .5s;"></div>
            </div></div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3,2])
    with c1:
        st.markdown(f'<h3 style="color:#94a3b8;font-size:14px;font-weight:600;margin-bottom:12px;">📋 LETZTE TRANSAKTIONEN</h3>', unsafe_allow_html=True)
        recent = df_month.sort_values('datum_dt', ascending=False).head(8)
        if recent.empty:
            st.markdown('<p style="color:#475569;text-align:center;padding:30px;">Keine Transaktionen diesen Monat</p>', unsafe_allow_html=True)
        else:
            for _, row in recent.iterrows():
                typ = str(row.get('typ',''))
                betrag_num = float(row.get('betrag_num',0))
                if typ == 'Einnahme': col_b, sign = '#4ade80', '+'
                elif typ == 'Depot': col_b, sign = '#38bdf8', '-'
                elif typ == 'Spartopf': col_b, sign = '#a78bfa', '-'
                else: col_b, sign = '#f87171', '-'
                display_b = abs(betrag_num)
                ts = format_timestamp(row.get('timestamp',''), row.get('datum',''))
                notiz = str(row.get('notiz',''))
                notiz_html = f' <span style="color:#475569;font-size:11px;">· {notiz[:25]}{"..." if len(notiz)>25 else ""}</span>' if notiz else ""
                st.markdown(f'''<div style="display:flex;justify-content:space-between;align-items:center;
                    padding:10px 14px;margin-bottom:6px;background:#0f172a;border-radius:10px;border-left:3px solid {col_b};">
                    <div>
                        <span style="font-size:13px;font-weight:600;color:#f1f5f9;">{row.get("kategorie","")}</span>
                        {notiz_html}
                        <br><span style="font-size:11px;color:#475569;">{ts}</span>
                    </div>
                    <span style="font-size:14px;font-weight:800;color:{col_b};">{sign}{display_b:.2f} {sym}</span>
                </div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<h3 style="color:#94a3b8;font-size:14px;font-weight:600;margin-bottom:12px;">🥧 MONATSVERTEILUNG</h3>', unsafe_allow_html=True)
        try:
            import plotly.express as px
            pie_data = {'Einnahmen':ein_m,'Ausgaben':aus_m,'Depot':abs(dep_m),'Sparen':abs(sp_m)}
            pie_data = {k:v for k,v in pie_data.items() if v > 0}
            if pie_data:
                fig = px.pie(values=list(pie_data.values()), names=list(pie_data.keys()),
                             color_discrete_sequence=['#4ade80','#f87171','#38bdf8','#a78bfa'],
                             hole=0.4)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  font_color='#94a3b8', margin=dict(t=10,b=10,l=10,r=10),
                                  legend=dict(font=dict(color='#94a3b8')))
                fig.update_traces(textfont_color='#f1f5f9')
                st.plotly_chart(fig, use_container_width=True)
        except: pass

# ── TRANSAKTIONEN ────────────────────────────────────────────
def show_transaktionen(user, df_all, settings):
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']
    section_header("💸","Transaktionen","Einnahmen, Ausgaben und Depot-Transaktionen")

    all_cats = DEFAULT_CATS.copy()
    for typ in ('Einnahme','Ausgabe','Depot'):
        custom = load_custom_cats(user, typ)
        all_cats[typ] = all_cats.get(typ,[]) + [c for c in custom if c not in all_cats.get(typ,[])]

    # ── New transaction form ──
    with st.expander("➕ Neue Transaktion hinzufügen", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
        with c1: typ = st.selectbox("Typ", ['Einnahme','Ausgabe','Depot'], key="new_tx_typ")
        with c2: kat = st.selectbox("Kategorie", all_cats.get(typ,[]), key="new_tx_kat")
        with c3: datum = st.date_input("Datum", value=datetime.date.today(), key="new_tx_datum")
        with c4: betrag = st.number_input(f"Betrag ({sym})", min_value=0.01, step=0.5, key="new_tx_betrag")
        notiz = st.text_input("Notiz (optional)", key="new_tx_notiz")
        if st.button("💾 Transaktion speichern", type="primary", use_container_width=True):
            betrag_save = betrag if typ == 'Einnahme' else -betrag
            try:
                df = _gs_read("transactions")
                new_row = pd.DataFrame([{'user':user,'datum':str(datum),
                    'timestamp':datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'typ':typ,'kategorie':kat,'betrag':betrag_save,'notiz':notiz,'deleted':''}])
                _gs_update("transactions", pd.concat([df, new_row], ignore_index=True))
                _gs_invalidate("transactions"); st.success("✅ Gespeichert!"); st.rerun()
            except Exception as e: st.error(f"Fehler: {e}")

    # ── Daueraufträge ──
    with st.expander("⚙️ Daueraufträge verwalten", expanded=False):
        das = load_dauerauftraege(user)
        if st.button("▶ Daueraufträge jetzt anwenden", use_container_width=True):
            booked = apply_dauerauftraege(user)
            if booked: st.success(f"{booked} Dauerauftrag/Aufträge gebucht!"); _gs_invalidate("transactions"); st.rerun()
            else: st.info("Keine neuen Buchungen (bereits gebucht oder keine aktiven Aufträge).")
        if das:
            for da in das:
                dc1,dc2,dc3 = st.columns([3,1,1])
                with dc1:
                    color = TYPE_COLORS.get(da['typ'],'#94a3b8')
                    st.markdown(f'<div style="padding:8px 12px;background:#0f172a;border-radius:8px;border-left:3px solid {color};">'
                        f'<span style="font-weight:600;color:#f1f5f9;">{da["name"]}</span> '
                        f'<span style="color:#64748b;font-size:12px;">{da["typ"]} · {da["kategorie"]} · {da["betrag"]} {sym}/Monat</span></div>',
                        unsafe_allow_html=True)
                with dc3:
                    if st.button("🗑️", key=f"del_da_{da['id']}"): delete_dauerauftrag(user, da['id']); st.rerun()
        else: st.markdown('<p style="color:#475569;">Noch keine Daueraufträge.</p>', unsafe_allow_html=True)
        if st.button("➕ Dauerauftrag hinzufügen"): add_dauerauftrag_dialog()

    # ── Transaction list ──
    if df_all.empty or 'datum' not in df_all.columns:
        st.info("Noch keine Transaktionen."); return

    df_all = df_all.copy()
    df_all['datum_dt'] = pd.to_datetime(df_all['datum'], errors='coerce')
    df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce').fillna(0)
    df_sorted = df_all.sort_values(['datum_dt','timestamp'], ascending=[False,False])

    search = st.text_input("🔍 Suche...", value=st.session_state.tx_search, key="tx_search_inp", placeholder="Kategorie, Notiz...")
    st.session_state.tx_search = search

    if search.strip():
        mask = (df_sorted['kategorie'].str.contains(search, case=False, na=False) |
                df_sorted['notiz'].str.contains(search, case=False, na=False))
        df_sorted = df_sorted[mask]

    PAGE_SIZE = 20
    total = len(df_sorted); pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    st.session_state.tx_page = min(st.session_state.tx_page, pages-1)
    page = st.session_state.tx_page
    df_page = df_sorted.iloc[page*PAGE_SIZE:(page+1)*PAGE_SIZE]

    st.markdown(f'<p style="color:#64748b;font-size:13px;margin-bottom:12px;">{total} Transaktionen · Seite {page+1}/{pages}</p>', unsafe_allow_html=True)

    for i, (_, row) in enumerate(df_page.iterrows()):
        typ = str(row.get('typ',''))
        bnum = float(row.get('betrag_num',0))
        if typ=='Einnahme': col_b,sign='#4ade80','+'
        elif typ=='Depot': col_b,sign='#38bdf8','-'
        elif typ=='Spartopf': col_b,sign='#a78bfa','-'
        else: col_b,sign='#f87171','-'
        display_b = abs(bnum); ts = format_timestamp(row.get('timestamp',''),row.get('datum',''))
        notiz = str(row.get('notiz',''))
        notiz_html = f' · <span style="color:#475569;font-size:11px;">{notiz[:30]}{"..." if len(notiz)>30 else ""}</span>' if notiz else ""
        rc1,rc2,rc3 = st.columns([6,1,1])
        with rc1:
            st.markdown(f'''<div style="display:flex;justify-content:space-between;align-items:center;
                padding:10px 14px;background:#0f172a;border-radius:10px;border-left:3px solid {col_b};">
                <div><span style="font-size:13px;font-weight:600;color:#f1f5f9;">{row.get("kategorie","")}</span>
                {notiz_html}<br><span style="font-size:11px;color:#475569;">{ts}</span></div>
                <span style="font-size:14px;font-weight:800;color:{col_b};">{sign}{display_b:.2f} {sym}</span>
            </div>''', unsafe_allow_html=True)
        with rc2:
            if st.button("✏️", key=f"edit_tx_{page}_{i}"): st.session_state.edit_idx = row.to_dict(); edit_transaction_dialog(row.to_dict())
        with rc3:
            if st.button("🗑️", key=f"del_tx_{page}_{i}"): delete_transaction_dialog(row.to_dict())

    if pages > 1:
        pc1,pc2,pc3 = st.columns(3)
        with pc1:
            if page > 0 and st.button("◀ Zurück", use_container_width=True): st.session_state.tx_page -= 1; st.rerun()
        with pc2:
            st.markdown(f'<div style="text-align:center;color:#64748b;font-size:13px;padding:8px;">{page+1} / {pages}</div>', unsafe_allow_html=True)
        with pc3:
            if page < pages-1 and st.button("Weiter ▶", use_container_width=True): st.session_state.tx_page += 1; st.rerun()

# ── ANALYSEN ─────────────────────────────────────────────────
def show_analysen(user, df_all, settings):
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']; acc2 = t['accent2']
    section_header("📊","Analysen","Interaktive Charts und Visualisierungen")

    if df_all.empty or 'datum' not in df_all.columns:
        st.info("Noch keine Transaktionen vorhanden."); return

    df_all = df_all.copy()
    df_all['datum_dt'] = pd.to_datetime(df_all['datum'], errors='coerce')
    df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce').fillna(0)

    now = datetime.date.today()
    offset = st.session_state.analysen_month_offset
    target = (now.replace(day=1) + datetime.timedelta(days=32*(-offset))).replace(day=1) if offset else now.replace(day=1)

    col_nav = st.columns([1,3,1])
    with col_nav[0]:
        if st.button("◀", key="an_prev"): st.session_state.analysen_month_offset += 1; st.rerun()
    with col_nav[1]:
        st.markdown(f'<div style="text-align:center;color:#94a3b8;font-weight:600;padding:8px;">{target.strftime("%B %Y")}</div>', unsafe_allow_html=True)
    with col_nav[2]:
        if offset > 0 and st.button("▶", key="an_next"): st.session_state.analysen_month_offset -= 1; st.rerun()

    df_month = df_all[(df_all['datum_dt'].dt.year==target.year)&(df_all['datum_dt'].dt.month==target.month)]

    try:
        import plotly.graph_objects as go
        import plotly.express as px

        # ── 1. SPARZIEL ──────────────────────────────────────────
        st.markdown("---")
        st.markdown(f'<h3 style="color:{pri};font-size:16px;font-weight:700;">🎯 Sparziel diesen Monat</h3>', unsafe_allow_html=True)

        spar_goal = load_goal(user)
        ein_m = df_month[df_month['typ']=='Einnahme']['betrag_num'].sum()
        aus_m = abs(df_month[df_month['typ']=='Ausgabe']['betrag_num'].sum())
        # Depot and Spartopf einzahlungen count as "gespart" (v5 change)
        monat_dep = abs(df_month[df_month['typ']=='Depot']['betrag_num'].sum())
        monat_sp_einzahl = abs(df_month[(df_month['typ']=='Spartopf')&(df_month['betrag_num']<0)]['betrag_num'].sum())
        bank_aktuell = ein_m - aus_m - monat_dep - monat_sp_einzahl
        akt_spar = bank_aktuell + monat_dep + monat_sp_einzahl  # = ein_m - aus_m

        sg1, sg2, sg3 = st.columns(3)
        def spar_metric(col, label, value, color):
            col.markdown(f'''<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;text-align:center;">
                <p style="color:#64748b;font-size:12px;margin:0;">{label}</p>
                <h3 style="color:{color};font-size:20px;font-weight:800;margin:4px 0;">{value:.2f} {sym}</h3>
            </div>''', unsafe_allow_html=True)
        spar_metric(sg1, "🏦 Kontostand (Bank)", bank_aktuell, '#38bdf8')
        spar_metric(sg2, "📈 Depot (gespart)", monat_dep, '#4ade80')
        spar_metric(sg3, "🪣 Spartöpfe (gespart)", monat_sp_einzahl, '#a78bfa')

        if spar_goal > 0:
            pct = min(akt_spar / spar_goal, 1.0) if spar_goal else 0
            bar_color = "#4ade80" if pct >= 1.0 else "#fb923c" if pct >= 0.5 else "#f87171"
            st.markdown(f'''<div style="margin-top:16px;background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <span style="color:#94a3b8;font-size:13px;">Sparziel-Fortschritt</span>
                    <span style="color:#f1f5f9;font-size:13px;font-weight:600;">{akt_spar:.2f} / {spar_goal:.2f} {sym} ({pct*100:.0f}%)</span>
                </div>
                <div style="background:#1e293b;border-radius:6px;height:10px;">
                    <div style="width:{pct*100:.1f}%;background:{bar_color};border-radius:6px;height:10px;"></div>
                </div></div>''', unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="color:#475569;font-size:13px;margin-top:8px;">Gesamt gespart: <strong style="color:{pri}">{akt_spar:.2f} {sym}</strong> · Kein Sparziel gesetzt.</p>', unsafe_allow_html=True)

        if st.button("✏️ Sparziel bearbeiten"): edit_goal_dialog(spar_goal)

        # ── 2. AUSGABEN nach Kategorie (Balken) ──────────────────
        st.markdown("---")
        df_aus = df_all[df_all['typ']=='Ausgabe'].copy()
        df_aus_year = df_aus[df_aus['datum_dt'].dt.year == now.year].copy()
        year_months = max(1, now.month if now.year == target.year else 12)

        if not df_aus_year.empty:
            kat_grp_year = df_aus_year.groupby('kategorie')['betrag_num'].apply(lambda x: abs(x.sum())).reset_index()
            kat_grp_year.columns = ['kategorie','betrag_num']
            kat_grp_year['avg_monthly'] = kat_grp_year['betrag_num'] / year_months
            kat_grp_year = kat_grp_year.sort_values('avg_monthly', ascending=True).tail(10)

            n = len(kat_grp_year)
            colors = PALETTE_AUS[:n] if n <= len(PALETTE_AUS) else PALETTE_AUS * (n // len(PALETTE_AUS) + 1)
            colors = colors[:n]

            fig_bar = go.Figure(go.Bar(
                y=kat_grp_year['kategorie'],
                x=kat_grp_year['avg_monthly'],
                orientation='h',
                marker_color=colors,
                text=[f"Ø {v:.2f} {sym}/Mo" for v in kat_grp_year['avg_monthly']],
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='#ffffff', size=12),
            ))
            fig_bar.update_layout(
                title=f"Top Ausgaben-Kategorien (Ø pro Monat · {now.year})",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'), height=350,
                xaxis=dict(showgrid=False, color='#475569', title=f"Ø {sym}/Monat"),
                yaxis=dict(showgrid=False, color='#94a3b8'),
                margin=dict(l=20,r=20,t=40,b=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── 3. EINNAHMEN vs AUSGABEN (linie) ─────────────────────
        st.markdown("---")
        df_trend = df_all[df_all['typ'].isin(['Einnahme','Ausgabe'])].copy()
        if not df_trend.empty:
            df_trend['month'] = df_trend['datum_dt'].dt.to_period('M').astype(str)
            monthly = df_trend.groupby(['month','typ'])['betrag_num'].sum().reset_index()
            monthly['betrag_num'] = monthly.apply(lambda r: r['betrag_num'] if r['typ']=='Einnahme' else abs(r['betrag_num']), axis=1)
            monthly = monthly.sort_values('month').tail(24)
            fig_line = go.Figure()
            for typ_name, color in [('Einnahme','#4ade80'),('Ausgabe','#f87171')]:
                sub = monthly[monthly['typ']==typ_name]
                if not sub.empty:
                    fig_line.add_trace(go.Scatter(x=sub['month'], y=sub['betrag_num'],
                        name=typ_name, line=dict(color=color, width=2), fill='tozeroy',
                        fillcolor=color.replace(')',',0.1)').replace('rgb','rgba') if 'rgb' in color else color + '1a'))
            fig_line.update_layout(
                title="Einnahmen vs. Ausgaben (letzte 24 Monate)",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'), height=300,
                xaxis=dict(showgrid=False, color='#475569'),
                yaxis=dict(showgrid=False, color='#475569', title=sym),
                legend=dict(font=dict(color='#94a3b8')),
                margin=dict(l=20,r=20,t=40,b=20),
            )
            st.plotly_chart(fig_line, use_container_width=True)

        # ── 4. HEATMAP ───────────────────────────────────────────
        st.markdown("---")
        st.markdown(f'<h3 style="color:{pri};font-size:16px;font-weight:700;">🗓️ Ausgaben-Heatmap</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color:#64748b;font-size:13px;margin-bottom:16px;">Hellere Felder = höhere Ausgaben an diesem Tag.</p>', unsafe_allow_html=True)

        h_offset = st.session_state.heatmap_month_offset
        hmap_target = (now.replace(day=1) + datetime.timedelta(days=32*(-h_offset))).replace(day=1) if h_offset else now.replace(day=1)
        hcol1,hcol2,hcol3 = st.columns([1,3,1])
        with hcol1:
            if st.button("◀", key="hm_prev"): st.session_state.heatmap_month_offset += 1; st.rerun()
        with hcol2:
            st.markdown(f'<div style="text-align:center;color:#94a3b8;font-weight:600;padding:8px;">{hmap_target.strftime("%B %Y")}</div>', unsafe_allow_html=True)
        with hcol3:
            if h_offset > 0 and st.button("▶", key="hm_next"): st.session_state.heatmap_month_offset -= 1; st.rerun()

        df_hm = df_all[(df_all['typ']=='Ausgabe')&(df_all['datum_dt'].dt.year==hmap_target.year)&(df_all['datum_dt'].dt.month==hmap_target.month)].copy()
        import calendar
        cal = calendar.monthcalendar(hmap_target.year, hmap_target.month)
        day_spend = {}
        if not df_hm.empty:
            for _, row in df_hm.iterrows():
                d = row['datum_dt'].day if pd.notna(row['datum_dt']) else None
                if d: day_spend[d] = day_spend.get(d, 0) + abs(float(row['betrag_num']))
        max_val = max(day_spend.values()) if day_spend else 1
        day_names = ['Mo','Di','Mi','Do','Fr','Sa','So']
        hm_html = '<div style="overflow-x:auto;"><table style="border-collapse:separate;border-spacing:4px;width:100%;">'
        hm_html += '<tr>' + ''.join(f'<th style="color:#475569;font-size:11px;text-align:center;padding:4px;">{d}</th>' for d in day_names) + '</tr>'
        for week in cal:
            hm_html += '<tr>'
            for day in week:
                if day == 0:
                    hm_html += '<td style="background:#0a1020;border-radius:6px;height:44px;"></td>'
                else:
                    val = day_spend.get(day, 0)
                    if val > 0:
                        # v5: lighter = more spending
                        intensity = val / max_val
                        r = int(100 + intensity * 155)  # 100→255 as intensity increases
                        g = int(10 + intensity * 90)    # 10→100
                        b = int(10 + intensity * 5)     # 10→15
                        bg = f"rgba({r},{g},{b},0.90)"
                        text_color = "#fff"
                    else:
                        bg = "#0f172a"; text_color = "#334155"
                    hm_html += (f'<td style="background:{bg};border-radius:6px;text-align:center;height:44px;vertical-align:middle;cursor:default;"'
                        f' title="{val:.2f} {sym}"><span style="font-size:12px;font-weight:600;color:{text_color};">{day}</span>'
                        + (f'<br><span style="font-size:9px;color:{text_color};opacity:0.8;">{val:.0f}</span>' if val > 0 else "")
                        + '</td>')
            hm_html += '</tr>'
        hm_html += '</table></div>'
        st.markdown(hm_html, unsafe_allow_html=True)

    except ImportError:
        st.warning("Plotly nicht installiert.")
    except Exception as e:
        st.error(f"Fehler in Analysen: {e}")

# ── SPARTÖPFE ────────────────────────────────────────────────
def show_spartoepfe(user, df_all, settings):
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']
    section_header("🪣","Spartöpfe","Spare gezielt für deine Ziele")

    toepfe = load_toepfe(user)

    if st.button("➕ Neuen Spartopf erstellen", type="primary"): add_topf_dialog()

    if not toepfe:
        st.markdown('<div style="text-align:center;padding:60px;color:#475569;">Noch keine Spartöpfe. Erstelle deinen ersten!</div>', unsafe_allow_html=True)
        return

    cols = st.columns(min(3, len(toepfe)))
    for i, topf in enumerate(toepfe):
        with cols[i % 3]:
            pct = min(topf['gespart'] / topf['ziel'], 1.0) if topf['ziel'] > 0 else 0
            bar_color = "#4ade80" if pct >= 1.0 else topf['farbe']
            st.markdown(f'''<div style="background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:20px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <span style="font-size:28px;">{topf["emoji"]}</span>
                    <span style="font-size:13px;font-weight:700;color:#f1f5f9;">{topf["name"]}</span>
                </div>
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                        <span style="font-size:12px;color:#64748b;">{topf["gespart"]:.2f} {sym}</span>
                        <span style="font-size:12px;color:#64748b;">{topf["ziel"]:.2f} {sym}</span>
                    </div>
                    <div style="background:#1e293b;border-radius:6px;height:8px;">
                        <div style="width:{pct*100:.1f}%;background:{bar_color};border-radius:6px;height:8px;"></div>
                    </div>
                    <p style="text-align:right;font-size:11px;color:#475569;margin:4px 0 0;">{pct*100:.0f}%</p>
                </div></div>''', unsafe_allow_html=True)

            d_in = st.number_input(f"Einzahlen ({sym})", min_value=0.01, step=5.0, key=f"topf_in_{topf['id']}")
            c1,c2,c3 = st.columns(3)
            with c1:
                if st.button("↓ Einzahlen", key=f"topf_dep_{topf['id']}", use_container_width=True, type="primary"):
                    update_topf_gespart(user, topf['id'], topf['name'], d_in); _gs_invalidate("toepfe","transactions"); st.rerun()
            with c2:
                if st.button("✏️", key=f"topf_edit_{topf['id']}", use_container_width=True):
                    st.session_state.topf_edit_data = topf; st.rerun()
            with c3:
                if st.button("🗑️", key=f"topf_del_{topf['id']}", use_container_width=True):
                    st.session_state.topf_delete_id = topf['id']
                    st.session_state.topf_delete_name = topf['name']; st.rerun()

    if st.session_state.topf_edit_data:
        edit_topf_dialog(st.session_state.topf_edit_data)
    if st.session_state.topf_delete_id:
        delete_topf_dialog(st.session_state.topf_delete_id, st.session_state.topf_delete_name)

# ── EINSTELLUNGEN ────────────────────────────────────────────
def show_einstellungen(user, settings):
    sym = CURRENCY_SYMBOLS.get(settings.get('currency','EUR'),'€')
    t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
    pri = t['primary']
    section_header("⚙️","Einstellungen","Personalisiere deine Erfahrung")

    tab_profil, tab_aussehen, tab_kategorien, tab_budget = st.tabs(["👤 Profil","🎨 Aussehen","🏷️ Kategorien","💰 Budget"])

    with tab_profil:
        st.markdown("#### Benutzerprofil")
        try:
            df_users = _gs_read("users")
            user_row = df_users[df_users['username']==user]
            email_val = user_row.iloc[-1].get('email','') if not user_row.empty else ''
        except: email_val = ''
        st.markdown(f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin-bottom:16px;">'
            f'<p style="color:#64748b;font-size:12px;margin:0;">Benutzername</p>'
            f'<p style="color:#f1f5f9;font-size:16px;font-weight:700;margin:4px 0 0;">{user}</p>'
            f'<p style="color:#64748b;font-size:12px;margin:8px 0 0;">E-Mail</p>'
            f'<p style="color:#f1f5f9;font-size:14px;margin:4px 0 0;">{email_val}</p></div>', unsafe_allow_html=True)

        with st.expander("🔑 Passwort ändern"):
            old_pw = st.text_input("Altes Passwort", type="password", key="chg_old")
            new_pw1 = st.text_input("Neues Passwort", type="password", key="chg_new1")
            new_pw2 = st.text_input("Neues Passwort bestätigen", type="password", key="chg_new2")
            if st.button("💾 Passwort speichern", use_container_width=True):
                try:
                    df = _gs_read("users"); match = df[(df['username']==user)&(df['password']==make_hashes(old_pw))]
                    if match.empty: st.error("Altes Passwort falsch.")
                    elif new_pw1 != new_pw2: st.error("Passwörter stimmen nicht überein.")
                    else:
                        ok, msg = check_password_strength(new_pw1)
                        if not ok: st.error(msg)
                        else:
                            df.loc[df['username']==user,'password'] = make_hashes(new_pw1)
                            _gs_update("users", df); st.success("Passwort geändert!")
                except Exception as e: st.error(f"Fehler: {e}")

        st.markdown("---")
        if st.button("🚪 Abmelden", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
        if not st.session_state.confirm_delete_account:
            if st.button("🗑️ Account löschen", use_container_width=True):
                st.session_state.confirm_delete_account = True; st.rerun()
        else:
            st.error("Wirklich Account und alle Daten löschen?")
            ca,cb = st.columns(2)
            with ca:
                if st.button("Abbrechen", use_container_width=True):
                    st.session_state.confirm_delete_account = False; st.rerun()
            with cb:
                if st.button("🗑️ Ja, löschen", use_container_width=True, type="primary"):
                    try:
                        for ws in ("users","transactions","categories","settings","goals","dauerauftraege","toepfe"):
                            try:
                                df = _gs_read(ws)
                                if 'user' in df.columns: df = df[df['user']!=user]
                                elif 'username' in df.columns: df = df[df['username']!=user]
                                _gs_update(ws, df)
                            except: pass
                        for k in list(st.session_state.keys()): del st.session_state[k]
                        st.rerun()
                    except Exception as e: st.error(f"Fehler: {e}")

    with tab_aussehen:
        st.markdown("#### Theme")
        theme_cols = st.columns(3)
        theme_icons = {'Ocean Blue':'🌊','Emerald Green':'🌿','Deep Purple':'🔮'}
        for i, (tc, tname) in enumerate(zip(theme_cols, THEMES.keys())):
            with tc:
                th = THEMES[tname]; selected = st.session_state.theme == tname
                btn_type = "primary" if selected else "secondary"
                if st.button(f"{theme_icons.get(tname,'🎨')} {tname}", key=f"theme_{tname}", use_container_width=True, type=btn_type):
                    st.session_state.theme = tname
                    save_user_settings(user, theme=tname); st.rerun()
                st.markdown(f'<div style="height:6px;border-radius:3px;background:{th["primary"]};margin-top:4px;"></div>', unsafe_allow_html=True)

    with tab_kategorien:
        st.markdown("#### Eigene Kategorien")
        if st.button("➕ Neue Kategorie", type="primary"): add_cat_dialog()
        for typ in ('Einnahme','Ausgabe','Depot'):
            custom = load_custom_cats(user, typ)
            if custom:
                color = '#4ade80' if typ=='Einnahme' else '#f87171' if typ=='Ausgabe' else '#38bdf8'
                st.markdown(f'<h4 style="color:{color};font-size:13px;margin:16px 0 8px;">{typ}</h4>', unsafe_allow_html=True)
                for cat in custom:
                    cc1,cc2,cc3 = st.columns([5,1,1])
                    with cc1:
                        st.markdown(f'<div style="padding:8px 12px;background:#0f172a;border-radius:8px;color:#f1f5f9;font-size:13px;">{cat}</div>', unsafe_allow_html=True)
                    with cc2:
                        if st.button("✏️", key=f"ecat_{typ}_{cat}"):
                            st.session_state.edit_cat_data = {'user':user,'typ':typ,'kategorie':cat}; st.rerun()
                    with cc3:
                        if st.button("🗑️", key=f"dcat_{typ}_{cat}"):
                            st.session_state.delete_cat_data = {'user':user,'typ':typ,'kategorie':cat}; st.rerun()

        if st.session_state.edit_cat_data: edit_cat_dialog(st.session_state.edit_cat_data)
        if st.session_state.delete_cat_data: delete_cat_dialog(st.session_state.delete_cat_data)

    with tab_budget:
        st.markdown("#### Monatliches Budget")
        budget_curr = float(settings.get('budget',0) or 0)
        st.markdown(f'<p style="color:#94a3b8;">Aktuelles Budget: <strong style="color:{pri}">{budget_curr:.2f} {sym}</strong></p>', unsafe_allow_html=True)
        new_budget = st.number_input(f"Neues Budget ({sym})", min_value=0.0, value=budget_curr, step=50.0)
        curr_list = list(CURRENCY_SYMBOLS.keys())
        curr_curr = settings.get('currency','EUR')
        curr_idx = curr_list.index(curr_curr) if curr_curr in curr_list else 0
        new_curr = st.selectbox("Währung", curr_list, index=curr_idx, format_func=lambda c: f"{c} ({CURRENCY_SYMBOLS[c]})")
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            save_user_settings(user, budget=new_budget, currency=new_curr); _gs_invalidate("settings"); st.success("Gespeichert!"); st.rerun()

# ── MAIN APP ─────────────────────────────────────────────────
def main():
    inject_theme(st.session_state.get('theme','Ocean Blue'))

    if not st.session_state.logged_in:
        show_login(); return

    user = st.session_state.user_name

    # First-login onboarding
    if st.session_state.get('show_onboarding_prefs'):
        onboarding_prefs_dialog()

    # Walkthrough
    if st.session_state.get('show_walkthrough'):
        walkthrough_dialog()

    # Sidebar
    with st.sidebar:
        t = THEMES.get(st.session_state.get('theme','Ocean Blue'), THEMES['Ocean Blue'])
        pri = t['primary']; acc2 = t['accent2']
        st.markdown(f'''<div style="padding:20px 0 16px;text-align:center;border-bottom:1px solid #1e293b;margin-bottom:16px;">
            <div style="font-size:32px;">⚖️</div>
            <h2 style="font-size:18px;font-weight:800;background:linear-gradient(135deg,{pri},{acc2});
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:4px 0;">Balancely</h2>
            <p style="font-size:12px;color:#475569;margin:0;">Hallo, {user} 👋</p>
        </div>''', unsafe_allow_html=True)

        nav_items = [("🏠","Dashboard"),("💸","Transaktionen"),("📊","Analysen"),("🪣","Spartöpfe"),("⚙️","Einstellungen")]
        for icon, label in nav_items:
            active = st.session_state.get('_last_menu','') == label
            btn_style = f"background:linear-gradient(135deg,{pri},{acc2});" if active else "background:#1e293b;"
            if st.button(f"{icon} {label}", key=f"nav_{label}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state._last_menu = label; st.rerun()

        st.markdown("---")
        if st.button("🗺️ App-Tour starten", use_container_width=True):
            st.session_state.show_walkthrough = True; st.session_state.walkthrough_step = 0; st.rerun()

    menu = st.session_state.get('_last_menu','Dashboard')

    # Load user data
    try:
        df_all = _gs_read("transactions")
        if not df_all.empty and 'user' in df_all.columns:
            df_all = df_all[
                (df_all['user'] == user) &
                (~df_all['deleted'].astype(str).str.strip().str.lower().isin(['true','1','1.0']))
            ].copy()
        else:
            df_all = pd.DataFrame()
    except: df_all = pd.DataFrame()

    settings = load_user_settings(user)

    if menu == "Dashboard": show_dashboard(user, df_all, settings)
    elif menu == "Transaktionen": show_transaktionen(user, df_all, settings)
    elif menu == "Analysen": show_analysen(user, df_all, settings)
    elif menu == "Spartöpfe": show_spartoepfe(user, df_all, settings)
    elif menu == "Einstellungen": show_einstellungen(user, settings)
    else: show_dashboard(user, df_all, settings)

main()
