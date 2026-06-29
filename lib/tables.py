"""Tabla de varianza estilo Zebra BI / IBCS (Año Ant. vs Actual, ΔPY abs y %)."""
from __future__ import annotations

import math
import pandas as pd

from .data import COL_CICLO
from . import metrics as M
from .theme import NAVY, DANGER, SLATE


def build_rows(scope: pd.DataFrame, key: str, ciclo: int, prev: int | None) -> list[dict]:
    """Filas jerárquicas: subtotal por campus + sus programas + Total general."""
    cur = scope[scope[COL_CICLO] == ciclo]
    pre = scope[scope[COL_CICLO] == prev] if prev else cur.iloc[0:0]
    rows: list[dict] = []

    # campus ordenados por valor actual (desc)
    camp_order = (cur.groupby("campus").apply(lambda g: M.compute(g, key))
                  .sort_values(ascending=False).index.tolist())
    for campus in camp_order:
        cc, pc = cur[cur.campus == campus], pre[pre.campus == campus]
        rows.append({"level": "campus", "label": campus,
                     "ant": M.compute(pc, key) if len(pc) else math.nan,
                     "act": M.compute(cc, key)})
        progs = [(prog, M.compute(pc[pc.programa == prog], key) if len(pc) else math.nan,
                  M.compute(cc[cc.programa == prog], key))
                 for prog in cc.programa.unique()]
        for prog, b, a in sorted(progs, key=lambda x: -(x[2] if x[2] == x[2] else -1)):
            rows.append({"level": "prog", "label": prog, "ant": b, "act": a})

    rows.append({"level": "total", "label": "Total",
                 "ant": M.compute(pre, key) if prev else math.nan,
                 "act": M.compute(cur, key)})

    for r in rows:
        r["dpy"] = (r["act"] - r["ant"]) if (r["ant"] == r["ant"]) else math.nan
        r["dpy_pct"] = (r["dpy"] / r["ant"] * 100) if (r["ant"] not in (0, math.nan) and r["ant"] == r["ant"] and r["ant"] != 0) else math.nan
    return rows


def _dbar(val: float, maxabs: float) -> str:
    """Barra divergente centrada en cero: positivo→derecha (navy), negativo→izquierda (rojo)."""
    if maxabs == 0 or val != val:
        return '<div class="dbar"></div>'
    w = min(abs(val) / maxabs * 46, 46)
    if val >= 0:
        seg = f'<span style="left:50%;width:{w:.1f}%;background:{NAVY}"></span>'
    else:
        seg = f'<span style="right:50%;width:{w:.1f}%;background:{DANGER}"></span>'
    return f'<div class="dbar">{seg}</div>'


def _num(val: float, fmt: str) -> str:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "—"
    return fmt.format(val)


def variance_table_html(rows: list[dict], key: str) -> str:
    dfmt = M.METRICS[key]["dfmt"]
    vfmt = M.METRICS[key]["fmt"]
    max_dpy = max((abs(r["dpy"]) for r in rows if r["dpy"] == r["dpy"]), default=1)
    max_pct = max((abs(r["dpy_pct"]) for r in rows if r["dpy_pct"] == r["dpy_pct"]), default=1)

    body = []
    for r in rows:
        cls = {"campus": "vt-campus", "total": "vt-total", "prog": "vt-prog"}[r["level"]]
        dcol = NAVY if (r["dpy"] == r["dpy"] and r["dpy"] >= 0) else DANGER
        pcol = NAVY if (r["dpy_pct"] == r["dpy_pct"] and r["dpy_pct"] >= 0) else DANGER
        dtxt = _num(r["dpy"], dfmt)
        ptxt = (f'{r["dpy_pct"]:+.1f}%' if r["dpy_pct"] == r["dpy_pct"] else "—")
        body.append(
            f'<tr class="{cls}">'
            f'<td class="lab">{r["label"]}</td>'
            f'<td class="num dim">{_num(r["ant"], vfmt)}</td>'
            f'<td class="num">{_num(r["act"], vfmt)}</td>'
            f'<td class="barc">{_dbar(r["dpy"], max_dpy)}<span class="bv" style="color:{dcol}">{dtxt}</span></td>'
            f'<td class="barc">{_dbar(r["dpy_pct"], max_pct)}<span class="bv" style="color:{pcol}">{ptxt}</span></td>'
            f'</tr>'
        )
    return (
        '<div class="vt-wrap"><table class="vt">'
        '<thead><tr>'
        '<th class="lab">Programa / Campus</th><th>Año Ant.</th><th>Año Actual</th>'
        '<th>&Delta;PY</th><th>&Delta;PY %</th>'
        '</tr></thead><tbody>'
        + "".join(body) +
        '</tbody></table></div>'
    )


# Columnas activables de la tabla de clústers: key -> (label, fn, fmt)
CLUSTER_COLS = {
    "corte": ("Avg punto de corte", M.m_punto_corte, "{:,.0f}"),
    "pct":   ("Avg % Ingreso",      M.m_pct,         "{:.1f}%"),
    "sust":  ("Sustentantes Total", M.m_sustentantes, "{:,.0f}"),
    "adm":   ("Admitidos Total",    M.m_admitidos,   "{:,.0f}"),
    "cen":   ("Avg Ceneval Adm.",   M.m_avg_cen,     "{:,.0f}"),
    "minpm": ("Mín. Pensamiento Adm.", M.m_min_pm,   "{:,.0f}"),
}


def cluster_table_html(d2026: pd.DataFrame, col_keys: list[str], expand: bool = True) -> str:
    """Tabla jerárquica Clúster → Programa con columnas activables; subtotales y total recalculados.

    Si `expand` es False, solo se muestran los clústers (colapsados) + el Total.
    """
    clusters = sorted(d2026["cluster"].dropna().unique())
    head = '<th class="lab">Clúster / Programa</th><th>Núm. Lic.</th>' + \
        "".join(f'<th>{CLUSTER_COLS[k][0]}</th>' for k in col_keys)

    def cells(sub: pd.DataFrame) -> str:
        return "".join(f'<td class="num">{_num(CLUSTER_COLS[k][1](sub), CLUSTER_COLS[k][2])}</td>'
                       for k in col_keys)

    body = []
    caret = "▾" if expand else "▸"
    for cl in clusters:
        cc = d2026[d2026["cluster"] == cl]
        body.append(f'<tr class="vt-campus"><td class="lab">{caret} {cl}</td>'
                    f'<td class="num">{cc["programa"].nunique()}</td>{cells(cc)}</tr>')
        if expand:
            progs = sorted(cc["programa"].unique(),
                           key=lambda p: -(M.m_pct(cc[cc["programa"] == p]) or -1))
            for prog in progs:
                pg = cc[cc["programa"] == prog]
                body.append(f'<tr class="vt-prog"><td class="lab">{prog}</td>'
                            f'<td class="num">1</td>{cells(pg)}</tr>')
    body.append(f'<tr class="vt-total"><td class="lab">Total</td>'
                f'<td class="num">{d2026["programa"].nunique()}</td>{cells(d2026)}</tr>')

    return (f'<div class="vt-wrap"><table class="vt"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
