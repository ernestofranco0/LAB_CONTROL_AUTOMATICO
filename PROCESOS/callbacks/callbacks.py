from dash import Input, Output, State, ctx
import plotly.graph_objs as go
import numpy as np
from utils.opc_client import opc_client_instance 
from collections import deque
import time

from calculos.pidManager import pid_h1, pid_h2, PID_H1, PID_H2

def register_callbacks(app):

    def faseNoMinima(gammaUno , gammaDos):
        while gammaUno + gammaUno <= 1:
            gammaUno += 0.01
            gammaDos += 0.01

        return gammaUno, gammaDos

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
        'g2': deque(maxlen=buffer_size)
    }

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
    def update_niveles(n):
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

            # Agregar a historial
            historial['t'].append(t_actual)
            historial['h1'].append(h1)
            historial['h2'].append(h2)
            historial['h3'].append(h3)
            historial['h4'].append(h4)
            historial['v1'].append(v1)
            historial['v2'].append(v2)
            historial['g1'].append(g1)
            historial['g2'].append(g2)

            def build_fig(x, y, title):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(x), y=list(y), mode='lines+markers'))
                fig.update_layout(title=title, xaxis_title='Tiempo [s]')
                return fig

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
            print(mensaje_error)

            def error_fig(title):
                return go.Figure().update_layout(
                    title=title,
                    xaxis_title='Tiempo [s]',
                    annotations=[{
                        'text': mensaje_error,
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'color': 'red'}
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
        mensajes = []
        try:
            if v1 is not None:
                opc_client_instance.escribir("valvula1", float(v1))
                mensajes.append("✅ Válvula 1 escrita.")
            if v2 is not None:
                opc_client_instance.escribir("valvula2", float(v2))
                mensajes.append("✅ Válvula 2 escrita.")
            if gamma1 is not None:
                opc_client_instance.escribir("razon1", float(gamma1))
                mensajes.append("✅ Razón 1 escrita.")
            if gamma2 is not None:
                opc_client_instance.escribir("razon2", float(gamma2))
                mensajes.append("✅ Razón 2 escrita.")

            if not mensajes:
                return "⚠️ No se ingresó ningún valor."

            return " | ".join(mensajes)

        except Exception as e:
            return f"❌ Error al aplicar valores: {e}"

    # Callback para ingresar parametros PID
    @app.callback(
        Output('modo-automatico', 'children'),
        Input('aplicar-PID', 'n_clicks'),
        State('auto-h1-ref', 'value'),
        State('auto-h2-ref', 'value'),
        State('auto-kp', 'value'),
        State('auto-ki', 'value'),
        State('auto-kd', 'value'),
        State('auto-aw', 'value'),
        State('modo-switch', 'value'),
        prevent_initial_call=True
    )


    def aplicarPID(n_clicks, h1ref, h2ref, kp, ki, kd, aw, switch_value):

        if n_clicks is not None:
            pid_h1.setParams(kp, ki, kd, h1ref, aw) #Setear los parametros de los PID's
            pid_h1.reset()
            pid_h2.setParams(kp, ki, kd, h2ref, aw)
            pid_h2.reset()
            PID_H1.setParams(kp, ki, kd, h2ref, aw)
            PID_H1.reset()
            PID_H2.setParams(kp, ki, kd, h2ref, aw)
            PID_H2.reset()


            lecturaH1 = opc_client_instance.read_tank_level(1) #Para que los PID lean los niveles de los estanques.
            lecturaH2 = opc_client_instance.read_tank_level(2)

            salidah1 = pid_h1.compute(lecturaH1) #Calcula el voltage para la bomba.
            salidah2 = pid_h2.compute(lecturaH2)
            salidaH1 = PID_H1.compute(lecturaH1) #Calcula las razones para las bombas 
            salidaH2 = PID_H2.compute(lecturaH2)

            #El controlador envia el voltge correspondiente a la valvula
            opc_client_instance.escribir("valvula1", float(salidah1))
            opc_client_instance.escribir("valvula2", float(salidah2))

            if switch_value:                                            #Revisa si esta activada la fase no minima

               razon1 ,razon2 = faseNoMinima(salidaH1 , salidaH2)       #Lleva las razones a fase no minima
               opc_client_instance.escribir("razon1", float(razon1))   #Las carga al cliente
               opc_client_instance.escribir("razon2", float(razon2))

            else:
               opc_client_instance.escribir("razon1", float(salidaH1))  
               opc_client_instance.escribir("razon2", float(salidaH2))

#Estan comentados, para que la pagina funcione, mientras la simulación no este funcionando.

            mensaje = (
            f"Parámetros PID H1:\n"
            f"Kp = {pid_h1.Kp}, Ki = {pid_h1.Ki}, Kd = {pid_h1.Kd}, "
            f"Setpoint = {pid_h1.setpoint}, Anti-Windup = {pid_h1.anti_windup_gain}\n"
            f"Parámetros PID H2:\n"
            f"Kp = {pid_h2.Kp}, Ki = {pid_h2.Ki}, Kd = {pid_h2.Kd}, "
            f"Setpoint = {pid_h2.setpoint}, Anti-Windup = {pid_h2.anti_windup_gain}"
        )
            return mensaje
        
        return 'Cambios no aplicados, revise sus parametros'

def register_alarm_callback(app):
    pass
    # @app.callback(
    #     Output('alarma-tanques', 'children'),
    #     Input('intervalo-alarmas', 'n_intervals')
    # )
    # def actualizar_alarmas(n):
    #     mensajes = []
    #     with opc_client_instance._lock:
    #         for tanque, estado in opc_client_instance.alarm_states.items():
    #             if estado:
    #                 mensajes.append(f"⚠️ Tanque {tanque} bajo nivel crítico")
    #     return " | ".join(mensajes) if mensajes else ""
