# app.py (versão corrigida para o mapa)

import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import os
import plotly.express as px
import pandas as pd
from shapely.geometry import box
from rasterio.warp import transform_bounds


# Importações para mapas interativos
import folium
from streamlit_folium import st_folium
import base64 # NOVO: Importar base64
from io import BytesIO # NOVO: Importar BytesIO
from PIL import Image # NOVO: Importar Image do PIL

# --- CONFIGURAÇÕES DO DASHBOARD ---
MAP_DIR = 'outputs/maps'
BACIA_PATH = 'data/bacia/limite_bacia_varzea.shp'
CSV_AREAS = 'outputs/area_por_classe.csv'
METRICS_DIR = "outputs/metrics"

CLASS_MAPPING = {
    0: "Água",
    1: "Floresta Nativa",
    2: "Floresta Plantada",
    3: "Agricultura",
    4: "Agricultura em Pousio",
    5: "Solo Exposto"
}
CLASS_COLORS = ["#1f77b4", "#2ca02c", "#88f85f", "#ff7f0e", "#bcbd22", "#8c564b"] 

st.set_page_config(page_title="Dashboard de Uso da Terra da Bacia do Rio da Várzea", layout="wide", initial_sidebar_state="expanded")
st.title("🌱 Dashboard de Classificação de Uso e Cobertura da Terra da Bacia do Rio da Várzea")

# --- LEITURA DA BACIA ---
try:
    bacia = gpd.read_file(BACIA_PATH, encoding='latin1')
    bacia_wgs84 = bacia.to_crs(epsg=4326) # Reprojetar para WGS84 para o Folium
except Exception as e:
    st.error(f"Erro ao ler shapefile da bacia: {e}. Verifique o caminho e a integridade do arquivo.")
    st.stop()

# --- CARREGAMENTO DE DADOS (CACHE) ---
@st.cache_data
def load_classified_rasters_info(map_dir):
    raster_files = sorted([f for f in os.listdir(map_dir) if f.endswith('.tif')])
    rasters_info = {}
    for filename in raster_files:
        year = int(filename.replace("classified_", "").replace(".tif", ""))
        rasters_info[year] = os.path.join(map_dir, filename)
    return rasters_info

@st.cache_data
def load_area_data(csv_path):
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if not all(isinstance(x, str) for x in df["Classe"].unique()):
            df["Classe"] = df["Classe"].map(CLASS_MAPPING)
        df["Área_km2"] = df["Área_ha"] / 100.0
        return df
    return pd.DataFrame()

@st.cache_data
def load_metrics_data(metrics_dir):
    all_metrics_data = []
    if os.path.exists(metrics_dir):
        metric_files = sorted([f for f in os.listdir(metrics_dir) if f.endswith('.csv')])
        for metric_file in metric_files:
            ano = int(os.path.basename(metric_file).split("_")[-1].replace(".csv", ""))
            df_metrics_year = pd.read_csv(os.path.join(metrics_dir, metric_file))
            df_metrics_year["Ano"] = ano
            if "Classe" in df_metrics_year.columns and not all(isinstance(x, str) for x in df_metrics_year["Classe"].unique()):
                df_metrics_year["Classe"] = df_metrics_year["Classe"].map(CLASS_MAPPING)
            all_metrics_data.append(df_metrics_year)
    return pd.concat(all_metrics_data, ignore_index=True) if all_metrics_data else pd.DataFrame()


rasters_info = load_classified_rasters_info(MAP_DIR)
if not rasters_info:
    st.error(f"Nenhum arquivo GeoTIFF classificado encontrado na pasta {MAP_DIR}. Por favor, execute src/5_classify.py.")
    st.stop()

df_total_area = load_area_data(CSV_AREAS)
if df_total_area.empty:
    st.error(f"Arquivo de áreas por classe não encontrado ou vazio em {CSV_AREAS}. Por favor, execute src/area_by_class.py.")
    st.stop()

df_all_metrics = load_metrics_data(METRICS_DIR)

# --- SIDEBAR (SELEÇÃO DE ANO) ---
st.sidebar.header("⚙️ Opções do Mapa")
years_available = sorted(rasters_info.keys())
selected_year = st.sidebar.selectbox("📅 Selecione o Ano para Visualização:", years_available, index=len(years_available)-1)

# --- VISUALIZAÇÃO DO MAPA CLASSIFICADO ---
st.header(f"🗺️ Mapa Classificado - Ano {selected_year}")
raster_to_display_path = rasters_info[selected_year]

try:
    with rasterio.open(raster_to_display_path) as src:
        raster_data = src.read(1)
        nodata_val = src.nodata if src.nodata is not None else 255
        
        # Obter o centro do raster e bounds em WGS84 para Folium
        src_crs = src.crs
        left, bottom, right, top = rasterio.warp.transform_bounds(src_crs, 'EPSG:4326', src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
        center_lon = (left + right) / 2
        center_lat = (bottom + top) / 2
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10) # Ajuste o zoom_start se necessário

        # Adicionar o polígono da bacia como GeoJSON
        if not bacia_wgs84.empty:
            folium.GeoJson(bacia_wgs84.__geo_interface__,
                           style_function=lambda x: {"fillColor": "#00000000", "color": "blue", "weight": 2}).add_to(m)

        # Mapear valores de classe para cores RGB e criar uma imagem RGBA para o overlay
        rgba_image = np.zeros((raster_data.shape[0], raster_data.shape[1], 4), dtype=np.uint8)

        for class_id, class_name in CLASS_MAPPING.items():
            # Acessar a cor de forma segura, garantindo que CLASS_COLORS tenha índice suficiente
            color_index = class_id 
            if color_index < len(CLASS_COLORS):
                color_hex = CLASS_COLORS[color_index]
            else: # Fallback para cor padrão se não houver cor definida
                color_hex = "#808080" # Cinza
            
            color_rgb = px.colors.hex_to_rgb(color_hex)
            mask_class = (raster_data == class_id)
            rgba_image[mask_class, 0] = color_rgb[0] # R
            rgba_image[mask_class, 1] = color_rgb[1] # G
            rgba_image[mask_class, 2] = color_rgb[2] # B
            rgba_image[mask_class, 3] = 255 # Alpha (opaco)

        # Definir transparência para pixels NODATA
        nodata_mask = (raster_data == nodata_val)
        rgba_image[nodata_mask, 3] = 0 # Define o canal alpha para 0 (totalmente transparente)

        # NOVO: Converter a imagem PIL para Base64 Data URI
        img_pil = Image.fromarray(rgba_image)
        buffered = BytesIO()
        img_pil.save(buffered, format="PNG") # Salvar como PNG
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        data_url = f"data:image/png;base64,{encoded_image}"

        folium.raster_layers.ImageOverlay(
            image=data_url, # Passar a Data URI aqui
            bounds=[[bottom, left], [top, right]], # [south, west], [north, east]
            opacity=0.7,
            name=f"Mapa Classificado {selected_year}"
        ).add_to(m)
        
        folium.LayerControl().add_to(m)

        st_data = st_folium(m, width=900, height=500)

except Exception as e:
    st.error(f"Erro ao exibir o mapa classificado para o ano {selected_year}: {e}. Verifique se o arquivo está íntegro e se os dados estão corretos.")
    st.markdown("---")

# --- SEÇÃO DE ÁREAS POR CLASSE ---
st.markdown("---")
col_area_chart, col_area_table = st.columns([1.4, 0.6])

with col_area_chart:
    st.subheader("📊 Gráfico de Área por Classe (Ano Selecionado)")
    df_area_selected_year = df_total_area[df_total_area["Ano"] == selected_year].copy()
    category_orders = [CLASS_MAPPING[i] for i in sorted(CLASS_MAPPING.keys())]
    
    fig_area_bar = px.bar(df_area_selected_year, x="Classe", y="Área_km2", color="Classe",
                     category_orders={"Classe": category_orders},
                     color_discrete_sequence=CLASS_COLORS,
                     title=f"Distribuição de Área - {selected_year}")
    fig_area_bar.update_layout(xaxis_title="Classe", yaxis_title="Área (km²)", showlegend=False)
    st.plotly_chart(fig_area_bar, use_container_width=True)

with col_area_table:
    st.subheader("📋 Tabela de Área por Classe (Ano Selecionado)")
    df_area_display = df_area_selected_year[["Classe", "Área_km2"]].copy()
    df_area_display["Área_km2"] = df_area_display["Área_km2"].round(2)
    st.dataframe(df_area_display, use_container_width=True)
    csv_area = df_area_display.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Baixar Tabela em CSV", csv_area, file_name=f"area_por_classe_{selected_year}.csv", mime='text/csv')


# --- GRÁFICOS DE TENDÊNCIA ANUAL ---
st.markdown("---")
st.subheader("📈 Tendências Anuais (Todos os Anos)")

# 1. Área Total por Ano
if not df_total_area.empty:
    df_area_total_by_year = df_total_area.groupby("Ano")["Área_km2"].sum().reset_index()
    fig_total_area_line = px.line(df_area_total_by_year, x="Ano", y="Área_km2", 
                                  title="Área Total Classificada por Ano",
                                  labels={"Área_km2": "Área Total (km²)"})
    fig_total_area_line.update_traces(mode='lines+markers')
    st.plotly_chart(fig_total_area_line, use_container_width=True)

# 2. Área por Classe ao Longo dos Anos (Gráfico de Linhas por Classe)
if not df_total_area.empty:
    # Para garantir que todas as classes apareçam na legenda e nas cores
    df_area_by_class_over_years = df_total_area.pivot_table(index='Ano', columns='Classe', values='Área_km2').fillna(0).reset_index()
    
    fig_class_area_line = px.line(df_area_by_class_over_years, x="Ano", y=df_area_by_class_over_years.columns[1:], 
                                  title="Área por Classe ao Longo dos Anos",
                                  labels={"value": "Área (km²)", "variable": "Classe"},
                                  color_discrete_map={CLASS_MAPPING[k]: CLASS_COLORS[k] for k in CLASS_MAPPING.keys() if k < len(CLASS_COLORS)}) # Mapear cores pelo nome da classe, com fallback
    fig_class_area_line.update_traces(mode='lines+markers')
    fig_class_area_line.update_layout(hovermode="x unified") # Melhora a interatividade do hover
    st.plotly_chart(fig_class_area_line, use_container_width=True)


# --- MÉTRICAS DE AVALIAÇÃO (COM TENDÊNCIA) ---
st.markdown("---")
st.subheader("📈 Métricas de Avaliação (F1-Score, Acurácia, etc.)")

if df_all_metrics.empty:
    st.warning(f"Nenhuma métrica encontrada na pasta {METRICS_DIR}. Por favor, certifique-se de que as métricas foram calculadas e salvas.")
else:
    # 1. Métrica Global (Média F1-Score, Acurácia, etc.)
    if "f1-score" in df_all_metrics.columns and "support" in df_all_metrics.columns:
        df_f1_weighted = df_all_metrics.copy()
        # Garante que 'support' seja numérico antes da soma
        df_f1_weighted['support'] = pd.to_numeric(df_f1_weighted['support'], errors='coerce').fillna(0)
        
        # Adicione uma coluna para o F1-Score total (não ponderado) se quiser, ou use outras métricas
        # Por exemplo, acurácia global pode ser calculada se você tiver os valores brutos de TN, FP, FN, TP
        
        # Calcular média ponderada do F1-Score por ano
        df_f1_per_year = df_f1_weighted.groupby('Ano').apply(
            lambda x: x['f1-score'].mean() # Média simples do F1-score por ano, se não houver 'support' global
            # lambda x: (x['f1-score'] * x['support']).sum() / x['support'].sum() if x['support'].sum() > 0 else 0 # Média ponderada
        ).reset_index(name='F1-Score Médio') # Alterado para Média simples para simplicidade, se quiser ponderado volte a linha de cima
        
        fig_f1_line = px.line(df_f1_per_year, x="Ano", y="F1-Score Médio", 
                              title="F1-Score Médio por Ano",
                              labels={"F1-Score Médio": "F1-Score"})
        fig_f1_line.update_traces(mode='lines+markers')
        st.plotly_chart(fig_f1_line, use_container_width=True)

    # 2. Métricas Detalhadas por Classe e Ano
    st.markdown("#### Métricas Detalhadas por Classe e Ano")
    
    metric_selected_year = st.sidebar.selectbox("📅 Selecione o Ano para Métricas Detalhadas:", years_available, key='metric_year_select')
    df_metrics_selected_year = df_all_metrics[df_all_metrics["Ano"] == metric_selected_year].copy()

    if not df_metrics_selected_year.empty:
        fig_metrics_bar = px.bar(df_metrics_selected_year, x="Classe", y="f1-score", color="Classe",
                                 color_discrete_sequence=CLASS_COLORS,
                                 title=f"F1-Score por Classe - Ano {metric_selected_year}")
        fig_metrics_bar.update_layout(xaxis_title="Classe", yaxis_title="F1-Score", showlegend=False)
        st.plotly_chart(fig_metrics_bar, use_container_width=True)

        st.dataframe(df_metrics_selected_year.drop(columns=['Ano']), use_container_width=True)
        csv_metrics_selected = df_metrics_selected_year.to_csv(index=False).encode('utf-8')
        st.download_button(f"⬇️ Baixar Métricas {metric_selected_year}", csv_metrics_selected,
                            file_name=f"metricas_{metric_selected_year}.csv", mime='text/csv')
    else:
        st.info(f"Nenhuma métrica detalhada disponível para o ano {metric_selected_year}.")


st.sidebar.markdown("---")
st.sidebar.markdown("""---  
**Desenvolvido por Emanuel Araújo Silva**✨  
Laboratório de Geoprocessamento e Sensoriamento Remoto - LGSR  
UFSM-FW""" )