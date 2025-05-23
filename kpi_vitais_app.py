
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("KPI VITAIS - Análise Dinâmica")

# --- Carregar o arquivo Excel ---
uploaded_file = st.file_uploader("Escolha a planilha KPI VITAIS:", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # --- Prepara colunas auxiliares ---
    df['SessionDate - Info_str'] = df['SessionDate - Info'].astype(str)
    df['SessionLapDate'] = df['SessionName - Info'] + ' | Lap ' + df['Lap - Info'].astype(str) + ' | ' + df['SessionDate - Info_str']

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
        color="SessionDate - Info",
        markers=True,
        labels={
            "SessionLapDate": "Session | Lap | Date",
            y_axis: y_axis,
            "SessionDate - Info": "Data da Sessão"
        },
        title=f"{y_axis} por Session/Lap/Date"
    )

    fig.update_layout(
        xaxis_tickangle=90,
        xaxis_title="Session | Lap | Date",
        yaxis_title=y_axis,
        legend_title="Data",
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

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
