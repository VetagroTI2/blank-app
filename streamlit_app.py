import streamlit as st
import pandas as pd
import plotly.express as px
import json
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

# -------------------------
# Carregar base de dados
# -------------------------
arquivo = "denuncias_vigilancia_sanitaria_fortaleza_bigdata.csv"
df = pd.read_csv(arquivo, encoding="latin1", sep=";")

st.set_page_config(page_title="Dashboard de Denúncias", layout="wide")

# -------------------------
# Tratativa e limpeza de dados base de dados
# -------------------------

#Tirar as linhas vazias
df.dropna(inplace=True)
#Tirar as linhas duplicadas
df.drop_duplicates(inplace=True)
#colocar o nome das colunas em minusculo
df.columns = [c.lower() for c in df.columns]


# -------------------------
# Menu lateral
# -------------------------
menu = st.sidebar.radio(
    "Escolha a análise",
    [
        "📊 Visão Geral",
        "🏙️ Ranking de Bairros",
        "🍽️ Tipos de Problemas em Restaurantes",
        "📈 Evolução Temporal",
        "📌 Situação Atual (Status)",
        "♻️ Reincidência de Denúncias",
        "🗺️ Mapa"
    ]
)

# -------------------------
# VISÃO GERAL
# -------------------------
if menu == "📊 Visão Geral":
    st.title("📊 Visão Geral das Denúncias")

    # Status
    status_count = df['status_denuncia'].value_counts().reset_index()
    status_count.columns = ['Status', 'Quantidade']
    fig1 = px.bar(status_count, x='Status', y='Quantidade', title="Status das denúncias")
    st.plotly_chart(fig1, use_container_width=True)

    # Canal de entrada
    canal_count = df['canal_entrada'].value_counts().reset_index()
    canal_count.columns = ['Canal', 'Quantidade']
    fig2 = px.pie(canal_count, names='Canal', values='Quantidade', title='Canais de Entrada')
    st.plotly_chart(fig2, use_container_width=True)


# -------------------------
# RANKING DE BAIRROS
# -------------------------
elif menu == "🏙️ Ranking de Bairros":
    st.title("🏙️ Ranking de Bairros com mais Denúncias")

    bairro_count = df['bairro'].value_counts().reset_index()
    bairro_count.columns = ['Bairro', 'Quantidade']

    # Gráfico de barras horizontais
    fig = px.bar(
        bairro_count.sort_values("Quantidade", ascending=True),
        x="Quantidade",
        y="Bairro",
        orientation="h",
        title="Ranking de Bairros por Número de Denúncias"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Resposta analítica
    top_bairros = bairro_count.head(5)
    st.markdown("### 📌 Análise")
    st.write(
        f"Os bairros com maior número de denúncias são **{', '.join(top_bairros['Bairro'])}**, "
        f"liderando o ranking geral. Isso indica áreas prioritárias para intensificação da fiscalização."
    )


# -------------------------
# TIPOS DE PROBLEMAS EM RESTAURANTES
# -------------------------
elif menu == "🍽️ Tipos de Problemas em Restaurantes":
    st.title("🍽️ Tipos de Problemas Mais Denunciados em Restaurantes")

    if "assunto_denuncia" in df.columns:
        problema_count = df['assunto_denuncia'].value_counts().reset_index()
        problema_count.columns = ['Problema', 'Quantidade']

        fig = px.bar(
            problema_count.sort_values("Quantidade", ascending=True),
            x="Quantidade",
            y="Problema",
            orientation="h",
            title="Problemas Mais Frequentes em Restaurantes"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📌 Análise")
        top_problemas = problema_count.head(3)
        st.write(
            f"As categorias mais recorrentes são **{', '.join(top_problemas['Problema'])}**, "
            "relacionadas principalmente a condições higiênico-sanitárias, manipulação de alimentos e validade."
        )
    else:
        st.warning("⚠️ A coluna 'tipo_problema' não existe no dataset.")


# -------------------------
# EVOLUÇÃO TEMPORAL
# -------------------------
elif menu == "📈 Evolução Temporal":
    st.title("📈 Evolução Temporal das Denúncias")

    if "data_denuncia" in df.columns:
        df["data_denuncia"] = pd.to_datetime(df["data_denuncia"], errors="coerce")

        # Criar coluna de ano-mês como string (YYYY-MM)
        df["ano_mes"] = df["data_denuncia"].dt.to_period("M").astype(str)

        time_series = df.groupby("ano_mes").size().reset_index(name="Quantidade")

        fig = px.line(time_series, x="ano_mes", y="Quantidade", markers=True,
                      title="Evolução Mensal das Denúncias")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📌 Análise")
        st.write(
            "A série temporal mostra variações sazonais, com picos em determinados meses, "
            "sugerindo períodos de maior fiscalização ou maior incidência de irregularidades."
        )
    else:
        st.warning("⚠️ A coluna 'data_registro' não existe no dataset.")


# -------------------------
# SITUAÇÃO ATUAL (STATUS)
# -------------------------
elif menu == "📌 Situação Atual (Status)":
    st.title("📌 Situação Atual das Denúncias")

    status_count = df['status_denuncia'].value_counts(normalize=False).reset_index()
    status_count.columns = ['Status', 'Quantidade']

    fig = px.bar(status_count, x='Status', y='Quantidade', title="Distribuição por Status")
    st.plotly_chart(fig, use_container_width=True)

    # Percentuais
    total = status_count["Quantidade"].sum()
    status_count["Percentual"] = (status_count["Quantidade"] / total * 100).round(1)

    st.markdown("### 📌 Análise")
    st.write(
        "A análise dos status evidencia a eficiência da vigilância sanitária: "
        f"aproximadamente {status_count.iloc[0]['Percentual']}% das denúncias estão em **{status_count.iloc[0]['Status']}**, "
        "o que mostra o andamento do processo de apuração."
    )


# -------------------------
# REINCIDÊNCIA DE DENÚNCIAS
# -------------------------
elif menu == "♻️ Reincidência de Denúncias":
    st.title("♻️ Reincidência de Denúncias em Bairros")

    if "bairro" in df.columns and "data_denuncia" in df.columns:
        # Converter para datetime
        df["data_denuncia"] = pd.to_datetime(df["data_denuncia"], errors="coerce")
        df["ano_mes"] = df["data_denuncia"].dt.to_period("M").astype(str)

        # Contar denúncias por bairro e mês
        reincidencia = df.groupby(["bairro", "ano_mes"]).size().reset_index(name="Quantidade")

        # Heatmap (bairro x tempo)
        fig = px.density_heatmap(
            reincidencia,
            x="ano_mes",
            y="bairro",
            z="Quantidade",
            color_continuous_scale="Reds",
            title="Heatmap de Reincidência de Denúncias por Bairro ao Longo do Tempo"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📌 Análise")
        st.write(
            "A reincidência é medida pelo número de vezes em que um bairro aparece com novas denúncias em meses diferentes. "
            "O heatmap evidencia os bairros mais críticos e os períodos com maior concentração de problemas, "
            "enquanto o gráfico empilhado mostra a contribuição de cada bairro ao longo do tempo."
        )

    else:
        st.warning("⚠️ As colunas 'bairro' e/ou 'data_denuncia' não existem no dataset.")


# -------------------------
# MAPA
# -------------------------
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Denúncias por Bairro - Fortaleza")

    if "denuncias" not in df.columns:
        df_map = df.groupby("bairro").size().reset_index(name="denuncias")
    else:
        df_map = df.copy()

    df_map["BAIRRO"] = df_map["bairro"].str.strip().str.upper()
    bairro_denuncias = df_map.set_index("BAIRRO")["denuncias"].to_dict()

    with open(r"Bairros_de_Fortaleza.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    for feature in geojson_data["features"]:
        feature["properties"]["Nome"] = feature["properties"]["Nome"].strip().upper()

    m = folium.Map(location=[-3.73, -38.54], zoom_start=11)

    min_denuncias = min(bairro_denuncias.values())
    max_denuncias = max(bairro_denuncias.values())
    colormap = cm.LinearColormap(colors=["green", "red"], vmin=min_denuncias, vmax=max_denuncias,
                                 caption="Número de Denúncias")

    def style_function(feature):
        bairro = feature["properties"]["Nome"]
        n_denuncias = bairro_denuncias.get(bairro, 0)
        return {"fillColor": colormap(n_denuncias), "color": "black", "weight": 1, "fillOpacity": 0.6}

    folium.GeoJson(
        geojson_data,
        name="Bairros",
        tooltip=folium.GeoJsonTooltip(fields=["Nome"], aliases=["Bairro:"], localize=True),
        style_function=style_function
    ).add_to(m)

    colormap.add_to(m)
    st_folium(m, width=900, height=600)
