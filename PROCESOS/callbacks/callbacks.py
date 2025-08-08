from dash import Input, Output
import plotly.graph_objs as go
import numpy as np

def register_callbacks(app):

    @app.callback(
        Output('nivel-tanque-1', 'figure'),
        Output('nivel-tanque-2', 'figure'),
        Output('nivel-tanque-3', 'figure'),
        Output('nivel-tanque-4', 'figure'),
        Input('interval-update', 'n_intervals')
    )
    def update_niveles(n):
        # Simulación: variación senoidal + ruido
        t = np.linspace(0, 10, 100)
        h1 = 20 + 5 * np.sin(0.5 * t + n * 0.1) + np.random.normal(0, 0.5, size=100)
        h2 = 25 + 4 * np.sin(0.6 * t + n * 0.1) + np.random.normal(0, 0.5, size=100)
        h3 = 15 + 3 * np.sin(0.4 * t + n * 0.1) + np.random.normal(0, 0.3, size=100)
        h4 = 10 + 2 * np.sin(0.3 * t + n * 0.1) + np.random.normal(0, 0.3, size=100)

        def build_fig(y, title):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=t, y=y, mode='lines', name=title))
            fig.update_layout(title=title, xaxis_title='Tiempo [s]', yaxis_title='Nivel [cm]')
            return fig

        return (
            build_fig(h1, 'Nivel Tanque 1'),
            build_fig(h2, 'Nivel Tanque 2'),
            build_fig(h3, 'Nivel Tanque 3'),
            build_fig(h4, 'Nivel Tanque 4'),
        )
