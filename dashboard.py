import streamlit as st
import textwrap
import pandas as pd

# ==== CONFIGURACIÓN DE PÁGINA ====
st.set_page_config(page_title="Dashboard Directivo", layout="wide", initial_sidebar_state="collapsed")

# ==== CSS PERSONALIZADO ====
st.markdown(textwrap.dedent("""
<style>
    /* ----- EMBUDO EMPRESAS (TEMA CLARO) ----- */
    .funnel-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f7f9fc;
        padding: 40px;
        border-radius: 12px;
        color: #333;
        margin-bottom: 50px;
    }
    .main-title { color: #8b96a1; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 600; }
    .funnel-title { color: #1a2b49; font-size: 36px; font-weight: bold; margin-bottom: 5px; }
    .funnel-subtitle { color: #637381; font-size: 14px; margin-bottom: 30px; }
    .date-badge { float: right; border: 1px solid #dfe3e8; padding: 8px 16px; border-radius: 20px; font-size: 14px; color: #637381; background-color: white; }
    
    .stage-1 { background-color: #003380; color: white; border-radius: 12px; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 3; }
    .connector-1 { height: 60px; background: #d4def0; clip-path: polygon(0 0, 100% 0, 95% 100%, 5% 100%); margin-top: -10px; position: relative; z-index: 2; }
    .stage-2-container { background-color: white; border-radius: 12px; padding: 20px 0; margin: -10px 5% 0 5%; box-shadow: 0 4px 12px rgba(0,0,0,0.05); position: relative; z-index: 3; border: 1px solid #eee; }
    .connector-2 { height: 50px; background: #bce3cf; clip-path: polygon(5% 0, 95% 0, 75% 100%, 25% 100%); margin-top: -10px; position: relative; z-index: 2; }
    .stage-3 { background-color: #00994d; color: white; border-radius: 12px; padding: 20px 30px; margin: 0 15%; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 3; }
    
    .stage-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }
    .stage-name { font-size: 20px; font-weight: bold; margin-top: 5px; }
    .stage-value { font-size: 38px; font-weight: bold; }
    .stage-2-header { padding: 0 20px 10px 20px; font-size: 11px; color: #637381; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; border-bottom: 2px solid transparent; }
    .channels-row { display: flex; width: 100%; flex-wrap: nowrap; overflow: hidden; }
    .channel-box { flex: 1; padding: 15px 10px; border-right: 1px solid #eee; min-width: 0; }
    .channel-box:last-child { border-right: none; }
    
    .border-retail { border-top: 4px solid #003380; } .border-food { border-top: 4px solid #0077b6; } .border-valores { border-top: 4px solid #28a745; } .border-distribuidor { border-top: 4px solid #dc3545; }
    .channel-name { font-size: 14px; font-weight: 600; color: #1a2b49; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .channel-reg { font-size: 26px; font-weight: bold; color: #1a2b49; display: flex; align-items: baseline; }
    .reg-label { font-size: 10px; font-weight: normal; color: #637381; margin-left: 3px; }
    .channel-cont-value { font-size: 20px; font-weight: bold; display: flex; align-items: baseline; }
    .color-retail { color: #003380; } .color-food { color: #0077b6; } .color-valores { color: #28a745; } .color-distribuidor { color: #dc3545; }
    .conversion-rate { font-size: 12px; color: #637381; margin: 8px 0; display: flex; align-items: center; }
    .conversion-rate svg { margin-right: 3px; width: 10px; height: 10px; }
    .stage-3-pct { font-size: 18px; font-weight: normal; margin-left: 8px; opacity: 0.9; }

    /* ----- EMBUDO NEGOCIOS (TEMA OSCURO) ----- */
    .negocios-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #0b111a;
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
        color: #8b96a1;
        font-size: 14px;
        margin-bottom: 40px;
    }
    .negocios-subtitle span { color: #3b82f6; font-weight: bold; }
    
    .funnel-layer {
        margin: 0 auto 10px auto;
        border-radius: 12px;
        padding: 15px 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #0b111a;
        font-weight: bold;
    }
    
    .layer-count-group { text-align: left; }
    .layer-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 2px; }
    .layer-count { font-size: 24px; display: flex; justify-content: flex-start; align-items: baseline; }
    .layer-count-label { font-size: 12px; font-weight: normal; margin-left: 5px; opacity: 0.8; }
    
    .layer-value-group { text-align: right; }
    .layer-value { font-size: 20px; font-weight: bold;}
    .layer-val-label { font-size: 10px; font-weight: normal; opacity: 0.8; display: block; margin-top: 2px;}

    /* Anchuras y colores manuales para simular el embudo */
    .bg-asignado { background-color: #1a73e8; width: 100%; color: white; }
    .bg-contactado { background-color: #12b5cb; width: 85%; color: #0b111a; }
    .bg-negociacion { background-color: #9370db; width: 85%; color: white; }
    .bg-ganada { background-color: #28a745; width: 70%; color: #0b111a; }
    .bg-perdida { background-color: #ea4335; width: 70%; color: white; }
    .bg-pausado { background-color: #d28c46; width: 55%; color: #0b111a; }
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
    return df_emp, df_neg

df_empresas_raw, df_negocios_raw = load_data()

# --- Procesando EMPRESAS ---
df_empresas = df_empresas_raw.copy()
total_registradas = len(df_empresas.dropna(subset=['ID de registro']))
total_contactadas = df_empresas['CONTACTADO'].sum() if pd.api.types.is_bool_dtype(df_empresas['CONTACTADO']) else (df_empresas['CONTACTADO'] == True).sum()
pct_total = f"{(total_contactadas/total_registradas)*100:.1f}%" if total_registradas > 0 else "0%"

channels_data = []
class_map = {'Retail': 'retail', 'Food Service': 'food', 'Valores': 'valores', 'Distribuidor': 'distribuidor'}

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

def render_embudo_empresas():
    channels_html = ""
    for ch in data_empresas['channels']:
        channels_html += f'''
<div class="channel-box border-{ch['class']}">
    <div class="channel-name">{ch['name']}</div>
    <div class="channel-reg">{ch['reg']}<span class="reg-label">reg.</span></div>
    <div class="conversion-rate">↓ {ch['conv']}</div>
    <div class="channel-cont-value color-{ch['class']}">{ch['cont']} <span class="reg-label" style="color:#637381;">cont.</span></div>
</div>'''
        
    html_str = f"""
<div class="funnel-container">
    <div class="date-badge">Ene — Mar 2026</div>
    <div class="main-title">JUNTA DIRECTIVA — 1Q 2026</div>
    <div class="funnel-title">Embudo de Empresas</div>
    <div class="funnel-subtitle">Registradas → Canal → Contactadas por canal</div>
    <div class="stage-1">
        <div><div class="stage-label">ETAPA 1</div><div class="stage-name">Registradas</div></div>
        <div class="stage-value">{data_empresas['total_registradas']}</div>
    </div>
    <div class="connector-1"></div>
    <div class="stage-2-container">
        <div class="stage-2-header">ETAPA 2 — DISTRIBUCIÓN POR CANAL</div>
        <div class="channels-row">
            {channels_html}
        </div>
    </div>
    <div class="connector-2"></div>
    <div class="stage-3">
        <div><div class="stage-label">ETAPA 3</div><div class="stage-name">Contactadas</div></div>
        <div><span class="stage-value">{data_empresas['total_contactadas']}</span><span class="stage-3-pct">({data_empresas['pct_total']})</span></div>
    </div>
</div>
    """
    st.markdown(html_str, unsafe_allow_html=True)

def render_embudo_negocios():
    html_layers = ""
    for item in data_negocios:
        html_layers += f"""
<div class="funnel-layer {item['bg']}">
    <div class="layer-count-group">
        <div class="layer-label">{item['label']}</div>
        <div class="layer-count">{item['count']} <span class="layer-count-label">negocios</span></div>
    </div>
    <div class="layer-value-group">
        <div class="layer-value">{item['val']}</div>
        <div class="layer-val-label">valor total</div>
    </div>
</div>
        """
        
    html_str = f"""
<div class="negocios-container">
    <div class="negocios-title">Embudo de Negocios</div>
    <div class="negocios-subtitle">{total_negocios_count} negocios · Valor total <span>{global_negocios_str}</span></div>
    <div style="width: 80%; margin: 0 auto;">
        {html_layers}
    </div>
</div>
    """
    st.markdown(html_str, unsafe_allow_html=True)

def main():
    st.title("📊 Dashboard Ejecutivo")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Conectado directamente a 'KPI Negocios'. Tiempo de actualización base: 5 seg.")
    with col_hz2:
        if st.button("🔄 Forzar Recarga de Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        render_embudo_empresas()
    with col2:
        render_embudo_negocios()

if __name__ == "__main__":
    main()
