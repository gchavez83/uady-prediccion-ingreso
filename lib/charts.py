"""Constructores de gráficos Plotly en estilo IBCS / Synapse."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .data import COL_ABV, COL_CEN, COL_PM
from . import metrics as M
from .theme import INK, NAVY, AZURE, AMBER, SLATE, SLATE_3, SUCCESS, DANGER, IVORY, CLUSTER_COLORS

FONT = "Geist, system-ui, sans-serif"


def _per_program(df_cycle: pd.DataFrame, df_prev: pd.DataFrame, bars_key: str) -> pd.DataFrame:
    """Tabla por ABV: valor de barra (ciclo y previo) + % ingreso, ordenada por %."""
    rows = []
    for abv, g in df_cycle.groupby(COL_ABV):
        prev = df_prev[df_prev[COL_ABV] == abv]
        rows.append({
            "abv": abv,
            "programa": g["programa"].iloc[0],
            "bar": M.compute(g, bars_key),
            "bar_prev": M.compute(prev, bars_key) if len(prev) else float("nan"),
            "pct": M.compute(g, "pct"),
        })
    t = pd.DataFrame(rows)
    t["dpy"] = t["bar"] - t["bar_prev"]
    return t.sort_values("pct").reset_index(drop=True)


def combo(df_cycle: pd.DataFrame, df_prev: pd.DataFrame, bars_key: str) -> go.Figure:
    """Combo IBCS: barras (métrica) + línea (% ingreso) + ΔPY, ordenado por % asc."""
    t = _per_program(df_cycle, df_prev, bars_key)
    label = M.METRICS[bars_key]["label"]
    fig = go.Figure()

    fig.add_bar(
        x=t["abv"], y=t["bar"], name=label,
        marker_color=NAVY, marker_line_width=0,
        text=[f"{v:,.0f}" for v in t["bar"]], textposition="inside",
        textfont=dict(color="white", size=10, family=FONT),
        customdata=t["programa"],
        hovertemplate="<b>%{customdata}</b> (%{x})<br>" + label + ": %{y:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=t["abv"], y=t["pct"], name="% Ingreso", yaxis="y2",
        mode="lines+markers", line=dict(color=AMBER, width=2),
        marker=dict(color=AMBER, size=6), customdata=t["programa"],
        hovertemplate="<b>%{customdata}</b> (%{x})<br>% Ingreso: %{y:.1f}%<extra></extra>",
    )
    # Anotaciones ΔPY (verde positivo / rojo negativo) sobre cada barra
    for _, r in t.iterrows():
        if r["dpy"] == r["dpy"]:  # no NaN
            fig.add_annotation(
                x=r["abv"], y=r["bar"], yshift=12, showarrow=False,
                text=f"{r['dpy']:+,.0f}",
                font=dict(size=9, family=FONT,
                          color=SUCCESS if r["dpy"] >= 0 else DANGER),
            )
    fig.update_layout(
        barmode="group", height=460, bargap=0.25,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=SLATE, size=11),
        showlegend=False,
        xaxis=dict(tickangle=-90, tickfont=dict(size=9), showgrid=False),
        yaxis=dict(title=label, showgrid=True, gridcolor="rgba(36,66,105,.08)", zeroline=False),
        yaxis2=dict(title="% Ingreso", overlaying="y", side="right",
                    range=[0, 105], showgrid=False, ticksuffix="%"),
    )
    return fig


def small_multiple(prog: str, series: list[float], cycles: list[int], key: str) -> go.Figure:
    """Mini-gráfica de tendencia de un programa: barras por ciclo + ΔPY + % final."""
    vfmt = M.METRICS[key]["fmt"]
    dfmt = M.METRICS[key]["dfmt"]
    deltas = [None] + [series[i] - series[i - 1] for i in range(1, len(series))]
    last_pct = None
    if len(series) >= 2 and series[-2] == series[-2] and series[-2] != 0:
        last_pct = (series[-1] - series[-2]) / series[-2] * 100

    fig = go.Figure()
    fig.add_bar(
        x=[str(c) for c in cycles], y=series, marker_color=NAVY, marker_line_width=0,
        hovertemplate="%{x}: " + "%{y:,.0f}<extra></extra>",
    )
    for i, d in enumerate(deltas):
        if d is not None and d == d and abs(d) > 1e-9:
            fig.add_annotation(x=str(cycles[i]), y=series[i], yshift=11, showarrow=False,
                               text=dfmt.format(d).replace(" pp", ""),
                               font=dict(size=8, family=FONT, color=SUCCESS if d > 0 else DANGER))
    titulo = prog if len(prog) <= 30 else prog[:28] + "…"
    sub = f"{vfmt.format(series[-1])}" if series[-1] == series[-1] else "—"
    if last_pct is not None:
        col = SUCCESS if last_pct >= 0 else DANGER
        sub += f"  <span style='color:{col}'>({last_pct:+.1f}%)</span>"
    fig.update_layout(
        height=190, margin=dict(l=6, r=6, t=40, b=6), bargap=0.35,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=SLATE, size=10), showlegend=False,
        title=dict(text=f"<b>{titulo}</b><br><span style='font-size:11px'>{sub}</span>",
                   font=dict(family=FONT, size=12, color=INK), x=0, xanchor="left"),
        xaxis=dict(tickfont=dict(size=9), showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
    )
    return fig


def cluster_scatter(d2026) -> go.Figure:
    """Dispersión de programas: X=Avg punto de corte, Y=%ingreso, tamaño=admitidos, color=clúster."""
    rows = []
    for prog, g in d2026.groupby("programa"):
        rows.append({
            "abv": g[COL_ABV].iloc[0], "cluster": g["cluster"].iloc[0],
            "corte": M.m_punto_corte(g), "pct": M.m_pct(g), "adm": M.m_admitidos(g),
            "prog": prog,
        })
    t = pd.DataFrame(rows)
    maxadm = max(t["adm"].max(), 1)
    sizeref = 2.0 * maxadm / (52.0 ** 2)
    fig = go.Figure()
    for cl in sorted(t["cluster"].dropna().unique()):
        s = t[t["cluster"] == cl]
        fig.add_scatter(
            x=s["corte"], y=s["pct"], mode="markers+text", name=cl,
            text=s["abv"], textposition="top center",
            textfont=dict(size=8, family=FONT, color=SLATE),
            marker=dict(size=s["adm"], sizemode="area", sizeref=sizeref, sizemin=4,
                        color=CLUSTER_COLORS.get(cl, AZURE), opacity=.82,
                        line=dict(width=1, color="white")),
            customdata=s[["prog", "adm"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Punto de corte: %{x:,.0f}"
                          "<br>% Ingreso: %{y:.1f}%<br>Admitidos: %{customdata[1]:,.0f}<extra>" + cl + "</extra>",
        )
    fig.update_layout(
        height=520, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=SLATE, size=11),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)),
        xaxis=dict(title="Avg. punto de corte (Ceneval)", showgrid=True, gridcolor="rgba(36,66,105,.08)", zeroline=False),
        yaxis=dict(title="% de Ingreso", showgrid=True, gridcolor="rgba(36,66,105,.08)",
                   zeroline=False, ticksuffix="%", range=[-3, 108]),
    )
    return fig


def quadrant(pdf, cen: float, pm: float, corte_cen: float, min_pm: float) -> go.Figure:
    """Dispersión Ceneval×Pensamiento de un programa, con 4 cuadrantes y el folio resaltado."""
    fig = go.Figure()
    fig.add_scatter(x=pdf[COL_CEN], y=pdf[COL_PM], mode="markers",
                    marker=dict(color="rgba(36,66,105,.16)", size=7), hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=[cen], y=[pm], mode="markers", showlegend=False,
                    marker=dict(color=AMBER, size=18, line=dict(width=2.5, color="white")),
                    hovertemplate=f"Ceneval {cen:.0f}<br>P. Mat. {pm:.0f}<extra>Tu folio</extra>")
    fig.add_vline(x=corte_cen, line=dict(dash="dash", color=SLATE, width=1.4),
                  annotation_text=f"Punto de Corte Ceneval: {corte_cen:.0f}",
                  annotation_position="top", annotation_font=dict(size=10, family=FONT, color=SLATE))
    fig.add_hline(y=min_pm, line=dict(dash="dash", color=SLATE, width=1.4),
                  annotation_text=f"P. Mat. Mínimo Admitido: {min_pm:.0f}",
                  annotation_position="bottom right", annotation_font=dict(size=10, family=FONT, color=SLATE))
    for xa, ya, txt in [(.985, .96, "1"), (.985, .04, "2"), (.015, .96, "3"), (.015, .04, "4")]:
        fig.add_annotation(xref="paper", yref="paper", x=xa, y=ya, text=f"<b>{txt}</b>",
                           showarrow=False, font=dict(size=22, family=FONT, color="rgba(36,66,105,.28)"))
    fig.update_layout(
        height=520, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=SLATE, size=11),
        xaxis=dict(title="Índice Ceneval", showgrid=True, gridcolor="rgba(36,66,105,.08)", zeroline=False),
        yaxis=dict(title="Índice Pensamiento Matemático", showgrid=True,
                   gridcolor="rgba(36,66,105,.08)", zeroline=False),
    )
    return fig
