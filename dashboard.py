import streamlit as st
import textwrap
import pandas as pd

# ==== CONFIGURACIÓN DE PÁGINA ====
st.set_page_config(page_title="Dashboard Directivo", layout="wide", initial_sidebar_state="collapsed")

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
    .border-valores { border-top: 4px solid #C7AB72; } 
    .border-distribuidor { border-top: 4px solid #C7AB72; }
    .channel-name { font-size: 14px; font-weight: 600; color: #1D1D1B; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .channel-reg { font-size: 26px; font-weight: bold; color: #1D1D1B; display: flex; align-items: baseline; }
    .reg-label { font-size: 10px; font-weight: normal; color: #6b6b69; margin-left: 3px; }
    .channel-cont-value { font-size: 20px; font-weight: bold; display: flex; align-items: baseline; }
    .color-retail { color: #1D1D1B; } 
    .color-food { color: #589642; } 
    .color-valores { color: #C7AB72; } 
    .color-distribuidor { color: #8a7452; }
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
    .bg-asignado   { background-color: #2e2e2b; color: #C7AB72; width: 100%; }
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
        
    return df_emp, df_neg, df_fid, df_roi

df_empresas_raw, df_negocios_raw, df_fid_raw, df_roi_raw = load_data()

# --- Procesando EMPRESAS ---
df_empresas = df_empresas_raw.copy()

channels_data = []
# Valores ha sido retirado del embudo de Empresas
class_map = {'Retail': 'retail', 'Food Service': 'food', 'Distribuidor': 'distribuidor'}

# Recalcular totales solo sobre los canales activos
df_empresas_active = df_empresas[df_empresas['Canal'].isin(class_map.keys())]
total_registradas = len(df_empresas_active.dropna(subset=['ID de registro']))
total_contactadas = (df_empresas_active['CONTACTADO'].sum()
    if pd.api.types.is_bool_dtype(df_empresas_active['CONTACTADO'])
    else (df_empresas_active['CONTACTADO'] == True).sum())
pct_total = f"{(total_contactadas/total_registradas)*100:.1f}%" if total_registradas > 0 else "0%"

for ch_name in class_map.keys():
    df_ch = df_empresas[df_empresas['Canal'] == ch_name]
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
    df_filtered = df_empresas[df_empresas['Canal'] == canal_name]
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
    <div class="date-badge">Ene — Mar 2026</div>
    <div class="main-title">JUNTA DIRECTIVA — 1Q 2026</div>
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

def main():
    st.title("📊 Dashboard Ejecutivo")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Conectado directamente a 'KPI Negocios'. Tiempo de actualización base: 5 seg.")
    with col_hz2:
        if st.button("🔄 Forzar Recarga de Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Embudos lado a lado
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        render_embudo_empresas()
    with col2:
        render_embudo_negocios()
        
    st.markdown("<br>", unsafe_allow_html=True)
    # Centering the donut chart below taking up an appropriate width space
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        render_fidelizacion()
    
    # ROI al fondo
    st.markdown("<hr style='margin: 30px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    render_roi_metrics()

if __name__ == "__main__":
    main()
