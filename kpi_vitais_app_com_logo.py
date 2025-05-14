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
