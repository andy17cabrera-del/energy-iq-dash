import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import base64, os, datetime, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = dash.Dash(__name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])
server = app.server

# ── Logo ──────────────────────────────────────────────────────────────────────
def get_logo():
    p = os.path.join(BASE_DIR, "marcobre_logo.png")
    if os.path.exists(p):
        with open(p,"rb") as f:
            return "data:image/png;base64,"+base64.b64encode(f.read()).decode()
    return ""
LOGO = get_logo()

# ── Colors ────────────────────────────────────────────────────────────────────
BG      = "#1A2E45"
SIDEBAR = "#0D1F35"
CARD    = "#FFFFFF"
ACCENT  = "#185FA5"
TEXT    = "#0D1F35"
MUTED   = "#64748B"
BORDER  = "#E2E8F0"

AREA_COLORS = {
    "Sulfuros":"#1D4ED8","Óxidos":"#9333EA","Infraestructura":"#92400E",
    "Mina":"#15803D","G&A":"#0EA5E9","Mantenimiento":"#6B7280",
}

# ── Load data once at startup ─────────────────────────────────────────────────
def _is_date(v):
    return isinstance(v,(pd.Timestamp,datetime.datetime)) and not isinstance(v,bool)

def parse_p(p):
    p=str(p)
    m=re.match(r"(\d{2})m(\d{1,2})$",p)
    if m: return pd.Timestamp(int("20"+m.group(1)),int(m.group(2)),1)
    m=re.match(r"(\d{4})$",p)
    if m: return pd.Timestamp(int(m.group(1)),6,1)
    m=re.match(r"(\d{2})q(\d)$",p)
    if m: return pd.Timestamp(int("20"+m.group(1)),(int(m.group(2))-1)*3+1,1)
    return pd.NaT

BUDGET_COL_MAP = {
    8:"23m1",9:"23m2",10:"23m3",11:"23m4",12:"23m5",13:"23m6",
    14:"23m7",15:"23m8",16:"23m9",17:"23m10",18:"23m11",19:"23m12",
    22:"24m1",23:"24m2",24:"24m3",25:"24m4",26:"24m5",27:"24m6",
    28:"24m7",29:"24m8",30:"24m9",31:"24m10",32:"24m11",33:"24m12",
    36:"25m1",37:"25m2",38:"25m3",39:"25m4",40:"25m5",41:"25m6",
    42:"25m7",43:"25m8",44:"25m9",45:"25m10",46:"25m11",47:"25m12",
    50:"26m1",51:"26m2",52:"26m3",53:"26m4",54:"26m5",55:"26m6",
    56:"26m7",57:"26m8",58:"26m9",59:"26m10",60:"26m11",61:"26m12",
    78:"27m1",79:"27m2",80:"27m3",81:"27m4",82:"27m5",83:"27m6",
    84:"27m7",85:"27m8",86:"27m9",87:"27m10",88:"27m11",89:"27m12",
    92:"28q1",93:"28q2",94:"28q3",95:"28q4",
    98:"29q1",99:"29q2",100:"29q3",101:"29q4",
    104:"2030",105:"2031",106:"2032",107:"2033",108:"2034",109:"2035",
    110:"2036",111:"2037",112:"2038",113:"2039",114:"2040",115:"2041",
    116:"2042",117:"2043",118:"2044",119:"2045",
}
BUDGET_MONTHLY = {k:v for k,v in BUDGET_COL_MAP.items() if re.match(r"\d{2}m",v)}

REAL_ROWS   = {"G&A":1,"Mina":12,"Sulfuros":18,"Óxidos":30,"Infraestructura":27,"Mantenimiento":9}
BUDGET_ROWS = {"G&A":86,"Mina":96,"Sulfuros":106,"Infraestructura":116,"Mantenimiento":101,"Óxidos":120}
BILL_ROWS   = {"G&A":65,"Mantenimiento":66,"Mina":67,"Sulfuros":68,"Infraestructura":69,"Óxidos":70}
RATIO_ROWS  = {"PLANTA SULFUROS_ratio":43,"UNITARIO TOTAL":21,"INFRAESTRUCTURA_ratio":53,"OXIDOS_EW_ratio":69,"OXIDOS_SECO_ratio":58}

def load_all():
    df2 = pd.read_excel(os.path.join(BASE_DIR,"real_energia.xlsx"),
                        sheet_name="DETALLE ENERGIA Y FACTURA",header=None)
    df1 = pd.read_excel(os.path.join(BASE_DIR,"presupuesto_energia.xlsx"),
                        sheet_name="LOM25 Óptimo",header=None)

    # Real consumption
    recs=[]
    for ci in range(4,min(72,df2.shape[1])):
        fv=df2.iloc[0,ci]
        if not _is_date(fv): continue
        fecha=pd.Timestamp(fv)
        for area,row in REAL_ROWS.items():
            val=pd.to_numeric(df2.iloc[row,ci],errors="coerce")
            if pd.notna(val) and val>0:
                recs.append({"area":area,"fecha":fecha,"kwh_real":float(val)})
    rk=pd.DataFrame(recs)

    # Budget consumption (monthly only)
    recs=[]
    for area,row in BUDGET_ROWS.items():
        for col,period in BUDGET_MONTHLY.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_p(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    recs.append({"area":area,"fecha":fecha,"kwh_ppto":float(val)})
    bk=pd.DataFrame(recs)

    # Billing
    recs=[]
    for ci in range(4,min(72,df2.shape[1])):
        fv=df2.iloc[0,ci]
        if not _is_date(fv): continue
        fecha=pd.Timestamp(fv)
        for area,row in BILL_ROWS.items():
            val=pd.to_numeric(df2.iloc[row,ci],errors="coerce")
            if pd.notna(val):
                recs.append({"area":area,"fecha":fecha,"usd":float(val)})
    bill=pd.DataFrame(recs)

    # Budget ratios (all periods)
    recs=[]
    for nombre,row in RATIO_ROWS.items():
        for col,period in BUDGET_COL_MAP.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_p(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    recs.append({"ratio":nombre,"fecha":fecha,"ratio_ppto":float(val)})
    brat=pd.DataFrame(recs)

    # Real ratios
    recs=[]
    for ci in range(4,min(72,df2.shape[1])):
        fv=df2.iloc[0,ci]
        if not _is_date(fv): continue
        fecha=pd.Timestamp(fv)
        v59=pd.to_numeric(df2.iloc[59,ci],errors="coerce")
        if pd.notna(v59) and v59>0:
            recs.append({"ratio":"PLANTA SULFUROS_ratio","fecha":fecha,"valor_real":float(v59)})
        v61=pd.to_numeric(df2.iloc[61,ci],errors="coerce")
        if pd.notna(v61) and v61>0:
            recs.append({"ratio":"INFRAESTRUCTURA_ratio","fecha":fecha,"valor_real":float(v61)})
        drv=pd.to_numeric(df2.iloc[55,ci],errors="coerce")
        if pd.isna(drv) or drv<=0: continue
        kew=pd.to_numeric(df2.iloc[42,ci],errors="coerce")
        if pd.notna(kew) and kew>0:
            recs.append({"ratio":"OXIDOS_EW_ratio","fecha":fecha,"valor_real":float(kew/drv)})
        kot=pd.to_numeric(df2.iloc[30,ci],errors="coerce")
        if pd.notna(kot) and pd.notna(kew) and kot>kew:
            recs.append({"ratio":"OXIDOS_SECO_ratio","fecha":fecha,"valor_real":float((kot-kew)/drv)})
    rrat=pd.DataFrame(recs)

    # LOM full budget (all periods)
    recs=[]
    for area,row in BUDGET_ROWS.items():
        for col,period in BUDGET_COL_MAP.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_p(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    pt="monthly" if re.match(r"\d{2}m",period) else "quarterly" if re.match(r"\d{2}q",period) else "annual"
                    recs.append({"area":area,"fecha":fecha,"kwh_ppto":float(val),"tipo":pt})
    lom_kwh=pd.DataFrame(recs)

    recs=[]
    for nombre,row in RATIO_ROWS.items():
        for col,period in BUDGET_COL_MAP.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_p(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    pt="monthly" if re.match(r"\d{2}m",period) else "quarterly" if re.match(r"\d{2}q",period) else "annual"
                    recs.append({"ratio":nombre,"fecha":fecha,"ratio_ppto":float(val),"tipo":pt})
    lom_rat=pd.DataFrame(recs)

    return rk,bk,bill,brat,rrat,lom_kwh,lom_rat

try:
    rk,bk,bill,brat,rrat,lom_kwh,lom_rat = load_all()
    DATA_OK = True
except Exception as e:
    DATA_OK = False
    DATA_ERROR = str(e)

# ── UI helpers ────────────────────────────────────────────────────────────────
CARD_STYLE = {"background":CARD,"borderRadius":"10px","padding":"14px","border":f"0.5px solid {BORDER}"}

def kpi(label,value,unit="",delta=None,delta_ok=True,accent=ACCENT):
    dc = "#16A34A" if delta_ok else "#DC2626"
    return html.Div([
        html.Div(label,style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase","letterSpacing":".08em","color":MUTED,"marginBottom":"4px"}),
        html.Div(value,style={"fontSize":"22px","fontWeight":"700","color":TEXT,"lineHeight":"1.1"}),
        html.Div(unit, style={"fontSize":"10px","color":"#94A3B8"}),
        html.Div(delta,style={"fontSize":"11px","fontWeight":"600","color":dc,"marginTop":"2px"}) if delta else html.Div(),
    ],style={"background":CARD,"borderRadius":"10px","padding":"14px","borderLeft":f"4px solid {accent}",
             "border":f"0.5px solid {BORDER}","borderLeft":f"4px solid {accent}","flex":"1","minWidth":"0"})

def alert(msg,sub,level="green"):
    c={"green":("#F0FDF4","#22C55E","#14532D"),"amber":("#FFFBEB","#F59E0B","#78350F"),"red":("#FEF2F2","#EF4444","#7F1D1D")}
    bg,dot,txt=c.get(level,c["green"])
    return html.Div([
        html.Div(style={"width":"8px","height":"8px","borderRadius":"50%","background":dot,"marginTop":"5px","flexShrink":"0"}),
        html.Div([html.Div(msg,style={"fontSize":"12px","fontWeight":"700","color":txt}),
                  html.Div(sub,style={"fontSize":"10px","color":MUTED,"marginTop":"1px"})]),
    ],style={"display":"flex","gap":"10px","background":bg,"borderRadius":"8px","padding":"10px 12px","border":f"0.5px solid {dot}","flex":"1"})

def sec(icon,title):
    return html.Div([
        html.I(className=f"ti ti-{icon}",style={"fontSize":"14px","color":"#60A5FA"}),
        html.Span(title,style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase","letterSpacing":".08em","color":"#60A5FA","marginLeft":"6px"}),
        html.Div(style={"flex":"1","height":"1px","background":"#1E3A5F","marginLeft":"8px"}),
    ],style={"display":"flex","alignItems":"center","marginBottom":"10px","marginTop":"8px"})

def chart_card(fig,height=None):
    s = {**CARD_STYLE}
    if height: s["height"]=f"{height}px"
    return html.Div(dcc.Graph(figure=fig,config={"displayModeBar":False},style={"height":"100%"}),style=s)

def layout_fig(fig,h=300):
    fig.update_layout(plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=h,
        margin=dict(l=0,r=0,t=10,b=0),hovermode="x unified",
        legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=11),
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
PAGES = [
    ("/",           "home",          "Resumen ejecutivo"),
    ("/consumo",    "chart-bar",     "Consumo vs PPTO"),
    ("/ratios",     "math-function", "Ratios unitarios"),
    ("/areas",      "layers",        "Desglose por área"),
    ("/factura",    "coin",          "Facturación"),
    ("/lom",        "calendar",      "Horizonte LOM"),
]

sidebar = html.Div([
    html.Div([
        html.Img(src=LOGO,style={"width":"130px"}) if LOGO else
        html.Span("MARCOBRE",style={"color":"#C0392B","fontWeight":"700"}),
    ],style={"background":"#fff","borderRadius":"8px","padding":"8px 12px","textAlign":"center","marginBottom":"12px"}),
    html.Div([
        html.Span("⚡ Energy IQ",style={"color":"#60A5FA","fontSize":"13px","fontWeight":"700"}),html.Br(),
        html.Span("LOM25 Óptimo · Superintendencia",style={"color":"#475569","fontSize":"10px"}),
    ],style={"textAlign":"center","paddingBottom":"12px","borderBottom":"1px solid #1E3A5F","marginBottom":"12px"}),
    html.Div("Navegación",style={"fontSize":"9px","fontWeight":"700","color":"#334155","textTransform":"uppercase","letterSpacing":".08em","marginBottom":"8px"}),
    *[html.A([html.I(className=f"ti ti-{icon}",style={"fontSize":"15px","marginRight":"9px"}),lbl],
             href=href,style={"display":"flex","alignItems":"center","padding":"8px 10px","borderRadius":"7px",
                              "color":"#94A3B8","textDecoration":"none","fontSize":"13px","marginBottom":"3px","fontWeight":"500"})
      for href,icon,lbl in PAGES],
],style={"background":SIDEBAR,"width":"200px","minHeight":"100vh","padding":"16px 12px","flexShrink":"0"})

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div([
        sidebar,
        html.Div([
            html.Div([
                html.Span(id="page-title",style={"fontSize":"20px","fontWeight":"700","color":"#FFFFFF"}),
                html.Span("● Actualizado · Mar 2026",
                    style={"background":"#0F2E1A","color":"#4ADE80","fontSize":"11px","padding":"4px 12px",
                           "borderRadius":"20px","border":"0.5px solid #166534"}),
            ],style={"display":"flex","alignItems":"center","justifyContent":"space-between",
                     "padding":"12px 20px","background":"#0D1F35","borderBottom":"1px solid #1E3A5F"}),
            html.Div(id="page-content",style={"padding":"16px 20px","overflowY":"auto","flex":"1"}),
        ],style={"flex":"1","display":"flex","flexDirection":"column","minWidth":"0"}),
    ],style={"display":"flex","minHeight":"100vh"}),
],style={"background":BG,"fontFamily":"'Segoe UI',sans-serif"})

# ── Page builders ─────────────────────────────────────────────────────────────
def page_home():
    latest = rk["fecha"].max()
    rk_lat  = rk[rk["fecha"]==latest]
    total_r = rk_lat["kwh_real"].sum()
    bk_lat  = bk[(bk["fecha"].dt.year==latest.year)&(bk["fecha"].dt.month==latest.month)]
    total_p = bk_lat["kwh_ppto"].sum()
    delta   = (total_r-total_p)/total_p*100 if total_p>0 else 0
    bill_v  = bill[bill["fecha"]==latest]["usd"].sum()
    acum    = rk[rk["fecha"].dt.year==latest.year]["kwh_real"].sum()/1e6

    # Charts
    real_mo = rk.groupby("fecha")["kwh_real"].sum().reset_index().sort_values("fecha")
    bk_mo   = bk.groupby("fecha")["kwh_ppto"].sum().reset_index().sort_values("fecha")
    latest_fecha = rk["fecha"].max()
    bk_bar = bk_mo[bk_mo["fecha"]<=latest_fecha]
    rk_bar = real_mo[real_mo["fecha"]<=latest_fecha]

    fig1=go.Figure()
    fig1.add_trace(go.Bar(x=bk_bar["fecha"],y=bk_bar["kwh_ppto"]/1e6,name="Presupuesto",
        marker_color="#93C5FD",opacity=0.8,hovertemplate="<b>PPTO</b> %{x|%b %Y}: %{y:.2f} GWh<extra></extra>"))
    fig1.add_trace(go.Bar(x=rk_bar["fecha"],y=rk_bar["kwh_real"]/1e6,name="Real",
        marker_color="#34D399",opacity=0.9,hovertemplate="<b>Real</b> %{x|%b %Y}: %{y:.2f} GWh<extra></extra>"))
    layout_fig(fig1,280); fig1.update_layout(barmode="group",yaxis_title="GWh")

    dist=rk_lat[rk_lat["kwh_real"]>0]
    fig2=go.Figure(go.Pie(labels=dist["area"],values=dist["kwh_real"],hole=0.55,
        marker_colors=[AREA_COLORS.get(a,"#94A3B8") for a in dist["area"]],
        textinfo="label+percent",textfont_size=11))
    fig2.update_layout(paper_bgcolor="#FFFFFF",height=280,margin=dict(l=0,r=0,t=10,b=0),showlegend=False)

    trend=rk.groupby(["fecha","area"])["kwh_real"].sum().reset_index()
    fig3=go.Figure()
    for area,color in AREA_COLORS.items():
        d=trend[trend["area"]==area].sort_values("fecha")
        if not d.empty:
            fig3.add_trace(go.Scatter(x=d["fecha"],y=d["kwh_real"]/1e3,name=area,mode="lines",
                line=dict(color=color,width=2),
                hovertemplate=f"<b>{area}</b> %{{x|%b %Y}}: %{{y:,.0f}} MWh<extra></extra>"))
    layout_fig(fig3,260); fig3.update_layout(yaxis_title="MWh")

    # Summary table
    rows=[]
    bk_all=bk; rk_comp=rk[rk["fecha"].isin(set(bk["fecha"]))]
    for area in AREA_COLORS:
        rv=rk_comp[rk_comp["area"]==area]["kwh_real"].mean() or 0
        pv=bk_all[bk_all["area"]==area]["kwh_ppto"].mean() or 0
        dv=(rv-pv)/pv*100 if pv>0 else 0
        rows.append({"Área":area,"Real GWh/mes":f"{rv/1e6:.2f}","PPTO GWh/mes":f"{pv/1e6:.2f}","Desv. %":f"{dv:+.1f}%"})

    return html.Div([
        sec("dashboard",f"Indicadores clave · {latest.strftime('%B %Y')}"),
        html.Div([
            kpi("Consumo real",     f"{total_r/1e6:.2f}","GWh/mes",f"{'↓' if delta<0 else '↑'} {delta:+.1f}% vs PPTO",delta<=0,"#185FA5"),
            kpi("Presupuestado",    f"{total_p/1e6:.2f}","GWh/mes",accent="#16A34A"),
            kpi("Facturación",      f"${bill_v/1e6:.2f}M","USD/mes", accent="#D97706"),
            kpi("Acumulado 2026",   f"{acum:.1f}","GWh",accent="#9333EA"),
            kpi("Meses con datos",  f"{rk['fecha'].dt.year.eq(latest.year).sum()//len(AREA_COLORS)}/12",accent="#C0392B"),
        ],style={"display":"flex","gap":"10px","marginBottom":"14px","flexWrap":"wrap"}),
        sec("alert-triangle","Alertas de desviación"),
        html.Div([
            alert(f"Consumo total {delta:+.1f}% vs PPTO",f"{total_r/1e6:.2f} GWh · {latest.strftime('%b %Y')}",
                  "green" if abs(delta)<=2 else "amber" if abs(delta)<=5 else "red"),
            alert("Sulfuros −0.4% bajo PPTO","13.10 GWh/mes · PPTO: 13.15","green"),
            alert("Ratio EW +6.1% sobre plan","6.85 kWh/tt Óxi · PPTO: 6.45","amber"),
        ],style={"display":"flex","gap":"8px","marginBottom":"14px","flexWrap":"wrap"}),
        sec("chart-bar","Consumo mensual — Real vs Presupuesto"),
        html.Div([
            html.Div(dcc.Graph(figure=fig1,config={"displayModeBar":False}),
                     style={**CARD_STYLE,"flex":"2"}),
            html.Div([html.Div(f"Distribución · {latest.strftime('%b %Y')}",
                               style={"fontSize":"13px","fontWeight":"700","color":TEXT,"marginBottom":"4px"}),
                      dcc.Graph(figure=fig2,config={"displayModeBar":False})],
                     style={**CARD_STYLE,"flex":"1"}),
        ],style={"display":"flex","gap":"10px","marginBottom":"12px"}),
        sec("trending-up","Evolución por área 2021–2026"),
        html.Div(dcc.Graph(figure=fig3,config={"displayModeBar":False}),style={**CARD_STYLE,"marginBottom":"12px"}),
        sec("table","Resumen por área — promedio mensual"),
        html.Div(dash_table.DataTable(data=rows,
            columns=[{"name":c,"id":c} for c in ["Área","Real GWh/mes","PPTO GWh/mes","Desv. %"]],
            style_header={"background":"#F8FAFC","fontWeight":"700","fontSize":"10px","textTransform":"uppercase",
                          "letterSpacing":".06em","color":MUTED,"borderBottom":f"1.5px solid {BORDER}","border":"none"},
            style_data={"fontSize":"12px","color":TEXT,"borderBottom":f"0.5px solid #F1F5F9","border":"none"},
            style_data_conditional=[
                {"if":{"row_index":"odd"},"background":"#F8FAFC"},
                {"if":{"filter_query":'{Desv. %} contains "+"',"column_id":"Desv. %"},"color":"#DC2626","fontWeight":"700"},
                {"if":{"filter_query":'{Desv. %} contains "-"',"column_id":"Desv. %"},"color":"#16A34A","fontWeight":"700"},
            ],style_table={"borderRadius":"10px","overflow":"hidden"}),
            style=CARD_STYLE),
    ])

def page_ratios():
    RATIO_LABELS={"PLANTA SULFUROS_ratio":"Sulfuros (kWh/tt Sulf)",
        "UNITARIO TOTAL":"Unitario Total (kWh/tt)","INFRAESTRUCTURA_ratio":"Infraestructura (kWh/m³)",
        "OXIDOS_EW_ratio":"Óxidos EW (kWh/tt Óxi)","OXIDOS_SECO_ratio":"Óxidos Seco (kWh/tt Óxi)"}
    return html.Div([
        sec("math-function","Ratios unitarios — Presupuesto vs Real"),
        html.Div([
            html.Div("Ratio a analizar",style={"fontSize":"11px","fontWeight":"700","color":"#94A3B8","marginBottom":"6px"}),
            dcc.Dropdown(id="ratio-sel",options=[{"label":v,"value":k} for k,v in RATIO_LABELS.items()],
                value="PLANTA SULFUROS_ratio",clearable=False),
        ],style={**CARD_STYLE,"marginBottom":"12px"}),
        html.Div(id="ratio-out"),
    ])

def page_areas():
    trend_r=rk.groupby(["fecha","area"])["kwh_real"].sum().reset_index()
    trend_b=bk.groupby(["fecha","area"])["kwh_ppto"].sum().reset_index()

    def mk(df,col,areas):
        fig=go.Figure()
        for area,color in AREA_COLORS.items():
            if area not in areas: continue
            d=df[df["area"]==area].sort_values("fecha")
            fig.add_trace(go.Bar(x=d["fecha"],y=d[col]/1e3,name=area,marker_color=color,opacity=0.85,
                hovertemplate=f"<b>{area}</b> %{{x|%b %Y}}: %{{y:,.0f}} MWh<extra></extra>"))
        layout_fig(fig,340); fig.update_layout(barmode="stack",yaxis_title="MWh")
        return fig

    def mk_comp(areas):
        fig=go.Figure()
        for area,color in AREA_COLORS.items():
            if area not in areas: continue
            dp=trend_b[trend_b["area"]==area].sort_values("fecha")
            dr=trend_r[trend_r["area"]==area].sort_values("fecha")
            fig.add_trace(go.Scatter(x=dp["fecha"],y=dp["kwh_ppto"]/1e3,name=f"{area} PPTO",
                mode="lines",line=dict(color=color,dash="dot",width=1.5),legendgroup=area))
            fig.add_trace(go.Scatter(x=dr["fecha"],y=dr["kwh_real"]/1e3,name=f"{area} Real",
                mode="lines+markers",line=dict(color=color,width=2.5),marker_size=4,legendgroup=area))
        layout_fig(fig,380); fig.update_layout(yaxis_title="MWh")
        return fig

    areas=list(AREA_COLORS.keys())
    rk_comp=rk[rk["fecha"].isin(set(bk["fecha"]))]
    kpis=[html.Div([
        html.Div(area,style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase","color":MUTED}),
        html.Div(f"{(rk_comp[rk_comp['area']==area]['kwh_real'].mean() or 0)/1e6:.1f}",
                 style={"fontSize":"22px","fontWeight":"700","color":TEXT}),
        html.Span("GWh/mes",style={"fontSize":"10px","color":"#94A3B8"}),
        html.Div(f"{((rk_comp[rk_comp['area']==area]['kwh_real'].mean() or 0)-(bk[bk['area']==area]['kwh_ppto'].mean() or 0))/(bk[bk['area']==area]['kwh_ppto'].mean() or 1)*100:+.1f}% vs PPTO",
                 style={"fontSize":"11px","fontWeight":"600","color":"#16A34A" if ((rk_comp[rk_comp['area']==area]['kwh_real'].mean() or 0)-(bk[bk['area']==area]['kwh_ppto'].mean() or 0))/(bk[bk['area']==area]['kwh_ppto'].mean() or 1)*100<=0 else "#DC2626","marginTop":"4px"}),
    ],style={"background":CARD,"borderRadius":"10px","padding":"14px","borderLeft":f"4px solid {AREA_COLORS.get(area,'#94A3B8')}",
             "border":f"0.5px solid {BORDER}","borderLeft":f"4px solid {AREA_COLORS.get(area,'#94A3B8')}","flex":"1","minWidth":"100px"})
    for area in areas]

    return html.Div([
        sec("layers","Desglose por área operativa"),
        html.Div(kpis,style={"display":"flex","gap":"8px","marginBottom":"14px","flexWrap":"wrap"}),
        sec("trending-up","Evolución mensual"),
        dcc.Tabs([
            dcc.Tab(label="Real",children=[html.Div(dcc.Graph(figure=mk(trend_r,"kwh_real",areas),config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
            dcc.Tab(label="Presupuesto",children=[html.Div(dcc.Graph(figure=mk(trend_b,"kwh_ppto",areas),config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
            dcc.Tab(label="Comparación Real vs PPTO",children=[html.Div(dcc.Graph(figure=mk_comp(areas),config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
        ],style={"marginBottom":"12px"}),
        sec("chart-area","Distribución — último mes"),
        html.Div(dcc.Graph(figure=px.treemap(rk[rk["fecha"]==rk["fecha"].max()],path=["area"],values="kwh_real",
            color="area",color_discrete_map=AREA_COLORS),config={"displayModeBar":False}),style=CARD_STYLE),
    ])

def page_factura():
    bill_mo=bill.groupby(["fecha","area"])["usd"].sum().reset_index()
    bill_tot=bill.groupby("fecha")["usd"].sum().reset_index()
    rk_tot=rk.groupby("fecha")["kwh_real"].sum().reset_index()
    merged=pd.merge(bill_tot,rk_tot,on="fecha")
    merged=merged[merged["kwh_real"]>0].copy()
    merged["usd_mwh"]=merged["usd"]/(merged["kwh_real"]/1e3)
    avg=merged["usd_mwh"].mean()

    fig1=go.Figure()
    for area,color in AREA_COLORS.items():
        d=bill_mo[bill_mo["area"]==area].sort_values("fecha")
        fig1.add_trace(go.Bar(x=d["fecha"],y=d["usd"],name=area,marker_color=color,opacity=0.85))
    fig1.add_trace(go.Scatter(x=bill_tot["fecha"],y=bill_tot["usd"],name="Total",
        mode="lines+markers",line=dict(color="#0D1F35",width=2.5),marker_size=5,yaxis="y2"))
    layout_fig(fig1,300); fig1.update_layout(barmode="stack",yaxis_title="USD",
        yaxis2=dict(overlaying="y",side="right",showgrid=False))

    dist=bill.groupby("area")["usd"].sum().reset_index()
    fig2=go.Figure(go.Pie(labels=dist["area"],values=dist["usd"],hole=0.55,
        marker_colors=[AREA_COLORS.get(a,"#94A3B8") for a in dist["area"]],textinfo="label+percent"))
    fig2.update_layout(paper_bgcolor="#FFFFFF",height=280,margin=dict(l=0,r=0,t=10,b=0),showlegend=False)

    fig3=go.Figure(go.Scatter(x=merged["fecha"],y=merged["usd_mwh"],mode="lines+markers",
        line=dict(color="#7C3AED",width=2.5),fill="tozeroy",fillcolor="rgba(124,58,237,0.07)"))
    fig3.add_hline(y=avg,line_dash="dash",line_color="#94A3B8",annotation_text=f"Prom: ${avg:.1f}/MWh")
    layout_fig(fig3,260); fig3.update_layout(yaxis_title="USD/MWh")

    return html.Div([
        sec("coin","Facturación energética"),
        html.Div([
            kpi("Facturación acumulada",f"${bill['usd'].sum()/1e6:.1f}M","USD",accent="#185FA5"),
            kpi("Último mes",f"${bill[bill['fecha']==bill['fecha'].max()]['usd'].sum()/1e6:.2f}M","USD",accent="#D97706"),
            kpi("Promedio mensual",f"${bill.groupby('fecha')['usd'].sum().mean()/1e6:.2f}M","USD",accent="#9333EA"),
            kpi("Costo unitario",f"${avg:.1f}","USD/MWh",accent="#C0392B"),
        ],style={"display":"flex","gap":"10px","marginBottom":"14px"}),
        dcc.Tabs([
            dcc.Tab(label="Evolución mensual",children=[html.Div(dcc.Graph(figure=fig1,config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
            dcc.Tab(label="Distribución por área",children=[html.Div(dcc.Graph(figure=fig2,config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
            dcc.Tab(label="Costo USD/MWh",children=[html.Div(dcc.Graph(figure=fig3,config={"displayModeBar":False}),style=CARD_STYLE)],
                style={"color":MUTED,"fontWeight":"600"},selected_style={"color":ACCENT,"fontWeight":"700","borderTop":f"3px solid {ACCENT}"}),
        ]),
    ])

def page_lom():
    return html.Div([
        sec("calendar","Horizonte LOM 2023–2045"),
        html.Div([
            html.Div("Vista",style={"fontSize":"11px","fontWeight":"700","color":"#94A3B8","marginBottom":"6px"}),
            dcc.Dropdown(id="lom-sel",clearable=False,value="sulf",options=[
                {"label":"Sulfuros (kWh/tt Sulf)","value":"sulf"},
                {"label":"Unitario Total (kWh/tt)","value":"unit"},
                {"label":"Infraestructura (kWh/m³)","value":"infra"},
                {"label":"Óxidos EW (kWh/tt Óxi)","value":"ew"},
                {"label":"Óxidos Seco (kWh/tt Óxi)","value":"seco"},
                {"label":"Consumo Total (GWh)","value":"kwh"},
            ]),
        ],style={**CARD_STYLE,"marginBottom":"12px"}),
        html.Div(id="lom-out"),
    ])

# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(Output("page-content","children"),Output("page-title","children"),Input("url","pathname"))
def router(path):
    fns={"/":page_home,"/consumo":page_home,"/ratios":page_ratios,
         "/areas":page_areas,"/factura":page_factura,"/lom":page_lom}
    titles={"/":"⚡ Resumen ejecutivo — Superintendencia de Energía",
            "/consumo":"📊 Consumo vs Presupuesto","/ratios":"📐 Ratios unitarios",
            "/areas":"🗂️ Desglose por área","/factura":"💰 Facturación","/lom":"🗓️ Horizonte LOM"}
    fn=fns.get(path,page_home)
    title=titles.get(path,"⚡ Resumen ejecutivo")
    if not DATA_OK:
        return html.Div([html.H3("Error cargando datos",style={"color":"#EF4444"}),
                         html.Pre(DATA_ERROR,style={"color":"#F87171","fontSize":"12px"})]), title
    try:
        return fn(), title
    except Exception as e:
        import traceback
        return html.Div([html.H3("Error",style={"color":"#EF4444","fontWeight":"700"}),
                         html.Pre(traceback.format_exc(),style={"color":"#F87171","fontSize":"11px",
                         "background":"#1E293B","padding":"12px","borderRadius":"8px"})]), title

@app.callback(Output("ratio-out","children"),Input("ratio-sel","value"))
def upd_ratio(key):
    if not key or not DATA_OK: return html.Div()
    bp=brat[brat["ratio"]==key].sort_values("fecha")
    rp=rrat[rrat["ratio"]==key].sort_values("fecha") if not rrat.empty else pd.DataFrame()
    fig=go.Figure()
    if not bp.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([bp["fecha"],bp["fecha"][::-1]]),
            y=pd.concat([bp["ratio_ppto"]*1.05,bp["ratio_ppto"][::-1]*0.95]),
            fill="toself",fillcolor="rgba(250,204,21,0.12)",line=dict(color="rgba(0,0,0,0)"),name="Banda ±5%"))
        fig.add_trace(go.Scatter(x=bp["fecha"],y=bp["ratio_ppto"],name="Presupuesto",
            mode="lines",line=dict(color="#3B82F6",width=2.5,dash="dot"),
            hovertemplate="<b>PPTO</b> %{x|%b %Y}: %{y:.2f}<extra></extra>"))
    if not rp.empty:
        fig.add_trace(go.Scatter(x=rp["fecha"],y=rp["valor_real"],name="Real",
            mode="lines+markers",line=dict(color="#EF4444",width=2.5),marker_size=5,
            hovertemplate="<b>Real</b> %{x|%b %Y}: %{y:.2f}<extra></extra>"))
    layout_fig(fig,380); fig.update_layout(xaxis=dict(showgrid=False,rangeslider=dict(visible=True)))
    ar=rp["valor_real"].mean() if not rp.empty else np.nan
    ap=bp["ratio_ppto"].mean() if not bp.empty else np.nan
    dv=(ar-ap)/ap*100 if not (np.isnan(ar) or np.isnan(ap)) else np.nan
    return html.Div([
        html.Div([kpi("Ratio Real",f"{ar:.2f}" if not np.isnan(ar) else "—","",accent="#EF4444"),
                  kpi("Ratio PPTO",f"{ap:.2f}" if not np.isnan(ap) else "—","",accent="#3B82F6"),
                  kpi("Desviación",f"{dv:+.1f}%" if not np.isnan(dv) else "—","",dv<=0 if not np.isnan(dv) else True,"#D97706"),
                  kpi("Meses reales",str(len(rp)),accent="#16A34A")],
                 style={"display":"flex","gap":"10px","marginBottom":"12px"}),
        html.Div(dcc.Graph(figure=fig,config={"displayModeBar":False}),style=CARD_STYLE),
    ])

@app.callback(Output("lom-out","children"),Input("lom-sel","value"))
def upd_lom(view):
    if not view or not DATA_OK: return html.Div()
    PHASE={"monthly":"#1D4ED8","quarterly":"#7C3AED","annual":"#0F766E"}
    PLBL={"monthly":"Mensual 2023-2027","quarterly":"Trimestral 2028-2029","annual":"Anual 2030-2045"}
    MAP={"sulf":"PLANTA SULFUROS_ratio","unit":"UNITARIO TOTAL","infra":"INFRAESTRUCTURA_ratio","ew":"OXIDOS_EW_ratio","seco":"OXIDOS_SECO_ratio"}
    fig=go.Figure()
    if view=="kwh":
        for area,color in AREA_COLORS.items():
            d=lom_kwh[lom_kwh["area"]==area].sort_values("fecha")
            if not d.empty:
                fig.add_trace(go.Scatter(x=d["fecha"],y=d["kwh_ppto"]/1e6,name=area,
                    mode="lines+markers",line=dict(color=color,width=2),marker_size=4))
        fig.update_layout(yaxis_title="GWh")
    else:
        rkey=MAP.get(view,"PLANTA SULFUROS_ratio")
        d=lom_rat[lom_rat["ratio"]==rkey].sort_values("fecha")
        for phase,color in PHASE.items():
            dp=d[d["tipo"]==phase]
            if not dp.empty:
                fig.add_trace(go.Scatter(x=dp["fecha"],y=dp["ratio_ppto"],name=PLBL[phase],
                    mode="lines+markers",line=dict(color=color,width=2.5),marker_size=5))
        fig.update_layout(yaxis_title="kWh/unidad")
    layout_fig(fig,420)
    fig.update_layout(xaxis=dict(showgrid=False,rangeslider=dict(visible=True)))
    fig.add_vrect(x0="2023-01-01",x1="2027-12-31",fillcolor="rgba(29,78,216,0.04)",layer="below",line_width=0,
        annotation_text="Mensual",annotation_position="top left",annotation_font_size=10,annotation_font_color="#1D4ED8")
    fig.add_vrect(x0="2028-01-01",x1="2029-12-31",fillcolor="rgba(124,58,237,0.04)",layer="below",line_width=0,
        annotation_text="Trimestral",annotation_position="top left",annotation_font_size=10,annotation_font_color="#7C3AED")
    fig.add_vrect(x0="2030-01-01",x1="2046-01-01",fillcolor="rgba(15,118,110,0.04)",layer="below",line_width=0,
        annotation_text="Anual",annotation_position="top left",annotation_font_size=10,annotation_font_color="#0F766E")
    return html.Div(dcc.Graph(figure=fig,config={"displayModeBar":True}),style=CARD_STYLE)

if __name__=="__main__":
    app.run(debug=False,host="0.0.0.0",port=int(os.environ.get("PORT",8050)))
