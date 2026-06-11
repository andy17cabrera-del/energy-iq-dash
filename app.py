import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import base64, os
from data_loader import (
    load_real, load_budget_kwh, load_billing,
    load_budget_ratios, load_real_ratios, BUDGET_DATES
)

# ── App setup ─────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True,
                meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])
server = app.server

# ── Logo ──────────────────────────────────────────────────────────────────────
def get_logo():
    logo_path = os.path.join(os.path.dirname(__file__), "marcobre_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""

LOGO = get_logo()

# ── Load data ─────────────────────────────────────────────────────────────────
rk = load_real()
bk = load_budget_kwh()
bill = load_billing()
brat = load_budget_ratios()
rrat = load_real_ratios()

AREA_COLORS = {
    "Sulfuros":"#1D4ED8","Óxidos":"#9333EA","Infraestructura":"#92400E",
    "Mina":"#15803D","G&A":"#0EA5E9","Mantenimiento":"#6B7280",
}

RATIO_LABELS = {
    "UNITARIO TOTAL":          "Unitario Total (kWh/tt)",
    "PLANTA SULFUROS_ratio":   "Sulfuros (kWh/tt Sulf)",
    "INFRAESTRUCTURA_ratio":   "Infraestructura (kWh/m³)",
    "OXIDOS_EW_ratio":         "Óxidos EW — Electrodeposición (kWh/tt Óxi)",
    "OXIDOS_SECO_ratio":       "Óxidos Seco — Instalaciones (kWh/tt Óxi)",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
COLORS = {
    "bg":        "#1A2E45",
    "sidebar":   "#0D1F35",
    "card":      "#FFFFFF",
    "accent":    "#185FA5",
    "text":      "#0D1F35",
    "muted":     "#64748B",
    "border":    "#E2E8F0",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
def make_sidebar():
    nav_items = [
        ("home",        "Resumen ejecutivo",    "page-home"),
        ("chart-bar",   "Consumo vs PPTO",      "page-consumo"),
        ("math-function","Ratios unitarios",    "page-ratios"),
        ("layers",      "Desglose por área",    "page-areas"),
        ("coin",        "Facturación",          "page-factura"),
        ("calendar",    "Horizonte LOM",        "page-lom"),
    ]
    links = []
    for icon, label, page_id in nav_items:
        links.append(
            html.A([
                html.I(className=f"ti ti-{icon}", style={"fontSize":"16px","marginRight":"10px"}),
                label
            ], id=f"nav-{page_id}", href=f"/{page_id.replace('page-','')}",
               style={
                   "display":"flex","alignItems":"center","padding":"8px 12px",
                   "borderRadius":"8px","color":"#94A3B8","textDecoration":"none",
                   "fontSize":"13px","marginBottom":"4px","fontWeight":"500",
               },
               className="nav-link-item")
        )
    return html.Div([
        html.Div([
            html.Img(src=LOGO, style={"width":"130px"}) if LOGO else
            html.Div([html.Span("M", style={"color":"#C0392B","fontWeight":"700","fontSize":"20px"}),
                      html.Span(" MARCOBRE", style={"color":"#1A3A5C","fontWeight":"700","fontSize":"14px"})]),
        ], style={"background":"#fff","borderRadius":"8px","padding":"8px 12px",
                  "textAlign":"center","marginBottom":"16px"}),
        html.Div([
            html.Span("⚡ Energy IQ", style={"color":"#60A5FA","fontSize":"13px","fontWeight":"700"}),
            html.Br(),
            html.Span("LOM25 Óptimo · Superintendencia", style={"color":"#475569","fontSize":"10px"}),
        ], style={"textAlign":"center","paddingBottom":"14px","borderBottom":"1px solid #1E3A5F","marginBottom":"14px"}),
        html.Div("Navegación", style={"fontSize":"9px","fontWeight":"700","color":"#334155",
                                       "textTransform":"uppercase","letterSpacing":".08em","marginBottom":"8px"}),
        *links,
    ], style={"background":COLORS["sidebar"],"width":"200px","minHeight":"100vh",
              "padding":"16px 12px","flexShrink":"0"})

# ── KPI Card ──────────────────────────────────────────────────────────────────
def kpi_card(label, value, unit="", delta=None, delta_ok=True, accent="#185FA5"):
    delta_color = "#16A34A" if delta_ok else "#DC2626"
    return html.Div([
        html.Div(label, style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase",
                                "letterSpacing":".08em","color":COLORS["muted"],"marginBottom":"4px"}),
        html.Div(value, style={"fontSize":"22px","fontWeight":"700","color":COLORS["text"],"lineHeight":"1.1"}),
        html.Div(unit,  style={"fontSize":"10px","color":"#94A3B8","marginBottom":"4px"}),
        html.Div(delta, style={"fontSize":"11px","fontWeight":"600","color":delta_color}) if delta else html.Div(),
    ], style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px 16px",
              "borderLeft":f"4px solid {accent}","flex":"1","minWidth":"0"})

# ── Alert ─────────────────────────────────────────────────────────────────────
def alert_box(msg, sub, level="green"):
    colors = {"green":("#F0FDF4","#22C55E","#14532D"),
              "amber":("#FFFBEB","#F59E0B","#78350F"),
              "red":  ("#FEF2F2","#EF4444","#7F1D1D")}
    bg, dot, txt = colors.get(level, colors["green"])
    return html.Div([
        html.Div(style={"width":"8px","height":"8px","borderRadius":"50%",
                        "background":dot,"marginTop":"4px","flexShrink":"0"}),
        html.Div([
            html.Div(msg, style={"fontSize":"12px","fontWeight":"700","color":txt}),
            html.Div(sub, style={"fontSize":"10px","color":COLORS["muted"],"marginTop":"2px"}),
        ])
    ], style={"display":"flex","gap":"10px","background":bg,"borderRadius":"8px",
              "padding":"10px 12px","border":f"0.5px solid {dot}","flex":"1"})

# ── Section header ────────────────────────────────────────────────────────────
def section_hd(icon, title):
    return html.Div([
        html.I(className=f"ti ti-{icon}", style={"fontSize":"14px","color":"#60A5FA"}),
        html.Span(title, style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase",
                                 "letterSpacing":".08em","color":"#60A5FA","marginLeft":"6px"}),
        html.Div(style={"flex":"1","height":"1px","background":"#1E3A5F","marginLeft":"8px"}),
    ], style={"display":"flex","alignItems":"center","marginBottom":"10px","marginTop":"6px"})

# ── Page: Resumen Ejecutivo ───────────────────────────────────────────────────
def page_home():
    latest = rk["fecha"].max()
    rk_lat  = rk[rk["fecha"] == latest]
    total_r = rk_lat["kwh_real"].sum()

    rk_comp = rk[rk["in_budget"] & rk["fecha"].dt.year.isin([2023,2024,2025,2026])]
    bk_same = bk[bk["fecha"].dt.year.isin([2023,2024,2025,2026])]
    bk_lat  = bk[(bk["fecha"].dt.year==latest.year)&(bk["fecha"].dt.month==latest.month)]
    total_p  = bk_lat["kwh_ppto"].sum()
    delta_pct= (total_r-total_p)/total_p*100 if total_p>0 else 0

    bill_lat = bill[bill["fecha"]==latest]["usd"].sum()
    acum_r   = rk[rk["fecha"].dt.year==latest.year]["kwh_real"].groupby(rk[rk["fecha"].dt.year==latest.year]["fecha"]).sum().sum() / 1e6

    # Charts
    real_mo  = rk.groupby("fecha")["kwh_real"].sum().reset_index().sort_values("fecha")
    bk_mo    = bk[bk["fecha"].isin(BUDGET_DATES)].groupby("fecha")["kwh_ppto"].sum().reset_index().sort_values("fecha")

    # Limitar barras al último mes con datos reales
    latest_real_fecha = rk["fecha"].max()
    bk_mo_bar = bk_mo[bk_mo["fecha"] <= latest_real_fecha]
    real_mo_bar = real_mo[real_mo["fecha"] <= latest_real_fecha]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=bk_mo_bar["fecha"],y=bk_mo_bar["kwh_ppto"]/1e6,
        name="Presupuesto",marker_color="#93C5FD",opacity=0.8,
        hovertemplate="<b>PPTO</b> %{x|%b %Y}: %{y:.2f} GWh<extra></extra>"))
    fig_bar.add_trace(go.Bar(x=real_mo_bar["fecha"],y=real_mo_bar["kwh_real"]/1e6,
        name="Real",marker_color="#34D399",opacity=0.9,
        hovertemplate="<b>Real</b> %{x|%b %Y}: %{y:.2f} GWh<extra></extra>"))
    fig_bar.update_layout(
        plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=260,
        margin=dict(l=0,r=0,t=10,b=0),barmode="group",
        legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=11),
        yaxis_title="GWh",hovermode="x unified",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))

    dist = rk_lat[rk_lat["kwh_real"]>0].copy()
    fig_donut = go.Figure(go.Pie(
        labels=dist["area"],values=dist["kwh_real"],hole=0.55,
        marker_colors=[AREA_COLORS.get(a,"#94A3B8") for a in dist["area"]],
        textinfo="label+percent",textfont_size=11))
    fig_donut.update_layout(
        paper_bgcolor="#FFFFFF",height=260,
        margin=dict(l=0,r=0,t=10,b=0),showlegend=False)

    # Area trend
    trend = rk.groupby(["fecha","area"])["kwh_real"].sum().reset_index()
    fig_trend = go.Figure()
    for area in ["Sulfuros","Óxidos","Infraestructura","Mina","G&A","Mantenimiento"]:
        d = trend[trend["area"]==area]
        fig_trend.add_trace(go.Scatter(
            x=d["fecha"],y=d["kwh_real"]/1e3,name=area,mode="lines",
            line=dict(color=AREA_COLORS.get(area,"#94A3B8"),width=2),
            hovertemplate=f"<b>{area}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} MWh<extra></extra>"))
    fig_trend.update_layout(
        plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=240,
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=11),
        yaxis_title="MWh",hovermode="x unified",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))

    # Summary table
    rows=[]
    for area in ["Sulfuros","Óxidos","Infraestructura","Mina","G&A","Mantenimiento"]:
        rv = rk_comp[rk_comp["area"]==area]["kwh_real"].mean() or 0
        pv = bk_same[bk_same["area"]==area]["kwh_ppto"].mean() or 0
        dv = (rv-pv)/pv*100 if pv>0 else 0
        rows.append({"Área":area,"Real prom GWh/mes":f"{rv/1e6:.2f}",
                     "PPTO prom GWh/mes":f"{pv/1e6:.2f}","Desv. %":f"{dv:+.1f}%"})

    return html.Div([
        section_hd("dashboard", f"Indicadores clave · {latest.strftime('%B %Y')}"),
        html.Div([
            kpi_card("Consumo real",      f"{total_r/1e6:.2f}", "GWh / mes",
                     f"{'↓' if delta_pct<0 else '↑'} {delta_pct:+.1f}% vs PPTO", delta_pct<=0, "#185FA5"),
            kpi_card("Presupuestado",     f"{total_p/1e6:.2f}", "GWh / mes", accent="#16A34A"),
            kpi_card("Facturación",       f"${bill_lat/1e6:.2f}M", "USD / mes",
                     f"{bill_lat/total_r*1000:.1f} USD/MWh" if total_r>0 else None, True, "#D97706"),
            kpi_card("Acumulado 2026",    f"{acum_r:.1f}", "GWh", accent="#9333EA"),
            kpi_card("Meses con datos",   f"{rk['fecha'].dt.year.eq(latest.year).sum()//6} / 12", accent="#C0392B"),
        ], style={"display":"flex","gap":"10px","marginBottom":"16px","flexWrap":"wrap"}),

        section_hd("alert-triangle", "Alertas de desviación"),
        html.Div([
            alert_box(f"Consumo total {delta_pct:+.1f}% vs PPTO",
                      f"{total_r/1e6:.2f} GWh · {latest.strftime('%b %Y')}",
                      "green" if abs(delta_pct)<=2 else "amber" if abs(delta_pct)<=5 else "red"),
            alert_box("Sulfuros −0.4% bajo PPTO",  "13.10 GWh/mes · PPTO: 13.15", "green"),
            alert_box("Ratio EW +6.1% sobre plan",  "6.85 kWh/tt Óxi · PPTO: 6.45", "amber"),
        ], style={"display":"flex","gap":"8px","marginBottom":"16px","flexWrap":"wrap"}),

        section_hd("chart-bar", "Consumo mensual — Real vs Presupuesto"),
        html.Div([
            html.Div(dcc.Graph(figure=fig_bar,config={"displayModeBar":False}),
                     style={"flex":"2","background":COLORS["card"],"borderRadius":"10px","padding":"14px","border":f"0.5px solid {COLORS['border']}"}),
            html.Div([
                html.Div("Distribución · "+latest.strftime("%b %Y"),
                         style={"fontSize":"13px","fontWeight":"700","color":COLORS["text"],"marginBottom":"4px"}),
                dcc.Graph(figure=fig_donut,config={"displayModeBar":False}),
            ], style={"flex":"1","background":COLORS["card"],"borderRadius":"10px","padding":"14px","border":f"0.5px solid {COLORS['border']}"}),
        ], style={"display":"flex","gap":"10px","marginBottom":"14px"}),

        section_hd("trending-up", "Evolución por área 2021–2026"),
        html.Div(dcc.Graph(figure=fig_trend,config={"displayModeBar":False}),
                 style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                        "border":f"0.5px solid {COLORS['border']}","marginBottom":"14px"}),

        section_hd("table", "Resumen por área — promedio mensual"),
        html.Div(dash_table.DataTable(
            data=rows,
            columns=[{"name":c,"id":c} for c in ["Área","Real prom GWh/mes","PPTO prom GWh/mes","Desv. %"]],
            style_header={"background":"#F8FAFC","fontWeight":"700","fontSize":"11px",
                          "textTransform":"uppercase","letterSpacing":".06em","color":COLORS["muted"],
                          "border":"none","borderBottom":f"1.5px solid {COLORS['border']}"},
            style_data={"fontSize":"12px","color":COLORS["text"],"border":"none",
                        "borderBottom":f"0.5px solid #F1F5F9"},
            style_data_conditional=[
                {"if":{"row_index":"odd"},"background":"#F8FAFC"},
                {"if":{"filter_query":'{Desv. %}  contains "+"',"column_id":"Desv. %"},"color":"#DC2626","fontWeight":"700"},
                {"if":{"filter_query":'{Desv. %} contains "-"',"column_id":"Desv. %"},"color":"#16A34A","fontWeight":"700"},
            ],
            style_table={"borderRadius":"10px","overflow":"hidden"},
        ), style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                  "border":f"0.5px solid {COLORS['border']}"}),
    ])

# ── Page: Ratios ──────────────────────────────────────────────────────────────
def page_ratios():
    return html.Div([
        section_hd("math-function", "Ratios unitarios — Presupuesto vs Real"),
        html.Div([
            html.Div("Ratio a analizar", style={"fontSize":"11px","fontWeight":"700","color":"#94A3B8","marginBottom":"6px"}),
            dcc.Dropdown(
                id="ratio-selector",
                options=[{"label":v,"value":k} for k,v in RATIO_LABELS.items()],
                value="PLANTA SULFUROS_ratio",
                clearable=False,
                style={"fontSize":"13px"}),
        ], style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                  "border":f"0.5px solid {COLORS['border']}","marginBottom":"12px"}),
        html.Div(id="ratio-content"),
    ])

# ── Page: Areas ───────────────────────────────────────────────────────────────
def page_areas():
    areas_all = list(AREA_COLORS.keys())
    rk_comp = rk[rk["in_budget"]].copy()
    bk_all  = bk.copy()

    kpis = []
    for area in areas_all:
        rv = rk_comp[rk_comp["area"]==area]["kwh_real"].mean() or 0
        pv = bk_all[bk_all["area"]==area]["kwh_ppto"].mean() or 0
        dv = (rv-pv)/pv*100 if pv>0 else 0
        color = AREA_COLORS.get(area,"#94A3B8")
        dcolor = "#16A34A" if dv<=0 else "#DC2626" if abs(dv)>5 else "#D97706"
        kpis.append(html.Div([
            html.Div(area, style={"fontSize":"10px","fontWeight":"700","textTransform":"uppercase",
                                   "letterSpacing":".06em","color":COLORS["muted"]}),
            html.Div(f"{rv/1e6:.1f}", style={"fontSize":"22px","fontWeight":"700","color":COLORS["text"]}),
            html.Span("GWh/mes", style={"fontSize":"10px","color":"#94A3B8"}),
            html.Div(f"{dv:+.1f}% vs PPTO", style={"fontSize":"11px","fontWeight":"600","color":dcolor,"marginTop":"4px"}),
        ], style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                  "borderLeft":f"4px solid {color}","flex":"1","minWidth":"0",
                  "border":f"0.5px solid {COLORS['border']}","borderLeft":f"4px solid {color}"}))

    trend = rk.groupby(["fecha","area"])["kwh_real"].sum().reset_index()
    trend_bk = bk.groupby(["fecha","area"])["kwh_ppto"].sum().reset_index()

    def make_area_fig(df, val_col, areas_list, chart_type="stack"):
        fig = go.Figure()
        for area in areas_list:
            d = df[df["area"]==area].sort_values("fecha")
            color = AREA_COLORS.get(area,"#94A3B8")
            fig.add_trace(go.Bar(x=d["fecha"],y=d[val_col]/1e3,name=area,
                marker_color=color,opacity=0.85,
                hovertemplate=f"<b>{area}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} MWh<extra></extra>"))
        fig.update_layout(barmode="stack" if chart_type=="stack" else "group",
            plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=320,
            margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h",yanchor="bottom",y=1.01),
            yaxis_title="MWh",hovermode="x unified",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))
        return fig

    def make_comp_fig(areas_list):
        fig = go.Figure()
        for area in areas_list:
            color = AREA_COLORS.get(area,"#94A3B8")
            dp = trend_bk[trend_bk["area"]==area].sort_values("fecha")
            dr = trend[trend["area"]==area].sort_values("fecha")
            fig.add_trace(go.Scatter(x=dp["fecha"],y=dp["kwh_ppto"]/1e3,
                name=f"{area} PPTO",mode="lines",
                line=dict(color=color,dash="dot",width=1.5),legendgroup=area))
            fig.add_trace(go.Scatter(x=dr["fecha"],y=dr["kwh_real"]/1e3,
                name=f"{area} Real",mode="lines+markers",
                line=dict(color=color,width=2.5),marker_size=4,legendgroup=area))
        fig.update_layout(plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=380,
            margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=10),
            yaxis_title="MWh",hovermode="x unified",
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))
        return fig

    fig_real = make_area_fig(trend,"kwh_real",areas_all)
    fig_ppto = make_area_fig(trend_bk,"kwh_ppto",areas_all)
    fig_comp = make_comp_fig(areas_all)
    fig = fig_real

    latest = rk["fecha"].max()
    tree = rk[rk["fecha"]==latest].copy()
    fig_tree = px.treemap(tree,path=["area"],values="kwh_real",
        color="area",color_discrete_map=AREA_COLORS,
        title=f"Distribución {latest.strftime('%B %Y')}")
    fig_tree.update_layout(height=300,margin=dict(l=0,r=0,t=40,b=0),paper_bgcolor="#FFFFFF")

    return html.Div([
        section_hd("layers","Desglose por área operativa"),
        html.Div(kpis, style={"display":"flex","gap":"8px","marginBottom":"14px","flexWrap":"wrap"}),
        section_hd("trending-up","Consumo real por área — evolución mensual"),
        dcc.Tabs([
            dcc.Tab(label="Real", children=[
                html.Div(dcc.Graph(figure=fig_real,config={"displayModeBar":False}),
                    style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                           "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
            dcc.Tab(label="Presupuesto", children=[
                html.Div(dcc.Graph(figure=fig_ppto,config={"displayModeBar":False}),
                    style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                           "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
            dcc.Tab(label="Comparación Real vs PPTO", children=[
                html.Div(dcc.Graph(figure=fig_comp,config={"displayModeBar":False}),
                    style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                           "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
        ], style={"marginBottom":"12px"}),
        section_hd("chart-area","Distribución — último mes"),
        html.Div(dcc.Graph(figure=fig_tree,config={"displayModeBar":False}),
                 style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                        "border":f"0.5px solid {COLORS['border']}"}),
    ])

# ── Page: Factura ─────────────────────────────────────────────────────────────
def page_factura():
    bill_mo = bill.groupby(["fecha","area"])["usd"].sum().reset_index()
    bill_total = bill.groupby("fecha")["usd"].sum().reset_index()
    fig = go.Figure()
    for area in list(AREA_COLORS.keys()):
        d = bill_mo[bill_mo["area"]==area].sort_values("fecha")
        fig.add_trace(go.Bar(x=d["fecha"],y=d["usd"],name=area,
            marker_color=AREA_COLORS.get(area,"#94A3B8"),opacity=0.85))
    fig.add_trace(go.Scatter(x=bill_total["fecha"],y=bill_total["usd"],
        name="Total",mode="lines+markers",line=dict(color="#0D1F35",width=2.5),
        marker_size=5,yaxis="y2"))
    fig.update_layout(
        barmode="stack",plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=320,
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h",yanchor="bottom",y=1.01),
        yaxis_title="USD",yaxis2=dict(overlaying="y",side="right",showgrid=False),
        hovermode="x unified",xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))

    total_acum = bill["usd"].sum()
    last_mo    = bill_total.iloc[-1]["usd"] if not bill_total.empty else 0
    prom_mo    = bill_total["usd"].mean()

    rk_all = rk.groupby("fecha")["kwh_real"].sum().reset_index()
    usd_mwh = pd.merge(bill_total,rk_all,on="fecha")
    usd_mwh = usd_mwh[usd_mwh["kwh_real"]>0].copy()
    usd_mwh["usd_mwh"] = usd_mwh["usd"]/(usd_mwh["kwh_real"]/1e3)
    fig2 = go.Figure(go.Scatter(x=usd_mwh["fecha"],y=usd_mwh["usd_mwh"],
        mode="lines+markers",line=dict(color="#7C3AED",width=2.5),
        fill="tozeroy",fillcolor="rgba(124,58,237,0.07)"))
    avg = usd_mwh["usd_mwh"].mean()
    fig2.add_hline(y=avg,line_dash="dash",line_color="#94A3B8",
                   annotation_text=f"Promedio: ${avg:.1f}/MWh")
    fig2.update_layout(
        plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=260,
        margin=dict(l=0,r=0,t=10,b=0),yaxis_title="USD/MWh",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#F1F5F9"))

    # Donut distribution
    dist = bill.groupby("area")["usd"].sum().reset_index()
    dist = dist[dist["usd"]>0].sort_values("usd",ascending=False)
    fig_donut = go.Figure(go.Pie(
        labels=dist["area"],values=dist["usd"],hole=0.55,
        marker_colors=[AREA_COLORS.get(a,"#94A3B8") for a in dist["area"]],
        textinfo="label+percent",textfont_size=11))
    fig_donut.update_layout(paper_bgcolor="#FFFFFF",height=280,
        margin=dict(l=0,r=0,t=10,b=0),showlegend=False)

    return html.Div([
        section_hd("coin","Facturación energética"),
        html.Div([
            kpi_card("Facturación acumulada", f"${total_acum/1e6:.1f}M","USD", accent="#185FA5"),
            kpi_card("Último mes",f"${last_mo/1e6:.2f}M","USD",accent="#D97706"),
            kpi_card("Promedio mensual",f"${prom_mo/1e6:.2f}M","USD",accent="#9333EA"),
            kpi_card("Costo unitario prom",f"${avg:.1f}","USD/MWh",accent="#C0392B"),
        ],style={"display":"flex","gap":"10px","marginBottom":"14px"}),
        dcc.Tabs([
            dcc.Tab(label="Evolución mensual", children=[
                html.Div(dcc.Graph(figure=fig,config={"displayModeBar":False}),
                    style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                           "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
            dcc.Tab(label="Distribución por área", children=[
                html.Div([
                    html.Div(dcc.Graph(figure=fig_donut,config={"displayModeBar":False}),style={"flex":"1"}),
                    html.Div([
                        html.Div([
                            html.Div(row["area"],style={"fontWeight":"700","fontSize":"13px","color":COLORS["text"]}),
                            html.Div(f"${row['usd']/1e6:.2f}M ({row['usd']/dist['usd'].sum()*100:.1f}%)",
                                     style={"fontSize":"12px","color":COLORS["muted"]}),
                            html.Hr(style={"margin":"6px 0","borderColor":"#F1F5F9"}),
                        ]) for _,row in dist.iterrows()
                    ],style={"flex":"1","padding":"14px"}),
                ],style={"display":"flex","background":COLORS["card"],"borderRadius":"10px",
                         "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
            dcc.Tab(label="Costo unitario USD/MWh", children=[
                html.Div(dcc.Graph(figure=fig2,config={"displayModeBar":False}),
                    style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                           "border":f"0.5px solid {COLORS['border']}"})
            ], style={"color":COLORS["muted"],"fontWeight":"600"},
               selected_style={"color":COLORS["accent"],"fontWeight":"700","borderTop":f"3px solid {COLORS['accent']}"}),
        ],style={"marginBottom":"12px"}),
    ])


# ── Page: LOM ────────────────────────────────────────────────────────────────
def page_lom():
    import re as re_module
    RATIO_COL_MAP = {
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
        92:"28q1",93:"28q2",94:"28q3",95:"28q4",96:"2028",
        98:"29q1",99:"29q2",100:"29q3",101:"29q4",102:"2029",
        104:"2030",105:"2031",106:"2032",107:"2033",108:"2034",109:"2035",
        110:"2036",111:"2037",112:"2038",113:"2039",114:"2040",115:"2041",
        116:"2042",117:"2043",118:"2044",119:"2045",
    }

    def period_type(p):
        p=str(p)
        if re_module.match(r"\d{2}m\d",p): return "monthly"
        if re_module.match(r"\d{2}q\d",p): return "quarterly"
        return "annual"

    PHASE_COLORS = {"monthly":"#1D4ED8","quarterly":"#7C3AED","annual":"#0F766E"}
    PHASE_LABELS = {"monthly":"Mensual 2023–2027","quarterly":"Trimestral 2028–2029","annual":"Anual 2030–2045"}

    LOM_OPTIONS = [
        {"label":"Consumo Total (GWh)","value":"kwh_total"},
        {"label":"Sulfuros (kWh/tt Sulf)","value":"sulf_ratio"},
        {"label":"Unitario Total (kWh/tt)","value":"unit_ratio"},
        {"label":"Infraestructura (kWh/m³)","value":"infra_ratio"},
        {"label":"Óxidos EW (kWh/tt Óxi)","value":"ew_ratio"},
        {"label":"Óxidos Seco (kWh/tt Óxi)","value":"seco_ratio"},
    ]

    return html.Div([
        section_hd("calendar","Horizonte LOM 2023–2045"),
        html.Div([
            html.Div("Vista principal",style={"fontSize":"11px","fontWeight":"700",
                "color":"#94A3B8","marginBottom":"6px"}),
            dcc.Dropdown(id="lom-selector",options=LOM_OPTIONS,
                value="sulf_ratio",clearable=False,style={"fontSize":"13px"}),
        ],style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                 "border":f"0.5px solid {COLORS['border']}","marginBottom":"12px"}),
        html.Div(id="lom-content"),
    ])

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div([
        make_sidebar(),
        html.Div([
            # Top bar
            html.Div([
                html.Div([
                    html.Span("⚡ ", style={"color":"#F59E0B"}),
                    html.Span("Resumen ejecutivo — Superintendencia de Energía",
                              style={"fontSize":"20px","fontWeight":"700","color":"#FFFFFF"}),
                ], id="page-title"),
                html.Div([
                    html.Span("● Actualizado · Mar 2026",
                              style={"background":"#0F2E1A","color":"#4ADE80","fontSize":"11px",
                                     "padding":"4px 12px","borderRadius":"20px",
                                     "border":"0.5px solid #166534","marginRight":"8px"}),
                ]),
            ], style={"display":"flex","alignItems":"center","justifyContent":"space-between",
                      "padding":"12px 20px","background":"#0D1F35",
                      "borderBottom":"1px solid #1E3A5F","marginBottom":"0"}),
            # Content
            html.Div(id="page-content",
                     style={"padding":"18px 20px","overflowY":"auto","flex":"1"}),
        ], style={"flex":"1","display":"flex","flexDirection":"column","minWidth":"0"}),
    ], style={"display":"flex","minHeight":"100vh"}),
], style={"background":COLORS["bg"],"fontFamily":"'Inter',sans-serif"})

# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(Output("page-content","children"),
              Output("page-title","children"),
              Input("url","pathname"))
def router(pathname):
    titles = {
        "/consumo":  "📊 Consumo vs Presupuesto",
        "/ratios":   "📐 Ratios unitarios",
        "/areas":    "🗂️ Desglose por área",
        "/factura":  "💰 Facturación energética",
        "/lom":      "🗓️ Horizonte LOM 2025–2045",
    }
    pages = {
        "/consumo": page_home,
        "/ratios":  page_ratios,
        "/areas":   page_areas,
        "/factura": page_factura,
        "/lom":     page_lom,
    }
    title_text = titles.get(pathname, "⚡ Resumen ejecutivo — Superintendencia de Energía")
    title_el = html.Span(title_text, style={"fontSize":"20px","fontWeight":"700","color":"#FFFFFF"})
    page_fn = pages.get(pathname, page_home)
    return page_fn(), title_el

@app.callback(Output("ratio-content","children"),
              Input("ratio-selector","value"))
def update_ratio(ratio_key):
    if not ratio_key:
        return html.Div()

    bp = brat[brat["ratio"]==ratio_key].sort_values("fecha")
    rp = rrat[rrat["ratio"]==ratio_key].sort_values("fecha") if not rrat.empty else pd.DataFrame()

    fig = go.Figure()
    if not bp.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([bp["fecha"],bp["fecha"][::-1]]),
            y=pd.concat([bp["ratio_ppto"]*1.05,bp["ratio_ppto"][::-1]*0.95]),
            fill="toself",fillcolor="rgba(250,204,21,0.12)",
            line=dict(color="rgba(0,0,0,0)"),name="Banda ±5%"))
        fig.add_trace(go.Scatter(x=bp["fecha"],y=bp["ratio_ppto"],name="Presupuesto",
            mode="lines",line=dict(color="#3B82F6",width=2.5,dash="dot"),
            hovertemplate="<b>PPTO</b> %{x|%b %Y}: %{y:.2f}<extra></extra>"))
    if not rp.empty:
        fig.add_trace(go.Scatter(x=rp["fecha"],y=rp["valor_real"],name="Real",
            mode="lines+markers",line=dict(color="#EF4444",width=2.5),
            marker_size=5,
            hovertemplate="<b>Real</b> %{x|%b %Y}: %{y:.2f}<extra></extra>"))
        if not bp.empty:
            chk = pd.merge(rp[["fecha","valor_real"]],bp[["fecha","ratio_ppto"]],on="fecha",how="inner")
            over = chk[chk["valor_real"]>chk["ratio_ppto"]*1.05]
            if not over.empty:
                fig.add_trace(go.Scatter(x=over["fecha"],y=over["valor_real"],
                    name="Sobre +5%",mode="markers",
                    marker=dict(color="#DC2626",size=12,symbol="x-thin",line_width=2)))

    fig.update_layout(
        plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=380,
        margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(orientation="h",yanchor="bottom",y=1.01),
        hovermode="x unified",yaxis_title=RATIO_LABELS.get(ratio_key,""),
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True)),
        yaxis=dict(gridcolor="#F1F5F9"))

    avg_r = rp["valor_real"].mean() if not rp.empty else np.nan
    avg_p = bp["ratio_ppto"].mean() if not bp.empty else np.nan
    dev   = (avg_r-avg_p)/avg_p*100 if (not np.isnan(avg_p) and not np.isnan(avg_r)) else np.nan

    return html.Div([
        html.Div([
            kpi_card("Ratio Real prom",  f"{avg_r:.2f}" if not np.isnan(avg_r) else "—","",accent="#EF4444"),
            kpi_card("Ratio PPTO prom",  f"{avg_p:.2f}" if not np.isnan(avg_p) else "—","",accent="#3B82F6"),
            kpi_card("Desviación prom",  f"{dev:+.1f}%" if not np.isnan(dev) else "—","",
                     delta_ok=not np.isnan(dev) and dev<=0, accent="#D97706"),
            kpi_card("Meses reales",     str(len(rp)),accent="#16A34A"),
        ],style={"display":"flex","gap":"10px","marginBottom":"12px"}),
        html.Div(dcc.Graph(figure=fig,config={"displayModeBar":False}),
                 style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
                        "border":f"0.5px solid {COLORS['border']}"}),
    ])

@app.callback(Output("lom-content","children"), Input("lom-selector","value"))
def update_lom(view):
    import re as re_mod, openpyxl as oxl
    BASE = os.path.dirname(os.path.abspath(__file__))
    df1 = __import__("pandas").read_excel(os.path.join(BASE,"presupuesto_energia.xlsx"),
        sheet_name="LOM25 Óptimo",header=None)

    RATIO_ROW_MAP = {
        "sulf_ratio":43,"unit_ratio":21,"infra_ratio":53,
        "ew_ratio":69,"seco_ratio":58,
    }
    KWH_ROWS = {"G&A":86,"Mina":96,"Sulfuros":106,"Infraestructura":116,"Mantenimiento":101,"Óxidos":120}
    COL_MAP = {
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
        92:"28q1",93:"28q2",94:"28q3",95:"28q4",96:"2028",
        98:"29q1",99:"29q2",100:"29q3",101:"29q4",102:"2029",
        104:"2030",105:"2031",106:"2032",107:"2033",108:"2034",109:"2035",
        110:"2036",111:"2037",112:"2038",113:"2039",114:"2040",115:"2041",
        116:"2042",117:"2043",118:"2044",119:"2045",
    }
    pd = __import__("pandas")

    def ptype(p):
        p=str(p)
        if re_mod.match(r"\d{2}m\d",p): return "monthly"
        if re_mod.match(r"\d{2}q\d",p): return "quarterly"
        return "annual"

    from data_loader import parse_period
    PHASE_COLORS={"monthly":"#1D4ED8","quarterly":"#7C3AED","annual":"#0F766E"}
    PHASE_LABELS={"monthly":"Mensual 2023–2027","quarterly":"Trimestral 2028–2029","annual":"Anual 2030–2045"}

    records=[]
    if view=="kwh_total":
        for area,row in KWH_ROWS.items():
            for col,period in COL_MAP.items():
                if col<df1.shape[1]:
                    val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                    fecha=parse_period(period)
                    if pd.notna(val) and val>0 and pd.notna(fecha):
                        records.append({"fecha":fecha,"val":float(val)/1e6,"tipo":ptype(period),"area":area})
        df_s=pd.DataFrame(records)
        fig=go.Figure()
        for phase,color in PHASE_COLORS.items():
            for area in list(KWH_ROWS.keys()):
                d=df_s[(df_s["tipo"]==phase)&(df_s["area"]==area)].sort_values("fecha")
                if not d.empty:
                    fig.add_trace(go.Scatter(x=d["fecha"],y=d["val"],name=f"{area} {PHASE_LABELS[phase]}",
                        mode="lines+markers",line=dict(color=AREA_COLORS.get(area,"#94A3B8"),width=2),
                        marker_size=4,showlegend=True,legendgroup=area))
        ylabel="GWh"
    else:
        row=RATIO_ROW_MAP.get(view,43)
        for col,period in COL_MAP.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_period(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    records.append({"fecha":fecha,"val":float(val),"tipo":ptype(period)})
        df_s=pd.DataFrame(records).sort_values("fecha")
        fig=go.Figure()
        for phase,color in PHASE_COLORS.items():
            d=df_s[df_s["tipo"]==phase]
            if not d.empty:
                fig.add_trace(go.Scatter(x=d["fecha"],y=d["val"],name=PHASE_LABELS[phase],
                    mode="lines+markers",line=dict(color=color,width=2.5),marker_size=5))
        ylabel="kWh/unidad"

    fig.update_layout(plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=420,
        margin=dict(l=0,r=0,t=20,b=0),
        legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=10),
        yaxis_title=ylabel,hovermode="x unified",
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True)),
        yaxis=dict(gridcolor="#F1F5F9"))

    # Add phase shading
    fig.add_vrect(x0="2023-01-01",x1="2027-12-31",fillcolor="rgba(29,78,216,0.04)",
        layer="below",line_width=0,annotation_text="Mensual",annotation_position="top left",
        annotation_font_size=10,annotation_font_color="#1D4ED8")
    fig.add_vrect(x0="2028-01-01",x1="2029-12-31",fillcolor="rgba(124,58,237,0.04)",
        layer="below",line_width=0,annotation_text="Trimestral",annotation_position="top left",
        annotation_font_size=10,annotation_font_color="#7C3AED")
    fig.add_vrect(x0="2030-01-01",x1="2046-01-01",fillcolor="rgba(15,118,110,0.04)",
        layer="below",line_width=0,annotation_text="Anual",annotation_position="top left",
        annotation_font_size=10,annotation_font_color="#0F766E")

    return html.Div(dcc.Graph(figure=fig,config={"displayModeBar":True}),
        style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
               "border":f"0.5px solid {COLORS['border']}"})


@app.callback(Output("lom-content","children"), Input("lom-selector","value"))
def update_lom(view):
    import re as re_mod
    import pandas as pd
    BASE = os.path.dirname(os.path.abspath(__file__))
    df1 = pd.read_excel(os.path.join(BASE,"presupuesto_energia.xlsx"),
        sheet_name="LOM25 Optimo",header=None)

    RATIO_ROW_MAP = {"sulf_ratio":43,"unit_ratio":21,"infra_ratio":53,"ew_ratio":69,"seco_ratio":58}
    KWH_ROWS = {"G&A":86,"Mina":96,"Sulfuros":106,"Infraestructura":116,"Mantenimiento":101,"Oxidos":120}
    COL_MAP = {
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

    def ptype(p):
        p=str(p)
        if re_mod.match(r"\d{2}m\d",p): return "monthly"
        if re_mod.match(r"\d{2}q\d",p): return "quarterly"
        return "annual"

    from data_loader import parse_period
    PHASE_COLORS={"monthly":"#1D4ED8","quarterly":"#7C3AED","annual":"#0F766E"}
    PHASE_LABELS={"monthly":"Mensual 2023-2027","quarterly":"Trimestral 2028-2029","annual":"Anual 2030-2045"}

    records=[]
    if view=="kwh_total":
        for area,row in KWH_ROWS.items():
            for col,period in COL_MAP.items():
                if col<df1.shape[1]:
                    val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                    fecha=parse_period(period)
                    if pd.notna(val) and val>0 and pd.notna(fecha):
                        records.append({"fecha":fecha,"val":float(val)/1e6,"tipo":ptype(period),"area":area})
        df_s=pd.DataFrame(records)
        fig=go.Figure()
        shown=set()
        for area in list(KWH_ROWS.keys()):
            d=df_s[df_s["area"]==area].sort_values("fecha")
            if not d.empty:
                color=AREA_COLORS.get(area,"#94A3B8")
                fig.add_trace(go.Scatter(x=d["fecha"],y=d["val"],name=area,
                    mode="lines+markers",line=dict(color=color,width=2),marker_size=4))
        ylabel="GWh"
    else:
        row=RATIO_ROW_MAP.get(view,43)
        for col,period in COL_MAP.items():
            if col<df1.shape[1]:
                val=pd.to_numeric(df1.iloc[row,col],errors="coerce")
                fecha=parse_period(period)
                if pd.notna(val) and val>0 and pd.notna(fecha):
                    records.append({"fecha":fecha,"val":float(val),"tipo":ptype(period)})
        df_s=pd.DataFrame(records).sort_values("fecha")
        fig=go.Figure()
        for phase,color in PHASE_COLORS.items():
            d=df_s[df_s["tipo"]==phase]
            if not d.empty:
                fig.add_trace(go.Scatter(x=d["fecha"],y=d["val"],name=PHASE_LABELS[phase],
                    mode="lines+markers",line=dict(color=color,width=2.5),marker_size=5))
        ylabel="kWh/unidad"

    fig.update_layout(plot_bgcolor="#FFFFFF",paper_bgcolor="#FFFFFF",height=420,
        margin=dict(l=0,r=0,t=30,b=0),
        legend=dict(orientation="h",yanchor="bottom",y=1.01,font_size=10),
        yaxis_title=ylabel,hovermode="x unified",
        xaxis=dict(showgrid=False,rangeslider=dict(visible=True)),
        yaxis=dict(gridcolor="#F1F5F9"))

    fig.add_vrect(x0="2023-01-01",x1="2027-12-31",fillcolor="rgba(29,78,216,0.04)",
        layer="below",line_width=0,annotation_text="Mensual",
        annotation_position="top left",annotation_font_size=10,annotation_font_color="#1D4ED8")
    fig.add_vrect(x0="2028-01-01",x1="2029-12-31",fillcolor="rgba(124,58,237,0.04)",
        layer="below",line_width=0,annotation_text="Trimestral",
        annotation_position="top left",annotation_font_size=10,annotation_font_color="#7C3AED")
    fig.add_vrect(x0="2030-01-01",x1="2046-01-01",fillcolor="rgba(15,118,110,0.04)",
        layer="below",line_width=0,annotation_text="Anual",
        annotation_position="top left",annotation_font_size=10,annotation_font_color="#0F766E")

    return html.Div(dcc.Graph(figure=fig,config={"displayModeBar":True}),
        style={"background":COLORS["card"],"borderRadius":"10px","padding":"14px",
               "border":f"0.5px solid {COLORS['border']}"})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
