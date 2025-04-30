
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import itertools

CAMINHO_ARQUIVO = r"C:/Users/vitor/OneDrive/Área de Trabalho/MotorSport/BTZ/KPI WINTAX/DataBase/KPI VITAIS - 25ET1.xlsx"

st.set_page_config(layout="wide")
st.image("btz_logo.png", width=200)
st.title("KPI VITAIS - Análise Dinâmica com Monitoramento")

if st.button("🔄 Atualizar planilha"):
    with st.spinner("Atualizando dados..."):
        try:
            df = pd.read_excel(CAMINHO_ARQUIVO)
            st.success("✅ Dados atualizados com sucesso!")

            # Adiciona coluna auxiliar
            df['SessionDate - Info_str'] = df['SessionDate - Info'].astype(str)
            df['SessionLapDate'] = df['SessionName - Info'] + ' | Lap ' + df['Lap - Info'].astype(str) + ' | ' + df['SessionDate - Info_str']

            # Seletores
            car_options = df['CarAlias - Info'].unique()
            car_selector = st.selectbox("Selecionar Carro", car_options)

            y_options = list(df.columns[8:41])
            y_selector = st.selectbox("Selecionar Métrica (Y)", y_options, index=y_options.index("Lap Time - Info"))

            df_filtrado = df[df['CarAlias - Info'] == car_selector]
            df_filtrado = df_filtrado.sort_values(by=['SessionDate - Info', 'SessionName - Info', 'Lap - Info'])

            fig, ax = plt.subplots(figsize=(14,7))

            cores = itertools.cycle(plt.cm.tab20.colors)
            cores_datas = {data: next(cores) for data in df_filtrado['SessionDate - Info'].unique()}

            for data, grupo in df_filtrado.groupby('SessionDate - Info'):
                cor = cores_datas[data]
                ax.plot(grupo['SessionLapDate'], grupo[y_selector], marker='o', color=cor, label=data.date())

            ax.set_title(f"{y_selector} por Dia/Sessão/Volta")
            ax.set_xlabel("Session | Lap | Date")
            ax.set_ylabel(y_selector)
            ax.tick_params(axis='x', rotation=90)
            ax.grid(axis='y')
            ax.legend(title="SessionDate")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Erro ao carregar o Excel: {e}")
else:
    st.info("Clique no botão acima para carregar os dados.")
