import datetime
import time
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from constants import TOPF_PALETTE

conn = st.connection("gsheets", type=GSheetsConnection)


# ── GSheet Cache ─────────────────────────────────────────────

def _gs_read(ws):
    k = f"_gs_cache_{ws}"
    if k not in st.session_state:
        st.session_state[k] = conn.read(worksheet=ws, ttl=0)
    return st.session_state[k].copy()


def _gs_update(ws, df):
    conn.update(worksheet=ws, data=df)
    st.session_state[f"_gs_cache_{ws}"] = df.copy()


def _gs_invalidate(*wss):
    for ws in wss:
        st.session_state.pop(f"_gs_cache_{ws}", None)


# ── Kategorien ───────────────────────────────────────────────

def load_custom_cats(user, typ):
    try:
        df = _gs_read("categories")
        if df.empty or 'user' not in df.columns:
            return []
        return df[(df['user'] == user) & (df['typ'] == typ)]['kategorie'].tolist()
    except:
        return []


def save_custom_cat(user, typ, kategorie):
    try:
        df = _gs_read("categories")
    except:
        df = pd.DataFrame(columns=['user', 'typ', 'kategorie'])
    _gs_update("categories", pd.concat(
        [df, pd.DataFrame([{'user': user, 'typ': typ, 'kategorie': kategorie}])],
        ignore_index=True
    ))


def delete_custom_cat(user, typ, kategorie):
    try:
        df = _gs_read("categories")
        _gs_update("categories", df[~((df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == kategorie))])
    except:
        pass


def update_custom_cat(user, typ, old_label, new_label):
    try:
        df = _gs_read("categories")
        df.loc[(df['user'] == user) & (df['typ'] == typ) & (df['kategorie'] == old_label), 'kategorie'] = new_label
        _gs_update("categories", df)
    except:
        pass


# ── Sparziel ─────────────────────────────────────────────────

def load_goal(user):
    try:
        df = _gs_read("goals")
        if df.empty or 'user' not in df.columns:
            return 0.0
        row = df[df['user'] == user]
        return float(row.iloc[-1].get('sparziel', 0) or 0) if not row.empty else 0.0
    except:
        return 0.0


def save_goal(user, goal):
    try:
        df = _gs_read("goals")
    except:
        df = pd.DataFrame(columns=['user', 'sparziel'])
    if 'user' not in df.columns:
        df = pd.DataFrame(columns=['user', 'sparziel'])
    mask = df['user'] == user
    if mask.any():
        df.loc[mask, 'sparziel'] = goal
    else:
        df = pd.concat([df, pd.DataFrame([{'user': user, 'sparziel': goal}])], ignore_index=True)
    _gs_update("goals", df)


# ── User-Einstellungen ───────────────────────────────────────

def load_user_settings(user):
    try:
        df = _gs_read("settings")
        if df.empty or 'user' not in df.columns:
            return {}
        row = df[df['user'] == user]
        if row.empty:
            return {}
        r = row.iloc[-1]
        return {
            'budget': float(r.get('budget', 0) or 0),
            'currency': str(r.get('currency', 'EUR') or 'EUR'),
            'avatar_url': str(r.get('avatar_url', '') or ''),
            'theme': str(r.get('theme', 'Ocean Blue') or 'Ocean Blue'),
            'last_username_change': str(r.get('last_username_change', '') or ''),
        }
    except:
        return {}


def save_user_settings(user, **kwargs):
    try:
        df = _gs_read("settings")
    except:
        df = pd.DataFrame(columns=['user', 'budget', 'currency', 'avatar_url', 'theme'])
    if 'user' not in df.columns:
        df = pd.DataFrame(columns=['user', 'budget', 'currency', 'avatar_url', 'theme'])
    mask = df['user'] == user
    if mask.any():
        for k, v in kwargs.items():
            df.loc[mask, k] = v
    else:
        row_data = {'user': user, 'budget': 0, 'currency': 'EUR', 'avatar_url': '', 'theme': 'Ocean Blue'}
        row_data.update(kwargs)
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
    _gs_update("settings", df)


# ── Daueraufträge ────────────────────────────────────────────

def load_dauerauftraege(user):
    try:
        df = _gs_read("dauerauftraege")
        if df.empty or 'user' not in df.columns:
            return []
        result = []
        for _, r in df[df['user'] == user].iterrows():
            if str(r.get('deleted', '')).strip().lower() in ('true', '1', '1.0'):
                continue
            result.append({
                'id': str(r.get('id', '')),
                'name': str(r.get('name', '')),
                'betrag': float(r.get('betrag', 0) or 0),
                'typ': str(r.get('typ', 'Ausgabe')),
                'kategorie': str(r.get('kategorie', '')),
                'aktiv': str(r.get('aktiv', 'True')),
            })
        return result
    except:
        return []


def save_dauerauftrag(user, name, betrag, typ, kategorie):
    try:
        df = _gs_read("dauerauftraege")
    except:
        df = pd.DataFrame(columns=['user', 'id', 'name', 'betrag', 'typ', 'kategorie', 'aktiv', 'deleted'])
    new_id = f"{user}_{int(time.time())}"
    new_row = pd.DataFrame([{
        'user': user, 'id': new_id, 'name': name,
        'betrag': betrag, 'typ': typ, 'kategorie': kategorie,
        'aktiv': 'True', 'deleted': '',
    }])
    _gs_update("dauerauftraege", pd.concat([df, new_row], ignore_index=True))


def delete_dauerauftrag(user, da_id):
    try:
        df = _gs_read("dauerauftraege")
        df.loc[(df['user'] == user) & (df['id'] == da_id), 'deleted'] = 'True'
        _gs_update("dauerauftraege", df)
    except:
        pass


def apply_dauerauftraege(user):
    try:
        das = load_dauerauftraege(user)
        if not das:
            return 0
        today = datetime.date.today()
        target_date = today.replace(day=1)
        df_t = _gs_read("transactions")
        booked = 0
        for da in das:
            if da['aktiv'] != 'True':
                continue
            already = df_t[
                (df_t['user'] == user) &
                (df_t['notiz'] == f"⚙️ Dauerauftrag: {da['name']}") &
                (df_t['datum'].astype(str).str.startswith(target_date.strftime('%Y-%m')))
            ] if not df_t.empty and 'user' in df_t.columns else pd.DataFrame()
            if not already.empty:
                continue
            betrag_save = da['betrag'] if da['typ'] in ('Einnahme', 'Depot') else -da['betrag']
            new_row = pd.DataFrame([{
                'user': user,
                'datum': str(target_date),
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                'typ': da['typ'],
                'kategorie': da['kategorie'],
                'betrag': betrag_save,
                'notiz': f"⚙️ Dauerauftrag: {da['name']}",
                'deleted': '',
            }])
            df_t = pd.concat([df_t, new_row], ignore_index=True)
            booked += 1
        if booked > 0:
            _gs_update("transactions", df_t)
        return booked
    except:
        return 0


# ── Spartöpfe ────────────────────────────────────────────────

def load_toepfe(user):
    try:
        df = _gs_read("toepfe")
        if df.empty or 'user' not in df.columns:
            return []
        result = []
        for _, r in df[df['user'] == user].iterrows():
            if str(r.get('deleted', '')).strip().lower() in ('true', '1', '1.0'):
                continue
            result.append({
                'id': str(r.get('id', '')),
                'name': str(r.get('name', '')),
                'ziel': float(r.get('ziel', 0) or 0),
                'gespart': float(r.get('gespart', 0) or 0),
                'emoji': str(r.get('emoji', '🪣')),
                'farbe': str(r.get('farbe', '#38bdf8')),
            })
        return result
    except:
        return []


def save_topf(user, name, ziel, emoji):
    try:
        df = _gs_read("toepfe")
    except:
        df = pd.DataFrame(columns=['user', 'id', 'name', 'ziel', 'gespart', 'emoji', 'farbe', 'deleted'])
    cnt = len(df[df['user'] == user]) if not df.empty and 'user' in df.columns else 0
    new_row = pd.DataFrame([{
        'user': user,
        'id': f"{user}_{int(time.time())}",
        'name': name,
        'ziel': ziel,
        'gespart': 0,
        'emoji': emoji,
        'farbe': TOPF_PALETTE[cnt % len(TOPF_PALETTE)],
        'deleted': '',
    }])
    _gs_update("toepfe", pd.concat([df, new_row], ignore_index=True))


def update_topf_gespart(user, topf_id, topf_name, delta):
    try:
        df = _gs_read("toepfe")
        mask = (df['user'] == user) & (df['id'] == topf_id)
        if mask.any():
            df.loc[mask, 'gespart'] = max(0, float(df.loc[mask, 'gespart'].values[0] or 0) + delta)
            _gs_update("toepfe", df)
    except:
        pass
    try:
        df_t = _gs_read("transactions")
        new_row = pd.DataFrame([{
            "user": user,
            "datum": str(datetime.date.today()),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "typ": "Spartopf",
            "kategorie": f"🪣 {topf_name}",
            "betrag": (-1 if delta > 0 else 1) * abs(delta),
            "notiz": f"{'↓' if delta > 0 else '↑'} {topf_name}",
            'deleted': '',
        }])
        _gs_update("transactions", pd.concat([df_t, new_row], ignore_index=True))
    except:
        pass


def delete_topf(user, topf_id):
    try:
        df = _gs_read("toepfe")
        df.loc[(df['user'] == user) & (df['id'] == topf_id), 'deleted'] = 'True'
        _gs_update("toepfe", df)
    except:
        pass


def update_topf_meta(user, topf_id, name, ziel, emoji):
    try:
        df = _gs_read("toepfe")
        mask = (df['user'] == user) & (df['id'] == topf_id)
        if mask.any():
            df.loc[mask, ['name', 'ziel', 'emoji']] = [name, ziel, emoji]
            _gs_update("toepfe", df)
    except:
        pass
