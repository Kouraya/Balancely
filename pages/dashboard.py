import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from constants import PALETTE_AUS, PALETTE_EIN, PALETTE_DEP, CURRENCY_SYMBOLS
from database import _gs_read, load_toepfe, load_goal
from styling import inject_theme


def render(user_name, user_settings, theme, currency_sym):
    now = datetime.datetime.now()
    st.markdown(
        f"<div style='margin-bottom:36px;margin-top:16px;'>"
        f"<h1 style='font-family:DM Sans,sans-serif;font-size:40px;font-weight:700;color:#e2e8f0;"
        f"margin:0 0 6px 0;letter-spacing:-1px;'>Deine Übersicht, {user_name}! ⚖️</h1>"
        f"<p style='font-family:DM Sans,sans-serif;color:#475569;font-size:15px;margin:0;'>Monatliche Finanzübersicht</p></div>",
        unsafe_allow_html=True,
    )

    offset  = st.session_state.get('dash_month_offset', 0)
    m_total = now.year * 12 + (now.month - 1) + offset
    t_year, t_month_idx = divmod(m_total, 12)
    t_month = t_month_idx + 1
    monat_label = datetime.date(t_year, t_month, 1).strftime("%B %Y")

    nav1, nav2, nav3 = st.columns([1, 5, 1])
    with nav1:
        if st.button("‹", use_container_width=True, key="dash_prev"):
            st.session_state['dash_month_offset'] -= 1
            st.session_state.update({'dash_selected_cat': None, 'dash_selected_typ': None, 'dash_selected_color': None})
            st.rerun()
    with nav2:
        st.markdown(
            f"<div style='text-align:center;font-family:DM Sans,sans-serif;font-size:14px;"
            f"font-weight:500;color:#64748b;padding:6px 0;'>{monat_label}</div>",
            unsafe_allow_html=True,
        )
    with nav3:
        if st.button("›", use_container_width=True, key="dash_next", disabled=(offset >= 0)):
            st.session_state['dash_month_offset'] += 1
            st.session_state.update({'dash_selected_cat': None, 'dash_selected_typ': None, 'dash_selected_color': None})
            st.rerun()

    try:
        df_t = _gs_read("transactions")
        if "user" not in df_t.columns:
            st.info("Noch keine Daten vorhanden.")
            return

        alle = df_t[df_t["user"] == user_name].copy()
        if "deleted" in alle.columns:
            alle = alle[~alle["deleted"].astype(str).str.strip().str.lower().isin(["true", "1", "1.0"])]
        alle["datum_dt"] = pd.to_datetime(alle["datum"], errors="coerce")
        monat_df = alle[(alle["datum_dt"].dt.year == t_year) & (alle["datum_dt"].dt.month == t_month)].copy()

        if monat_df.empty:
            st.markdown(
                f"<div style='text-align:center;padding:60px 20px;color:#334155;font-family:DM Sans,sans-serif;"
                f"font-size:15px;'>Keine Buchungen im {monat_label}</div>",
                unsafe_allow_html=True,
            )
            return

        monat_df["betrag_num"] = pd.to_numeric(monat_df["betrag"], errors="coerce")
        alle["betrag_num"]     = pd.to_numeric(alle["betrag"], errors="coerce")

        ein        = monat_df[monat_df["typ"] == "Einnahme"]["betrag_num"].sum()
        aus        = monat_df[monat_df["typ"] == "Ausgabe"]["betrag_num"].abs().sum()
        dep_monat  = monat_df[monat_df["typ"] == "Depot"]["betrag_num"].abs().sum()
        sp_netto   = monat_df[monat_df["typ"] == "Spartopf"]["betrag_num"].sum()
        bank       = ein - aus - dep_monat + sp_netto
        dep_gesamt = alle[alle["typ"] == "Depot"]["betrag_num"].abs().sum()
        topf_gesamt= sum(t['gespart'] for t in load_toepfe(user_name))
        networth   = bank + dep_gesamt + topf_gesamt

        bank_color = "#e2e8f0" if bank >= 0 else "#f87171"
        nw_color   = "#4ade80" if networth >= 0 else "#f87171"
        bank_str   = f"{bank:,.2f} {currency_sym}" if bank >= 0 else f"-{abs(bank):,.2f} {currency_sym}"
        nw_str     = f"{networth:,.2f} {currency_sym}" if networth >= 0 else f"-{abs(networth):,.2f} {currency_sym}"

        # Budget bar
        if offset == 0:
            _budget = user_settings.get('budget', 0)
            if _budget > 0:
                _bpct = min(aus / _budget * 100, 100)
                _bcol = "#4ade80" if _bpct < 60 else ("#facc15" if _bpct < 85 else "#f87171")
                _bem  = "🟢" if _bpct < 60 else ("🟡" if _bpct < 85 else "🔴")
                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
                    f"border:1px solid rgba(148,163,184,0.08);border-radius:14px;padding:14px 18px;margin-bottom:16px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;'>"
                    f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;'>{_bem} Monats-Budget</span>"
                    f"<span style='font-family:DM Mono,monospace;color:{_bcol};font-size:13px;font-weight:600;'>"
                    f"{aus:,.2f} / {_budget:,.2f} {currency_sym} · {_bpct:.0f}%</span></div>"
                    f"<div style='background:rgba(30,41,59,0.8);border-radius:99px;height:6px;overflow:hidden;'>"
                    f"<div style='width:{_bpct:.0f}%;height:100%;background:{_bcol};border-radius:99px;'></div></div></div>",
                    unsafe_allow_html=True,
                )

        # Sparziel alert
        if offset == 0:
            _goal    = load_goal(user_name)
            _sp_einz = abs(monat_df[(monat_df["typ"] == "Spartopf") & (monat_df["betrag_num"] < 0)]["betrag_num"].sum())
            if _goal > 0:
                _effektiv = bank + _sp_einz
                if _effektiv < _goal:
                    _fehl = _goal - _effektiv
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,rgba(251,113,133,0.08),rgba(239,68,68,0.05));"
                        f"border:1px solid rgba(248,113,113,0.25);border-left:3px solid #f87171;"
                        f"border-radius:14px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px;'>"
                        f"<span style='font-size:22px;'>⚠️</span><div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#fca5a5;font-weight:600;font-size:14px;margin-bottom:2px;'>"
                        f"Du liegst {_fehl:,.2f} {currency_sym} unter deinem Sparziel</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;'>"
                        f"Ziel: {_goal:,.2f} {currency_sym} · Gespart: {_effektiv:,.2f} {currency_sym}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    _ueber = _effektiv - _goal
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,rgba(74,222,128,0.05),rgba(34,197,94,0.03));"
                        f"border:1px solid rgba(74,222,128,0.2);border-left:3px solid #4ade80;"
                        f"border-radius:14px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;gap:14px;'>"
                        f"<span style='font-size:22px;'>✅</span><div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#86efac;font-weight:600;font-size:14px;margin-bottom:2px;'>"
                        f"Sparziel erreicht! +{_ueber:,.2f} {currency_sym} Puffer</div>"
                        f"<div style='font-family:DM Sans,sans-serif;color:#64748b;font-size:13px;'>"
                        f"Gespart: {_effektiv:,.2f} {currency_sym}</div></div></div>",
                        unsafe_allow_html=True,
                    )

        _sp_einz2 = abs(monat_df[(monat_df["typ"] == "Spartopf") & (monat_df["betrag_num"] < 0)]["betrag_num"].sum())
        dep_html = (
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(56,189,248,0.15);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Depot</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#38bdf8;font-size:24px;font-weight:600;'>{dep_monat:,.2f} {currency_sym}</div></div>"
        ) if dep_monat > 0 else ""
        topf_html = (
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(167,139,250,0.2);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#7c3aed;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Spartöpfe</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#a78bfa;font-size:24px;font-weight:600;'>{_sp_einz2:,.2f} {currency_sym}</div></div>"
        ) if _sp_einz2 > 0 else ""

        st.markdown(
            f"<div style='display:flex;gap:14px;margin:0 0 12px 0;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Bankkontostand</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>diesen Monat</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:{bank_color};font-size:24px;font-weight:600;'>{bank_str}</div></div>"
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(56,189,248,0.12);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e40af;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;'>Gesamtvermögen</div>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#1e293b;margin-bottom:10px;'>Bank + Depot + Töpfe</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:{nw_color};font-size:24px;font-weight:600;'>{nw_str}</div></div></div>"
            f"<div style='display:flex;gap:14px;margin:0 0 28px 0;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Einnahmen</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#4ade80;font-size:24px;font-weight:600;'>+{ein:,.2f} {currency_sym}</div></div>"
            f"<div style='flex:1;min-width:160px;background:linear-gradient(145deg,rgba(14,22,38,0.9),rgba(10,16,30,0.95));"
            f"border:1px solid rgba(148,163,184,0.08);border-radius:16px;padding:20px 22px;'>"
            f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#334155;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;'>Ausgaben</div>"
            f"<div style='font-family:DM Sans,sans-serif;color:#f87171;font-size:24px;font-weight:600;'>-{aus:,.2f} {currency_sym}</div></div>"
            + dep_html + topf_html + "</div>",
            unsafe_allow_html=True,
        )

        ausg_df  = monat_df[monat_df["typ"] == "Ausgabe"].copy()
        ausg_df["betrag_num"] = ausg_df["betrag_num"].abs()
        ein_df   = monat_df[monat_df["typ"] == "Einnahme"].copy()
        dep_df   = monat_df[monat_df["typ"] == "Depot"].copy()
        dep_df["betrag_num"] = pd.to_numeric(dep_df["betrag_num"], errors="coerce").abs()
        ausg_grp = ausg_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num", ascending=False)
        ein_grp  = ein_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num", ascending=False)
        dep_grp  = dep_df.groupby("kategorie")["betrag_num"].sum().reset_index().sort_values("betrag_num", ascending=False)

        all_cats, all_vals, all_colors, all_types = [], [], [], []
        for i, (_, row) in enumerate(ein_grp.iterrows()):
            all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
            all_colors.append(PALETTE_EIN[i % len(PALETTE_EIN)]); all_types.append("Einnahme")
        for i, (_, row) in enumerate(ausg_grp.iterrows()):
            all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
            all_colors.append(PALETTE_AUS[i % len(PALETTE_AUS)]); all_types.append("Ausgabe")
        for i, (_, row) in enumerate(dep_grp.iterrows()):
            all_cats.append(row["kategorie"]); all_vals.append(float(row["betrag_num"]))
            all_colors.append(PALETTE_DEP[i % len(PALETTE_DEP)]); all_types.append("Depot")

        fig = go.Figure(go.Pie(
            labels=all_cats, values=all_vals, hole=0.62,
            marker=dict(colors=all_colors, line=dict(color="rgba(5,10,20,0.8)", width=2)),
            textinfo="none", hoverinfo="none", direction="clockwise", sort=False, rotation=90,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20), height=380, autosize=True,
            annotations=[
                dict(text="BANK", x=0.5, y=0.62, showarrow=False,
                     font=dict(size=10, color="#334155", family="DM Mono, monospace"), xref="paper", yref="paper"),
                dict(text=f"<b>{bank_str}</b>", x=0.5, y=0.50, showarrow=False,
                     font=dict(size=22, color=bank_color, family="DM Sans, sans-serif"), xref="paper", yref="paper"),
                dict(text=f"+{ein:,.0f}  /  -{aus:,.0f} {currency_sym}", x=0.5, y=0.38, showarrow=False,
                     font=dict(size=11, color="#334155", family="DM Sans, sans-serif"), xref="paper", yref="paper"),
            ],
        )

        chart_col, legend_col = st.columns([2, 2])
        with chart_col:
            st.plotly_chart(fig, use_container_width=True, key="donut_combined")
        with legend_col:
            sel_cat   = st.session_state.get('dash_selected_cat')
            sel_typ   = st.session_state.get('dash_selected_typ')
            sel_color = st.session_state.get('dash_selected_color')
            if sel_cat and sel_typ:
                src_df = {"Ausgabe": ausg_df, "Einnahme": ein_df, "Depot": dep_df}.get(sel_typ, ausg_df)
                detail  = src_df[src_df["kategorie"] == sel_cat]
                total_d = detail["betrag_num"].sum()
                sign    = "−" if sel_typ == "Ausgabe" else "+"
                rows_html = "".join(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;padding:10px 0;"
                    f"border-bottom:1px solid rgba(255,255,255,0.05);'>"
                    f"<div style='display:flex;align-items:center;gap:10px;'>"
                    f"<span style='font-family:DM Mono,monospace;color:#64748b;font-size:12px;'>{tr['datum_dt'].strftime('%d.%m.')}</span>"
                    + (f"<span style='color:#94a3b8;font-size:13px;'>{str(tr.get('notiz', ''))}</span>"
                       if str(tr.get('notiz', '')).lower() not in ('nan', '') else "")
                    + f"</div><span style='color:{sel_color};font-weight:600;font-size:13px;font-family:DM Mono,monospace;'>"
                    f"{sign}{tr['betrag_num']:,.2f} {currency_sym}</span></div>"
                    for _, tr in detail.sort_values("datum_dt", ascending=False).iterrows()
                )
                if st.button("← Alle Kategorien", key="dash_back_btn"):
                    st.session_state.update({'dash_selected_cat': None, 'dash_selected_typ': None, 'dash_selected_color': None})
                    st.rerun()
                st.markdown(
                    f"<div style='background:linear-gradient(145deg,rgba(13,23,41,0.95),rgba(10,16,30,0.98));"
                    f"border:1px solid {sel_color}30;border-top:2px solid {sel_color};border-radius:14px;padding:18px 20px;margin-top:10px;'>"
                    f"<div style='font-family:DM Mono,monospace;color:{sel_color};font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>{sel_typ}</div>"
                    f"<div style='font-family:DM Sans,sans-serif;color:#e2e8f0;font-weight:600;font-size:16px;margin-bottom:4px;'>{sel_cat}</div>"
                    f"<div style='font-family:DM Mono,monospace;color:{sel_color};font-size:22px;font-weight:500;margin-bottom:18px;'>{sign}{total_d:,.2f} {currency_sym}</div>"
                    f"{rows_html}</div>",
                    unsafe_allow_html=True,
                )
            else:
                TYP_CONFIG    = {"Einnahme": ("EINNAHMEN", "#2b961f", "+"), "Ausgabe": ("AUSGABEN", "#ff5232", "−"), "Depot": ("DEPOT", "#2510a3", "")}
                available_types = list(dict.fromkeys(all_types))
                if st.session_state.get('dash_legend_tab') not in available_types:
                    st.session_state['dash_legend_tab'] = available_types[0] if available_types else "Ausgabe"
                active_tab_dash = st.session_state['dash_legend_tab']
                tab_cols = st.columns(len(available_types))
                for i, typ in enumerate(available_types):
                    lbl, _, _ = TYP_CONFIG.get(typ, (typ.upper(), "#64748b", ""))
                    with tab_cols[i]:
                        if st.button(lbl, key=f"dash_tab_{typ}", use_container_width=True,
                                     type="primary" if typ == active_tab_dash else "secondary"):
                            st.session_state['dash_legend_tab'] = typ
                            st.rerun()
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                _, color_active, sign_active = TYP_CONFIG.get(active_tab_dash, (active_tab_dash, "#64748b", ""))
                total_sum = sum(all_vals) if sum(all_vals) > 0 else 1
                for cat, val, color, typ in zip(all_cats, all_vals, all_colors, all_types):
                    if typ != active_tab_dash:
                        continue
                    col_legend, col_btn = st.columns([10, 1])
                    with col_legend:
                        st.markdown(
                            f"<div style='display:flex;align-items:center;justify-content:space-between;padding:7px 8px;border-radius:8px;'>"
                            f"<div style='display:flex;align-items:center;gap:10px;min-width:0;'>"
                            f"<div style='width:7px;height:7px;border-radius:50%;background:{color};flex-shrink:0;'></div>"
                            f"<span style='font-family:DM Sans,sans-serif;color:#94a3b8;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{cat}</span></div>"
                            f"<div style='display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;'>"
                            f"<span style='font-family:DM Mono,monospace;color:{color};font-weight:500;font-size:12px;'>{sign_active}{val:,.2f} {currency_sym}</span>"
                            f"<span style='font-family:DM Mono,monospace;color:#334155;font-size:11px;'>{val / total_sum * 100:.0f}%</span>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )
                    with col_btn:
                        if st.button("›", key=f"legend_btn_{cat}_{typ}"):
                            st.session_state.update({'dash_selected_cat': cat, 'dash_selected_typ': typ, 'dash_selected_color': color})
                            st.rerun()

    except Exception as e:
        st.warning(f"Verbindung wird hergestellt... ({e})")
