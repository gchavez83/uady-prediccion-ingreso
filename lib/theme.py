"""Sistema visual Synapse (IA Enterprise) para la app Streamlit.

Paleta y tipografía oficiales del manual de identidad (IAE-BRAND-001):
Ink #0A1628 · Azure #2A6FDB · Amber #F39A1E · Ivory #F7F4EE + soportes.
Fuentes: Instrument Serif (display/KPI), Geist (UI), JetBrains Mono (datos).
"""
from __future__ import annotations
import streamlit as st

# Paleta oficial -----------------------------------------------------------
INK = "#0A1628"
INK_1 = "#0E1D38"
NAVY = "#244269"
AZURE = "#2A6FDB"
AZURE_7 = "#1858C2"
AMBER = "#F39A1E"
IVORY = "#F7F4EE"
SLATE = "#38414F"
SLATE_3 = "#BFC6D2"
SUCCESS = "#0B8F6B"
DANGER = "#C53030"
# 5 colores de clúster (dentro de paleta de marca)
CLUSTER_COLORS = {
    "Cluster1": NAVY, "Cluster2": AZURE, "Cluster3": "#7A8CA8",
    "Cluster4": AZURE_7, "Cluster5": AMBER,
}

_FONTS = "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"


def inject_theme() -> None:
    st.markdown(f"""
    <style>
    @import url('{_FONTS}');
    :root{{
      --ink:{INK}; --ink-1:{INK_1}; --navy:{NAVY}; --azure:{AZURE}; --azure-7:{AZURE_7};
      --amber:{AMBER}; --ivory:{IVORY}; --slate:{SLATE}; --slate-3:{SLATE_3};
      --success:{SUCCESS}; --danger:{DANGER};
      --serif:'Instrument Serif',Georgia,serif;
      --sans:'Geist',system-ui,-apple-system,'Segoe UI',sans-serif;
      --mono:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;
      --line:rgba(36,66,105,.14);
    }}
    /* Canvas ivory + tipografía base Geist */
    [data-testid="stAppViewContainer"]{{background:{IVORY};}}
    /* Barra superior transparente: se funde con el fondo de cada página */
    [data-testid="stHeader"]{{background:transparent;}}
    .stApp{{background:{IVORY};}}
    html,body,[class*="st-"],.stMarkdown,.stButton,p,li,div{{font-family:var(--sans);}}
    /* Excepción: los iconos Material conservan su fuente (si no, la ligadura sale como texto) */
    [data-testid="stIconMaterial"]{{font-family:'Material Symbols Rounded' !important;}}
    .block-container{{padding-top:4rem;max-width:1200px;}}
    h1,h2,h3{{font-family:var(--serif);font-weight:400;letter-spacing:-.01em;color:{INK};}}

    /* ---- Campos de formulario destacados sobre el canvas ivory ---- */
    [data-testid="stNumberInput"] div[data-baseweb="input"],
    [data-testid="stTextInput"] div[data-baseweb="input"],
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] > div{{
      background:#fff !important;border:1px solid var(--line) !important;border-radius:10px !important;
      box-shadow:0 1px 2px rgba(10,22,40,.05);transition:border-color .15s,box-shadow .15s;}}
    [data-testid="stNumberInput"] input,[data-testid="stTextInput"] input{{background:#fff !important;}}
    [data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{{
      border-color:{AZURE} !important;box-shadow:0 0 0 3px rgba(42,111,219,.15);}}
    [data-testid="stWidgetLabel"] p,.stRadio label,.stSelectbox label{{font-weight:500;color:{INK};}}
    /* Botones del selector segmentado (stButtonGroup) del mismo ancho */
    [data-testid="stButtonGroup"]{{display:flex;flex-wrap:wrap;gap:6px;width:100%;}}
    [data-testid="stButtonGroup"] > div{{flex:1 1 0;min-width:130px;}}
    [data-testid="stButtonGroup"] button{{width:100%;}}
    h1{{font-size:2.5rem;line-height:1.05;}}
    /* Sidebar nav */
    [data-testid="stSidebar"]{{background:{INK};}}
    [data-testid="stSidebar"] *{{color:{IVORY};}}
    [data-testid="stSidebarNav"] a span{{font-family:var(--sans);}}

    /* ---- eyebrow / mono labels ---- */
    .syn-eyebrow{{font-family:var(--mono);font-size:.72rem;letter-spacing:.2em;
      text-transform:uppercase;color:{AMBER};}}

    /* ---- KPI cards ---- */
    .kpi-row{{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin:6px 0 8px;}}
    @media(max-width:1150px){{.kpi-row{{grid-template-columns:repeat(4,1fr);}}}}
    @media(max-width:680px){{.kpi-row{{grid-template-columns:repeat(2,1fr);}}}}
    .kpi{{min-width:0;background:#fff;border:1px solid var(--line);
      border-radius:15px;padding:16px 14px 12px;display:flex;flex-direction:column;gap:9px;
      box-shadow:0 1px 2px rgba(10,22,40,.04),0 10px 26px -16px rgba(10,22,40,.22);}}
    .kpi .k-lab{{font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;
      text-transform:uppercase;color:{SLATE};line-height:1.3;}}
    .kpi .k-val{{font-family:var(--serif);font-size:2.15rem;line-height:1;color:{INK};
      font-variant-numeric:tabular-nums;}}
    .kpi .k-spark{{height:34px;}}
    .kpi .k-spark svg{{width:100%;height:34px;display:block;}}
    .kpi .k-meta{{display:flex;flex-direction:column;align-items:flex-start;gap:4px;margin-top:auto;}}
    .kpi .k-delta{{display:inline-flex;align-items:center;gap:5px;font-size:.76rem;font-weight:600;
      font-variant-numeric:tabular-nums;padding:3px 9px;border-radius:999px;white-space:nowrap;max-width:100%;}}
    .k-good{{color:{SUCCESS};background:rgba(11,143,107,.12);}}
    .k-bad{{color:{DANGER};background:rgba(197,48,48,.10);}}
    .k-neutral,.k-flat{{color:{SLATE};background:rgba(56,65,79,.08);}}
    .kpi .k-vs{{font-family:var(--mono);font-size:.6rem;color:{SLATE_3};letter-spacing:.08em;white-space:nowrap;}}
    .kpi.k-hero{{background:linear-gradient(155deg,{INK},#13264a);border-color:transparent;}}
    .kpi.k-hero .k-lab{{color:#9fb0cc;}} .kpi.k-hero .k-val{{color:{AMBER};}}
    .kpi.k-hero .k-vs{{color:#7f90b4;}}
    .kpi.k-hero .k-bad{{color:#fcd9d4;background:rgba(197,48,48,.25);}}
    .kpi.k-hero .k-good{{color:#9fe7cf;background:rgba(11,143,107,.25);}}

    /* ---- tabla de varianza (Zebra BI / IBCS) ---- */
    .vt-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:#fff;}}
    .vt{{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:13px;min-width:640px;}}
    .vt th{{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;
      color:{SLATE};text-align:right;padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap;}}
    .vt th.lab{{text-align:left;}}
    .vt td{{padding:8px 14px;border-bottom:1px solid rgba(36,66,105,.07);}}
    .vt td.lab{{text-align:left;color:{INK};}}
    .vt td.num{{text-align:right;font-variant-numeric:tabular-nums;color:{INK};}}
    .vt td.num.dim{{color:{SLATE_3};}}
    .vt-prog td.lab{{padding-left:26px;color:{SLATE};font-size:12.5px;}}
    .vt-campus td{{background:rgba(36,66,105,.05);font-weight:600;}}
    .vt-campus td.lab{{font-size:11px;letter-spacing:.04em;text-transform:uppercase;font-family:var(--mono);}}
    .vt-total td{{border-top:2px solid {NAVY};font-weight:700;background:rgba(243,154,30,.06);}}
    .vt .barc{{width:150px;white-space:nowrap;}}
    .vt .dbar{{position:relative;display:inline-block;vertical-align:middle;width:96px;height:13px;
      background:linear-gradient(90deg,transparent 49.4%,rgba(56,65,79,.28) 49.4%,rgba(56,65,79,.28) 50.6%,transparent 50.6%);}}
    .vt .dbar span{{position:absolute;top:2px;height:9px;border-radius:2px;}}
    .vt .bv{{display:inline-block;margin-left:8px;font-variant-numeric:tabular-nums;font-weight:600;font-size:12px;}}

    /* ---- paneles de comparación (folio) ---- */
    .cmp{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;
      display:flex;flex-direction:column;gap:11px;
      box-shadow:0 1px 2px rgba(10,22,40,.04),0 10px 26px -16px rgba(10,22,40,.2);}}
    .cmp-h{{font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:{SLATE};}}
    .cmp-vals{{display:flex;align-items:flex-end;justify-content:space-between;gap:8px;}}
    .cmp-vals .k{{font-family:var(--mono);font-size:.56rem;letter-spacing:.06em;text-transform:uppercase;color:{SLATE_3};margin-bottom:3px;}}
    .cmp-mine{{font-family:var(--serif);font-size:1.95rem;line-height:1;color:{INK};font-variant-numeric:tabular-nums;}}
    .cmp-ref{{font-family:var(--serif);font-size:1.4rem;line-height:1;color:{SLATE};text-align:right;font-variant-numeric:tabular-nums;}}
    .cmp-vs{{font-family:var(--mono);font-size:.6rem;color:{SLATE_3};padding-bottom:5px;}}
    .cmp-badge{{align-self:flex-start;font-size:.78rem;font-weight:600;padding:4px 11px;border-radius:999px;}}
    </style>
    """, unsafe_allow_html=True)


def synapse_mark(size="40", on_dark: bool = True) -> str:
    """SVG del símbolo Synapse con su geometría oficial (grid 10×10 ×10)."""
    P = [(20, 28), (78, 22), (20, 72), (78, 78)]  # BI(nw) IA(ne) ML(sw) SW(se)
    edges = [(0, 1), (1, 3), (3, 2), (2, 0), (0, 3), (1, 2)]
    if on_dark:
        node, stroke, hole = IVORY, "rgba(147,161,188,.5)", INK
    else:
        node, stroke, hole = None, NAVY, "#fff"
    node_colors = [NAVY, AZURE, AZURE, NAVY]
    s = [f'<svg viewBox="0 0 100 100" width="{size}" height="{size}" aria-hidden="true">']
    for a, b in edges:
        s.append(f'<line x1="{P[a][0]}" y1="{P[a][1]}" x2="{P[b][0]}" y2="{P[b][1]}" '
                 f'stroke="{stroke}" stroke-width="1.6" stroke-linecap="round"/>')
    for i, (x, y) in enumerate(P):
        s.append(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{node or node_colors[i]}"/>')
    s.append(f'<circle cx="50" cy="50" r="8.5" fill="{AMBER}"/>'
             f'<circle cx="50" cy="50" r="3" fill="{hole}"/></svg>')
    return "".join(s)


def _sparkline(series, color, fill, base="rgba(36,66,105,.12)") -> str:
    vals = [v for v in series if v == v]  # drop NaN
    if not vals:
        return ""
    W, H, pad = 200, 34, 4
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(series)
    pts = []
    for i, v in enumerate(series):
        x = pad + i * (W - 2 * pad) / max(n - 1, 1)
        y = H - pad - ((v - mn) / rng) * (H - 2 * pad)
        pts.append((x, y))
    line = " ".join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    area = f"M{pad} {H} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{W-pad} {H} Z"
    ex, ey = pts[-1]
    return (f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none">'
            f'<line x1="{pad}" y1="{H-pad}" x2="{W-pad}" y2="{H-pad}" stroke="{base}" stroke-width="1"/>'
            f'<path d="{area}" fill="{fill}"/>'
            f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3" fill="{color}"/></svg>')


def kpi_card_html(label, value, delta, series, hero=False) -> str:
    """delta = dict {text, kind, arrow} de metrics.delta_info."""
    if hero:
        spark = _sparkline(series, AMBER, "rgba(243,154,30,.18)", base="rgba(255,255,255,.16)")
    else:
        spark = _sparkline(series, AZURE, "rgba(42,111,219,.10)")
    return (
        f'<div class="kpi{" k-hero" if hero else ""}">'
        f'<div class="k-lab">{label}</div>'
        f'<div class="k-val">{value}</div>'
        f'<div class="k-spark">{spark}</div>'
        f'<div class="k-meta">'
        f'<span class="k-delta k-{delta["kind"]}">{delta["arrow"]} {delta["text"]}</span>'
        f'<span class="k-vs">vs {delta.get("vs","año ant.")}</span>'
        f'</div></div>'
    )


def render_kpi_row(cards: list[str]) -> None:
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


_TONE = {"ink": SLATE_3, "success": SUCCESS, "danger": DANGER, "amber": AMBER, "azure": AZURE}


def stat_card(label: str, value: str, tone: str = "ink", sub: str = "", vsize: str = "1.7rem") -> str:
    """Tarjeta simple (sin sparkline): etiqueta mono + valor serif + riel de color por tono."""
    rail = _TONE.get(tone, SLATE_3)
    vcol = INK if tone in ("ink",) else rail
    sub_html = f'<div class="k-vs">{sub}</div>' if sub else ""
    return (f'<div class="kpi" style="border-left:4px solid {rail};min-height:auto;gap:6px;justify-content:flex-start">'
            f'<div class="k-lab">{label}</div>'
            f'<div class="k-val" style="font-size:{vsize};color:{vcol};line-height:1.14;overflow-wrap:anywhere">{value}</div>'
            f'{sub_html}</div>')


def render_grid(cards: list[str], cols: int) -> None:
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;margin:6px 0 8px;">'
        f'{"".join(cards)}</div>', unsafe_allow_html=True)


def comparison_panel(title, mine, ref, mine_lab, ref_lab, gap_text, tone, lo, hi) -> str:
    """Panel de comparación: tu valor vs un umbral, con barra y veredicto (tone good/bad)."""
    color = SUCCESS if tone == "good" else DANGER
    bar = compare_bar(mine, ref, lo, hi, color)
    return (
        f'<div class="cmp"><div class="cmp-h">{title}</div>'
        f'<div class="cmp-vals">'
        f'<div><div class="k">{mine_lab}</div><div class="cmp-mine">{mine:,.0f}</div></div>'
        f'<div class="cmp-vs">vs</div>'
        f'<div><div class="k" style="text-align:right">{ref_lab}</div><div class="cmp-ref">{ref:,.0f}</div></div>'
        f'</div>{bar}<div class="cmp-badge k-{tone}">{gap_text}</div></div>'
    )


def render_panels(panels: list[str]) -> None:
    st.markdown('<div style="display:flex;flex-direction:column;gap:14px;">'
                + "".join(panels) + "</div>", unsafe_allow_html=True)


def compare_bar(value: float, target: float, lo: float, hi: float, vcolor: str) -> str:
    """Barra horizontal del valor del aspirante con una marca (tick) en el punto de corte."""
    span = (hi - lo) or 1
    vw = max(0, min((value - lo) / span * 100, 100))
    tw = max(0, min((target - lo) / span * 100, 100))
    return (
        f'<div style="position:relative;height:30px;background:rgba(36,66,105,.07);border-radius:8px;overflow:hidden;">'
        f'<div style="position:absolute;left:0;top:0;bottom:0;width:{vw:.1f}%;background:{vcolor};border-radius:8px 0 0 8px;"></div>'
        f'<div style="position:absolute;left:{tw:.1f}%;top:-3px;bottom:-3px;width:3px;background:{AMBER};"></div>'
        f'<span style="position:absolute;right:8px;top:50%;transform:translateY(-50%);font-family:var(--mono);font-size:12px;color:#fff;font-weight:600;">{value:,.0f}</span>'
        f'</div>')
