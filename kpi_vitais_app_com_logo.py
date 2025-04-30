import streamlit as st
import pandas as pd
import plotly.express as px
import os
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=200)
st.title("KPI VITAIS - Análise Dinâmica")

# --- Carregar o arquivo Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # --- Prepara colunas auxiliares ---
    df['SessionDate - Info_str'] = df['SessionDate - Info'].astype(str)
    df['SessionDate - Info'] = pd.to_datetime(df['SessionDate - Info'], errors='coerce')
    df['SessionDate - Info_str'] = df['SessionDate - Info'].dt.strftime('%d/%m/%Y')
    df['Lap - Info'] = df['Lap - Info'].astype(str)  # garantir string

    df['SessionLapDate'] = df['SessionName - Info'].astype(str) + ' | Lap ' + df['Lap - Info'] + ' | ' + df['SessionDate - Info_str']

    # --- Sidebar para seleção ---
    st.sidebar.header("Filtros")
    car_alias = st.sidebar.selectbox("Selecione o CarAlias:", df['CarAlias - Info'].unique())
    y_axis = st.sidebar.selectbox("Selecione a métrica (Y Axis):", list(df.columns[8:41]))

    filtered_df = df[df['CarAlias - Info'] == car_alias]
    filtered_df = filtered_df.sort_values(by=['SessionDate - Info', 'SessionName - Info', 'Lap - Info'])

    # --- Gráfico Dinâmico ---
    fig = px.line(
        filtered_df,
        x="SessionLapDate",
        y=y_axis,
        color="TrackName - Info",
        markers=True,
        labels={
            "SessionLapDate": "Session | Lap | Date",
            y_axis: y_axis,
            "TrackName - Info": "Etapa"
        },
        title=f"{y_axis} por Session/Lap/Date"
    )

# Adicionar linha de tendência ao gráfico
import numpy as np
try:
    x_numeric = np.arange(len(filtered_df))
    y_values = filtered_df[y_axis].astype(float).values  # garantir numérico
    coef = np.polyfit(x_numeric, y_values, deg=1)
    trend = np.poly1d(coef)(x_numeric)

    fig.add_scatter(
        x=filtered_df["SessionLapDate"],
        y=trend,
        mode='lines',
        name='Tendência',
        line=dict(color='red', width=4, dash='solid'),  # destacada
        opacity=1.0,
        showlegend=True
    )
except Exception as e:
    st.warning(f"Não foi possível adicionar linha de tendência: {e}")

    # --- Exportar PDF ---
    st.sidebar.subheader("Exportar Gráficos em PDF")
    if st.sidebar.button("Exportar Todos KPIs para PDF"):
        pdf_filename = f"{car_alias}_KPIs.pdf"
        output_path = os.path.join("/tmp", pdf_filename)

        with PdfPages(output_path) as pdf:
            for metric in df.columns[8:41]:
                plt.figure(figsize=(14, 7))
                for session_date, group in filtered_df.groupby('SessionDate - Info'):
                    plt.plot(
                        group['SessionLapDate'],
                        group[metric],
                        marker='o',
                        label=session_date.date()
                    )
                plt.title(f"{metric} por Session/Lap/Date")
                plt.xlabel("Session | Lap | Date")
                plt.ylabel(metric)
                plt.xticks(rotation=90)
                plt.grid(axis='y')
                plt.legend(title='Data')
                plt.tight_layout()
                pdf.savefig()
                plt.close()

        with open(output_path, "rb") as file:
            btn = st.sidebar.download_button(
                label="Baixar PDF",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )
else:
    st.info("Envie o arquivo para iniciar a análise.")
