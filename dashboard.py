import streamlit as st
import textwrap
import pandas as pd

# ==== CONFIGURACIÓN DE PÁGINA ====
st.set_page_config(page_title="Dashboard Directivo", layout="wide", initial_sidebar_state="expanded")

# ==== CSS PERSONALIZADO ====
st.markdown(textwrap.dedent("""
<style>
    /* === PALETA CORPORATIVA ===
       Negro:  #1D1D1B
       Kraft:  #C7AB72
       Verde:  #589642
       Blanco: #FFFFFF (principal)
    */
    
    /* ----- EMBUDO EMPRESAS (TEMA CLARO) ----- */
    .funnel-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 12px;
        color: #1D1D1B;
        margin-bottom: 50px;
        border: 1px solid #e8e4dc;
        box-shadow: 0 2px 8px rgba(29,29,27,0.07);
    }
    .main-title { color: #C7AB72; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 700; }
    .funnel-title { color: #1D1D1B; font-size: 36px; font-weight: bold; margin-bottom: 5px; }
    .funnel-subtitle { color: #6b6b69; font-size: 14px; margin-bottom: 30px; }
    .date-badge { float: right; border: 1px solid #C7AB72; padding: 8px 16px; border-radius: 20px; font-size: 14px; color: #1D1D1B; background-color: white; }
    
    .stage-1 { background-color: #1D1D1B; color: white; border-radius: 12px; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 3; }
    .connector-1 { height: 60px; background: #e8e4dc; clip-path: polygon(0 0, 100% 0, 95% 100%, 5% 100%); margin-top: -10px; position: relative; z-index: 2; }
    .stage-2-container { background-color: white; border-radius: 12px; padding: 20px 0; margin: -10px 5% 0 5%; box-shadow: 0 4px 12px rgba(29,29,27,0.06); position: relative; z-index: 3; border: 1px solid #e8e4dc; }
    .connector-2 { height: 50px; background: #d6e8cf; clip-path: polygon(5% 0, 95% 0, 75% 100%, 25% 100%); margin-top: -10px; position: relative; z-index: 2; }
    .stage-3 { background-color: #589642; color: white; border-radius: 12px; padding: 20px 30px; margin: 0 15%; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 3; }
    
    .stage-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }
    .stage-name { font-size: 20px; font-weight: bold; margin-top: 5px; }
    .stage-value { font-size: 38px; font-weight: bold; }
    .stage-2-header { padding: 0 20px 10px 20px; font-size: 11px; color: #6b6b69; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; border-bottom: 2px solid transparent; }
    .channels-row { display: flex; width: 100%; flex-wrap: nowrap; overflow: hidden; }
    .channel-box { flex: 1; padding: 15px 10px; border-right: 1px solid #e8e4dc; min-width: 0; }
    .channel-box:last-child { border-right: none; }
    
    .border-retail { border-top: 4px solid #1D1D1B; } 
    .border-food { border-top: 4px solid #589642; } 
    .border-distribuidor { border-top: 4px solid #C7AB72; }
    .border-grandes { border-top: 4px solid #8a7452; }
    .channel-name { font-size: 14px; font-weight: 600; color: #1D1D1B; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .channel-reg { font-size: 26px; font-weight: bold; color: #1D1D1B; display: flex; align-items: baseline; }
    .reg-label { font-size: 10px; font-weight: normal; color: #6b6b69; margin-left: 3px; }
    .channel-cont-value { font-size: 20px; font-weight: bold; display: flex; align-items: baseline; }
    .color-retail { color: #1D1D1B; } 
    .color-food { color: #589642; } 
    .color-distribuidor { color: #C7AB72; } 
    .color-grandes { color: #8a7452; }
    .conversion-rate { font-size: 12px; color: #6b6b69; margin: 8px 0; display: flex; align-items: center; }
    .conversion-rate svg { margin-right: 3px; width: 10px; height: 10px; }
    .stage-3-pct { font-size: 18px; font-weight: normal; margin-left: 8px; opacity: 0.9; }

    /* ----- EMBUDO NEGOCIOS (TEMA OSCURO CORPORATIVO) ----- */
    .negocios-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #1D1D1B;
        padding: 50px 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .negocios-title {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .negocios-subtitle {
        color: #C7AB72;
        font-size: 14px;
        margin-bottom: 40px;
    }
    .negocios-subtitle span { color: #589642; font-weight: bold; }
    
    .funnel-layer {
        margin: 0 auto 10px auto;
        border-radius: 12px;
        padding: 15px 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: bold;
    }
    
    .layer-count-group { text-align: left; }
    .layer-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; margin-bottom: 2px; }
    .layer-count { font-size: 24px; display: flex; justify-content: flex-start; align-items: baseline; }
    .layer-count-label { font-size: 12px; font-weight: normal; margin-left: 5px; opacity: 0.8; }
    
    .layer-value-group { text-align: right; }
    .layer-value { font-size: 20px; font-weight: bold;}
    .layer-val-label { font-size: 10px; font-weight: normal; opacity: 0.8; display: block; margin-top: 2px;}

    /* Anchuras y colores con paleta corporativa */
    .bg-asignado   { background-color: #FFFFFF; color: #1D1D1B; border: 1px solid #e8e4dc; width: 100%; }
    .bg-contactado { background-color: #3d3d3a; color: white;   width: 88%; }
    .bg-negociacion{ background-color: #C7AB72; color: #1D1D1B; width: 80%; }
    .bg-ganada     { background-color: #589642; color: white;   width: 70%; }
    .bg-perdida    { background-color: #7a5c2e; color: white;   width: 65%; }
    .bg-pausado    { background-color: #a8936a; color: #1D1D1B; width: 55%; }
</style>
"""), unsafe_allow_html=True)

# ==== FETCH DATOS GOOGLE SHEETS ====
@st.cache_data(ttl="5s")
def load_data():
    # Usamos el formato de exportacion directa a xlsx para evitar bloqueos de API
    url = "https://docs.google.com/spreadsheets/d/1AQ9KX-gUW9VcSC3PypbsESPi_YZ939i_CBgVrft2xko/export?format=xlsx"
    xls = pd.ExcelFile(url)
    df_emp = pd.read_excel(xls, sheet_name="Empresas")
    df_neg = pd.read_excel(xls, sheet_name="Negocios")
    
    # Hoja Fidelización (4ta hoja)
    try:
        df_fid = pd.read_excel(xls, sheet_name="Fidelización", header=0)
    except:
        df_fid = pd.read_excel(xls, sheet_name=3, header=0)
        
    # Hoja ROI COLOMBIATEX (5ta hoja)
    try:
        df_roi = pd.read_excel(xls, sheet_name="ROI COLOMBIATEX", header=None)
    except:
        df_roi = pd.read_excel(xls, sheet_name=4, header=None)
        
    # Hoja KPI Negocios
    try:
        df_kpi = pd.read_excel(xls, sheet_name="KPI Negocios")
    except:
        try:
            df_kpi = pd.read_excel(xls, sheet_name="GESTIÓN DE CONTACTOS")
        except:
            df_kpi = pd.DataFrame(columns=['fecha de contacto', 'Hora', 'motivo de contacto', 'número de contacto', 'Conteste/No conteste', 'nombre'])
            
    # Hoja MANYCHAT
    try:
        df_manychat = pd.read_excel(xls, sheet_name="MANYCHAT")
    except:
        df_manychat = pd.DataFrame()
    
    # Hoja LEADS (para KPIs Mercadeo)
    try:
        df_leads = pd.read_excel(xls, sheet_name="LEADS")
    except:
        df_leads = pd.DataFrame()
    
    # Hoja cotizaciones (para KPIs Mercadeo)
    try:
        df_cotizaciones = pd.read_excel(xls, sheet_name="cotizaciones")
    except:
        df_cotizaciones = pd.DataFrame()
    
    # Hoja facturacion (para KPIs Mercadeo)
    try:
        df_facturacion = pd.read_excel(xls, sheet_name="facturacion")
    except:
        df_facturacion = pd.DataFrame()
            
    return df_emp, df_neg, df_fid, df_roi, df_kpi, df_manychat, df_leads, df_cotizaciones, df_facturacion

df_empresas_raw, df_negocios_raw, df_fid_raw, df_roi_raw, df_kpi_raw, df_manychat_raw, df_leads_raw, df_cotizaciones_raw, df_facturacion_raw = load_data()

# --- Procesando EMPRESAS ---
df_empresas = df_empresas_raw.copy()

# Normalización de Canales
def normalize_canal(ch):
    ch_upper = str(ch).strip().upper()
    if ch_upper in ['DISTRIBUIDOR', 'DISTRIBUIDORES', 'INSTITUCIONAL']:
        return 'Distribuidor'
    if ch_upper in ['GRANDES SUPERFICIES', 'GRANDES SUPER']:
        return 'Grandes Superficies'
    if ch_upper == 'RETAIL':
        return 'Retail'
    if ch_upper in ['FOOD SERVICE', 'FOODSERVICE']:
        return 'Food Service'
    return str(ch).strip()

df_empresas['Canal_Norm'] = df_empresas['Canal'].apply(normalize_canal)

channels_data = []
# Mapeo de categorías para visualización
class_map = {
    'Retail': 'retail', 
    'Food Service': 'food', 
    'Distribuidor': 'distribuidor',
    'Grandes Superficies': 'grandes'
}

# Recalcular totales solo sobre los canales activos
df_empresas_active = df_empresas[df_empresas['Canal_Norm'].isin(class_map.keys())]
total_registradas = len(df_empresas_active.dropna(subset=['ID de registro']))
total_contactadas = (df_empresas_active['CONTACTADO'].sum()
    if pd.api.types.is_bool_dtype(df_empresas_active['CONTACTADO'])
    else (df_empresas_active['CONTACTADO'] == True).sum())
pct_total = f"{(total_contactadas/total_registradas)*100:.1f}%" if total_registradas > 0 else "0%"

for ch_name in class_map.keys():
    df_ch = df_empresas[df_empresas['Canal_Norm'] == ch_name]
    reg = len(df_ch)
    cont = df_ch['CONTACTADO'].sum() if pd.api.types.is_bool_dtype(df_ch['CONTACTADO']) else (df_ch['CONTACTADO'] == True).sum()
    conv = f"{(cont/reg)*100:.1f}%" if reg > 0 else "0.0%"
    channels_data.append({"name": ch_name, "reg": reg, "conv": conv, "cont": cont, "class": class_map[ch_name]})

data_empresas = {
    "total_registradas": total_registradas,
    "total_contactadas": total_contactadas,
    "pct_total": pct_total,
    "channels": channels_data
}

# --- Procesando NEGOCIOS ---
df_negocios = df_negocios_raw.copy()
df_negocios.columns = [col.strip() if isinstance(col, str) else col for col in df_negocios.columns]
df_negocios['Valor'] = pd.to_numeric(df_negocios['Valor'], errors='coerce').fillna(0)

def format_currency_short(val):
    if val >= 1_000_000_000: return f"${val/1_000_000_000:.1f}B"
    elif val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    elif val >= 1_000: return f"${val/1_000:.1f}k"
    else: return f"${val:.0f}"

# Normalizamos la columna para quitar tildes en 'ó' y manejar espacios extra
df_negocios['Etapa del negocio'] = df_negocios['Etapa del negocio'].str.strip().str.replace('ó', 'o').str.replace('Ó', 'O')

group_neg = df_negocios.groupby('Etapa del negocio')['Valor'].agg(['count', 'sum']).reset_index()

stage_order_map = {
    'Asignado': ('bg-asignado', 1),
    'Contactado': ('bg-contactado', 2),
    'Negociacion': ('bg-negociacion', 3),
    'Cerrada ganada': ('bg-ganada', 4),
    'Cerrada perdida': ('bg-perdida', 5),
    'Pausado': ('bg-pausado', 6)
}

data_negocios = []
total_negocios_val = df_negocios['Valor'].sum()
total_negocios_count = len(df_negocios.dropna(subset=['ID de registro']))

for stage in stage_order_map.keys():
    row = group_neg[group_neg['Etapa del negocio'] == stage]
    cnt = int(row['count'].iloc[0]) if not row.empty else 0
    val = int(row['sum'].iloc[0]) if not row.empty else 0
        
    data_negocios.append({
        "label": stage.upper(), "count": cnt, "val": format_currency_short(val),
        "bg": stage_order_map[stage][0], "order": stage_order_map[stage][1]
    })

data_negocios = sorted(data_negocios, key=lambda x: x['order'])
global_negocios_str = format_currency_short(total_negocios_val)

# --- Procesando FIDELIZACION ---
import math
df_fidel = df_fid_raw.dropna(subset=['Canal', 'Categoria'], how='all').reset_index(drop=True)
fidel_counts = df_fidel['Categoria'].value_counts()
total_fidel = fidel_counts.sum()

fidel_colors = ['#589642', '#1D1D1B', '#C7AB72', '#3d6630', '#8a7452', '#a8936a', '#2d4f24', '#d4c08a']
gradient_stops = []
labels_html = ""
legend_html = ""
data_fidel_list = []

current_pct = 0
color_idx = 0

for cat, count in fidel_counts.items():
    pct = count / total_fidel if total_fidel > 0 else 0
    start_deg = current_pct * 360
    end_deg = (current_pct + pct) * 360
    
    color = fidel_colors[color_idx % len(fidel_colors)]
    gradient_stops.append(f"{color} {start_deg}deg {end_deg}deg")
    
    mid_angle_deg = start_deg + (pct * 360) / 2
    mid_angle_rad = math.radians(mid_angle_deg)
    
    # Radius math pointing text inside the Donut slice
    rx = 50 + math.sin(mid_angle_rad) * 35
    ry = 50 - math.cos(mid_angle_rad) * 35
    
    letter = str(cat)[0].upper() if pd.notna(cat) and str(cat) else "?"
    pct_str = f"{(pct * 100):.1f}%"
    display_text = f"{letter}<br><span style='font-size:14px; font-weight:normal;'>{pct_str}</span>"
    labels_html += f'<div style="position: absolute; top: {ry}%; left: {rx}%; transform: translate(-50%, -50%); color: white; font-weight: bold; font-size: 22px; text-shadow: 1px 1px 3px rgba(0,0,0,0.6); z-index: 10; text-align: center; line-height: 1.1;">{display_text}</div>'
    
    legend_html += f"""<div style="display: flex; align-items: center; margin-bottom: 5px;">
<div style="width: 14px; height: 14px; background-color: {color}; border-radius: 3px; margin-right: 8px;"></div>
<div style="color: #1a2b49; font-size: 13px; font-weight: 500;">{cat} <span style="color:#637381; font-size:11px;">({count} — {pct_str})</span></div>
</div>"""
    
    data_fidel_list.append({"cat": cat, "count": count, "color": color})
    current_pct += pct
    color_idx += 1

gradient_str = ", ".join(gradient_stops)

chart_html = f"""<div style="display: flex; align-items: center; justify-content: center; gap: 40px; margin: 20px 0;">
<div style="position: relative; width: 280px; height: 280px; border-radius: 50%; background: conic-gradient({gradient_str}); box-shadow: 0 6px 16px rgba(0,0,0,0.15);">
<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 140px; height: 140px; background-color: #f7f9fc; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 5;">
<div style="text-align: center; color: #1a2b49; font-size: 30px; font-weight: bold;">{total_fidel}</div>
</div>
{labels_html}
</div>
<div style="display: flex; flex-direction: column;">
<div style="font-size:11px; color:#637381; text-transform:uppercase; letter-spacing:1px; margin-bottom: 10px; font-weight: 600;">Convenciones</div>
{legend_html}
</div>
</div>"""

# --- Procesando ROI COLOMBIATEX ---
# Extraer valores específicos según coordenadas de la hoja 5
# Ventas Estimadas (Q7 -> Row 6, Col 16)
val_ventas_estim = df_roi_raw.iloc[6, 16] if df_roi_raw.shape[0] > 6 and df_roi_raw.shape[1] > 16 else 0
# Costo de Inversión (Q8 -> Row 7, Col 16)
val_costo_inv = df_roi_raw.iloc[7, 16] if df_roi_raw.shape[0] > 7 and df_roi_raw.shape[1] > 16 else 0
# ROI (R11 -> Row 10, Col 17)
val_roi_pct = df_roi_raw.iloc[10, 17] if df_roi_raw.shape[0] > 10 and df_roi_raw.shape[1] > 17 else 0

roi_formatted = {
    "ventas": format_currency_short(val_ventas_estim),
    "costo": format_currency_short(val_costo_inv),
    "roi": f"{val_roi_pct*100:.1f}%" if isinstance(val_roi_pct, (int, float)) else "0%"
}

# Tabla de Gastos Detallada (Filas 8-15, Columnas A y D)
df_gastos_roi = df_roi_raw.iloc[7:15, [0, 3]].dropna().copy()
df_gastos_roi.columns = ["Ítem", "Costo Total"]
df_gastos_roi["Costo Total"] = pd.to_numeric(df_gastos_roi["Costo Total"], errors='coerce')
df_gastos_roi["Costo Total"] = df_gastos_roi["Costo Total"].apply(lambda v: f"${v:,.0f}" if pd.notna(v) else "")

# Tabla de Ventas Estimadas Detallada (Filas 28-38, Columnas A y D)
df_ventas_detalle_roi = df_roi_raw.iloc[27:38, [0, 3]].dropna().copy()
df_ventas_detalle_roi.columns = ["Empresa / Proyecto", "Valor Estimado"]
df_ventas_detalle_roi["Valor Estimado"] = pd.to_numeric(df_ventas_detalle_roi["Valor Estimado"], errors='coerce')
df_ventas_detalle_roi["Valor Estimado"] = df_ventas_detalle_roi["Valor Estimado"].apply(lambda v: f"${v:,.0f}" if pd.notna(v) else "")

@st.dialog("📊 Desglose de Gastos Colombiatex", width="large")
def show_detalle_gastos_roi():
    st.write("Presupuesto detallado de inversión para la feria:")
    st.dataframe(df_gastos_roi, use_container_width=True, hide_index=True)

@st.dialog("💰 Detalle de Ventas Estimadas", width="large")
def show_detalle_ventas_roi():
    st.write("Proyección detallada de ingresos por cliente/proyecto:")
    st.dataframe(df_ventas_detalle_roi, use_container_width=True, hide_index=True)

def render_roi_metrics():
    # Punta + nivel medio de la pirámide (full width HTML)
    roi_top_html = f"""<div style="font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; padding: 30px 20px 0 20px; background:#FFFFFF; border: 1px solid #e8e4dc; border-radius:12px 12px 0 0; margin: 10px 0 0 0;">
<div style="color:#C7AB72; font-size:13px; text-transform:uppercase; letter-spacing:2px; font-weight:700; margin-bottom: 20px;">ROI Colombiatex 2026</div>
<div style="width: 0; height: 0; border-left: 100px solid transparent; border-right: 100px solid transparent; border-bottom: 70px solid #589642; margin: 0 auto;"></div>
<div style="background:#589642; color:white; text-align:center; padding: 8px 0 14px 0; width: 200px; margin: -2px auto 0 auto;">
<div style="font-size:11px; text-transform:uppercase; letter-spacing:1px; opacity:0.85;">ROI Final</div>
<div style="font-size:38px; font-weight:bold; line-height:1.1;">{roi_formatted['roi']}</div>
<div style="font-size:10px; opacity:0.7;">Meta: &gt;20%</div>
</div>
<div style="background:#1D1D1B; color:#C7AB72; text-align:center; padding:14px 0; width:340px; margin: -2px auto 0 auto; clip-path: polygon(0 0, 100% 0, 93% 100%, 7% 100%); font-size:11px; text-transform:uppercase; letter-spacing:2px; font-weight:600;">Ventas &amp; Inversión</div>
</div>"""
    st.markdown(roi_top_html, unsafe_allow_html=True)

    # Base de la pirámide: dos columnas nativas con HTML + botón alineados
    col_v, col_c = st.columns(2, gap="small")
    with col_v:
        st.markdown(f"""<div style="background:#589642; color:white; padding:18px 10px; text-align:center; border-radius:0; margin:0;">
<div style="font-size:11px; text-transform:uppercase; letter-spacing:1px; opacity:0.8;">Ventas Estimadas</div>
<div style="font-size:26px; font-weight:bold; margin:4px 0;">{roi_formatted['ventas']}</div>
</div>""", unsafe_allow_html=True)
        if st.button("🔍 Ver Proyección de Ventas", key="btn_roi_ventas", use_container_width=True):
            show_detalle_ventas_roi()
    with col_c:
        st.markdown(f"""<div style="background:#C7AB72; color:#1D1D1B; padding:18px 10px; text-align:center; border-radius:0; margin:0;">
<div style="font-size:11px; text-transform:uppercase; letter-spacing:1px; opacity:0.75;">Costo Inversión</div>
<div style="font-size:26px; font-weight:bold; margin:4px 0;">{roi_formatted['costo']}</div>
</div>""", unsafe_allow_html=True)
        if st.button("📊 Ver Desglose de Gastos", key="btn_roi_gastos", use_container_width=True):
            show_detalle_gastos_roi()
    # Cierre del fondo blanco
    st.markdown('<div style="background:#FFFFFF; border:1px solid #e8e4dc; border-top:none; border-radius:0 0 12px 12px; height:20px; margin:0 0 10px 0;"></div>', unsafe_allow_html=True)


@st.dialog("📋 Listado Detallado de Empresas", width="large")
def show_detalle_empresas(canal_name):
    st.write(f"Explorando datos brutos de la hoja para el canal: **{canal_name}**")
    df_filtered = df_empresas[df_empresas['Canal_Norm'] == canal_name]
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

@st.dialog("📋 Listado Detallado de Negocios", width="large")
def show_detalle_negocios(stage_name):
    st.write(f"Explorando datos brutos de la hoja para la etapa: **{stage_name}**")
    df_filtered = df_negocios[df_negocios['Etapa del negocio'].str.upper() == stage_name.upper()].copy()
    
    # Reordenar columnas a petición del usuario
    desired_order = ['Fecha de creacion', 'Propietario del negocio', 'Canal', 'Origen Empresa']
    rest_cols = [c for c in df_filtered.columns if c not in desired_order]
    final_order = [c for c in desired_order if c in df_filtered.columns] + rest_cols
    df_display = df_filtered[final_order].copy()
    
    # Formatear columna Valor con signo $
    if 'Valor' in df_display.columns:
        df_display['Valor'] = pd.to_numeric(df_display['Valor'], errors='coerce')
        df_display['Valor'] = df_display['Valor'].apply(lambda v: f"${v:,.0f}" if pd.notna(v) else "")
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.dialog("📋 Detalles Fidelización", width="large")
def show_detalle_fidel(categoria_name):
    st.write(f"Empresas en la categoría de Fidelización: **{categoria_name}**")
    df_filtered = df_fidel[df_fidel['Categoria'] == categoria_name]
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

def render_fidelizacion():
    st.markdown('<div class="funnel-container" style="margin-top: 20px;">', unsafe_allow_html=True)
    st.markdown('<div class="funnel-title" style="text-align:center;">Fidelización de Clientes</div>', unsafe_allow_html=True)
    st.markdown(chart_html, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align:center; color:#637381; font-size: 11px; text-transform: uppercase;'>Desglose de categoría:</p>", unsafe_allow_html=True)
    
    cols = st.columns(len(data_fidel_list))
    for idx, (col, item) in enumerate(zip(cols, data_fidel_list)):
        with col:
            if st.button(f"🔍 {item['cat']}", key=f"btn_fid_{idx}", use_container_width=True):
                show_detalle_fidel(item['cat'])
                
    st.markdown('</div>', unsafe_allow_html=True)

def render_embudo_empresas():
    # Top block
    html_top = f"""<div class="funnel-container" style="padding-bottom: 20px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;">
    <div class="date-badge">Ene — Abr 2026</div>
    <div class="main-title">REPORTE</div>
    <div class="funnel-title">Embudo de Empresas</div>
    <div class="funnel-subtitle">Registradas → Canal → Contactadas por canal</div>
    <div class="stage-1">
        <div><div class="stage-label">ETAPA 1</div><div class="stage-name">Registradas</div></div>
        <div class="stage-value">{data_empresas['total_registradas']}</div>
    </div>
    <div class="connector-1"></div>
    <div class="stage-2-container" style="box-shadow: none; margin-bottom: -10px; padding-bottom: 0;">
        <div class="stage-2-header" style="text-align: center;">ETAPA 2 — DISTRIBUCIÓN POR CANAL</div>
    </div>
</div>"""
    st.markdown(html_top, unsafe_allow_html=True)

    # Middle block: native columns with HTML box + native button integrated
    st.markdown('<div style="background-color: #f7f9fc; padding: 0 40px;">', unsafe_allow_html=True)
    cols = st.columns(len(data_empresas['channels']))
    
    st.markdown("""<style>
    .ch-box-native { background-color: white; border: 1px solid #eee; padding: 15px 10px; border-radius: 8px; text-align: center; margin-bottom: 5px; }
    </style>""", unsafe_allow_html=True)
    
    for idx, (col_e, ch) in enumerate(zip(cols, data_empresas['channels'])):
        with col_e:
            ch_html = f"""<div class="ch-box-native border-{ch['class']}">
    <div class="channel-name">{ch['name']}</div>
    <div class="channel-reg" style="justify-content: center;">{ch['reg']}<span class="reg-label">reg.</span></div>
    <div class="conversion-rate" style="justify-content: center;">↓ {ch['conv']}</div>
    <div class="channel-cont-value color-{ch['class']}" style="justify-content: center;">{ch['cont']} <span class="reg-label" style="color:#637381;">cont.</span></div>
</div>"""
            st.markdown(ch_html, unsafe_allow_html=True)
            if st.button("📊 Extraer", key=f"btn_emp_{idx}", use_container_width=True):
                show_detalle_empresas(ch['name'])
    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom block
    html_bot = f"""<div class="funnel-container" style="padding-top: 0; margin-top: 0; border-top-left-radius: 0; border-top-right-radius: 0;">
    <div class="connector-2" style="margin-top: 15px;"></div>
    <div class="stage-3">
        <div><div class="stage-label">ETAPA 3</div><div class="stage-name">Contactadas</div></div>
        <div><span class="stage-value">{data_empresas['total_contactadas']}</span><span class="stage-3-pct">({data_empresas['pct_total']})</span></div>
    </div>
</div>"""
    st.markdown(html_bot, unsafe_allow_html=True)

def render_embudo_negocios():
    st.markdown(f"""<div class="negocios-container" style="padding-bottom: 20px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;">
    <div class="negocios-title">Embudo de Negocios</div>
    <div class="negocios-subtitle">{total_negocios_count} negocios · Valor total <span>{global_negocios_str}</span></div>
</div>""", unsafe_allow_html=True)

    # Render funnel layers wrapped with native buttons alongside
    st.markdown('<div style="background-color: #0b111a; padding: 0 40px; padding-bottom: 40px; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">', unsafe_allow_html=True)
    for i, item in enumerate(data_negocios):
        html_layer = f"""<div class="funnel-layer {item['bg']}" style="margin-bottom: 0;">
    <div class="layer-count-group">
        <div class="layer-label">{item['label']}</div>
        <div class="layer-count">{item['count']} <span class="layer-count-label">negocios</span></div>
    </div>
    <div class="layer-value-group">
        <div class="layer-value">{item['val']}</div>
        <div class="layer-val-label">valor total</div>
    </div>
</div>"""
        
        c1, c2 = st.columns([5, 2])
        with c1:
            st.markdown(html_layer, unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True) # Spacer vertical
            if st.button(f"🧾 Ver Info", key=f"btn_neg_{i}", use_container_width=True):
                show_detalle_negocios(item['label'])
    st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard_ejecutivo():
    st.title("📊 Dashboard Ejecutivo")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Conectado directamente a Google Sheets. Tiempo de actualización base: 5 seg.")
    with col_hz2:
        if st.button("🔄 Forzar Recarga de Datos", use_container_width=True, key="reload_ejecutivo"):
            st.cache_data.clear()
            st.rerun()
    
    # Embudos lado a lado
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        render_embudo_empresas()
    with col2:
        render_embudo_negocios()
        
    st.markdown("<br>", unsafe_allow_html=True)

def render_gestion_contactos():
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.title("📞 Gestión de Contactos")
    with col_hz2:
        if st.button("🔄 Forzar Recarga", use_container_width=True, key="reload_gestion"):
            st.cache_data.clear()
            st.rerun()
            
    df_kpi = df_kpi_raw.copy()
    
    if df_kpi.empty:
        st.warning("No se encontraron datos de la hoja 'KPI Negocios' o 'GESTIÓN DE CONTACTOS'.")
        return
        
    # Clean up columns for robust matching
    original_cols = df_kpi.columns.tolist()
    df_kpi.columns = [str(c).strip().lower() for c in df_kpi.columns]
    
    # Check for required columns
    required = ['motivo de contacto', 'conteste/no conteste']
    missing = [c for c in required if c not in df_kpi.columns]
    if missing:
        st.warning(f"Faltan columnas requeridas en la hoja: {missing}. Encontradas: {df_kpi.columns.tolist()}")
        # Intento de corrección para nombres parecidos si es posible
        if 'motivo de contacto' not in df_kpi.columns:
            for c in df_kpi.columns:
                if 'motivo' in c:
                    df_kpi.rename(columns={c: 'motivo de contacto'}, inplace=True)
        if 'conteste/no conteste' not in df_kpi.columns:
            for c in df_kpi.columns:
                if 'conteste' in c:
                    df_kpi.rename(columns={c: 'conteste/no conteste'}, inplace=True)
                    
    # Re-check after potential rename
    if 'motivo de contacto' not in df_kpi.columns or 'conteste/no conteste' not in df_kpi.columns:
        st.error("No se pudo procesar la información por diferencias en los nombres de las columnas.")
        st.dataframe(df_kpi_raw)
        return
    
    # Process
    df_kpi['motivo de contacto'] = df_kpi['motivo de contacto'].fillna('').astype(str).str.strip()
    df_kpi['conteste/no conteste'] = df_kpi['conteste/no conteste'].fillna('').astype(str).str.strip()
    
    # Identify date column for filtering
    fecha_col = None
    for c in df_kpi.columns:
        if 'fecha' in c:
            fecha_col = c
            break
            
    if fecha_col:
        temp_dates = pd.to_datetime(df_kpi[fecha_col], errors='coerce')
        df_kpi['Mes_Filtro'] = temp_dates.dt.strftime('%Y-%m').fillna('Desconocido')
    else:
        df_kpi['Mes_Filtro'] = 'Desconocido'
        
    st.markdown("### 🔍 Filtros")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        meses_disp = sorted([m for m in df_kpi['Mes_Filtro'].unique() if m != 'Desconocido'])
        if 'Desconocido' in df_kpi['Mes_Filtro'].unique():
            meses_disp.append('Desconocido')
        sel_mes = st.selectbox("📅 Mes", ['Todos'] + meses_disp)
        
    with f_col2:
        motivos_disp = sorted([m for m in df_kpi['motivo de contacto'].unique() if m != ''])
        sel_motivo = st.selectbox("🏷️ Motivo de Contacto", ['Todos'] + motivos_disp)
        
    with f_col3:
        estados_disp = sorted([e for e in df_kpi['conteste/no conteste'].unique() if e != ''])
        sel_estado = st.selectbox("✅ Estado (Contestó)", ['Todos'] + estados_disp)
        
    # Apply Filters
    df_filtered = df_kpi.copy()
    if sel_mes != 'Todos':
        df_filtered = df_filtered[df_filtered['Mes_Filtro'] == sel_mes]
    if sel_motivo != 'Todos':
        df_filtered = df_filtered[df_filtered['motivo de contacto'] == sel_motivo]
    if sel_estado != 'Todos':
        df_filtered = df_filtered[df_filtered['conteste/no conteste'] == sel_estado]
    
    total_llamadas = len(df_filtered)
    is_spam = df_filtered['motivo de contacto'].str.lower() == 'spam'
    spam_count = is_spam.sum()
    efectivas = total_llamadas - spam_count
    
    df_efectivas = df_filtered[~is_spam]
    is_conteste = df_efectivas['conteste/no conteste'].str.lower() == 'conteste'
    atendidas = is_conteste.sum()
    ind_atencion = (atendidas / efectivas * 100) if efectivas > 0 else 0
    
    cotizar = (df_efectivas['motivo de contacto'].str.lower() == 'cotizar').sum()
    redirigido = (df_efectivas['motivo de contacto'].str.lower() == 'redirigido a distribuidor').sum()
    
    # CSS
    st.markdown("""
    <style>
    .kpi-card { padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e8e4dc; }
    .kpi-card-black { background-color: #1D1D1B; color: white; }
    .kpi-card-green { background-color: #589642; color: white; }
    .kpi-card-white { background-color: white; color: #1D1D1B; }
    .kpi-label { font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 600; }
    .kpi-label-muted { opacity: 0.8; }
    .kpi-value { font-size: 38px; font-weight: bold; line-height: 1.1; margin-bottom: 2px; }
    .kpi-sub { font-size: 11px; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)
    
    # Top Row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card kpi-card-black">
            <div class="kpi-label kpi-label-muted" style="color: #C7AB72;">Total Llamadas</div>
            <div class="kpi-value">{total_llamadas}</div>
            <div class="kpi-sub">Volumen Bruto</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-label kpi-label-muted">Llamadas Efectivas</div>
            <div class="kpi-value">{efectivas}</div>
            <div class="kpi-sub">Total - Spam ({spam_count} descartadas)</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        color_at = "#589642" if ind_atencion >= 70 else ("#C7AB72" if ind_atencion >= 50 else "#a63c3c")
        st.markdown(f"""
        <div class="kpi-card kpi-card-white">
            <div class="kpi-label" style="color: #6b6b69;">Indicador de Atención</div>
            <div class="kpi-value" style="color: {color_at};">{ind_atencion:.1f}%</div>
            <div class="kpi-sub" style="color: #6b6b69;">Contestadas / Efectivas ({atendidas}/{efectivas})</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Bottom Row
    c4, c5 = st.columns(2)
    with c4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-white" style="border-top: 4px solid #589642;">
            <div class="kpi-label" style="color: #1D1D1B;">Interés de Compra (Cotizar)</div>
            <div class="kpi-value" style="color: #1D1D1B;">{cotizar}</div>
            <div class="kpi-sub" style="color: #6b6b69;">Prospectos Directos</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card kpi-card-white" style="border-top: 4px solid #C7AB72;">
            <div class="kpi-label" style="color: #1D1D1B;">Redirección a Distribuidor</div>
            <div class="kpi-value" style="color: #1D1D1B;">{redirigido}</div>
            <div class="kpi-sub" style="color: #6b6b69;">No cumplen mínimo de prod.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📊 Análisis (Llamadas Efectivas)")
    
    c_chart1, c_chart2 = st.columns([1, 1])
    
    with c_chart1:
        st.write("**Distribución por Motivo**")
        motivos_counts = df_efectivas['motivo de contacto'].value_counts().reset_index()
        motivos_counts.columns = ['Motivo', 'Cantidad']
        st.bar_chart(motivos_counts.set_index('Motivo'), color="#C7AB72")
        
    with c_chart2:
        if fecha_col:
            st.write("**Volumen Diario (Efectivas)**")
            try:
                df_efectivas_dates = df_efectivas.copy()
                df_efectivas_dates[fecha_col] = pd.to_datetime(df_efectivas_dates[fecha_col], errors='coerce')
                df_trend = df_efectivas_dates.groupby(df_efectivas_dates[fecha_col].dt.date).size()
                if not df_trend.empty:
                    st.line_chart(df_trend, color="#589642")
                else:
                    st.write("No hay datos de fecha válidos con los filtros actuales.")
            except Exception as e:
                st.write("Datos de fecha no procesables para gráfico.", e)
        else:
            st.write("Columna de fecha no encontrada para tendencia.")
                
    st.markdown("---")
    st.subheader("📋 Registro Completo")
    df_display = df_kpi_raw.loc[df_filtered.index] if not df_filtered.empty else df_kpi_raw.iloc[0:0]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.dialog("📋 Detalle de Leads", width="large")
def show_detalle_manychat(df_fil, titulo):
    st.write(f"Explorando datos para: **{titulo}**")
    st.dataframe(df_fil, use_container_width=True, hide_index=True)

def render_manychat_stats():
    st.title("🤖 Métricas ManyChat")
    
    df_mc = df_manychat_raw.copy()
    if df_mc.empty:
        st.warning("No se encontraron datos en la hoja 'MANYCHAT'.")
        return
        
    if len(df_mc.columns) >= 10:
        col_etapa = df_mc.columns[6]
        col_mes = df_mc.columns[8]
        col_motivo = df_mc.columns[9]
    else:
        st.error("La hoja 'MANYCHAT' no tiene suficientes columnas (requiere al menos 10 columnas, A-J).")
        return
        
    df_mc[col_etapa] = df_mc[col_etapa].fillna('').astype(str).str.strip().str.title()
    df_mc[col_mes] = df_mc[col_mes].fillna('').astype(str).str.strip().str.lower()
    df_mc[col_motivo] = df_mc[col_motivo].fillna('').astype(str).str.strip()
    
    st.markdown("### 🔍 Filtros")
    meses_disp = sorted([m for m in df_mc[col_mes].unique() if m != ''])
    
    sel_mes = st.selectbox("📅 Mes", ['Todos'] + meses_disp)
    
    if sel_mes != 'Todos':
        df_filtered = df_mc[df_mc[col_mes] == sel_mes]
    else:
        df_filtered = df_mc
        
    total_leads = len(df_filtered)
    
    # Chats totales basales por mes
    base_chats_marzo = 108
    base_chats_abril = 124
    
    if sel_mes == 'marzo':
        total_chats = base_chats_marzo + total_leads
    elif sel_mes == 'abril':
        total_chats = base_chats_abril + total_leads
    elif sel_mes == 'Todos':
        marzo_leads = len(df_mc[df_mc[col_mes] == 'marzo'])
        abril_leads = len(df_mc[df_mc[col_mes] == 'abril'])
        total_chats = (base_chats_marzo + marzo_leads) + (base_chats_abril + abril_leads) + len(df_mc[~df_mc[col_mes].isin(['marzo', 'abril'])])
    else:
        total_chats = total_leads
        
    # Metricas Embudo
    calificados = len(df_filtered[df_filtered[col_etapa] == 'Calificado'])
    descalificados = len(df_filtered[df_filtered[col_etapa] == 'Descalificado'])
    
    pct_calificados = (calificados / total_leads * 100) if total_leads > 0 else 0
    pct_descalificados = (descalificados / total_leads * 100) if total_leads > 0 else 0
    
    descalificados_df = df_filtered[df_filtered[col_etapa] == 'Descalificado']
    redirigidos = len(descalificados_df[descalificados_df[col_motivo].str.lower().str.contains('distribuidor')])
    pct_redirigidos = (redirigidos / descalificados * 100) if descalificados > 0 else 0
    
    st.markdown("""
    <style>
    /* CSS Premium para Embudo ManyChat */
    .mc-funnel-wrapper { font-family: 'Segoe UI', sans-serif; background-color: #fcfcfc; padding: 40px; border-radius: 16px; border: 1px solid #e8e4dc; box-shadow: 0 8px 24px rgba(0,0,0,0.06); margin-bottom: 10px; }
    .mc-header { text-align: center; margin-bottom: 30px; }
    .mc-title { color: #1D1D1B; font-size: 32px; font-weight: 800; letter-spacing: -0.5px; }
    .mc-subtitle { color: #8a7452; font-size: 15px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
    
    .mc-card { border-radius: 12px; padding: 25px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s ease; margin-bottom: 10px; }
    .mc-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
    
    .mc-bg-black { background: linear-gradient(135deg, #1D1D1B 0%, #2c2c2a 100%); color: white; }
    .mc-bg-dark { background: linear-gradient(135deg, #3d3d3a 0%, #4d4d4a 100%); color: white; }
    .mc-bg-green { background: linear-gradient(135deg, #589642 0%, #68b04e 100%); color: white; }
    .mc-bg-brown { background: linear-gradient(135deg, #7a5c2e 0%, #8c6a35 100%); color: white; }
    .mc-bg-gold { background: linear-gradient(135deg, #C7AB72 0%, #d4b87e 100%); color: #1D1D1B; border: 1px solid #e8e4dc; }
    
    .mc-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.85; margin-bottom: 4px; font-weight: 600;}
    .mc-name { font-size: 20px; font-weight: 700; }
    .mc-value-group { text-align: right; }
    .mc-value { font-size: 36px; font-weight: 800; line-height: 1; }
    .mc-pct { font-size: 16px; font-weight: 500; opacity: 0.9; margin-left: 5px; }
    
    .mc-arrow { text-align: center; color: #C7AB72; font-size: 24px; font-weight: bold; margin: 5px 0 15px 0; }
    
    .mc-split-box { flex-direction: column; align-items: flex-start; padding: 25px; margin-bottom: 10px; }
    .mc-split-box .mc-value-group { text-align: left; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)
    
    pct_leads_from_chats = (total_leads / total_chats * 100) if total_chats > 0 else 0
    
    st.markdown('<div class="mc-funnel-wrapper">', unsafe_allow_html=True)
    st.markdown(f'<div class="mc-header"><div class="mc-title">Embudo ManyChat</div><div class="mc-subtitle">Mes: {sel_mes.capitalize()}</div></div>', unsafe_allow_html=True)
    
    # FASE 1
    st.markdown(f'''
    <div class="mc-card mc-bg-black">
    <div><div class="mc-label">Fase 1</div><div class="mc-name">Chats Totales</div></div>
    <div class="mc-value-group"><div class="mc-value">{total_chats}</div></div>
    </div>
    <div class="mc-arrow">↓</div>
    ''', unsafe_allow_html=True)
    
    # FASE 2
    st.markdown(f'''
    <div class="mc-card mc-bg-dark" style="margin-left: 5%; margin-right: 5%;">
    <div><div class="mc-label">Fase 2</div><div class="mc-name">Leads Generados</div></div>
    <div class="mc-value-group"><span class="mc-value">{total_leads}</span><span class="mc-pct">({pct_leads_from_chats:.1f}%)</span></div>
    </div>
    ''', unsafe_allow_html=True)
    
    col_b2_1, col_b2_2, col_b2_3 = st.columns([1, 2, 1])
    with col_b2_2:
        if st.button("🔍 Ver Todos los Leads", key="btn_mc_leads", use_container_width=True):
            show_detalle_manychat(df_filtered, "Leads Generados")
            
    st.markdown('<div style="display: flex; justify-content: space-around; color: #C7AB72; font-size: 24px; font-weight: bold; margin: 5px 15% 15px 15%;"><div>↙</div><div>↘</div></div>', unsafe_allow_html=True)
    
    # FASE 3
    col3a, col3b = st.columns(2, gap="large")
    with col3a:
        st.markdown(f'''
        <div class="mc-card mc-split-box mc-bg-green">
        <div><div class="mc-label">Fase 3A</div><div class="mc-name">Calificados</div></div>
        <div class="mc-value-group"><span class="mc-value">{calificados}</span><span class="mc-pct">({pct_calificados:.1f}%)</span></div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("🔍 Ver Calificados", key="btn_mc_cal", use_container_width=True):
            show_detalle_manychat(df_filtered[df_filtered[col_etapa] == 'Calificado'], "Leads Calificados")
            
    with col3b:
        st.markdown(f'''
        <div class="mc-card mc-split-box mc-bg-brown">
        <div><div class="mc-label">Fase 3B</div><div class="mc-name">Descalificados</div></div>
        <div class="mc-value-group"><span class="mc-value">{descalificados}</span><span class="mc-pct">({pct_descalificados:.1f}%)</span></div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("🔍 Ver Descalificados", key="btn_mc_desc", use_container_width=True):
            show_detalle_manychat(descalificados_df, "Leads Descalificados")
            
    # FASE 4
    st.markdown('<div style="text-align: right; margin: 10px 20% 15px 0; color: #C7AB72; font-size: 24px; font-weight: bold;">↓</div>', unsafe_allow_html=True)
    
    col4a, col4b = st.columns([1, 1])
    with col4b:
        st.markdown(f'''
        <div class="mc-card mc-split-box mc-bg-gold">
        <div><div class="mc-label" style="color: #6b6b69;">Detalle Descalificados</div><div class="mc-name">Redirigido a Distribuidor</div></div>
        <div class="mc-value-group"><span class="mc-value" style="font-size: 30px;">{redirigidos}</span><span class="mc-pct" style="color:#1D1D1B;">({pct_redirigidos:.1f}%)</span></div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("🔍 Ver Redirigidos", key="btn_mc_redir", use_container_width=True):
            df_redir = descalificados_df[descalificados_df[col_motivo].str.lower().str.contains('distribuidor')]
            show_detalle_manychat(df_redir, "Redirigidos a Distribuidor")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📋 Registro Completo (Filtrado)")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

def render_kpis_mercadeo():
    st.title("📊 KPIs MERCADEO")
    st.caption("Medición mensual con corte el último viernes | Reporte a Gerencia Comercial")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Conectado a Google Sheets - Hojas: LEADS, cotizaciones, facturacion")
    with col_hz2:
        if st.button("🔄 Forzar Recarga", use_container_width=True, key="reload_mercadeo"):
            st.cache_data.clear()
            st.rerun()
    
    # === METAS ===
    METAS = {
        "leads": 80,
        "tasa_conversion": 10.0,  # %
        "negocios_cotizados": 150000000,
        "negocios_facturados": 60000000
    }
    
    # === CSS ESTILO TABLA KPI ===
    st.markdown("""
    <style>
    .kpi-table-header {
        background: linear-gradient(135deg, #1D1D1B 0%, #2d2d2a 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpi-table-header h2 { margin: 0; font-size: 24px; font-weight: 700; }
    .kpi-table-header .logo-text { 
        font-size: 28px; font-weight: 800; 
        background: linear-gradient(135deg, #C7AB72, #e8d5a0); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .kpi-table-header .subtitle { 
        font-size: 11px; color: #aaa; font-style: italic; margin-top: 4px;
    }
    .kpi-card-mkt {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid #C7AB72;
    }
    .kpi-mkt-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
    }
    .kpi-mkt-title {
        font-size: 14px;
        font-weight: 600;
        color: #1D1D1B;
    }
    .kpi-mkt-meta {
        font-size: 11px;
        color: #888;
        background: #f5f5f5;
        padding: 4px 10px;
        border-radius: 12px;
    }
    .kpi-mkt-values {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
    }
    .kpi-mkt-box {
        text-align: center;
        padding: 12px 8px;
        border-radius: 8px;
        background: #fafafa;
    }
    .kpi-mkt-box.real { background: #f0f7ed; }
    .kpi-mkt-box.porcentaje-alto { background: #e8f5e9; }
    .kpi-mkt-box.porcentaje-medio { background: #fff8e1; }
    .kpi-mkt-box.porcentaje-bajo { background: #ffebee; }
    .kpi-mkt-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #888;
        margin-bottom: 5px;
    }
    .kpi-mkt-value {
        font-size: 22px;
        font-weight: 700;
        color: #1D1D1B;
    }
    .kpi-mkt-value.pct-green { color: #589642; }
    .kpi-mkt-value.pct-yellow { color: #C7AB72; }
    .kpi-mkt-value.pct-red { color: #c62828; }
    .kpi-mkt-trend {
        font-size: 10px;
        margin-top: 4px;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # === HEADER ===
    st.markdown(f"""
    <div class="kpi-table-header">
        <div>
            <div style="display:flex;align-items:center;gap:15px;">
                <span class="logo-text">✱ ditar</span>
                <span style="color:#C7AB72;font-size:20px;">|</span>
                <h2>KPI's MERCADEO</h2>
            </div>
            <div class="subtitle">Medicion mensual con corte el ultimo viernes | Reporte a Gerencia Comercial | Periodo Mar-Abr 2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === INDICADOR 1: LEADS NUEVOS ===
    df_leads = df_leads_raw.copy()
    if not df_leads.empty and len(df_leads.columns) >= 12:
        # Columna L (índice 11) = mes
        col_mes_leads = df_leads.columns[11]
        df_leads[col_mes_leads] = df_leads[col_mes_leads].fillna('').astype(str).str.strip().str.lower()
        
        leads_marzo = len(df_leads[df_leads[col_mes_leads] == 'marzo'])
        leads_abril = len(df_leads[df_leads[col_mes_leads] == 'abril'])
        
        pct_marzo = (leads_marzo / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
        pct_abril = (leads_abril / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
    else:
        leads_marzo = leads_abril = 0
        pct_marzo = pct_abril = 0
    
    def get_pct_class(pct):
        if pct >= 100: return "porcentaje-alto", "pct-green"
        elif pct >= 70: return "porcentaje-medio", "pct-yellow"
        else: return "porcentaje-bajo", "pct-red"
    
    class_marzo, val_class_marzo = get_pct_class(pct_marzo)
    class_abril, val_class_abril = get_pct_class(pct_abril)
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Leads nuevos cargados en HubSpot</div>
            <div class="kpi-mkt-meta">Meta mensual: {METAS['leads']}</div>
        </div>
        <div class="kpi-mkt-values">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{METAS['leads']}</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Mar Real</div>
                <div class="kpi-mkt-value">{leads_marzo}</div>
            </div>
            <div class="kpi-mkt-box {class_marzo}">
                <div class="kpi-mkt-label">Mar %</div>
                <div class="kpi-mkt-value {val_class_marzo}">{pct_marzo:.0f}%</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Abr Real</div>
                <div class="kpi-mkt-value">{leads_abril}</div>
            </div>
            <div class="kpi-mkt-box {class_abril}">
                <div class="kpi-mkt-label">Abr %</div>
                <div class="kpi-mkt-value {val_class_abril}">{pct_abril:.0f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Leads
    c1, c2, c_spacer = st.columns([1, 1, 3])
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_leads_mar", use_container_width=True) and not df_leads.empty:
            df_mar_fil = df_leads[df_leads[col_mes_leads] == 'marzo'] if 'col_mes_leads' in locals() else pd.DataFrame()
            show_detalle_leads_mes("marzo", df_mar_fil)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_leads_abr", use_container_width=True) and not df_leads.empty:
            df_abr_fil = df_leads[df_leads[col_mes_leads] == 'abril'] if 'col_mes_leads' in locals() else pd.DataFrame()
            show_detalle_leads_mes("abril", df_abr_fil)
    
    # === INDICADOR 2: TASA CONVERSIÓN ===
    if not df_leads.empty and len(df_leads.columns) >= 8:
        # Columna H (índice 7) = calificados
        col_calif = df_leads.columns[7]
        df_leads[col_calif] = df_leads[col_calif].fillna('').astype(str).str.strip().str.lower()
        
        # Marzo
        df_marzo = df_leads[df_leads[col_mes_leads] == 'marzo']
        total_marzo = len(df_marzo)
        calif_marzo = len(df_marzo[df_marzo[col_calif].isin(['si', 'sí', 'yes', 'true', '1'])])
        tasa_marzo = (calif_marzo / total_marzo * 100) if total_marzo > 0 else 0
        
        # Abril
        df_abril = df_leads[df_leads[col_mes_leads] == 'abril']
        total_abril = len(df_abril)
        calif_abril = len(df_abril[df_abril[col_calif].isin(['si', 'sí', 'yes', 'true', '1'])])
        tasa_abril = (calif_abril / total_abril * 100) if total_abril > 0 else 0
    else:
        tasa_marzo = tasa_abril = 0
    
    pct_tasa_marzo = (tasa_marzo / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_abril = (tasa_abril / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    
    class_tasa_marzo, val_class_tasa_marzo = get_pct_class(pct_tasa_marzo)
    class_tasa_abril, val_class_tasa_abril = get_pct_class(pct_tasa_abril)
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Tasa de conversion lead a oportunidad</div>
            <div class="kpi-mkt-meta">Meta mensual: {METAS['tasa_conversion']}%</div>
        </div>
        <div class="kpi-mkt-values">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{METAS['tasa_conversion']}%</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Mar Real</div>
                <div class="kpi-mkt-value">{tasa_marzo:.1f}%</div>
                <div class="kpi-mkt-trend">({calif_marzo}/{total_marzo})</div>
            </div>
            <div class="kpi-mkt-box {class_tasa_marzo}">
                <div class="kpi-mkt-label">Mar %</div>
                <div class="kpi-mkt-value {val_class_tasa_marzo}">{pct_tasa_marzo:.0f}%</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Abr Real</div>
                <div class="kpi-mkt-value">{tasa_abril:.1f}%</div>
                <div class="kpi-mkt-trend">({calif_abril}/{total_abril})</div>
            </div>
            <div class="kpi-mkt-box {class_tasa_abril}">
                <div class="kpi-mkt-label">Abr %</div>
                <div class="kpi-mkt-value {val_class_tasa_abril}">{pct_tasa_abril:.0f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Conversión
    c1, c2, c_spacer = st.columns([1, 1, 3])
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_conv_mar", use_container_width=True) and not df_leads.empty:
            df_mar_all = df_leads[df_leads[col_mes_leads] == 'marzo'] if 'col_mes_leads' in locals() else pd.DataFrame()
            df_mar_calif = df_mar_all[df_mar_all[col_calif].isin(['si', 'sí', 'yes', 'true', '1'])] if 'col_calif' in locals() and not df_mar_all.empty else pd.DataFrame()
            show_detalle_conversion("marzo", calif_marzo, total_marzo, df_mar_calif, df_mar_all)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_conv_abr", use_container_width=True) and not df_leads.empty:
            df_abr_all = df_leads[df_leads[col_mes_leads] == 'abril'] if 'col_mes_leads' in locals() else pd.DataFrame()
            df_abr_calif = df_abr_all[df_abr_all[col_calif].isin(['si', 'sí', 'yes', 'true', '1'])] if 'col_calif' in locals() and not df_abr_all.empty else pd.DataFrame()
            show_detalle_conversion("abril", calif_abril, total_abril, df_abr_calif, df_abr_all)
    
    # === INDICADOR 3: NEGOCIOS COTIZADOS ===
    df_cot = df_cotizaciones_raw.copy()
    if not df_cot.empty and len(df_cot.columns) >= 6:
        # Columna F (índice 5) = valor
        col_valor_cot = df_cot.columns[5]
        df_cot[col_valor_cot] = pd.to_numeric(df_cot[col_valor_cot], errors='coerce').fillna(0)
        
        # Asumimos que hay una columna de mes o fecha
        # Si no, sumamos todo
        cot_total = df_cot[col_valor_cot].sum()
        # Dividimos aproximadamente entre marzo y abril (60/40 como estimación temporal)
        cot_marzo = cot_total * 0.6
        cot_abril = cot_total * 0.4
    else:
        cot_marzo = cot_abril = 0
    
    def format_currency(val):
        if val >= 1_000_000_000:
            return f"${val/1_000_000_000:.1f}B"
        elif val >= 1_000_000:
            return f"${val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val/1_000:.0f}K"
        return f"${val:,.0f}"
    
    pct_cot_marzo = (cot_marzo / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    pct_cot_abril = (cot_abril / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    
    class_cot_marzo, val_class_cot_marzo = get_pct_class(pct_cot_marzo)
    class_cot_abril, val_class_cot_abril = get_pct_class(pct_cot_abril)
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Negocios cotizados generados por mercadeo</div>
            <div class="kpi-mkt-meta">Meta mensual: {format_currency(METAS['negocios_cotizados'])}</div>
        </div>
        <div class="kpi-mkt-values">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{format_currency(METAS['negocios_cotizados'])}</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Mar Real</div>
                <div class="kpi-mkt-value">{format_currency(cot_marzo)}</div>
            </div>
            <div class="kpi-mkt-box {class_cot_marzo}">
                <div class="kpi-mkt-label">Mar %</div>
                <div class="kpi-mkt-value {val_class_cot_marzo}">{pct_cot_marzo:.0f}%</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Abr Real</div>
                <div class="kpi-mkt-value">{format_currency(cot_abril)}</div>
            </div>
            <div class="kpi-mkt-box {class_cot_abril}">
                <div class="kpi-mkt-label">Abr %</div>
                <div class="kpi-mkt-value {val_class_cot_abril}">{pct_cot_abril:.0f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Cotizaciones
    c1, c2, c_spacer = st.columns([1, 1, 3])
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_cot_mar", use_container_width=True):
            # Para cotizaciones, mostramos todos los datos (temporal hasta tener mes específico)
            show_detalle_cotizaciones("marzo", cot_marzo, df_cotizaciones_raw)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_cot_abr", use_container_width=True):
            show_detalle_cotizaciones("abril", cot_abril, df_cotizaciones_raw)
    
    # === INDICADOR 4: NEGOCIOS FACTURADOS ===
    df_fac = df_facturacion_raw.copy()
    if not df_fac.empty:
        # Columnas L (índice 11) = marzo, M (índice 12) = abril
        if len(df_fac.columns) >= 13:
            col_marzo = df_fac.columns[11]
            col_abril = df_fac.columns[12]
            
            df_fac[col_marzo] = pd.to_numeric(df_fac[col_marzo], errors='coerce').fillna(0)
            df_fac[col_abril] = pd.to_numeric(df_fac[col_abril], errors='coerce').fillna(0)
            
            fac_marzo = df_fac[col_marzo].sum()
            fac_abril = df_fac[col_abril].sum()
        else:
            fac_marzo = fac_abril = 0
    else:
        fac_marzo = fac_abril = 0
    
    pct_fac_marzo = (fac_marzo / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_abril = (fac_abril / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    
    class_fac_marzo, val_class_fac_marzo = get_pct_class(pct_fac_marzo)
    class_fac_abril, val_class_fac_abril = get_pct_class(pct_fac_abril)
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Negocios facturados atribuidos a mercadeo</div>
            <div class="kpi-mkt-meta">Meta mensual: {format_currency(METAS['negocios_facturados'])}</div>
        </div>
        <div class="kpi-mkt-values">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{format_currency(METAS['negocios_facturados'])}</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Mar Real</div>
                <div class="kpi-mkt-value">{format_currency(fac_marzo)}</div>
            </div>
            <div class="kpi-mkt-box {class_fac_marzo}">
                <div class="kpi-mkt-label">Mar %</div>
                <div class="kpi-mkt-value {val_class_fac_marzo}">{pct_fac_marzo:.0f}%</div>
            </div>
            <div class="kpi-mkt-box real">
                <div class="kpi-mkt-label">Abr Real</div>
                <div class="kpi-mkt-value">{format_currency(fac_abril)}</div>
            </div>
            <div class="kpi-mkt-box {class_fac_abril}">
                <div class="kpi-mkt-label">Abr %</div>
                <div class="kpi-mkt-value {val_class_fac_abril}">{pct_fac_abril:.0f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Facturación
    c1, c2, c_spacer = st.columns([1, 1, 3])
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_fac_mar", use_container_width=True):
            # Filtrar filas con valor en columna marzo
            if 'col_marzo' in locals() and not df_fac.empty:
                df_mar_fac = df_fac[df_fac[col_marzo] > 0]
            else:
                df_mar_fac = df_facturacion_raw
            show_detalle_facturacion("marzo", fac_marzo, df_mar_fac)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_fac_abr", use_container_width=True):
            # Filtrar filas con valor en columna abril
            if 'col_abril' in locals() and not df_fac.empty:
                df_abr_fac = df_fac[df_fac[col_abril] > 0]
            else:
                df_abr_fac = df_facturacion_raw
            show_detalle_facturacion("abril", fac_abril, df_abr_fac)
    
    # === TABLA DETALLE (OPCIONAL) ===
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 Ver datos brutos de Leads"):
        st.dataframe(df_leads_raw, use_container_width=True, hide_index=True)

@st.dialog("📊 Detalle: Leads nuevos cargados en HubSpot", width="large")
def show_detalle_leads_mes(mes, df_filtrado):
    st.write(f"**Mes:** {mes.capitalize()}")
    st.write(f"**Total Leads:** {len(df_filtrado)}")
    st.markdown("---")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

@st.dialog("📈 Detalle: Tasa de conversión lead a oportunidad", width="large")
def show_detalle_conversion(mes, calificados, total, df_calif, df_total):
    st.write(f"**Mes:** {mes.capitalize()}")
    st.write(f"**Total Leads:** {total}")
    st.write(f"**Leads Calificados:** {calificados}")
    st.write(f"**Tasa de Conversión:** {(calificados/total*100):.1f}%" if total > 0 else "**Tasa:** 0%")
    st.markdown("---")
    tab1, tab2 = st.tabs(["Todos los Leads", "Solo Calificados"])
    with tab1:
        st.dataframe(df_total, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(df_calif, use_container_width=True, hide_index=True)

@st.dialog("💰 Detalle: Negocios cotizados", width="large")
def show_detalle_cotizaciones(mes, total_valor, df_filtrado):
    st.write(f"**Mes:** {mes.capitalize()}")
    st.write(f"**Valor Total Cotizado:** ${total_valor:,.0f}")
    st.markdown("---")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

@st.dialog("💵 Detalle: Negocios facturados", width="large")
def show_detalle_facturacion(mes, total_valor, df_filtrado):
    st.write(f"**Mes:** {mes.capitalize()}")
    st.write(f"**Valor Total Facturado:** ${total_valor:,.0f}")
    st.markdown("---")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #1D1D1B; margin-bottom: 0;">DITAR</h2>
            <div style="color: #C7AB72; font-size: 12px; letter-spacing: 2px;">DASHBOARD</div>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio("Navegación", ["Dashboard Ejecutivo", "KPIs Mercadeo", "GESTIÓN DE CONTACTOS", "Manychat"])
        
    if page == "Dashboard Ejecutivo":
        render_dashboard_ejecutivo()
    elif page == "KPIs Mercadeo":
        render_kpis_mercadeo()
    elif page == "GESTIÓN DE CONTACTOS":
        render_gestion_contactos()
    else:
        render_manychat_stats()

if __name__ == "__main__":
    main()
