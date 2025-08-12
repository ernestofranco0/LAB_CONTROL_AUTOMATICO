from dash import Input, Output, State, ctx
import plotly.graph_objs as go
import numpy as np
from utils.opc_client import opc_client_instance 


def register_callbacks(app):

    # Actualización de gráficos de nivel (simulados por ahora)
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

    # Callback modo manual: escritura a OPC
    @app.callback(
        Output('mensaje-manual', 'children'),
        Input('aplicar-manual', 'n_clicks'),
        State('manual-v1', 'value'),
        State('manual-v2', 'value'),
        State('manual-gamma1', 'value'),
        State('manual-gamma2', 'value'),
        prevent_initial_call=True
    )
    def aplicar_modo_manual(n_clicks, v1, v2, gamma1, gamma2):
        try:
            if v1 is not None:
                opc_client_instance.write_valve_voltage(1, float(v1))
            if v2 is not None:
                opc_client_instance.write_valve_voltage(2, float(v2))
            if gamma1 is not None:
                opc_client_instance.write_flow_ratio(1, float(gamma1))
            if gamma2 is not None:
                opc_client_instance.write_flow_ratio(2, float(gamma2))

            return "✅ Valores escritos correctamente al servidor OPC UA"
        except Exception as e:
            return f"❌ Error al escribir valores: {e}"

    # Callback para mostrar valores actuales del modo manual
    @app.callback(
        Output('valores-actuales-manual', 'children'),
        Input('intervalo-manual', 'n_intervals')
    )
    def actualizar_valores_actuales(n):
        try:
            u1 = opc_client_instance.read_valve_voltage(1)
            u2 = opc_client_instance.read_valve_voltage(2)
            g1 = opc_client_instance.read_flow_ratio(1)
            g2 = opc_client_instance.read_flow_ratio(2)

            if None in (u1, u2, g1, g2):
                return "⚠️ No conectado al servidor OPC UA o datos no disponibles."

            return f"Válvulas actuales: V1 = {u1:.2f} V, V2 = {u2:.2f} V | Razones actuales: γ1 = {g1:.2f}, γ2 = {g2:.2f}"
        except Exception as e:
            return f"⚠️ Error al leer valores actuales: {e}"

def register_alarm_callback(app):
    @app.callback(
        Output('alarma-tanques', 'children'),
        Input('intervalo-alarmas', 'n_intervals')
    )
    def actualizar_alarmas(n):
        mensajes = []
        with opc_client_instance._lock:
            for tanque, estado in opc_client_instance.alarm_states.items():
                if estado:
                    mensajes.append(f"⚠️ Tanque {tanque} bajo nivel crítico")
        return " | ".join(mensajes) if mensajes else ""
