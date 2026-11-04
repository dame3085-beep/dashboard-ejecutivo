import streamlit as st
import textwrap
import pandas as pd
import re
import time
import unicodedata

KPI_YEAR = 2026
KPI_MONTH_NAMES = {
    3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre",
}
KPI_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1AQ9KX-gUW9VcSC3PypbsESPi_YZ939i_CBgVrft2xko/edit"
KPI_SHEET_IDS = {"LEADS": 1368127647, "COTIZACIONES": 116166388, "FACTURACION": 1076419284}
# Historical total expressly retained by the user; do not fabricate a source row.
KPI_LEAD_TOTAL_OVERRIDES = {"mayo": 48}


def kpi_text(value):
    if value is None or pd.isna(value):
        return ""
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(value).strip().lower())
                   if not unicodedata.combining(ch))


def kpi_column(frame, *names):
    columns = {kpi_text(column): column for column in frame.columns}
    return next((columns[kpi_text(name)] for name in names if kpi_text(name) in columns), None)


def kpi_date(value):
    if value is None or pd.isna(value) or value == "":
        return pd.NaT
    if isinstance(value, (int, float)):
        return pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=not bool(re.match(r"^\d{4}-\d{2}-\d{2}", str(value))))
    if pd.notna(parsed) and parsed.tzinfo is not None:
        return parsed.tz_convert("America/Bogota").tz_localize(None)
    return parsed


def kpi_month(value):
    text = kpi_text(value)
    for month, name in KPI_MONTH_NAMES.items():
        if text == name:
            # Historical LEADS stores the attributed month as Spanish text.
            return name
    date = kpi_date(value)
    return KPI_MONTH_NAMES.get(date.month, "") if pd.notna(date) and date.year == KPI_YEAR else ""


def kpi_qualified(value):
    return kpi_text(value) in {"calificado", "calificada", "qualified"}


def kpi_lead_total(month, frame):
    if frame.empty:
        return 0
    return max(len(frame), KPI_LEAD_TOTAL_OVERRIDES.get(kpi_text(month), 0))


def kpi_lead_direction(value):
    """Reporting convention: Angie is inbound and Daniel is outbound."""
    adviser = " ".join(kpi_text(value).split())
    if adviser == "angie" or (adviser.startswith("angie ") and "trujillo" in adviser.split()):
        return "in"
    if adviser == "daniel" or (adviser.startswith("daniel ") and "merino" in adviser.split()):
        return "out"
    return ""


def kpi_lead_breakdown(frame):
    # Column C is authoritative; the lowercase duplicate in O is only a fallback.
    owner_columns = [column for column in frame.columns if kpi_text(column) == "propietario del lead"]
    owner_columns.sort(key=lambda column: column != "Propietario del lead")
    owners = pd.Series("", index=frame.index, dtype=object)
    for column in owner_columns:
        owners = owners.mask(owners.eq(""), frame[column].map(kpi_text))
    directions = owners.map(kpi_lead_direction)
    return {
        "in": int(directions.eq("in").sum()),
        "out": int(directions.eq("out").sum()),
        "unknown": int(directions.eq("").sum()),
    }


def kpi_amount(value):
    if value is None or pd.isna(value) or str(value).strip() in {"", "-", "--", "$ -"}:
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"[^0-9,.-]", "", str(value))
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    elif "," in text:
        text = text.replace(",", "") if len(text.rsplit(",", 1)[1]) == 3 else text.replace(",", ".")
    elif text.count(".") > 1 or ("." in text and len(text.rsplit(".", 1)[1]) == 3):
        text = text.replace(".", "")
    number = pd.to_numeric(text, errors="coerce")
    return -abs(number) if re.search(r"\([^)]*\d[^)]*\)", str(value)) else number


def kpi_leads(frame):
    result = frame.copy()
    month_col = kpi_column(result, "Fecha de asignación al propietario", "Mes")
    if month_col is not None:
        result[month_col] = result[month_col].map(kpi_month)
    return result


def kpi_quotes(frame):
    result = frame.copy()
    date_col = kpi_column(result, "Fecha de atribución", "Fecha de creación")
    value_col = kpi_column(result, "Valor")
    result["mes_nombre"] = ""
    if value_col is not None:
        result[value_col] = result[value_col].map(kpi_amount)
    if date_col is not None:
        result[date_col] = result[date_col].map(kpi_date)
        result["mes_nombre"] = result[date_col].map(
            lambda date: KPI_MONTH_NAMES.get(date.month, "") if pd.notna(date) and date.year == KPI_YEAR else ""
        )
    return result


def kpi_billing_detail(frame, value_col):
    if value_col is None or value_col not in frame.columns:
        return pd.DataFrame(columns=["Razón social", "Marca", "Valor facturado (COP)"])
    name_col = kpi_column(frame, "RAZON SOCIAL", "Razón social")
    brand_col = kpi_column(frame, "MARCA", "Marca")
    amounts = frame[value_col].map(kpi_amount).fillna(0)
    result = pd.DataFrame({
        "Razón social": frame[name_col].fillna("") if name_col is not None else "",
        "Marca": frame[brand_col].fillna("") if brand_col is not None else "",
        "Valor facturado (COP)": amounts,
    })
    return result.loc[amounts.ne(0)].copy()


def kpi_billing_columns(frame):
    """Resolve monthly columns in both GViz text and XLSX date-header formats."""
    labels = {name: month for month, name in KPI_MONTH_NAMES.items()}
    labels.update({name[:3]: month for month, name in KPI_MONTH_NAMES.items()})
    labels.update({"abrl": 4, "sept": 9, "set": 9, "setiembre": 9})
    columns = {}
    for column in frame.columns:
        text = kpi_text(column)
        match = re.fullmatch(r"([a-z]+)\.?[\s/_-]+(\d{2}|\d{4})", text)
        if match:
            year = int(match[2]) + (2000 if len(match[2]) == 2 else 0)
            month = labels.get(match[1]) if year == KPI_YEAR else None
        elif not isinstance(column, str) or re.match(r"^\d{4}-\d{2}-\d{2}", text):
            date = kpi_date(column)
            month = date.month if pd.notna(date) and date.year == KPI_YEAR else None
        else:
            month = None
        if month in KPI_MONTH_NAMES:
            columns[month] = column
    return columns


def kpi_cop(value):
    return "$" + f"{value:,.0f}".replace(",", ".")


def kpi_record_id(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


def kpi_records_table(frame, object_type=None):
    result = frame.drop(columns=["mes_nombre", "propietario del lead"], errors="ignore").copy()
    for column in result.columns:
        label = kpi_text(column)
        if re.search(r"\bids?\b", label):
            # IDs are labels, not numbers; keep mixed Excel/text IDs Arrow-safe.
            result[column] = result[column].map(kpi_record_id)
        elif label not in {"valor", "valor facturado (cop)"}:
            # Descriptive fields can mix text and numeric association IDs in Sheets.
            result[column] = result[column].map(
                lambda value: "" if pd.isna(value) else str(value)
            )
    # Column L is a month label in the source; label it honestly in the detail.
    if object_type == "0-136":
        result = result.rename(columns={"Fecha de asignación al propietario": "Mes de atribución"})
    elif object_type == "0-3":
        result = result.rename(columns={"Fecha de creación": "Fecha de atribución", "Origen Empresa": "Origen de negocio"})
    record_col = kpi_column(result, "ID de registro")
    config = {}
    if object_type and record_col is not None:
        def record_link(value):
            record_id = kpi_record_id(value)
            if not record_id.isdigit():
                return None
            return f"https://app.hubspot.com/contacts/50182138/record/{object_type}/{record_id}?utm_source=dashboard&utm_medium=detail"
        result["HubSpot"] = result[record_col].map(record_link)
        config["HubSpot"] = st.column_config.LinkColumn("HubSpot", display_text="Abrir ↗")
    for column in ("Valor", "Valor facturado (COP)"):
        if column in result.columns:
            config[column] = st.column_config.NumberColumn(column, format="$ %.2f")
    st.dataframe(result, column_config=config, width="stretch", hide_index=True)


def kpi_source_link(sheet):
    st.link_button("Abrir fuente en Google Sheets", f"{KPI_SHEETS_URL}#gid={KPI_SHEET_IDS[sheet]}")

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
    .border-otros { border-top: 4px solid #6b6b69; }
    .channel-name { font-size: 14px; font-weight: 600; color: #1D1D1B; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .channel-reg { font-size: 26px; font-weight: bold; color: #1D1D1B; display: flex; align-items: baseline; }
    .reg-label { font-size: 10px; font-weight: normal; color: #6b6b69; margin-left: 3px; }
    .channel-cont-value { font-size: 20px; font-weight: bold; display: flex; align-items: baseline; }
    .color-retail { color: #1D1D1B; } 
    .color-food { color: #589642; } 
    .color-distribuidor { color: #C7AB72; } 
    .color-grandes { color: #8a7452; }
    .color-otros { color: #6b6b69; }
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

    /* Paneles de filtros: compactos y alineados con la identidad visual */
    div[data-testid="stExpander"] {
        border: 1px solid #e8e4dc;
        border-radius: 12px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfaf7 100%);
        box-shadow: 0 6px 18px rgba(29, 29, 27, 0.05);
        overflow: hidden;
    }
    div[data-testid="stExpander"] details summary {
        color: #1D1D1B;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    div[data-testid="stExpander"] [data-testid="stCaptionContainer"] {
        color: #75674e;
        margin-bottom: 0.2rem;
    }
    span[data-baseweb="tag"] {
        background-color: #efe7d7 !important;
        color: #1D1D1B !important;
        border-radius: 999px !important;
    }
    div[data-baseweb="select"] > div,
    div[data-testid="stDateInput"] input {
        border-color: #ddd3c0 !important;
        border-radius: 9px !important;
    }
</style>
"""), unsafe_allow_html=True)

# ==== FETCH DATOS GOOGLE SHEETS ====
@st.cache_data(ttl="5s")
def load_data():
    # Usamos el formato de exportacion directa a xlsx para evitar bloqueos de API
    url = (
        "https://docs.google.com/spreadsheets/d/1AQ9KX-gUW9VcSC3PypbsESPi_YZ939i_CBgVrft2xko/"
        f"export?format=xlsx&cachebust={time.time_ns()}"
    )
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
    
    # Hoja LEADS (para KPIs Mercadeo) - intentar varios nombres
    df_leads = pd.DataFrame()
    for nombre in ["LEADS", "Leads", "leads"]:
        try:
            df_leads = pd.read_excel(xls, sheet_name=nombre)
            break
        except:
            continue
    
    # Hoja COTIZACIONES (mayúsculas como aparece en el sheet)
    df_cotizaciones = pd.DataFrame()
    for nombre in ["COTIZACIONES", "Cotizaciones", "cotizaciones", "COTIZACIÓN", "Cotización", "cotización"]:
        try:
            df_cotizaciones = pd.read_excel(xls, sheet_name=nombre)
            break
        except:
            continue
    
    # Consolidado KPI: preferir FACTURACION, no la pestaña histórica Facturación.
    df_facturacion = pd.DataFrame()
    for nombre in ["FACTURACION", "FACTURACIÓN", "Facturacion", "Facturación", "facturacion", "facturación"]:
        try:
            df_facturacion = pd.read_excel(xls, sheet_name=nombre)
            break
        except:
            continue
    # La exportación XLSX de Google puede conservar una versión anterior durante varios minutos.
    # Para este KPI, GViz refleja los cambios de la pestaña de forma inmediata.
    try:
        facturacion_url = (
            "https://docs.google.com/spreadsheets/d/1AQ9KX-gUW9VcSC3PypbsESPi_YZ939i_CBgVrft2xko/"
            f"gviz/tq?tqx=out:csv&sheet=FACTURACION&headers=1&cachebust={time.time_ns()}"
        )
        df_facturacion_live = pd.read_csv(facturacion_url)
        if (kpi_column(df_facturacion_live, "RAZON SOCIAL") is not None
                and set(KPI_MONTH_NAMES).issubset(kpi_billing_columns(df_facturacion_live))):
            df_facturacion = df_facturacion_live
    except Exception:
        pass
    
    # Guardar nombres de hojas disponibles para debug
    sheet_names = xls.sheet_names
            
    return df_emp, df_neg, df_fid, df_roi, df_kpi, df_manychat, df_leads, df_cotizaciones, df_facturacion, sheet_names

df_empresas_raw, df_negocios_raw, df_fid_raw, df_roi_raw, df_kpi_raw, df_manychat_raw, df_leads_raw, df_cotizaciones_raw, df_facturacion_raw, sheet_names_available = load_data()

# --- Procesando EMPRESAS ---
df_empresas = df_empresas_raw.dropna(subset=['ID de registro']).copy()

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
    return 'Otros'

df_empresas['Canal_Norm'] = df_empresas['Canal'].apply(normalize_canal)

# Valor estable y legible para filtrar registros sin asesor asignado.
if 'Propietario' in df_empresas.columns:
    df_empresas['Asesor_Filtro'] = (
        df_empresas['Propietario']
        .fillna('Sin asesor')
        .astype(str)
        .str.strip()
        .replace('', 'Sin asesor')
    )
else:
    df_empresas['Asesor_Filtro'] = 'Sin asesor'

channels_data = []
# Mapeo de categorías para visualización
class_map = {
    'Retail': 'retail', 
    'Food Service': 'food', 
    'Distribuidor': 'distribuidor',
    'Grandes Superficies': 'grandes',
    'Otros': 'otros'
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
df_negocios['Fecha_Filtro'] = pd.to_datetime(df_negocios['Fecha de creacion'], errors='coerce')
df_negocios['Propietario del negocio'] = df_negocios['Propietario del negocio'].fillna('Sin asesor').astype(str).str.strip()

def format_currency_short(val):
    if val >= 1_000_000_000: return f"${val/1_000_000_000:.1f}B"
    elif val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    elif val >= 1_000: return f"${val/1_000:.1f}k"
    else: return f"${val:.0f}"

# Normalizamos la columna para quitar tildes en 'ó' y manejar espacios extra
df_negocios['Etapa del negocio'] = (
    df_negocios['Etapa del negocio']
    .astype(str)
    .str.strip()
    .str.replace('\u00f3', 'o', regex=False)
    .str.replace('\u00d3', 'O', regex=False)
)

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
def show_detalle_empresas(canal_name, asesores_seleccionados):
    st.write(f"Registros de la hoja **Empresas** para el canal: **{canal_name}**. Incluye el periodo Ene-Jul 2026.")
    df_filtered = df_empresas[
        (df_empresas['Canal_Norm'] == canal_name)
        & (df_empresas['Asesor_Filtro'].isin(asesores_seleccionados))
    ].copy()
    df_filtered.drop(columns=['Canal_Norm', 'Asesor_Filtro'], errors='ignore', inplace=True)
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

@st.dialog("📋 Listado Detallado de Negocios", width="large")
def show_detalle_negocios(stage_name, df_source):
    st.write(f"Explorando datos brutos de la hoja para la etapa: **{stage_name}**")
    df_filtered = df_source[df_source['Etapa del negocio'].str.upper() == stage_name.upper()].copy()
    
    # Reordenar columnas a petición del usuario
    desired_order = ['Fecha de creacion', 'Propietario del negocio', 'Canal', 'Origen Empresa']
    rest_cols = [c for c in df_filtered.columns if c not in desired_order]
    final_order = [c for c in desired_order if c in df_filtered.columns] + rest_cols
    df_display = df_filtered[final_order].copy()
    df_display.drop(columns=['Fecha_Filtro'], errors='ignore', inplace=True)
    
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
    asesores_disponibles = sorted(df_empresas_active['Asesor_Filtro'].unique().tolist())
    canales_disponibles = [
        canal for canal in class_map
        if canal in df_empresas_active['Canal_Norm'].unique()
    ]

    with st.expander("⚙️ Filtrar empresas", expanded=True):
        st.caption("Combina asesores y canales para explorar el embudo.")
        asesores_seleccionados = st.multiselect(
            "Asesor",
            options=asesores_disponibles,
            default=asesores_disponibles,
            key="filtro_empresas_asesores",
            help="Selecciona uno o varios asesores."
        )
        canales_seleccionados = st.multiselect(
            "Canal",
            options=canales_disponibles,
            default=canales_disponibles,
            key="filtro_empresas_canales",
            help="Selecciona uno o varios canales."
        )

    if not asesores_seleccionados or not canales_seleccionados:
        st.info("Selecciona al menos un asesor y un canal para visualizar el embudo.")
        return

    df_empresas_filtrado = df_empresas_active[
        df_empresas_active['Asesor_Filtro'].isin(asesores_seleccionados)
        & df_empresas_active['Canal_Norm'].isin(canales_seleccionados)
    ].copy()

    total_registradas_filtrado = len(df_empresas_filtrado)
    total_contactadas_filtrado = (
        df_empresas_filtrado['CONTACTADO'].sum()
        if pd.api.types.is_bool_dtype(df_empresas_filtrado['CONTACTADO'])
        else (df_empresas_filtrado['CONTACTADO'] == True).sum()
    )
    pct_total_filtrado = (
        f"{(total_contactadas_filtrado / total_registradas_filtrado) * 100:.1f}%"
        if total_registradas_filtrado > 0 else "0.0%"
    )

    channels_data_filtrado = []
    for ch_name in canales_seleccionados:
        df_ch = df_empresas_filtrado[df_empresas_filtrado['Canal_Norm'] == ch_name]
        reg = len(df_ch)
        cont = (
            df_ch['CONTACTADO'].sum()
            if pd.api.types.is_bool_dtype(df_ch['CONTACTADO'])
            else (df_ch['CONTACTADO'] == True).sum()
        )
        conv = f"{(cont / reg) * 100:.1f}%" if reg > 0 else "0.0%"
        channels_data_filtrado.append({
            "name": ch_name,
            "reg": reg,
            "conv": conv,
            "cont": cont,
            "class": class_map[ch_name]
        })

    html_top = f"""<div class="funnel-container" style="padding-bottom: 20px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;">
    <div class="date-badge">Ene — Jul 2026</div>
    <div class="main-title">REPORTE</div>
    <div class="funnel-title">Embudo de Empresas</div>
    <div class="funnel-subtitle">Registradas → Canal → Contactadas por canal</div>
    <div class="stage-1">
        <div><div class="stage-label">ETAPA 1</div><div class="stage-name">Registradas</div></div>
        <div class="stage-value">{total_registradas_filtrado}</div>
    </div>
    <div class="connector-1"></div>
    <div class="stage-2-container" style="box-shadow: none; margin-bottom: -10px; padding-bottom: 0;">
        <div class="stage-2-header" style="text-align: center;">ETAPA 2 — DISTRIBUCIÓN POR CANAL</div>
    </div>
</div>"""
    st.markdown(html_top, unsafe_allow_html=True)

    st.markdown('<div style="background-color: #f7f9fc; padding: 0 40px;">', unsafe_allow_html=True)
    cols = st.columns(len(channels_data_filtrado))
    st.markdown("""<style>
    .ch-box-native { background-color: white; border: 1px solid #eee; padding: 15px 10px; border-radius: 8px; text-align: center; margin-bottom: 5px; }
    </style>""", unsafe_allow_html=True)

    for col_e, ch in zip(cols, channels_data_filtrado):
        with col_e:
            ch_html = f"""<div class="ch-box-native border-{ch['class']}">
    <div class="channel-name">{ch['name']}</div>
    <div class="channel-reg" style="justify-content: center;">{ch['reg']}<span class="reg-label">reg.</span></div>
    <div class="conversion-rate" style="justify-content: center;">↓ {ch['conv']}</div>
    <div class="channel-cont-value color-{ch['class']}" style="justify-content: center;">{ch['cont']} <span class="reg-label" style="color:#637381;">cont.</span></div>
</div>"""
            st.markdown(ch_html, unsafe_allow_html=True)
            if st.button("📊 Extraer", key=f"btn_emp_{ch['class']}", use_container_width=True):
                show_detalle_empresas(ch['name'], asesores_seleccionados)
    st.markdown('</div>', unsafe_allow_html=True)

    html_bot = f"""<div class="funnel-container" style="padding-top: 0; margin-top: 0; border-top-left-radius: 0; border-top-right-radius: 0;">
    <div class="connector-2" style="margin-top: 15px;"></div>
    <div class="stage-3">
        <div><div class="stage-label">ETAPA 3</div><div class="stage-name">Contactadas</div></div>
        <div><span class="stage-value">{total_contactadas_filtrado}</span><span class="stage-3-pct">({pct_total_filtrado})</span></div>
    </div>
</div>"""
    st.markdown(html_bot, unsafe_allow_html=True)

def render_embudo_negocios():
    fechas_validas = df_negocios['Fecha_Filtro'].dropna()
    if fechas_validas.empty:
        st.warning("No hay fechas válidas en la hoja de negocios.")
        return

    asesores_disponibles = sorted(df_negocios['Propietario del negocio'].unique().tolist())
    etapas_disponibles = list(stage_order_map.keys())

    with st.expander("⚙️ Filtrar negocios", expanded=True):
        st.caption("Ajusta el periodo, los asesores y las etapas visibles.")
        rango_fechas = st.date_input(
            "Rango de fechas",
            value=(fechas_validas.min().date(), fechas_validas.max().date()),
            min_value=fechas_validas.min().date(),
            max_value=fechas_validas.max().date(),
            key="filtro_negocios_rango_fechas",
        )
        asesores_seleccionados = st.multiselect(
            "Asesor",
            options=asesores_disponibles,
            default=asesores_disponibles,
            key="filtro_negocios_asesores",
            help="Selecciona uno o varios asesores.",
        )
        etapas_seleccionadas = st.multiselect(
            "Etapa",
            options=etapas_disponibles,
            default=etapas_disponibles,
            key="filtro_negocios_etapas",
            help="Selecciona una o varias etapas.",
            format_func=lambda etapa: etapa.replace("Negociacion", "Negociación"),
        )

    if not isinstance(rango_fechas, (tuple, list)) or len(rango_fechas) != 2:
        st.info("Selecciona la fecha inicial y la fecha final del periodo.")
        return
    fecha_inicio, fecha_fin = rango_fechas

    if fecha_inicio > fecha_fin:
        st.warning("La fecha inicial no puede ser posterior a la fecha final.")
        return
    if not asesores_seleccionados or not etapas_seleccionadas:
        st.info("Selecciona al menos un asesor y una etapa para visualizar el embudo.")
        return

    df_negocios_filtrado = df_negocios[
        (df_negocios['Fecha_Filtro'].dt.date >= fecha_inicio)
        & (df_negocios['Fecha_Filtro'].dt.date <= fecha_fin)
        & (df_negocios['Propietario del negocio'].isin(asesores_seleccionados))
        & (df_negocios['Etapa del negocio'].isin(etapas_seleccionadas))
    ].copy()

    group_neg_filtrado = (
        df_negocios_filtrado.groupby('Etapa del negocio')['Valor']
        .agg(['count', 'sum'])
        .reset_index()
    )
    data_negocios_filtrado = []
    for stage in etapas_seleccionadas:
        row = group_neg_filtrado[group_neg_filtrado['Etapa del negocio'] == stage]
        count = int(row['count'].iloc[0]) if not row.empty else 0
        value = float(row['sum'].iloc[0]) if not row.empty else 0
        data_negocios_filtrado.append({
            "label": stage.upper(),
            "count": count,
            "val": format_currency_short(value),
            "bg": stage_order_map[stage][0],
            "order": stage_order_map[stage][1],
        })
    data_negocios_filtrado.sort(key=lambda item: item['order'])
    total_negocios_filtrado = len(df_negocios_filtrado.dropna(subset=['ID de registro']))
    valor_negocios_filtrado = format_currency_short(df_negocios_filtrado['Valor'].sum())

    st.markdown(f"""<div class="negocios-container" style="padding-bottom: 20px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;">
    <div class="negocios-title">Embudo de Negocios</div>
    <div class="negocios-subtitle">{total_negocios_filtrado} negocios · Valor total <span>{valor_negocios_filtrado}</span></div>
</div>""", unsafe_allow_html=True)

    # Render funnel layers wrapped with native buttons alongside
    st.markdown('<div style="background-color: #0b111a; padding: 0 40px; padding-bottom: 40px; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">', unsafe_allow_html=True)
    for i, item in enumerate(data_negocios_filtrado):
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
                show_detalle_negocios(item['label'], df_negocios_filtrado)
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
    st.caption("Medición mensual de meses cerrados | Reporte a Gerencia Comercial")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Datos desde Google Sheets · Detalle mensual de leads, cotizaciones y facturación")
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
        padding: 25px 20px;
        margin-bottom: 25px;
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
        grid-template-columns: 92px repeat(5, minmax(0, 1fr));
        gap: 12px;
        align-items: stretch;
    }
    .kpi-seven-months {
        grid-template-columns: 92px repeat(7, minmax(0, 1fr));
        gap: 8px;
    }
    .kpi-mkt-box {
        text-align: center;
        padding: 15px 10px;
        border-radius: 8px;
        background: #fafafa;
    }
    .kpi-mkt-box.real { background: #e8f5e9; }
    .kpi-mkt-box.porcentaje-alto { background: #c8e6c9; }
    .kpi-mkt-box.porcentaje-medio { background: #ffe082; }
    .kpi-mkt-box.porcentaje-bajo { background: #ef9a9a; }
    .kpi-mkt-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #666;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .kpi-mkt-value {
        font-size: 28px;
        font-weight: 700;
        color: #1D1D1B;
        line-height: 1.2;
    }
    .kpi-mkt-value.pct-green { color: #2e7d32; }
    .kpi-mkt-value.pct-yellow { color: #f57c00; }
    .kpi-mkt-value.pct-red { color: #c62828; }
    .kpi-mkt-pct {
        font-size: 14px;
        font-weight: 600;
        margin-top: 4px;
        display: block;
    }
    .kpi-mkt-pct.pct-green { color: #2e7d32; }
    .kpi-mkt-pct.pct-yellow { color: #f57c00; }
    .kpi-mkt-pct.pct-red { color: #c62828; }
    .kpi-mkt-trend {
        font-size: 11px;
        margin-top: 6px;
        color: #666;
        font-weight: 500;
    }
    .kpi-month-card {
        border: 1px solid #ebe6dc;
        border-radius: 10px;
        overflow: hidden;
        background: #fff;
        min-width: 0;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }
    .kpi-month-card:hover {
        transform: translateY(-2px);
        border-color: #d8c69f;
        box-shadow: 0 8px 18px rgba(29,29,27,.08);
    }
    .kpi-month-name {
        padding: 8px 10px;
        background: #f5f1e9;
        color: #6f6045;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .08em;
        text-align: center;
    }
    .kpi-month-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
    }
    .kpi-month-metric {
        padding: 12px 6px;
        text-align: center;
        background: #e8f5e9;
    }
    .kpi-month-metric + .kpi-month-metric { border-left: 1px solid rgba(29,29,27,.08); }
    .kpi-month-metric.porcentaje-alto { background: #c8e6c9; }
    .kpi-month-metric.porcentaje-medio { background: #ffe082; }
    .kpi-month-metric.porcentaje-bajo { background: #ef9a9a; }
    .kpi-month-metric span {
        display: block;
        color: #6b6b67;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kpi-month-metric strong {
        color: #1D1D1B;
        font-size: 21px;
        line-height: 1;
    }
    .kpi-month-metric strong.pct-green { color: #2e7d32; }
    .kpi-month-metric strong.pct-yellow { color: #f57c00; }
    .kpi-month-metric strong.pct-red { color: #c62828; }
    .kpi-month-detail {
        display: block;
        margin-top: 4px;
        color: #73736f;
        font-size: 9px;
        font-weight: 600;
    }
    .kpi-lead-split {
        min-height: 24px;
        font-size: 9px;
        line-height: 1.35;
        font-weight: 500;
        letter-spacing: 0;
        text-transform: none;
    }
    .kpi-billing-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #ffffff 0%, #fcfaf5 100%);
    }
    .kpi-billing-card::after {
        content: "";
        position: absolute;
        width: 180px;
        height: 180px;
        right: -105px;
        top: -110px;
        border-radius: 50%;
        background: rgba(199,171,114,.12);
        pointer-events: none;
        z-index: 0;
    }
    .kpi-billing-card > * { position: relative; z-index: 1; }
    .kpi-billing-title-wrap {
        display: flex;
        align-items: center;
        gap: 9px;
        flex-wrap: wrap;
    }
    .kpi-audited-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 9px;
        border-radius: 999px;
        background: #e8f3e4;
        color: #3f7131;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: .04em;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .kpi-month-card.is-latest {
        border-color: #C7AB72;
        box-shadow: 0 6px 16px rgba(127,100,48,.14);
    }
    .kpi-month-card.is-latest .kpi-month-name {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 6px;
        background: #1D1D1B;
        color: #fff;
    }
    .kpi-latest-badge {
        padding: 2px 5px;
        border-radius: 999px;
        background: #C7AB72;
        color: #1D1D1B;
        font-size: 7px;
        letter-spacing: .05em;
    }
    .kpi-billing-card .kpi-mkt-values {
        grid-template-columns: 92px repeat(7, minmax(0, 1fr));
        gap: 8px;
    }
    .kpi-billing-card .kpi-month-metric strong {
        font-size: clamp(17px, 1.2vw, 21px);
        white-space: nowrap;
    }
    .kpi-billing-summary {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 13px;
        padding-top: 12px;
        border-top: 1px solid #eee8dc;
    }
    .kpi-billing-summary-item {
        display: flex;
        justify-content: center;
        align-items: baseline;
        gap: 7px;
        color: #77716a;
        font-size: 10px;
        text-align: center;
    }
    .kpi-billing-summary-item strong {
        color: #1D1D1B;
        font-size: 13px;
    }
    .kpi-billing-summary-item strong.positive { color: #3f7f31; }
    @media (max-width: 1050px) {
        .kpi-mkt-values { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .kpi-billing-card .kpi-mkt-values { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (max-width: 650px) {
        .kpi-card-mkt { padding: 20px 14px; }
        .kpi-mkt-header { gap: 8px; flex-wrap: wrap; }
        .kpi-mkt-values { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
        .kpi-mkt-value { font-size: 23px; }
        .kpi-month-metric strong { font-size: 17px; }
        .kpi-billing-summary { grid-template-columns: 1fr; gap: 6px; }
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
            <div class="subtitle">Medición mensual de meses cerrados | Reporte a Gerencia Comercial | Mar–Sep 2026 · Septiembre cerrado (1–30)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === DIAGNÓSTICO AUTOMÁTICO ===
    hay_problema = df_leads_raw.empty or df_cotizaciones_raw.empty or df_facturacion_raw.empty
    
    if hay_problema:
        st.error("⚠️ **Faltan datos en una o más hojas: LEADS, COTIZACIONES o FACTURACION**")
        st.write("**Hojas disponibles en el archivo Google Sheets:**")
        st.code(sheet_names_available)
        st.write("**Buscando hojas con nombres similares...**")
        # Intentar encontrar hojas similares
        similares_leads = [s for s in sheet_names_available if 'lead' in s.lower() or 'hubspot' in s.lower()]
        similares_cot = [s for s in sheet_names_available if 'cot' in s.lower() or 'presupuesto' in s.lower()]
        similares_fac = [s for s in sheet_names_available if 'fact' in s.lower() or 'venta' in s.lower() or 'ingreso' in s.lower()]
        if similares_leads:
            st.write(f"Posibles hojas de LEADS: {similares_leads}")
        if similares_cot:
            st.write(f"Posibles hojas de cotizaciones: {similares_cot}")
        if similares_fac:
            st.write(f"Posibles hojas de facturacion: {similares_fac}")
        st.warning("Revisa los nombres de hojas y recarga")
    else:
        # Mostrar resumen en verde si todo OK
        with st.expander("✅ Diagnóstico de datos", expanded=False):
            st.write(f"**LEADS:** {len(df_leads_raw)} filas, columnas: {list(df_leads_raw.columns) if not df_leads_raw.empty else 'N/A'}")
            st.write(f"**cotizaciones:** {len(df_cotizaciones_raw)} filas, columnas: {list(df_cotizaciones_raw.columns) if not df_cotizaciones_raw.empty else 'N/A'}")
            st.write(f"**facturacion:** {len(df_facturacion_raw)} filas, columnas: {list(df_facturacion_raw.columns) if not df_facturacion_raw.empty else 'N/A'}")
    
    # === DETECCIÓN DE COLUMNAS EN LEADS ===
    # Columna L = mes de atribución; conservar la atribución histórica de ferias.
    # Columna H (índice 7) = Etapa del lead = CALIFICACIÓN
    df_leads = kpi_leads(df_leads_raw)
    leads_marzo = leads_abril = leads_mayo = leads_junio = leads_julio = leads_agosto = 0
    leads_septiembre = 0
    pct_marzo = pct_abril = pct_mayo = pct_junio = pct_julio = pct_agosto = 0
    col_mes_leads = None
    col_calif = None
    
    if not df_leads.empty:
        col_mes_leads = kpi_column(df_leads, "Fecha de asignación al propietario", "Mes")
        col_calif = kpi_column(df_leads, "Etapa del lead")
        
        # Calcular leads por mes
        if col_mes_leads:
            df_leads[col_mes_leads] = df_leads[col_mes_leads].fillna('').astype(str).str.strip().str.lower()
            leads_marzo = len(df_leads[df_leads[col_mes_leads] == 'marzo'])
            leads_abril = len(df_leads[df_leads[col_mes_leads] == 'abril'])
            leads_mayo = kpi_lead_total("mayo", df_leads[df_leads[col_mes_leads] == 'mayo'])
            leads_junio = len(df_leads[df_leads[col_mes_leads] == 'junio'])
            leads_julio = len(df_leads[df_leads[col_mes_leads] == 'julio'])
            leads_agosto = len(df_leads[df_leads[col_mes_leads] == 'agosto'])
            leads_septiembre = len(df_leads[df_leads[col_mes_leads] == 'septiembre'])
                
            pct_marzo = (leads_marzo / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
            pct_abril = (leads_abril / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
            pct_mayo = (leads_mayo / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
            pct_junio = (leads_junio / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
            pct_julio = (leads_julio / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
            pct_agosto = (leads_agosto / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0

    pct_septiembre = (leads_septiembre / METAS["leads"]) * 100 if METAS["leads"] > 0 else 0
    
    def get_pct_class(pct):
        if pct >= 100: return "porcentaje-alto", "pct-green"
        elif pct >= 60: return "porcentaje-medio", "pct-yellow"
        else: return "porcentaje-bajo", "pct-red"

    def round_pct(pct):
        """Redondeo comercial: 62.5 se presenta como 63, no 62."""
        return int(float(pct) + 0.5)
    
    class_marzo, val_class_marzo = get_pct_class(pct_marzo)
    class_abril, val_class_abril = get_pct_class(pct_abril)
    class_mayo, val_class_mayo = get_pct_class(pct_mayo)
    class_junio, val_class_junio = get_pct_class(pct_junio)
    class_julio, val_class_julio = get_pct_class(pct_julio)
    class_agosto, val_class_agosto = get_pct_class(pct_agosto)
    class_septiembre, val_class_septiembre = get_pct_class(pct_septiembre)

    meses_leads = [
        ("MAR", leads_marzo, pct_marzo, class_marzo, val_class_marzo, False),
        ("ABR", leads_abril, pct_abril, class_abril, val_class_abril, False),
        ("MAY", leads_mayo, pct_mayo, class_mayo, val_class_mayo, False),
        ("JUN", leads_junio, pct_junio, class_junio, val_class_junio, False),
        ("JUL", leads_julio, pct_julio, class_julio, val_class_julio, False),
        ("AGO", leads_agosto, pct_agosto, class_agosto, val_class_agosto, False),
        ("SEP", leads_septiembre, pct_septiembre, class_septiembre, val_class_septiembre, True),
    ]
    nombres_meses_leads = {name[:3].upper(): name for name in KPI_MONTH_NAMES.values()}
    meses_leads_html = []
    for mes, real, pct, pct_class, value_class, is_latest in meses_leads:
        df_mes = (
            df_leads[df_leads[col_mes_leads] == nombres_meses_leads[mes]]
            if col_mes_leads else df_leads.iloc[0:0]
        )
        desglose = kpi_lead_breakdown(df_mes)
        sin_clasificar = desglose["unknown"] + max(0, real - len(df_mes))
        detalle = f'in: {desglose["in"]}, out: {desglose["out"]}'
        if sin_clasificar:
            detalle += f'<br>sin clasificar: {sin_clasificar}'
        meses_leads_html.append(
            f'<div class="kpi-month-card{" is-latest" if is_latest else ""}">'
            f'<div class="kpi-month-name">{mes}</div>'
            f'<div class="kpi-month-metrics">'
            f'<div class="kpi-month-metric"><span>Real</span><strong>{real}</strong>'
            '<small class="kpi-month-detail kpi-lead-split" '
            'title="Por asesor registrado: Angie Trujillo = inbound; Daniel Meriño = outbound">'
            f'{detalle}</small></div>'
            f'<div class="kpi-month-metric {pct_class}"><span>Cumpl.</span><strong class="{value_class}">{round_pct(pct)}%</strong></div>'
            f'</div></div>'
        )
    meses_leads_html = "".join(meses_leads_html)
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Leads nuevos cargados en HubSpot</div>
            <div class="kpi-mkt-meta">Meta mensual: {METAS['leads']}</div>
        </div>
        <div class="kpi-mkt-values kpi-seven-months">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{METAS['leads']}</div>
            </div>
            {meses_leads_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Leads
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_leads_mar", use_container_width=True):
            df_mar_fil = df_leads[df_leads[col_mes_leads] == 'marzo'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("marzo", df_mar_fil)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_leads_abr", use_container_width=True):
            df_abr_fil = df_leads[df_leads[col_mes_leads] == 'abril'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("abril", df_abr_fil)
    with c3:
        if st.button("🔍 Ver detalle Mayo", key="btn_leads_may", use_container_width=True):
            df_may_fil = df_leads[df_leads[col_mes_leads] == 'mayo'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("mayo", df_may_fil)
    with c4:
        if st.button("🔍 Ver detalle Junio", key="btn_leads_jun", use_container_width=True):
            df_jun_fil = df_leads[df_leads[col_mes_leads] == 'junio'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("junio", df_jun_fil)
    with c5:
        if st.button("🔍 Ver detalle Julio", key="btn_leads_jul", use_container_width=True):
            df_jul_fil = df_leads[df_leads[col_mes_leads] == 'julio'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("julio", df_jul_fil)
    with c6:
        if st.button("🔍 Ver detalle Agosto", key="btn_leads_ago", use_container_width=True):
            df_ago_fil = df_leads[df_leads[col_mes_leads] == 'agosto'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("agosto", df_ago_fil)
    with c7:
        if st.button("🔍 Ver detalle Septiembre", key="btn_leads_sep", use_container_width=True):
            df_sep_fil = df_leads[df_leads[col_mes_leads] == 'septiembre'] if col_mes_leads else pd.DataFrame()
            show_detalle_leads_mes("septiembre", df_sep_fil)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # === INDICADOR 2: TASA CONVERSIÓN ===
    # Columna H (índice 7) = Etapa del lead
    # Coincidencia exacta: "Descalificado" no cuenta como "Calificado".
    tasa_marzo = tasa_abril = tasa_mayo = tasa_junio = tasa_julio = tasa_agosto = 0
    calif_marzo = calif_abril = calif_mayo = calif_junio = calif_julio = calif_agosto = 0
    total_marzo = total_abril = total_mayo = total_junio = total_julio = total_agosto = 0
    calif_septiembre = total_septiembre = tasa_septiembre = 0
    
    if not df_leads.empty and col_mes_leads and col_calif:
        def es_calificado(val):
            return kpi_qualified(val)
        
        # Marzo
        df_marzo = df_leads[df_leads[col_mes_leads] == 'marzo']
        total_marzo = len(df_marzo)
        calif_marzo = len(df_marzo[df_marzo[col_calif].apply(es_calificado)])
        tasa_marzo = (calif_marzo / total_marzo * 100) if total_marzo > 0 else 0
        
        # Abril
        df_abril = df_leads[df_leads[col_mes_leads] == 'abril']
        total_abril = len(df_abril)
        calif_abril = len(df_abril[df_abril[col_calif].apply(es_calificado)])
        tasa_abril = (calif_abril / total_abril * 100) if total_abril > 0 else 0

        # Mayo
        df_mayo = df_leads[df_leads[col_mes_leads] == 'mayo']
        total_mayo = len(df_mayo)
        calif_mayo = len(df_mayo[df_mayo[col_calif].apply(es_calificado)])
        tasa_mayo = (calif_mayo / total_mayo * 100) if total_mayo > 0 else 0

        # Junio
        df_junio = df_leads[df_leads[col_mes_leads] == 'junio']
        total_junio = len(df_junio)
        calif_junio = len(df_junio[df_junio[col_calif].apply(es_calificado)])
        tasa_junio = (calif_junio / total_junio * 100) if total_junio > 0 else 0

        # Julio
        df_julio = df_leads[df_leads[col_mes_leads] == 'julio']
        total_julio = len(df_julio)
        calif_julio = len(df_julio[df_julio[col_calif].apply(es_calificado)])
        tasa_julio = (calif_julio / total_julio * 100) if total_julio > 0 else 0

        # Agosto
        df_agosto = df_leads[df_leads[col_mes_leads] == 'agosto']
        total_agosto = len(df_agosto)
        calif_agosto = len(df_agosto[df_agosto[col_calif].apply(es_calificado)])
        tasa_agosto = (calif_agosto / total_agosto * 100) if total_agosto > 0 else 0

        df_septiembre = df_leads[df_leads[col_mes_leads] == 'septiembre']
        total_septiembre = len(df_septiembre)
        calif_septiembre = len(df_septiembre[df_septiembre[col_calif].apply(es_calificado)])
        tasa_septiembre = (calif_septiembre / total_septiembre * 100) if total_septiembre > 0 else 0
    
    pct_tasa_marzo = (tasa_marzo / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_abril = (tasa_abril / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_mayo = (tasa_mayo / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_junio = (tasa_junio / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_julio = (tasa_julio / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_agosto = (tasa_agosto / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    pct_tasa_septiembre = (tasa_septiembre / METAS["tasa_conversion"]) * 100 if METAS["tasa_conversion"] > 0 else 0
    
    class_tasa_marzo, val_class_tasa_marzo = get_pct_class(pct_tasa_marzo)
    class_tasa_abril, val_class_tasa_abril = get_pct_class(pct_tasa_abril)
    class_tasa_mayo, val_class_tasa_mayo = get_pct_class(pct_tasa_mayo)
    class_tasa_junio, val_class_tasa_junio = get_pct_class(pct_tasa_junio)
    class_tasa_julio, val_class_tasa_julio = get_pct_class(pct_tasa_julio)
    class_tasa_agosto, val_class_tasa_agosto = get_pct_class(pct_tasa_agosto)
    class_tasa_septiembre, val_class_tasa_septiembre = get_pct_class(pct_tasa_septiembre)

    meses_conversion = [
        ("MAR", tasa_marzo, calif_marzo, total_marzo, pct_tasa_marzo, class_tasa_marzo, val_class_tasa_marzo, False),
        ("ABR", tasa_abril, calif_abril, total_abril, pct_tasa_abril, class_tasa_abril, val_class_tasa_abril, False),
        ("MAY", tasa_mayo, calif_mayo, total_mayo, pct_tasa_mayo, class_tasa_mayo, val_class_tasa_mayo, False),
        ("JUN", tasa_junio, calif_junio, total_junio, pct_tasa_junio, class_tasa_junio, val_class_tasa_junio, False),
        ("JUL", tasa_julio, calif_julio, total_julio, pct_tasa_julio, class_tasa_julio, val_class_tasa_julio, False),
        ("AGO", tasa_agosto, calif_agosto, total_agosto, pct_tasa_agosto, class_tasa_agosto, val_class_tasa_agosto, False),
        ("SEP", tasa_septiembre, calif_septiembre, total_septiembre, pct_tasa_septiembre, class_tasa_septiembre, val_class_tasa_septiembre, True),
    ]
    meses_conversion_html = "".join(
        f'<div class="kpi-month-card{" is-latest" if is_latest else ""}">'
        f'<div class="kpi-month-name">{mes}</div>'
        f'<div class="kpi-month-metrics">'
        f'<div class="kpi-month-metric"><span>Real</span><strong>{tasa:.1f}%</strong>'
        f'<small class="kpi-month-detail">{calificados}/{total}</small></div>'
        f'<div class="kpi-month-metric {pct_class}"><span>Cumpl.</span>'
        f'<strong class="{value_class}">{round_pct(cumplimiento)}%</strong></div>'
        f'</div></div>'
        for mes, tasa, calificados, total, cumplimiento, pct_class, value_class, is_latest in meses_conversion
    )
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Tasa de conversión lead a oportunidad</div>
            <div class="kpi-mkt-meta">Meta mensual: {METAS['tasa_conversion']}%</div>
        </div>
        <div class="kpi-mkt-values kpi-seven-months">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{METAS['tasa_conversion']}%</div>
            </div>
            {meses_conversion_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Conversión
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_conv_mar", use_container_width=True):
            df_mar_all = df_leads[df_leads[col_mes_leads] == 'marzo'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("marzo", df_mar_all)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_conv_abr", use_container_width=True):
            df_abr_all = df_leads[df_leads[col_mes_leads] == 'abril'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("abril", df_abr_all)
    with c3:
        if st.button("🔍 Ver detalle Mayo", key="btn_conv_may", use_container_width=True):
            df_may_all = df_leads[df_leads[col_mes_leads] == 'mayo'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("mayo", df_may_all)
    with c4:
        if st.button("🔍 Ver detalle Junio", key="btn_conv_jun", use_container_width=True):
            df_jun_all = df_leads[df_leads[col_mes_leads] == 'junio'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("junio", df_jun_all)
    with c5:
        if st.button("🔍 Ver detalle Julio", key="btn_conv_jul", use_container_width=True):
            df_jul_all = df_leads[df_leads[col_mes_leads] == 'julio'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("julio", df_jul_all)
    with c6:
        if st.button("🔍 Ver detalle Agosto", key="btn_conv_ago", use_container_width=True):
            df_ago_all = df_leads[df_leads[col_mes_leads] == 'agosto'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("agosto", df_ago_all)
    with c7:
        if st.button("🔍 Ver detalle Septiembre", key="btn_conv_sep", use_container_width=True):
            df_sep_all = df_leads[df_leads[col_mes_leads] == 'septiembre'] if col_mes_leads else pd.DataFrame()
            show_detalle_conversion("septiembre", df_sep_all)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === INDICADOR 3: NEGOCIOS COTIZADOS (A-H según especificación) ===
    # Columna F (índice 5) = Valor
    # Columna G (índice 6) = Fecha de atribución mensual del negocio
    df_cot = kpi_quotes(df_cotizaciones_raw)
    cot_marzo = cot_abril = cot_mayo = cot_junio = cot_julio = cot_agosto = 0
    cot_septiembre = 0
    
    if not df_cot.empty and kpi_column(df_cot, "Valor") is not None:
        col_valor_cot = kpi_column(df_cot, "Valor")
        
        cot_marzo = df_cot[df_cot['mes_nombre'] == 'marzo'][col_valor_cot].sum()
        cot_abril = df_cot[df_cot['mes_nombre'] == 'abril'][col_valor_cot].sum()
        cot_mayo = df_cot[df_cot['mes_nombre'] == 'mayo'][col_valor_cot].sum()
        cot_junio = df_cot[df_cot['mes_nombre'] == 'junio'][col_valor_cot].sum()
        cot_julio = df_cot[df_cot['mes_nombre'] == 'julio'][col_valor_cot].sum()
        cot_agosto = df_cot[df_cot['mes_nombre'] == 'agosto'][col_valor_cot].sum()
        cot_septiembre = df_cot[df_cot['mes_nombre'] == 'septiembre'][col_valor_cot].sum()
    
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
    pct_cot_mayo = (cot_mayo / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    pct_cot_junio = (cot_junio / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    pct_cot_julio = (cot_julio / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    pct_cot_agosto = (cot_agosto / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    pct_cot_septiembre = (cot_septiembre / METAS["negocios_cotizados"]) * 100 if METAS["negocios_cotizados"] > 0 else 0
    
    class_cot_marzo, val_class_cot_marzo = get_pct_class(pct_cot_marzo)
    class_cot_abril, val_class_cot_abril = get_pct_class(pct_cot_abril)
    class_cot_mayo, val_class_cot_mayo = get_pct_class(pct_cot_mayo)
    class_cot_junio, val_class_cot_junio = get_pct_class(pct_cot_junio)
    class_cot_julio, val_class_cot_julio = get_pct_class(pct_cot_julio)
    class_cot_agosto, val_class_cot_agosto = get_pct_class(pct_cot_agosto)
    class_cot_septiembre, val_class_cot_septiembre = get_pct_class(pct_cot_septiembre)

    meses_cot = [
        ("MAR", cot_marzo, pct_cot_marzo, class_cot_marzo, val_class_cot_marzo, False),
        ("ABR", cot_abril, pct_cot_abril, class_cot_abril, val_class_cot_abril, False),
        ("MAY", cot_mayo, pct_cot_mayo, class_cot_mayo, val_class_cot_mayo, False),
        ("JUN", cot_junio, pct_cot_junio, class_cot_junio, val_class_cot_junio, False),
        ("JUL", cot_julio, pct_cot_julio, class_cot_julio, val_class_cot_julio, False),
        ("AGO", cot_agosto, pct_cot_agosto, class_cot_agosto, val_class_cot_agosto, False),
        ("SEP", cot_septiembre, pct_cot_septiembre, class_cot_septiembre, val_class_cot_septiembre, True),
    ]
    meses_cot_html = "".join(
        f'<div class="kpi-month-card{" is-latest" if is_latest else ""}">'
        f'<div class="kpi-month-name">{mes}</div>'
        f'<div class="kpi-month-metrics">'
        f'<div class="kpi-month-metric"><span>Real</span><strong>{format_currency(real)}</strong></div>'
        f'<div class="kpi-month-metric {pct_class}"><span>Cumpl.</span><strong class="{value_class}">{round_pct(pct)}%</strong></div>'
        f'</div></div>'
        for mes, real, pct, pct_class, value_class, is_latest in meses_cot
    )
    
    st.markdown(f"""
    <div class="kpi-card-mkt">
        <div class="kpi-mkt-header">
            <div class="kpi-mkt-title">Negocios cotizados generados por mercadeo</div>
            <div class="kpi-mkt-meta">Meta mensual: {format_currency(METAS['negocios_cotizados'])}</div>
        </div>
        <div class="kpi-mkt-values kpi-seven-months">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{format_currency(METAS['negocios_cotizados'])}</div>
            </div>
            {meses_cot_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Cotizaciones
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_cot_mar", use_container_width=True):
            df_cot_mar = df_cot[df_cot['mes_nombre'] == 'marzo']
            show_detalle_cotizaciones("marzo", df_cot_mar)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_cot_abr", use_container_width=True):
            df_cot_abr = df_cot[df_cot['mes_nombre'] == 'abril']
            show_detalle_cotizaciones("abril", df_cot_abr)
    with c3:
        if st.button("🔍 Ver detalle Mayo", key="btn_cot_may", use_container_width=True):
            df_cot_may = df_cot[df_cot['mes_nombre'] == 'mayo']
            show_detalle_cotizaciones("mayo", df_cot_may)
    with c4:
        if st.button("🔍 Ver detalle Junio", key="btn_cot_jun", use_container_width=True):
            df_cot_jun = df_cot[df_cot['mes_nombre'] == 'junio']
            show_detalle_cotizaciones("junio", df_cot_jun)
    with c5:
        if st.button("🔍 Ver detalle Julio", key="btn_cot_jul", use_container_width=True):
            df_cot_jul = df_cot[df_cot['mes_nombre'] == 'julio']
            show_detalle_cotizaciones("julio", df_cot_jul)
    with c6:
        if st.button("🔍 Ver detalle Agosto", key="btn_cot_ago", use_container_width=True):
            df_cot_ago = df_cot[df_cot['mes_nombre'] == 'agosto']
            show_detalle_cotizaciones("agosto", df_cot_ago)
    with c7:
        if st.button("🔍 Ver detalle Septiembre", key="btn_cot_sep", use_container_width=True):
            df_cot_sep = df_cot[df_cot['mes_nombre'] == 'septiembre']
            show_detalle_cotizaciones("septiembre", df_cot_sep)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === INDICADOR 4: NEGOCIOS FACTURADOS ===
    df_fac = df_facturacion_raw.copy()
    fac_marzo = fac_abril = fac_mayo = fac_junio = fac_julio = fac_agosto = 0
    fac_septiembre = 0
    col_marzo_fac = col_abril_fac = col_mayo_fac = col_junio_fac = col_julio_fac = col_agosto_fac = col_septiembre_fac = None

    def limpiar_valor_facturacion(serie):
        return serie.map(kpi_amount).fillna(0)
    
    columnas_facturacion = kpi_billing_columns(df_fac)
    meses_sin_columna = [
        name.capitalize() for month, name in KPI_MONTH_NAMES.items()
        if month not in columnas_facturacion
    ]
    if meses_sin_columna:
        st.error(
            "No se pudieron identificar los encabezados de facturación de: "
            + ", ".join(meses_sin_columna)
            + ". Recarga los datos. No se muestran ceros ni totales parciales como si fueran facturación real."
        )
        return

    if not df_fac.empty:
        # Both sources use the same month map, including typed Excel date headers.
        (col_marzo_fac, col_abril_fac, col_mayo_fac, col_junio_fac,
         col_julio_fac, col_agosto_fac, col_septiembre_fac) = (
            columnas_facturacion[month] for month in KPI_MONTH_NAMES
        )
        
        # Calcular totales
        if col_marzo_fac:
            df_fac[col_marzo_fac] = limpiar_valor_facturacion(df_fac[col_marzo_fac])
            fac_marzo = df_fac[col_marzo_fac].sum()
        if col_abril_fac:
            df_fac[col_abril_fac] = limpiar_valor_facturacion(df_fac[col_abril_fac])
            fac_abril = df_fac[col_abril_fac].sum()
        if col_mayo_fac:
            df_fac[col_mayo_fac] = limpiar_valor_facturacion(df_fac[col_mayo_fac])
            fac_mayo = df_fac[col_mayo_fac].sum()
        if col_junio_fac:
            df_fac[col_junio_fac] = limpiar_valor_facturacion(df_fac[col_junio_fac])
            fac_junio = df_fac[col_junio_fac].sum()
        if col_julio_fac:
            df_fac[col_julio_fac] = limpiar_valor_facturacion(df_fac[col_julio_fac])
            fac_julio = df_fac[col_julio_fac].sum()
        if col_agosto_fac:
            df_fac[col_agosto_fac] = limpiar_valor_facturacion(df_fac[col_agosto_fac])
            fac_agosto = df_fac[col_agosto_fac].sum()
        if col_septiembre_fac:
            df_fac[col_septiembre_fac] = limpiar_valor_facturacion(df_fac[col_septiembre_fac])
            fac_septiembre = df_fac[col_septiembre_fac].sum()
    
    pct_fac_marzo = (fac_marzo / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_abril = (fac_abril / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_mayo = (fac_mayo / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_junio = (fac_junio / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_julio = (fac_julio / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_agosto = (fac_agosto / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    pct_fac_septiembre = (fac_septiembre / METAS["negocios_facturados"]) * 100 if METAS["negocios_facturados"] > 0 else 0
    
    class_fac_marzo, val_class_fac_marzo = get_pct_class(pct_fac_marzo)
    class_fac_abril, val_class_fac_abril = get_pct_class(pct_fac_abril)
    class_fac_mayo, val_class_fac_mayo = get_pct_class(pct_fac_mayo)
    class_fac_junio, val_class_fac_junio = get_pct_class(pct_fac_junio)
    class_fac_julio, val_class_fac_julio = get_pct_class(pct_fac_julio)
    class_fac_agosto, val_class_fac_agosto = get_pct_class(pct_fac_agosto)
    class_fac_septiembre, val_class_fac_septiembre = get_pct_class(pct_fac_septiembre)

    meses_fac = [
        ("MAR", fac_marzo, pct_fac_marzo, class_fac_marzo, val_class_fac_marzo, False),
        ("ABR", fac_abril, pct_fac_abril, class_fac_abril, val_class_fac_abril, False),
        ("MAY", fac_mayo, pct_fac_mayo, class_fac_mayo, val_class_fac_mayo, False),
        ("JUN", fac_junio, pct_fac_junio, class_fac_junio, val_class_fac_junio, False),
        ("JUL", fac_julio, pct_fac_julio, class_fac_julio, val_class_fac_julio, False),
        ("AGO", fac_agosto, pct_fac_agosto, class_fac_agosto, val_class_fac_agosto, False),
        ("SEP", fac_septiembre, pct_fac_septiembre, class_fac_septiembre, val_class_fac_septiembre, True),
    ]
    meses_fac_html = "".join(
        (
            '<div class="kpi-month-card' + (' is-latest' if es_ultimo else '') + '">'
            f'<div class="kpi-month-name">{mes}'
            + ('<span class="kpi-latest-badge">CERRADO</span>' if es_ultimo else '')
            + '</div>'
            + '<div class="kpi-month-metrics">'
            + f'<div class="kpi-month-metric"><span>Real</span><strong>{format_currency(real)}</strong></div>'
            + f'<div class="kpi-month-metric {pct_class}"><span>Cumpl.</span><strong class="{value_class}">{pct:.0f}%</strong></div>'
            + '</div></div>'
        )
        for mes, real, pct, pct_class, value_class, es_ultimo in meses_fac
    )

    fac_periodo_total = sum(real for _, real, *_ in meses_fac)
    fac_promedio = fac_periodo_total / len(meses_fac) if meses_fac else 0
    variacion_fac_septiembre = ((fac_septiembre / fac_agosto) - 1) * 100 if fac_agosto else 0
    
    st.markdown(f"""
    <div class="kpi-card-mkt kpi-billing-card">
        <div class="kpi-mkt-header">
            <div class="kpi-billing-title-wrap">
                <div class="kpi-mkt-title">Negocios facturados atribuidos a mercadeo</div>
                <span class="kpi-audited-badge">✓ Datos auditados</span>
            </div>
            <div class="kpi-mkt-meta">Septiembre cerrado · Meta: {format_currency(METAS['negocios_facturados'])}</div>
        </div>
        <div class="kpi-mkt-values">
            <div class="kpi-mkt-box">
                <div class="kpi-mkt-label">Meta</div>
                <div class="kpi-mkt-value">{format_currency(METAS['negocios_facturados'])}</div>
            </div>
            {meses_fac_html}
        </div>
        <div class="kpi-billing-summary">
            <div class="kpi-billing-summary-item"><span>Total Mar–Sep</span><strong>{format_currency(fac_periodo_total)}</strong></div>
            <div class="kpi-billing-summary-item"><span>Promedio mensual</span><strong>{format_currency(fac_promedio)}</strong></div>
            <div class="kpi-billing-summary-item"><span>Sep vs. Ago</span><strong class="{'positive' if variacion_fac_septiembre >= 0 else ''}">{variacion_fac_septiembre:+.0f}%</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones detalle Facturación
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        if st.button("🔍 Ver detalle Marzo", key="btn_fac_mar", use_container_width=True):
            df_mar_fac = kpi_billing_detail(df_fac, col_marzo_fac)
            show_detalle_facturacion("marzo", df_mar_fac)
    with c2:
        if st.button("🔍 Ver detalle Abril", key="btn_fac_abr", use_container_width=True):
            df_abr_fac = kpi_billing_detail(df_fac, col_abril_fac)
            show_detalle_facturacion("abril", df_abr_fac)
    with c3:
        if st.button("🔍 Ver detalle Mayo", key="btn_fac_may", use_container_width=True):
            df_may_fac = kpi_billing_detail(df_fac, col_mayo_fac)
            show_detalle_facturacion("mayo", df_may_fac)
    with c4:
        if st.button("🔍 Ver detalle Junio", key="btn_fac_jun", use_container_width=True):
            df_jun_fac = kpi_billing_detail(df_fac, col_junio_fac)
            show_detalle_facturacion("junio", df_jun_fac)
    with c5:
        if st.button("🔍 Ver detalle Julio", key="btn_fac_jul", use_container_width=True):
            df_jul_fac = kpi_billing_detail(df_fac, col_julio_fac)
            show_detalle_facturacion("julio", df_jul_fac)
    with c6:
        if st.button("🔍 Ver detalle Agosto", key="btn_fac_ago", use_container_width=True):
            df_ago_fac = kpi_billing_detail(df_fac, col_agosto_fac)
            show_detalle_facturacion("agosto", df_ago_fac)
    with c7:
        if st.button("🔍 Ver detalle Septiembre", key="btn_fac_sep", use_container_width=True):
            df_sep_fac = kpi_billing_detail(df_fac, col_septiembre_fac)
            show_detalle_facturacion("septiembre", df_sep_fac)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === TABLA DETALLE (OPCIONAL) ===
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 Ver datos de Leads (Google Sheets)"):
        st.caption("Cada botón de detalle muestra los registros del mes seleccionado.")
        kpi_records_table(df_leads_raw, "0-136")

@st.dialog("📊 Detalle: Leads nuevos cargados en HubSpot", width="large")
def show_detalle_leads_mes(mes, df_filtrado):
    st.caption(f"{mes.capitalize()} {KPI_YEAR} · LEADS")
    total = kpi_lead_total(mes, df_filtrado)
    st.metric("Leads nuevos", total)
    desglose = kpi_lead_breakdown(df_filtrado)
    sin_clasificar = desglose["unknown"] + max(0, total - len(df_filtrado))
    detalle = f'in: {desglose["in"]}, out: {desglose["out"]}'
    if sin_clasificar:
        detalle += f", sin clasificar: {sin_clasificar}"
    st.caption(detalle)
    st.caption("Por asesor registrado: Angie Trujillo = inbound; Daniel Meriño = outbound.")
    if total > len(df_filtrado):
        st.info(
            f"{len(df_filtrado)} registros disponibles en Sheets + "
            f"{total - len(df_filtrado)} de ajuste manual autorizado. "
            "El total histórico se conserva; el ajuste no tiene una ficha individual en la fuente."
        )
    if df_filtrado.empty:
        st.info("No hay registros de este mes en la fuente disponible.")
    else:
        kpi_records_table(df_filtrado, "0-136")
    kpi_source_link("LEADS")

@st.dialog("📈 Detalle: Tasa de conversión lead a oportunidad", width="large")
def show_detalle_conversion(mes, df_total):
    st.caption(f"{mes.capitalize()} {KPI_YEAR} · LEADS")
    stage_col = kpi_column(df_total, "Etapa del lead")
    df_calif = df_total[df_total[stage_col].map(kpi_qualified)] if stage_col is not None else df_total.iloc[0:0]
    total, calificados = len(df_total), len(df_calif)
    c1, c2, c3 = st.columns(3)
    c1.metric("Leads", total)
    c2.metric("Calificados", calificados)
    c3.metric("Conversión", f"{(calificados / total * 100):.1f}%" if total else "0.0%")
    tab1, tab2 = st.tabs([f"Todos los leads ({total})", f"Calificados ({calificados})"])
    with tab1:
        kpi_records_table(df_total, "0-136")
    with tab2:
        kpi_records_table(df_calif, "0-136")
    kpi_source_link("LEADS")

@st.dialog("💰 Detalle: Negocios cotizados", width="large")
def show_detalle_cotizaciones(mes, df_filtrado):
    st.caption(f"{mes.capitalize()} {KPI_YEAR} · COTIZACIONES")
    value_col = kpi_column(df_filtrado, "Valor")
    amounts = df_filtrado[value_col].map(kpi_amount) if value_col is not None else pd.Series(dtype=float)
    c1, c2, c3 = st.columns(3)
    c1.metric("Negocios", len(df_filtrado))
    c2.metric("Con valor", int((amounts.notna() & amounts.ne(0)).sum()))
    c3.metric("Valor cotizado", kpi_cop(amounts.sum()))
    if df_filtrado.empty:
        st.info("No hay negocios de este mes en la fuente disponible.")
    else:
        kpi_records_table(df_filtrado, "0-3")
    st.caption("La fecha de atribución determina el mes del KPI. Los importes vacíos se conservan sin valor.")
    kpi_source_link("COTIZACIONES")

@st.dialog("💵 Detalle: Negocios facturados", width="large")
def show_detalle_facturacion(mes, df_filtrado):
    st.caption(f"{mes.capitalize()} {KPI_YEAR} · FACTURACION")
    total = df_filtrado["Valor facturado (COP)"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Empresas con movimientos", len(df_filtrado))
    c2.metric("Valor neto facturado", kpi_cop(total))
    if df_filtrado.empty:
        st.info("No hay movimientos de este mes en la fuente disponible.")
    else:
        kpi_records_table(df_filtrado)
    st.caption("Se muestran únicamente los valores del mes seleccionado. El total incluye ajustes y notas crédito.")
    kpi_source_link("FACTURACION")

def render_fidelizacion_roi():
    st.title("🤝 Fidelización y ROI")
    st.caption("Métricas de fidelización de clientes y retorno de inversión Colombiatex 2026")
    
    col_hz1, col_hz2 = st.columns([4, 1])
    with col_hz1:
        st.write("Conectado directamente a Google Sheets. Tiempo de actualización base: 5 seg.")
    with col_hz2:
        if st.button("🔄 Forzar Recarga", use_container_width=True, key="reload_fidel_roi"):
            st.cache_data.clear()
            st.rerun()
            
    # Centering the donut chart below taking up an appropriate width space
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        render_fidelizacion()
    
    # ROI al fondo
    st.markdown("<hr style='margin: 30px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    render_roi_metrics()

def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #1D1D1B; margin-bottom: 0;">DITAR</h2>
            <div style="color: #C7AB72; font-size: 12px; letter-spacing: 2px;">DASHBOARD</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.radio("Navegación", ["KPIs Mercadeo"], index=0)

    render_kpis_mercadeo()

if __name__ == "__main__":
    main()
