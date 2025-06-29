# 🌱 Land Use Dashboard - Várzea, RS

Este repositório contém a versão pública do **Dashboard de Classificação de Uso e Cobertura da Terra**, desenvolvido com foco na **Bacia Hidrográfica do Rio da Várzea (RS)**, utilizando imagens Sentinel-2 classificadas com modelo Random Forest.

O dashboard permite a visualização interativa de mapas classificados, métricas de avaliação (como F1-Score) e tendências anuais por classe de uso do solo.

---

## 🔗 Acesse o Dashboard

> [Clique aqui para acessar o app online](https://land-use-dashboard.streamlit.app/)  
> *(será atualizado assim que o deploy no Streamlit Cloud for concluído)*

---

## 📦 Funcionalidades

- Visualização interativa do **mapa classificado por ano**
- Gráficos dinâmicos de **área por classe** e **tendência temporal**
- Tabelas e **download em CSV** das métricas e estatísticas por classe
- Dashboard totalmente construído com **Python + Streamlit + Plotly + Folium**

---

## 🗂️ Estrutura dos dados (versão pública)

Esta versão contém apenas os dados processados essenciais para visualização:

LandUseDashboard_Publico/
├── app.py # Código principal do dashboard Streamlit
├── outputs/
│ ├── maps/ # Mapas classificados por ano (.tif)
│ ├── area_por_classe.csv # Tabela com área por classe (ha)
│ └── metrics/ # Métricas de avaliação por ano (.csv)
├── data/
│ └── bacia/
│ └── limite_bacia_varzea.shp # Shapefile da bacia (vetor)
├── requirements.txt # Dependências do projeto
└── README.md # Este arquivo
---

## ⚙️ Requisitos para execução local

Instale as dependências com:

```bash
pip install -r requirements.txt

streamlit run app.py

👨‍💻 Desenvolvedor
Prof. Dr. Emanuel Araújo Silva
Laboratório de Geoprocessamento e Sensoriamento Remoto - LGSR
Universidade Federal de Santa Maria – UFSM/FW
📧 emanuel.ufrpe@gmail.com

📜 Licença
Este projeto está disponível para fins acadêmicos e de demonstração.
Consulte o autor para uso comercial ou adaptação em larga escala.
