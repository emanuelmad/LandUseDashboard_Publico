# 🌱 LandUseDashboard Público

Este projeto apresenta um **Dashboard Interativo de Classificação de Uso e Cobertura da Terra** com base em imagens Sentinel-2 processadas localmente, utilizando **Random Forest**.

Desenvolvido com **Python**, **Streamlit**, **Plotly** e bibliotecas de geoprocessamento.

---

## 🔍 Funcionalidades

- Visualização de mapas classificados por ano.
- Gráficos interativos com área por classe.
- Tendência anual de métricas e classes.
- Tabelas exportáveis (área e métricas).
- Totalmente **offline** (sem Google Earth Engine).

---

## 📦 Estrutura da Pasta Pública
LandUseDashboard_Publico/
├── app.py
├── requirements.txt
├── outputs/
│ ├── maps/ # GeoTIFFs classificados (ano base)
│ ├── metrics/ # CSV com métricas por ano
│ └── area_por_classe.csv # Tabela com áreas por classe/ano
├── data/
│ └── bacia/
│ └── limite_bacia_varzea.shp (.shx, .dbf, .prj...)
└── README.md


---

## 🚀 Como Executar Localmente

1. Clone o repositório:

```bash
git clone https://github.com/emanuelmad/LandUseDashboard_Publico.git
cd LandUseDashboard_Publico

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt

streamlit run app.py

🌍 Desenvolvido por
Prof. Dr. Emanuel Araújo Silva
Laboratório de Geoprocessamento e Sensoriamento Remoto (LGSR)
Universidade Federal de Santa Maria (UFSM) – Frederico Westphalen – RS
