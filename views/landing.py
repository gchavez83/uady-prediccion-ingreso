"""Portada Synapse — acceso al Modelo Predictivo o al Dashboard Analítico."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO, COL_EST, COL_ABV, ADM
from lib.theme import synapse_mark, INK, AZURE, AMBER, IVORY

df = load_fact()
registros = len(df)
cs = sorted(int(c) for c in df[COL_CICLO].unique())
n_prog = df[COL_ABV].nunique()
n_campus = df["campus"].nunique()
admitidos = int((df[COL_EST] == ADM).sum())

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"]{{background:{INK} !important;
  background-image:
    radial-gradient(680px 380px at 88% -6%, rgba(243,154,30,.16), transparent 62%),
    radial-gradient(720px 520px at 100% 112%, rgba(42,111,219,.12), transparent 60%) !important;}}
.stApp,[data-testid="stHeader"]{{background:{INK} !important;}}
.syn-hero{{display:grid;grid-template-columns:1.2fr .8fr;gap:20px;align-items:center;
  padding:30px 0 8px;}}
.syn-hero .eb{{font-family:var(--mono);font-size:.78rem;letter-spacing:.22em;text-transform:uppercase;
  color:{AMBER};margin-bottom:18px;}}
.syn-hero h1{{font-family:var(--serif);font-size:clamp(38px,6vw,70px);line-height:1.02;color:#fff;margin:0;}}
.syn-hero h1 em{{font-style:italic;color:{AMBER};}}
.syn-hero p{{color:#93a1bc;font-size:1.05rem;max-width:46ch;margin:18px 0 0;}}
.syn-mk{{justify-self:center;width:min(290px,80%);opacity:.96;}}
@media(max-width:820px){{
  .syn-hero{{grid-template-columns:1fr;gap:4px;}}
  .syn-mk{{display:none;}}
  .syn-hero h1{{font-size:2.2rem;}}
}}
.syn-stats{{display:flex;flex-wrap:wrap;border:1px solid rgba(191,198,210,.16);border-radius:14px;
  background:rgba(255,255,255,.025);margin:26px 0 6px;overflow:hidden;}}
.syn-stats .s{{flex:1 1 0;min-width:120px;padding:14px 18px;border-right:1px solid rgba(191,198,210,.16);}}
.syn-stats .s:last-child{{border-right:none;}}
.syn-stats .n{{font-family:var(--serif);font-size:1.8rem;color:#fff;}}
.syn-stats .l{{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:#93a1bc;margin-top:6px;}}
.syn-card{{display:block;background:linear-gradient(180deg,#0E1D38,{INK});
  border:1px solid rgba(191,198,210,.16);border-radius:18px;padding:24px;text-decoration:none;
  position:relative;overflow:hidden;transition:transform .2s,border-color .2s;height:100%;}}
.syn-card:hover{{transform:translateY(-4px);}}
.syn-card::before{{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ac);}}
.syn-card .nd{{font-family:var(--mono);font-size:.65rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ac);}}
.syn-card h2{{font-family:var(--serif);font-size:1.7rem;color:#fff;margin:10px 0 6px;}}
.syn-card p{{color:#93a1bc;font-size:.92rem;margin:0 0 14px;}}
.syn-card .go{{font-weight:600;color:#fff;font-size:.92rem;}}
.syn-card .go b{{color:var(--ac);}}
.syn-ia{{--ac:{AZURE};}} .syn-bi{{--ac:{AMBER};}}
[data-testid="stSidebar"]{{background:{INK};}}
</style>

<div class="syn-hero">
  <div>
    <div class="eb">Analítica de Ingreso · UADY</div>
    <h1>Datos de admisión,<br><em>convertidos en decisiones.</em></h1>
    <p>Resultados públicos de admisión a licenciatura de la UADY, {cs[0]}–{cs[-1]}.
       Predice tu ingreso o explora la historia completa.</p>
  </div>
  <div class="syn-mk">{synapse_mark('100%', on_dark=True)}</div>
</div>

<div class="syn-stats">
  <div class="s"><div class="n">{registros:,}</div><div class="l">Registros</div></div>
  <div class="s"><div class="n">{len(cs)}</div><div class="l">Ciclos · {cs[0]}–{cs[-1]}</div></div>
  <div class="s"><div class="n">{n_prog}</div><div class="l">Programas</div></div>
  <div class="s"><div class="n">{n_campus}</div><div class="l">Campus</div></div>
  <div class="s"><div class="n">{admitidos:,}</div><div class="l">Admitidos históricos</div></div>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="medium")
with c1:
    st.markdown(f"""<a class="syn-card syn-ia" href="modelo" target="_self">
      <div class="nd">Nodo · IA / ML</div>
      <h2>Modelo Predictivo</h2>
      <p>Estima tu probabilidad de admisión y tu posición con modelos de ML calibrados,
         y simula tu resultado en otras licenciaturas.</p>
      <div class="go">Abrir modelo <b>→</b></div></a>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<a class="syn-card syn-bi" href="resumen" target="_self">
      <div class="nd">Nodo · Business Intelligence</div>
      <h2>Dashboard Analítico</h2>
      <p>Explora sustentantes, admitidos, puntos de corte, tendencias y clústers de
         programas a lo largo de cinco ciclos, por campus y licenciatura.</p>
      <div class="go">Abrir dashboard <b>→</b></div></a>""", unsafe_allow_html=True)
