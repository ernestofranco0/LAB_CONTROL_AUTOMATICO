from dash import Input, Output, State
import plotly.graph_objects as go
from collections import deque
import time

from utils.opc_client import opc_client_instance
from calculos.pidManager import pid_h1, pid_h2, apply_params

def register_callbacks(app):
    # -----------------------------
    # Buffers en memoria (plot/series)
    # -----------------------------
    buffer_size = 100
    historial = {
        't': deque(maxlen=buffer_size),
        'h1': deque(maxlen=buffer_size),
        'h2': deque(maxlen=buffer_size),
        'h3': deque(maxlen=buffer_size),
        'h4': deque(maxlen=buffer_size),
        'v1': deque(maxlen=buffer_size),
        'v2': deque(maxlen=buffer_size),
        'g1': deque(maxlen=buffer_size),
        'g2': deque(maxlen=buffer_size),
    }

    def build_fig(x, y, title):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(x), y=list(y), mode='lines+markers'))
        fig.update_layout(title=title, xaxis_title='Tiempo [s]')
        return fig

    # -----------------------------
    # Visualización en tiempo real
    # -----------------------------
    @app.callback(
        Output('nivel-tanque-1', 'figure'),
        Output('nivel-tanque-2', 'figure'),
        Output('nivel-tanque-3', 'figure'),
        Output('nivel-tanque-4', 'figure'),
        Output('voltaje-valvula-1', 'figure'),
        Output('voltaje-valvula-2', 'figure'),
        Output('razon-flujo-1', 'figure'),
        Output('razon-flujo-2', 'figure'),
        Input('interval-update', 'n_intervals')
    )
    def update_niveles(_n):
        try:
            t_actual = time.time()

            h1 = opc_client_instance.read_tank_level(1)
            h2 = opc_client_instance.read_tank_level(2)
            h3 = opc_client_instance.read_tank_level(3)
            h4 = opc_client_instance.read_tank_level(4)

            v1 = opc_client_instance.read_valve_voltage(1)
            v2 = opc_client_instance.read_valve_voltage(2)

            g1 = opc_client_instance.read_flow_ratio(1)
            g2 = opc_client_instance.read_flow_ratio(2)

            if None in (h1, h2, h3, h4, v1, v2, g1, g2):
                raise ValueError("Datos no disponibles")

            historial['t'].append(t_actual)
            historial['h1'].append(h1)
            historial['h2'].append(h2)
            historial['h3'].append(h3)
            historial['h4'].append(h4)
            historial['v1'].append(v1)
            historial['v2'].append(v2)
            historial['g1'].append(g1)
            historial['g2'].append(g2)

            return (
                build_fig(historial['t'], historial['h1'], 'Nivel Tanque 1'),
                build_fig(historial['t'], historial['h2'], 'Nivel Tanque 2'),
                build_fig(historial['t'], historial['h3'], 'Nivel Tanque 3'),
                build_fig(historial['t'], historial['h4'], 'Nivel Tanque 4'),
                build_fig(historial['t'], historial['v1'], 'Voltaje Válvula 1'),
                build_fig(historial['t'], historial['v2'], 'Voltaje Válvula 2'),
                build_fig(historial['t'], historial['g1'], 'Razón de Flujo 1'),
                build_fig(historial['t'], historial['g2'], 'Razón de Flujo 2'),
            )

        except Exception as e:
            mensaje_error = f"Error: {e}"
            def error_fig(title):
                return go.Figure().update_layout(
                    title=title,
                    xaxis_title='Tiempo [s]',
                    annotations=[{
                        'text': mensaje_error,
                        'xref': 'paper', 'yref': 'paper',
                        'showarrow': False, 'font': {'color': 'red'}
                    }]
                )
            return (
                error_fig('Nivel Tanque 1'),
                error_fig('Nivel Tanque 2'),
                error_fig('Nivel Tanque 3'),
                error_fig('Nivel Tanque 4'),
                error_fig('Voltaje Válvula 1'),
                error_fig('Voltaje Válvula 2'),
                error_fig('Razón de Flujo 1'),
                error_fig('Razón de Flujo 2'),
            )

    # -----------------------------
    # MODO MANUAL: escribir u y γ
    # -----------------------------
    @app.callback(
        Output('mensaje-manual', 'children'),
        Input('aplicar-manual', 'n_clicks'),
        State('manual-v1', 'value'),
        State('manual-v2', 'value'),
        State('manual-gamma1', 'value'),
        State('manual-gamma2', 'value'),
        prevent_initial_call=True
    )
    def aplicar_modo_manual(_n_clicks, v1, v2, gamma1, gamma2):
        mensajes = []
        try:
            if v1 is not None:
                opc_client_instance.escribir("valvula1", float(v1))
                mensajes.append("✅ Válvula 1 escrita")
            if v2 is not None:
                opc_client_instance.escribir("valvula2", float(v2))
                mensajes.append("✅ Válvula 2 escrita")
            if gamma1 is not None:
                opc_client_instance.escribir("razon1", float(gamma1))
                mensajes.append("✅ Razón γ1 escrita")
            if gamma2 is not None:
                opc_client_instance.escribir("razon2", float(gamma2))
                mensajes.append("✅ Razón γ2 escrita")

            if not mensajes:
                return "⚠️ No se ingresó ningún valor."

            # Consejo sobre fase (no modifica nada automáticamente)
            total = (gamma1 or 0) + (gamma2 or 0)
            consejo = ""
            if gamma1 is not None or gamma2 is not None:
                if total < 1.0:
                    consejo = " | Modo: tendencia a FASE NO MÍNIMA (γ1+γ2<1)."
                elif total > 1.0:
                    consejo = " | Modo: tendencia a FASE MÍNIMA (γ1+γ2>1)."
                else:
                    consejo = " | Límite entre mínima/no mínima (γ1+γ2≈1)."

            return " | ".join(mensajes) + consejo

        except Exception as e:
            return f"❌ Error al aplicar valores: {e}"

    # -----------------------------
    # MODO AUTOMÁTICO: PID solo u1,u2
    # -----------------------------
    @app.callback(
        Output('modo-automatico', 'children'),
        Input('intervalo-automatico', 'n_intervals'),
        State('modo-switch', 'value')
    )
    def ejecutar_PID_en_lazo_cerrado(_n, switch_value):
        try:
            h1 = opc_client_instance.read_tank_level(1)
            h2 = opc_client_instance.read_tank_level(2)
            if h1 is None or h2 is None:
                return "⚠️ No se pudo leer el nivel de los tanques."

            # Calcular voltajes (γ NO se toca en automático)
            v1 = pid_h1.compute(h1)
            v2 = pid_h2.compute(h2)

            opc_client_instance.escribir("valvula1", float(v1))
            opc_client_instance.escribir("valvula2", float(v2))

            # Mensaje informativo del switch (no cambia γ, guía al usuario)
            if switch_value:
                return (f"✅ PID ejecutado: V1={v1:.2f}, V2={v2:.2f} | "
                        "Sugerencia: para FASE NO MÍNIMA ajusta γ en Modo Manual a γ1+γ2<1.")
            else:
                return f"✅ PID ejecutado: V1={v1:.2f}, V2={v2:.2f}"

        except Exception as e:
            return f"❌ Error en lazo cerrado PID: {e}"

    # -----------------------------
    # Actualizar parámetros del PID
    # -----------------------------
    @app.callback(
        Output('modo-automatico', 'children', allow_duplicate=True),
        Input('aplicar-PID', 'n_clicks'),
        State('auto-h1-ref', 'value'),
        State('auto-h2-ref', 'value'),
        State('auto-kp', 'value'),
        State('auto-ki', 'value'),
        State('auto-kd', 'value'),
        State('auto-aw', 'value'),
        prevent_initial_call=True
    )
    def aplicarPID(n_clicks, h1ref, h2ref, kp, ki, kd, aw):
        if not n_clicks:
            return "⚠️ No se aplicaron cambios."

        try:
            # Valores por defecto razonables si algún campo viene vacío
            kp = kp if kp is not None else pid_h1.Kp
            ki = ki if ki is not None else pid_h1.Ki
            kd = kd if kd is not None else pid_h1.Kd
            aw = aw if aw is not None else pid_h1.anti_windup_gain
            h1ref = h1ref if h1ref is not None else pid_h1.setpoint
            h2ref = h2ref if h2ref is not None else pid_h2.setpoint

            apply_params(kp, ki, kd, h1ref, h2ref, aw)
            return "✅ Parámetros PID actualizados."
        except Exception as e:
            return f"❌ Error al actualizar PID: {e}"
