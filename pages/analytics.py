import streamlit as st

st.components.v1.html("""
<button onclick="findScroller()" style="padding:10px;margin:5px;">🔍 Scrollendes Element finden</button>
<button onclick="tryScroll()" style="padding:10px;margin:5px;">⬆️ Nach oben scrollen</button>
<div id="out" style="font-family:monospace;font-size:12px;margin-top:10px;white-space:pre-wrap;"></div>

<script>
function log(msg) {
    document.getElementById('out').textContent += msg + '\\n';
}

function findScroller() {
    document.getElementById('out').textContent = '';
    var doc = window.parent.document;
    var all = doc.querySelectorAll('*');
    var scrollers = [];
    all.forEach(function(el) {
        if (el.scrollTop > 0) {
            scrollers.push({
                tag: el.tagName,
                id: el.id,
                classes: el.className.toString().substring(0,60),
                dataTestId: el.getAttribute('data-testid') || '',
                scrollTop: el.scrollTop,
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight
            });
        }
    });
    if (scrollers.length === 0) {
        log('Kein Element mit scrollTop > 0 gefunden!');
        log('window.parent.scrollY: ' + window.parent.scrollY);
        log('window.parent.pageYOffset: ' + window.parent.pageYOffset);
        log('document.documentElement.scrollTop: ' + doc.documentElement.scrollTop);
        log('document.body.scrollTop: ' + doc.body.scrollTop);
    } else {
        scrollers.forEach(function(s) {
            log('TAG: ' + s.tag + ' | testid: ' + s.dataTestId + ' | class: ' + s.classes);
            log('  scrollTop=' + s.scrollTop + ' scrollHeight=' + s.scrollHeight + ' clientHeight=' + s.clientHeight);
        });
    }
}

function tryScroll() {
    document.getElementById('out').textContent = '';
    var doc = window.parent.document;
    var all = doc.querySelectorAll('*');
    all.forEach(function(el) {
        if (el.scrollHeight > el.clientHeight) {
            var before = el.scrollTop;
            el.scrollTop = 0;
            if (before !== el.scrollTop || before > 0) {
                log('Gescrollt: ' + (el.getAttribute('data-testid') || el.tagName + '.' + el.className.toString().substring(0,30)));
                log('  vorher=' + before + ' nachher=' + el.scrollTop);
            }
        }
    });
    log('window.parent.scrollY vorher: ' + window.parent.scrollY);
    window.parent.scrollTo(0, 0);
    log('window.parent.scrollY nachher: ' + window.parent.scrollY);
}
</script>
""", height=300)
import calendar
import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from constants import PALETTE_AUS, PALETTE_EIN, PALETTE_DEP
from database import _gs_read, load_goal, save_goal


def render(user_name, currency_sym):
    st.markdown(
        "<div style='margin-bottom:36px;margin-top:16px;'>"
        "<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;"
        "margin:0 0 6px 0;letter-spacing:-1px;'>Analysen &amp; Trends 📊</h1>"
        "<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>"
        "Kaufverhalten, Zeitraumübersicht &amp; Sparziele</p></div>",
        unsafe_allow_html=True,
    )

    try:
        df_raw = _gs_read("transactions")
    except Exception as e:
        st.warning(f"Verbindung wird hergestellt... ({e})")
        return

    if df_raw.empty or 'user' not in df_raw.columns:
        st.info("Noch keine Buchungen vorhanden.")
        return

    df_all = df_raw[df_raw['user'] == user_name].copy()
    if 'deleted' in df_all.columns:
        df_all = df_all[~df_all['deleted'].astype(str).str.strip().str.lower().isin(['true', '1', '1.0'])]
    df_all['datum_dt']   = pd.to_datetime(df_all['datum'], errors='coerce')
    df_all['betrag_num'] = pd.to_numeric(df_all['betrag'], errors='coerce')
    df_all = df_all.dropna(subset=['datum_dt'])

    if df_all.empty:
        st.info("Noch keine Buchungen vorhanden.")
        return

    now   = datetime.datetime.now()
    today = now.date()

    # ── Zeitraum-Selektor ─────────────────────────────────────
    zeitraum = st.session_state['analysen_zeitraum']
    zt1, zt2, zt3, _ = st.columns([1, 1, 1, 3])
    for (label, key), col in zip(
        [("Wöchentlich", "zt_weekly"), ("Monatlich", "zt_monthly"), ("Jährlich", "zt_yearly")],
        [zt1, zt2, zt3],
    ):
        with col:
            if st.button(
                label + (" ✓" if zeitraum == label else ""), key=key,
                use_container_width=True, type="primary" if zeitraum == label else "secondary",
            ):
                st.session_state['analysen_zeitraum'] = label
                st.session_state['analysen_month_offset'] = 0
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if zeitraum == "Monatlich":
        an_offset  = st.session_state.get('analysen_month_offset', 0)
        m_total    = now.year * 12 + (now.month - 1) + an_offset
        an_year, an_mi = divmod(m_total, 12)
        an_month   = an_mi + 1
        an_label   = datetime.date(an_year, an_month, 1).strftime("%B %Y")
        an1, an2, an3 = st.columns([1, 5, 1])
        with an1:
            if st.button("‹", key="an_prev", use_container_width=True):
                st.session_state['analysen_month_offset'] -= 1; st.rerun()
        with an2:
            st.markdown(f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:13px;color:#64748b;padding:6px 0;'>{an_label}</div>", unsafe_allow_html=True)
        with an3:
            if st.button("›", key="an_next", use_container_width=True, disabled=(an_offset >= 0)):
                st.session_state['analysen_month_offset'] += 1; st.rerun()
        period_mask  = (df_all['datum_dt'].dt.year == an_year) & (df_all['datum_dt'].dt.month == an_month)
        period_label = an_label
    elif zeitraum == "Wöchentlich":
        ws = today - datetime.timedelta(days=today.weekday())
        we = ws + datetime.timedelta(days=6)
        period_mask  = (df_all['datum_dt'].dt.date >= ws) & (df_all['datum_dt'].dt.date <= we)
        period_label = f"{ws.strftime('%d.%m.')} – {we.strftime('%d.%m.%Y')}"
    else:
        period_mask  = df_all['datum_dt'].dt.year == now.year
        period_label = str(now.year)

    period_df = df_all[period_mask].copy()
    st.markdown(f"<div style='font-family:DM Mono,monospace;color:#475569;font-size:11px;letter-spacing:1px;margin-bottom:18px;'>{period_label}</div>", unsafe_allow_html=True)

    def make_donut(grp, palette, label, sign, center_color, key_suffix):
        if grp.empty:
            return
        cats   = grp['kategorie'].tolist()
        vals   = grp['betrag_num'].abs().tolist()
        colors = [palette[i % len(palette)] for i in range(len(cats))]
        total  = sum(vals) if sum(vals) > 0 else 1
        fig = go.Figure(go.Pie(
            labels=cats, values=vals, hole=0.60,
            marker=dict(colors=colors, line=dict(color="rgba(5,10,20,0.9)", width=2)),
            textinfo="none", hoverinfo="none", direction="clockwise", sort=False, rotation=90,
        ))
        fig.update_traces(hovertemplate=None)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10), height=240, autosize=True, dragmode=False,
            annotations=[dict(
                text=f"<b>{sign}{total:,.2f} {currency_sym}</b>", x=0.5, y=0.5, showarrow=False,
                font=dict(size=15, color=center_color, family="DM Sans, sans-serif"), xref="paper", yref="paper",
            )],
        )
        rows = "".join(
            f"<div style='display:flex;align-items:center;justify-content:space-between;padding:5px 0;"
            f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
            f"<div style='display:flex;align-items:center;gap:8px;min-width:0;flex:1;'>"
            f"<div style='width:7px;height:7px;border-radius:50%;background:{col};flex-shrink:0;'></div>"
            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{cat}</span></div>"
            f"<div style='display:flex;align-items:center;gap:6px;flex-shrink:0;margin-left:10px;'>"
            f"<span style='font-family:DM Mono,monospace;color:{col};font-size:11px;font-weight:500;'>{sign}{val:,.2f} {currency_sym}</span>"
            f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>{val / total * 100:.0f}%</span></div></div>"
            for cat, val, col in zip(cats, vals, colors)
        )
        st.markdown(
            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:18px 22px;margin-bottom:16px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>{label}</div>",
            unsafe_allow_html=True,
        )
        pie_col, leg_col = st.columns([1, 1])
        with pie_col:
            st.plotly_chart(fig, use_container_width=True, key=f"donut_{key_suffix}_{zeitraum}_{period_label}", config={"displayModeBar": False, "staticPlot": True})
        with leg_col:
            st.markdown(f"<div style='padding:4px 0;'>{rows}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if period_df.empty:
        st.markdown(
            "<div style='text-align:center;padding:40px 20px;color:#334155;font-family:DM Sans,sans-serif;font-size:15px;'>"
            "Keine Buchungen im gewählten Zeitraum.</div>",
            unsafe_allow_html=True,
        )
    else:
        aus_p = period_df[period_df['typ'] == 'Ausgabe'].copy()
        aus_p['betrag_num'] = aus_p['betrag_num'].abs()
        make_donut(aus_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False), PALETTE_AUS, "Ausgaben", "−", "#f87171", "aus")
        ein_p = period_df[period_df['typ'] == 'Einnahme'].copy()
        make_donut(ein_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False), PALETTE_EIN, "Einnahmen", "+", "#4ade80", "ein")
        dep_p = period_df[period_df['typ'] == 'Depot'].copy()
        dep_p['betrag_num'] = dep_p['betrag_num'].abs()
        make_donut(dep_p.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False), PALETTE_DEP, "Depot", "", "#38bdf8", "dep")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Kaufverhalten ─────────────────────────────────────────
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>"
        "Kaufverhalten <span style=\"font-size:9px;color:#1e293b;\">(Ø letzte 12 Monate)</span></p>",
        unsafe_allow_html=True,
    )
    kv_l, kv_r = st.columns(2)
    _twelve_months_ago = now - datetime.timedelta(days=365)

    with kv_l:
        aus_all = df_all[(df_all['typ'] == 'Ausgabe') & (df_all['datum_dt'] >= _twelve_months_ago)].copy()
        aus_all['betrag_num'] = aus_all['betrag_num'].abs()
        _months_in_range = max(aus_all['datum_dt'].dt.to_period('M').nunique(), 1)
        kat_grp_sum = aus_all.groupby('kategorie')['betrag_num'].sum()
        kat_avg = (kat_grp_sum / _months_in_range).reset_index()
        kat_grp = kat_avg.sort_values('betrag_num', ascending=True).tail(8)
        if not kat_grp.empty:
            REDS = ['#7f1d1d', '#991b1b', '#b91c1c', '#dc2626', '#ef4444', '#f87171', '#fca5a5', '#fecaca']
            fig_kat = go.Figure(go.Bar(
                x=kat_grp['betrag_num'], y=kat_grp['kategorie'], orientation='h',
                marker=dict(color=REDS[:len(kat_grp)], cornerradius=6),
                text=[f"Ø {v:,.0f} {currency_sym}" for v in kat_grp['betrag_num']],
                textposition='inside', insidetextanchor='middle',
                textfont=dict(size=11, color='rgba(255,255,255,0.85)', family='DM Mono, monospace'),
                hovertemplate=None,
            ))
            fig_kat.update_traces(hovertemplate=None)
            fig_kat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=280, margin=dict(t=0, b=0, l=0, r=10), dragmode=False,
                xaxis=dict(showgrid=False, showticklabels=False, showline=False, fixedrange=True),
                yaxis=dict(tickfont=dict(size=12, color='#94a3b8', family='DM Sans, sans-serif'), showgrid=False, showline=False, fixedrange=True, automargin=True),
            )
            st.markdown("<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:8px;'>Top Ausgabe-Kategorien — Ø pro Monat</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_kat, use_container_width=True, key="kat_chart", config={"displayModeBar": False, "staticPlot": True})
        else:
            st.info("Keine Ausgaben vorhanden.")

    with kv_r:
        aus_all2 = df_all[(df_all['typ'] == 'Ausgabe') & (df_all['datum_dt'] >= _twelve_months_ago)].copy()
        aus_all2['betrag_num'] = aus_all2['betrag_num'].abs()
        aus_all2['wochentag'] = aus_all2['datum_dt'].dt.day_name()
        wt_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        wt_de    = {'Monday': 'Mo', 'Tuesday': 'Di', 'Wednesday': 'Mi', 'Thursday': 'Do', 'Friday': 'Fr', 'Saturday': 'Sa', 'Sunday': 'So'}
        if not aus_all2.empty:
            heat = aus_all2.groupby('wochentag')['betrag_num'].mean().reindex(wt_order).fillna(0)
            fig_heat = go.Figure(go.Bar(
                x=[wt_de.get(d, d) for d in heat.index], y=heat.values,
                marker=dict(color=heat.values, colorscale=[[0, '#1a0505'], [0.5, '#dc2626'], [1, '#ff5232']], showscale=False, cornerradius=6),
                text=[f"{v:,.0f} {currency_sym}" if v > 0 else "" for v in heat.values],
                textposition='inside', insidetextanchor='middle',
                textfont=dict(size=10, color='rgba(255,255,255,0.7)', family='DM Mono, monospace'),
                hovertemplate=None,
            ))
            fig_heat.update_traces(hovertemplate=None)
            fig_heat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=280, margin=dict(t=0, b=0, l=0, r=0), dragmode=False,
                xaxis=dict(tickfont=dict(size=13, color='#94a3b8', family='DM Sans, sans-serif'), showgrid=False, showline=False, fixedrange=True),
                yaxis=dict(showgrid=False, showticklabels=False, showline=False, fixedrange=True),
            )
            st.markdown("<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:8px;'>Ø Ausgaben nach Wochentag</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_heat, use_container_width=True, key="heat_chart", config={"displayModeBar": False, "staticPlot": True})

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Kalender-Heatmap ──────────────────────────────────────
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Kalender-Heatmap</p>",
        unsafe_allow_html=True,
    )
    hm_offset  = st.session_state.get('heatmap_month_offset', 0)
    hm_m_total = now.year * 12 + (now.month - 1) + hm_offset
    hm_year, hm_mi = divmod(hm_m_total, 12)
    hm_month = hm_mi + 1
    hm_label = datetime.date(hm_year, hm_month, 1).strftime("%B %Y")
    hn1, hn2, hn3 = st.columns([1, 5, 1])
    with hn1:
        if st.button("‹", key="hm_prev", use_container_width=True):
            st.session_state['heatmap_month_offset'] -= 1; st.rerun()
    with hn2:
        st.markdown(f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:13px;color:#64748b;padding:6px 0;'>{hm_label}</div>", unsafe_allow_html=True)
    with hn3:
        if st.button("›", key="hm_next", use_container_width=True, disabled=(hm_offset >= 0)):
            st.session_state['heatmap_month_offset'] += 1; st.rerun()

    hm_df = df_all[
        (df_all['datum_dt'].dt.year == hm_year) &
        (df_all['datum_dt'].dt.month == hm_month) &
        (df_all['typ'] == 'Ausgabe')
    ].copy()
    hm_df['betrag_num'] = hm_df['betrag_num'].abs()
    tages_summen  = hm_df.groupby(hm_df['datum_dt'].dt.day)['betrag_num'].sum()
    max_val       = max(tages_summen.max() if not tages_summen.empty else 1, 1)
    days_in_month = calendar.monthrange(hm_year, hm_month)[1]
    first_weekday = calendar.monthrange(hm_year, hm_month)[0]

    header_html = "".join(
        f"<div style='width:42px;text-align:center;font-family:DM Mono,monospace;font-size:10px;color:#334155;padding-bottom:4px;'>{d}</div>"
        for d in ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
    )
    cal_cells = "<div style='width:42px;height:42px;'></div>" * first_weekday
    for day in range(1, days_in_month + 1):
        val = tages_summen.get(day, 0)
        intensity = val / max_val if max_val > 0 else 0
        is_today  = (hm_year == now.year and hm_month == now.month and day == now.day)
        if val == 0:
            bg, text_color = "rgba(15,23,42,0.6)", "#1e293b"
        else:
            r, g, b = int(20 + intensity * 235), int(5 + (1 - intensity) * 30), int(5 + (1 - intensity) * 10)
            bg = f"rgba({r},{g},{b},0.85)"
            text_color = "#ffffff" if intensity > 0.3 else "#94a3b8"
        border = "2px solid #38bdf8" if is_today else "1px solid rgba(148,163,184,0.06)"
        cal_cells += (
            f"<div title='{day}. {hm_label}: {val:.2f} {currency_sym}' style='width:42px;height:42px;border-radius:8px;"
            f"background:{bg};border:{border};display:flex;flex-direction:column;align-items:center;justify-content:center;'>"
            f"<span style='font-family:DM Mono,monospace;font-size:11px;color:#334155;line-height:1;'>{day}</span>"
            + (f"<span style='font-family:DM Mono,monospace;font-size:8px;color:{text_color};line-height:1;margin-top:2px;'>{val:.0f}{currency_sym}</span>" if val > 0 else "")
            + "</div>"
        )
    st.markdown(
        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
        f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
        f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-bottom:14px;'>Ausgaben pro Tag — hellere Felder = höhere Ausgaben</div>"
        f"<div style='display:flex;gap:6px;margin-bottom:6px;'>{header_html}</div>"
        f"<div style='display:flex;flex-wrap:wrap;gap:6px;'>{cal_cells}</div>"
        f"<div style='display:flex;align-items:center;gap:8px;margin-top:14px;'>"
        f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#334155;'>0 {currency_sym}</span>"
        f"<div style='height:6px;flex:1;max-width:120px;border-radius:3px;background:linear-gradient(to right,rgba(15,23,42,0.6),#ff0000);'></div>"
        f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#64748b;'>{max_val:.0f} {currency_sym}</span></div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Monatsende-Prognose ───────────────────────────────────
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Monatsende-Prognose</p>",
        unsafe_allow_html=True,
    )
    curr_month_df = df_all[(df_all['datum_dt'].dt.year == now.year) & (df_all['datum_dt'].dt.month == now.month)].copy()
    today_day     = now.day
    days_in_cur   = calendar.monthrange(now.year, now.month)[1]
    days_left     = days_in_cur - today_day
    curr_ein      = curr_month_df[curr_month_df['typ'] == 'Einnahme']['betrag_num'].sum()
    curr_aus      = curr_month_df[curr_month_df['typ'] == 'Ausgabe']['betrag_num'].abs().sum()
    curr_dep      = curr_month_df[curr_month_df['typ'] == 'Depot']['betrag_num'].sum()
    curr_sp_netto = curr_month_df[curr_month_df['typ'] == 'Spartopf']['betrag_num'].sum()
    daily_rate    = curr_aus / today_day if today_day > 0 else 0
    fc_aus_total  = daily_rate * days_in_cur
    fc_remaining  = daily_rate * days_left
    fc_bank       = curr_ein - fc_aus_total - curr_dep + curr_sp_netto
    curr_bank     = curr_ein - curr_aus - curr_dep + curr_sp_netto
    fc_color   = "#4ade80" if fc_bank >= 0 else "#f87171"
    fc_str     = f"+{fc_bank:,.2f} {currency_sym}" if fc_bank >= 0 else f"-{abs(fc_bank):,.2f} {currency_sym}"
    curr_color = "#4ade80" if curr_bank >= 0 else "#f87171"
    curr_str   = f"+{curr_bank:,.2f} {currency_sym}" if curr_bank >= 0 else f"-{abs(curr_bank):,.2f} {currency_sym}"
    month_pct  = today_day / days_in_cur * 100

    fc_col_l, fc_col_r = st.columns(2)
    with fc_col_l:
        st.markdown(
            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;'>Prognose für {now.strftime('%B %Y')}</div>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
            f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Monatsverlauf</span>"
            f"<span style='font-family:DM Mono,monospace;color:#64748b;font-size:12px;'>Tag {today_day}/{days_in_cur}</span></div>"
            f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:5px;margin-bottom:16px;'>"
            f"<div style='width:{month_pct:.0f}%;height:100%;background:#475569;border-radius:99px;'></div></div>"
            f"<div style='display:flex;flex-direction:column;gap:8px;'>"
            f"<div style='display:flex;justify-content:space-between;'>"
            f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ø Tagesausgaben</span>"
            f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>{daily_rate:,.2f} {currency_sym}/Tag</span></div>"
            f"<div style='display:flex;justify-content:space-between;'>"
            f"<span style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Noch {days_left} Tage → ca.</span>"
            f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{fc_remaining:,.2f} {currency_sym}</span></div>"
            f"<div style='border-top:1px solid rgba(148,163,184,0.08);padding-top:10px;display:flex;justify-content:space-between;align-items:baseline;'>"
            f"<span style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;font-weight:500;'>Prognose Monatsende</span>"
            f"<span style='font-family:DM Mono,monospace;color:{fc_color};font-size:18px;font-weight:600;'>{fc_str}</span>"
            f"</div></div></div>",
            unsafe_allow_html=True,
        )
    with fc_col_r:
        goal_fc   = load_goal(user_name)
        goal_html = ""
        if goal_fc > 0:
            diff_goal = fc_bank - goal_fc
            on_track  = fc_bank >= goal_fc
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
                f"<div style='font-family:DM Mono,monospace;color:#475569;font-size:11px;'>{_g_pre}{abs(diff_goal):,.2f} {currency_sym}</div></div></div>"
            )
        st.markdown(
            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
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
            f"{goal_html}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Spar-Potenzial ────────────────────────────────────────
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Spar-Potenzial</p>",
        unsafe_allow_html=True,
    )
    hist_df = df_all[
        ~((df_all['datum_dt'].dt.year == now.year) & (df_all['datum_dt'].dt.month == now.month)) &
        (df_all['typ'] == 'Ausgabe')
    ].copy()
    hist_df['betrag_num'] = hist_df['betrag_num'].abs()
    hist_df = hist_df[hist_df['datum_dt'] >= now - datetime.timedelta(days=90)]

    if not hist_df.empty and not curr_month_df.empty:
        hist_months  = max(hist_df['datum_dt'].dt.to_period('M').nunique(), 1)
        avg_per_kat  = hist_df.groupby('kategorie')['betrag_num'].sum() / hist_months
        curr_aus_df  = curr_month_df[curr_month_df['typ'] == 'Ausgabe'].copy()
        curr_aus_df['betrag_num'] = curr_aus_df['betrag_num'].abs()
        curr_per_kat = curr_aus_df.groupby('kategorie')['betrag_num'].sum()
        potenzial_rows = sorted([
            {'kategorie': kat, 'aktuell': curr_per_kat.get(kat, 0), 'durchschn': avg_per_kat.get(kat, 0),
             'diff_pct': (curr_per_kat.get(kat, 0) - avg_per_kat.get(kat, 0)) / avg_per_kat.get(kat, 0) * 100,
             'diff_eur': curr_per_kat.get(kat, 0) - avg_per_kat.get(kat, 0)}
            for kat in curr_per_kat.index
            if avg_per_kat.get(kat, 0) > 0 and curr_per_kat.get(kat, 0) > avg_per_kat.get(kat, 0) * 1.1
        ], key=lambda x: x['diff_eur'], reverse=True)

        if potenzial_rows:
            total_potenzial = sum(r['diff_eur'] for r in potenzial_rows)
            st.markdown(
                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;margin-bottom:12px;'>"
                f"<div style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:14px;margin-bottom:16px;'>"
                f"Diesen Monat hast du in <b style='color:#e2e8f0;'>{len(potenzial_rows)} Kategorien</b> mehr ausgegeben als im Durchschnitt. "
                f"Spar-Potenzial: <span style='color:#4ade80;font-weight:600;'>{total_potenzial:,.2f} {currency_sym}</span></div>",
                unsafe_allow_html=True,
            )
            for r in potenzial_rows:
                bar_pct = min(r['diff_pct'], 200) / 200 * 100
                st.markdown(
                    f"<div style='margin-bottom:14px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;'>"
                    f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{r['kategorie']}</span>"
                    f"<div style='display:flex;gap:14px;'>"
                    f"<span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>{r['aktuell']:,.2f} {currency_sym}</span>"
                    f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>Ø {r['durchschn']:,.2f} {currency_sym}</span>"
                    f"<span style='font-family:DM Mono,monospace;color:#facc15;font-size:12px;font-weight:600;'>+{r['diff_pct']:.0f}%</span>"
                    f"</div></div>"
                    f"<div style='background:rgba(30,41,59,0.6);border-radius:99px;height:4px;'>"
                    f"<div style='width:{bar_pct:.0f}%;height:100%;border-radius:99px;background:linear-gradient(to right,#facc15,#f87171);'></div></div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;margin-top:4px;'>"
                    f"Da könntest du ca. <span style='color:#4ade80;font-weight:500;'>{r['diff_eur']:,.2f} {currency_sym}</span> sparen</div></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                "border:1px solid rgba(74,222,128,0.12);border-left:3px solid #4ade80;border-radius:16px;padding:18px 22px;'>"
                "<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:14px;font-weight:500;'>🎉 Alles im grünen Bereich!</div>"
                "<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-top:6px;'>Deine Ausgaben liegen diesen Monat im normalen Rahmen.</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='color:#334155;font-family:DM Sans,sans-serif;font-size:14px;padding:16px;'>Zu wenig Daten für Vergleich.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Sparziel ─────────────────────────────────────────────
    st.markdown(
        "<p style='font-family:DM Mono,monospace;color:#334155;font-size:10px;font-weight:500;"
        "letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;'>Sparziel</p>",
        unsafe_allow_html=True,
    )
    current_goal = load_goal(user_name)
    df_month = df_all[(df_all['datum_dt'].dt.year == now.year) & (df_all['datum_dt'].dt.month == now.month)].copy()
    df_month['betrag_num'] = pd.to_numeric(df_month['betrag'], errors='coerce')
    monat_ein        = df_month[df_month['typ'] == 'Einnahme']['betrag_num'].sum()
    monat_aus        = df_month[df_month['typ'] == 'Ausgabe']['betrag_num'].abs().sum()
    monat_dep        = df_month[df_month['typ'] == 'Depot']['betrag_num'].sum()
    monat_sp_einzahl = abs(df_month[(df_month['typ'] == 'Spartopf') & (df_month['betrag_num'] < 0)]['betrag_num'].sum())
    monat_sp_netto   = df_month[df_month['typ'] == 'Spartopf']['betrag_num'].sum()
    bank_aktuell     = monat_ein - monat_aus - monat_dep + monat_sp_netto
    akt_spar         = bank_aktuell + monat_sp_einzahl + abs(monat_dep)

    sg_col_l, sg_col_r = st.columns([1, 1])
    with sg_col_l:
        with st.form("sparziel_form"):
            goal_input = st.number_input(
                f"Monatliches Sparziel ({currency_sym})", min_value=0.0,
                value=float(current_goal), step=50.0, format="%.2f",
            )
            if st.form_submit_button("Sparziel speichern", use_container_width=True, type="primary"):
                save_goal(user_name, goal_input)
                st.success("✅ Sparziel gespeichert!")
                st.rerun()
        spar_color = '#4ade80' if akt_spar >= 0 else '#f87171'
        spar_str   = f"{akt_spar:,.2f} {currency_sym}" if akt_spar >= 0 else f"-{abs(akt_spar):,.2f} {currency_sym}"
        st.markdown(
            f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.8),rgba(10,16,30,0.9));"
            f"border:1px solid rgba(148,163,184,0.06);border-radius:12px;padding:16px 18px;margin-top:10px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;'>{now.strftime('%B %Y')}</div>"
            f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Einnahmen</div><div style='font-family:DM Mono,monospace;color:#4ade80;font-size:12px;'>+{monat_ein:,.2f} {currency_sym}</div></div>"
            f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Ausgaben</div><div style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>-{monat_aus:,.2f} {currency_sym}</div></div>"
            + (f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Depot</div><div style='font-family:DM Mono,monospace;color:#38bdf8;font-size:12px;'>📦 {abs(monat_dep):,.2f} {currency_sym}</div></div>" if monat_dep != 0 else "")
            + (f"<div style='display:flex;justify-content:space-between;'><div style='font-family:DM Sans,sans-serif;color:#475569;font-size:12px;'>Spartöpfe</div><div style='font-family:DM Mono,monospace;color:#a78bfa;font-size:12px;'>🪣 {monat_sp_einzahl:,.2f} {currency_sym}</div></div>" if monat_sp_einzahl > 0 else "")
            + f"<div style='border-top:1px solid rgba(148,163,184,0.08);margin-top:8px;padding-top:8px;display:flex;justify-content:space-between;'>"
            f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:12px;font-weight:500;'>Gespart (inkl. Töpfe &amp; Depot)</div>"
            f"<div style='font-family:DM Mono,monospace;color:{spar_color};font-size:13px;font-weight:600;'>{spar_str}</div></div></div>",
            unsafe_allow_html=True,
        )

    with sg_col_r:
        if current_goal > 0:
            fehlbetrag  = current_goal - akt_spar
            erreicht    = akt_spar >= current_goal
            pct_display = max(0, min(akt_spar / current_goal * 100, 100))
            bar_color   = '#4ade80' if erreicht else ('#facc15' if pct_display >= 60 else '#f87171')
            spar_color2 = '#4ade80' if akt_spar >= 0 else '#f87171'
            spar_str2   = f"{akt_spar:,.2f} {currency_sym}" if akt_spar >= 0 else f"-{abs(akt_spar):,.2f} {currency_sym}"
            st.markdown(
                f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;'>"
                f"<span style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;'>Fortschritt</span>"
                f"<span style='font-family:DM Mono,monospace;font-size:13px;color:{bar_color};font-weight:600;'>{pct_display:.0f}%</span></div>"
                f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:6px;overflow:hidden;margin-bottom:16px;'>"
                f"<div style='height:100%;width:{pct_display}%;background:{bar_color};border-radius:99px;'></div></div>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<div><div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;'>Aktuell gespart</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:{spar_color2};font-size:18px;font-weight:600;'>{spar_str2}</div></div>"
                f"<div style='text-align:right;'><div style='font-family:DM Mono,monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;'>Ziel</div>"
                f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-size:18px;font-weight:600;'>{current_goal:,.2f} {currency_sym}</div></div></div></div>",
                unsafe_allow_html=True,
            )
            if not erreicht and fehlbetrag > 0:
                aus_monat = df_month[df_month['typ'] == 'Ausgabe'].copy()
                aus_monat['betrag_num'] = aus_monat['betrag_num'].abs()
                kat_monat = aus_monat.groupby('kategorie')['betrag_num'].sum().reset_index().sort_values('betrag_num', ascending=False)
                if not kat_monat.empty:
                    remaining  = fehlbetrag
                    rows_html  = ""
                    for _, kr in kat_monat.iterrows():
                        if remaining <= 0:
                            break
                        cut = min(kr['betrag_num'], remaining)
                        rows_html += (
                            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:9px 0;"
                            f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{kr['kategorie']}</span>"
                            f"<div><span style='font-family:DM Mono,monospace;color:#f87171;font-size:12px;'>−{cut:,.2f} {currency_sym}</span>"
                            f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;margin-left:8px;'>({cut / kr['betrag_num'] * 100:.0f}%)</span></div></div>"
                        )
                        remaining -= cut
                    st.markdown(
                        f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                        f"border:1px solid rgba(248,113,113,0.1);border-left:3px solid #f87171;border-radius:16px;padding:18px 20px;margin-top:12px;'>"
                        f"<div style='font-family:DM Mono,monospace;font-size:9px;color:#ef4444;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Noch {fehlbetrag:,.2f} {currency_sym} bis zum Ziel</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;margin-bottom:12px;'>Diese Kategorien könntest du reduzieren:</div>"
                        f"{rows_html}</div>",
                        unsafe_allow_html=True,
                    )
            elif erreicht:
                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                    f"border:1px solid rgba(74,222,128,0.15);border-left:3px solid #4ade80;border-radius:16px;padding:18px 20px;margin-top:12px;'>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:14px;font-weight:500;'>🎉 Sparziel diesen Monat erreicht!</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#475569;font-size:13px;margin-top:6px;'>Du hast {akt_spar - current_goal:,.2f} {currency_sym} mehr gespart als geplant.</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div style='background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.06);border-radius:12px;"
                "padding:20px 22px;color:#334155;font-family:DM Sans,sans-serif;font-size:14px;'>"
                "Trage links ein Sparziel ein, um Empfehlungen zu erhalten.</div>",
                unsafe_allow_html=True,
            )
