import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=1000)
st.title("KPI VITAIS - Análise Dinâmica")

# --- Upload do Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])
if uploaded_file:
    # Ler apenas colunas A até BN para base de dados de métricas
    df = pd.read_excel(uploaded_file, usecols="A:BN")
    df.columns = df.columns.str.strip()

    # Identificar colunas-chave
    col_session = [c for c in df.columns if "SessionName" in c][0]
    col_lap     = [c for c in df.columns if "Lap" in c][0]
    col_date    = [c for c in df.columns if "SessionDate" in c][0]
    col_car     = [c for c in df.columns if "CarAlias" in c][0]
    col_track   = [c for c in df.columns if "TrackName" in c][0]
    col_run     = [c for c in df.columns if "Run" in c and "Info" in c][0]

    # Criar eixo X composto
    df["SessionLapDate"] = (
        df[col_date].astype(str) + " | Run " + df[col_run].astype(str)
        + " | Lap " + df[col_lap].astype(str) + " | " + df[col_session].astype(str)
        + " | Track " + df[col_track].astype(str)
    )

    # ---------------- Helpers numéricos (conversão no plot) ----------------
    def as_numeric_column(frame, colname):
        """Cria e retorna o nome de uma coluna numérica convertida a partir de 'colname'."""
        new = f"__num__{colname}"
        frame[new] = pd.to_numeric(frame[colname], errors="coerce")
        return new

    # --- Sidebar: filtros gráficos de linha ---
    st.sidebar.header("Line Graphic Filters")
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", df[col_car].dropna().unique())
    track_options = ["VISUALIZAR TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
    track_sel = st.sidebar.selectbox("Selecione a Etapa (TrackName):", track_options)

    # Lista de métricas: mantém TODAS as colunas de métricas (não filtra por dtype)
    metric_options = list(df.columns[8:])

    # Pré-seleções desejadas
    preselect_metrics = {
        1: "pOil - Min",
        2: "pOil - Max",
        3: "pOil - Avg",
        4: "pFuel - Min",
        5: "pFuel - Max",
        6: "pFuel - Avg",
        7: "tWater - Max",
        8: "VBatt - Min"
    }

    def get_default_index(metric_name):
        return metric_options.index(metric_name) if metric_name in metric_options else 0

    # Seleção de métricas para Gráficos 1 a 8
    metric1 = st.sidebar.selectbox("Selecione métrica Gráfico 1:", metric_options, index=get_default_index(preselect_metrics[1]), key="metric_1")
    metric2 = st.sidebar.selectbox("Selecione métrica Gráfico 2:", metric_options, index=get_default_index(preselect_metrics[2]), key="metric_2")

    extra_metrics = {}
    for i in range(3, 9):
        extra_metrics[i] = st.sidebar.selectbox(
            f"Selecione métrica Gráfico {i}:",
            metric_options,
            index=get_default_index(preselect_metrics[i]),
            key=f"metric_extra_{i}"
        )

    # Scatter filters continuam separados
    st.sidebar.header("Scatter Graph Filters")
    track_disp     = st.sidebar.selectbox("Etapa - Scatter:", track_options, key="track_disp")
    metric_x       = st.sidebar.selectbox("Métrica X (Scatter):", metric_options, key="x_disp")
    metric_y       = st.sidebar.selectbox("Métrica Y (Scatter):", metric_options, key="y_disp")
    show_trendline = st.sidebar.checkbox("Mostrar linha de tendência")

    # Filtrar DataFrame principal
    filtered_df = df[df[col_car] == car_alias]
    if track_sel != "VISUALIZAR TODAS AS ETAPAS":
        filtered_df = filtered_df[filtered_df[col_track] == track_sel]
    filtered_df = filtered_df.sort_values(by=[col_date, col_run, col_lap, col_session, col_track])

    # Preparar DataFrame para scatter
    df_disp = df.copy()
    if track_disp != "VISUALIZAR TODAS AS ETAPAS":
        df_disp = df_disp[df_disp[col_track] == track_disp]

    # Função helper para plot de linha com stats (converte métrica para numérico aqui)
    def plot_line_stats(data, metric, title):
        if data.empty:
            return None, "_Sem dados_"

        data = data.copy()
        num_col = as_numeric_column(data, metric)
        fig = px.line(
            data, x="SessionLapDate", y=num_col, color=col_track, markers=True,
            labels={"SessionLapDate": "Date | Run | Lap | Session | Track", num_col: metric, col_track: "Etapa"},
            title=title
        )
        fig.update_layout(
            height=300,
            title_font=dict(size=20),
            xaxis=dict(tickangle=90, tickfont=dict(size=6)),
            yaxis=dict(title_font=dict(size=15))
        )
        vals = data[num_col].dropna()
        if not vals.empty:
            mn, mx = vals.min(), vals.max()
            mn_row = data.loc[vals.idxmin()]
            mx_row = data.loc[vals.idxmax()]
            fig.add_scatter(
                x=[mn_row["SessionLapDate"]], y=[mn], mode="markers+text",
                marker=dict(symbol="triangle-down", size=8), text=[f"Min: {mn:.3f}"], textposition="bottom center"
            )
            fig.add_scatter(
                x=[mx_row["SessionLapDate"]], y=[mx], mode="markers+text",
                marker=dict(symbol="triangle-up", size=8), text=[f"Max: {mx:.3f}"], textposition="top center"
            )
            stats_text = f"**Stats**: Min={mn:.3f}, Max={mx:.3f}, Avg={vals.mean():.3f}"
        else:
            stats_text = "_Sem dados numéricos válidos para estatísticas_"
        return fig, stats_text

    # Configuração dos 9 gráficos
    chart_configs = [
        ("line", metric1, "Gráfico 1"),
        ("line", metric2, "Gráfico 2"),
    ] + [
        ("line", extra_metrics[i], f"Gráfico {i}") for i in range(3, 9)
    ] + [("scatter", None, "Scatter Plot")]

    # Exibir 3x3 grid
    for row in range(3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            idx = row * 3 + col_idx
            kind, metric, title = chart_configs[idx]
            with col:
                if kind == "line":
                    fig, stats = plot_line_stats(filtered_df, metric, title)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.subheader(title)
                        st.info("Sem dados para este gráfico com os filtros atuais.")
                    st.markdown(stats)
                else:
                    if df_disp.empty:
                        st.subheader(title)
                        st.info("Sem dados para o scatter com os filtros atuais.")
                    else:
                        tmp = df_disp.copy()
                        num_x = as_numeric_column(tmp, metric_x)
                        num_y = as_numeric_column(tmp, metric_y)
                        trend = "ols" if show_trendline else None
                        fig_sc = px.scatter(
                            tmp, x=num_x, y=num_y, color=col_track,
                            trendline=trend,
                            hover_data=[col_session, col_lap, col_run],
                            labels={num_x: metric_x, num_y: metric_y, col_track: "Etapa"},
                            title=title
                        )
                        fig_sc.update_layout(
                            height=300,
                            title_font=dict(size=20),
                            xaxis=dict(tickfont=dict(size=6)),
                            yaxis=dict(title_font=dict(size=15))
                        )
                        st.plotly_chart(fig_sc, use_container_width=True)
else:
    st.info("Envie o arquivo para iniciar a análise.")
