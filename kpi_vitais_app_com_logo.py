# --- GRÁFICO 3: Dispersão com filtros dedicados ---
st.markdown("---")
st.subheader("Gráfico de Dispersão Personalizado")
st.sidebar.header("Filtros Dispersão")

track_options_disp = ["TODAS AS ETAPAS"] + sorted(df[col_track].dropna().unique().tolist())
track_disp = st.sidebar.selectbox("Etapa (TrackName) - Dispersão:", track_options_disp, key="track_disp")

metric_x = st.sidebar.selectbox("Métrica no eixo X:", list(df.columns[8:]), key="x_disp")
metric_y = st.sidebar.selectbox("Métrica no eixo Y:", list(df.columns[8:]), key="y_disp")

df_disp = df.copy()
if track_disp != "TODAS AS ETAPAS":
    df_disp = df_disp[df_disp[col_track] == track_disp]

try:
    fig3 = px.scatter(
        df_disp,
        x=metric_x,
        y=metric_y,
        color=col_track,
        trendline="ols",
        hover_data=[col_session, col_lap, col_run],
        title=f"Dispersão: {metric_x} vs {metric_y}"
    )
except Exception:
    fig3 = px.scatter(
        df_disp,
        x=metric_x,
        y=metric_y,
        color=col_track,
        hover_data=[col_session, col_lap, col_run],
        title=f"Dispersão: {metric_x} vs {metric_y}"
    )

fig3.update_layout(
    height=600,
    xaxis=dict(tickfont=dict(size=8)),
    yaxis=dict(tickfont=dict(size=8)),
    legend=dict(
        orientation="v",
        x=1.02,
        y=1,
        xanchor="left",
        font=dict(size=10)
    )
)
st.plotly_chart(fig3, use_container_width=True)
