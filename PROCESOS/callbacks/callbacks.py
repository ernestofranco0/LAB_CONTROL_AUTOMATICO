from dash import Input, Output, State, no_update, html, dcc
import plotly.graph_objects as go
from collections import deque
import time
import io
import numpy as np
import pandas as pd

from utils.opc_client import opc_client_instance
from calculos.pidManager import pid_h1, pid_h2, apply_params  # apply_params queda por compatibilidad

def register_callbacks(app):
    # -----------------------------
    # Buffers en memoria (plot/series)
    # -----------------------------
    buffer_size = 100
    historial = {
        't0': None,  # para tiempo relativo
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

    def _rel_time():
        t = time.time()
        if historial['t0'] is None:
            historial['t0'] = t
        return t - historial['t0']

    def build_fig(x, y, title, yref=None, band=None):
        fig = go.Figure()
        fig.add_scatter(x=list(x), y=list(y), mode='lines', name=title)

        if yref is not None:
            # Línea central (referencia)
            fig.add_hline(y=yref, line_dash='dot', line_color='black',
                          annotation_text='ref', annotation_position='top right')

            if band is not None and band > 0:
                y_up = yref + band
                y_dn = yref - band
                # Banda sombreada (entre y_dn y y_up)
                fig.add_shape(
                    type="rect",
                    xref="paper", yref="y",
                    x0=0, x1=1, y0=y_dn, y1=y_up,
                    line=dict(width=0),
                    fillcolor="rgba(0, 150, 255, 0.12)"
                )
                # Líneas superior e inferior
                fig.add_hline(y=y_up, line_dash='dash', line_color='rgba(0,150,255,0.7)')
                fig.add_hline(y=y_dn, line_dash='dash', line_color='rgba(0,150,255,0.7)')

        fig.update_layout(title=title, xaxis_title='Tiempo [s]',
                          margin=dict(l=20, r=20, t=40, b=20), height=260)
        return fig

    def build_dual_u(x, y1, y2):
        fig = go.Figure()
        fig.add_scatter(x=list(x), y=list(y1), mode='lines', name='u1 (V)')
        fig.add_scatter(x=list(x), y=list(y2), mode='lines', name='u2 (V)')
        fig.update_layout(title='Voltajes aplicados', xaxis_title='Tiempo [s]',
                          legend_orientation='h',
                          margin=dict(l=20, r=20, t=40, b=20), height=300)
        return fig

    # -----------------------------
    # Helpers PID
    # -----------------------------
    def _apply_one_pid(pid, kp=None, ki=None, kd=None, aw=None, sp=None):
        """
        Aplica parámetros a un objeto PID con la mejor compatibilidad posible.
        Prioriza métodos; si no existen, asigna atributos.
        """
        for meth in ('update_params', 'set_params', 'set_gains'):
            if hasattr(pid, meth):
                try:
                    getattr(pid, meth)(
                        kp if kp is not None else pid.Kp,
                        ki if ki is not None else pid.Ki,
                        kd if kd is not None else pid.Kd,
                        aw if aw is not None else getattr(pid, 'anti_windup_gain', None)
                    )
                    break
                except TypeError:
                    getattr(pid, meth)(
                        kp if kp is not None else pid.Kp,
                        ki if ki is not None else pid.Ki,
                        kd if kd is not None else pid.Kd
                    )
                    break
                except Exception:
                    pass

        if kp is not None and hasattr(pid, 'Kp'): pid.Kp = kp
        if ki is not None and hasattr(pid, 'Ki'): pid.Ki = ki
        if kd is not None and hasattr(pid, 'Kd'): pid.Kd = kd
        if aw is not None:
            if hasattr(pid, 'anti_windup_gain'):
                pid.anti_windup_gain = aw
            elif hasattr(pid, 'aw'):
                pid.aw = aw

        if sp is not None:
            if hasattr(pid, 'setpoint'):
                pid.setpoint = sp
            elif hasattr(pid, 'r'):
                pid.r = sp

    # -----------------------------
    # Visualización en tiempo real (MODO MANUAL)
    # -----------------------------
    @app.callback(
        Output('nivel-manual-1', 'figure'),
        Output('nivel-manual-2', 'figure'),
        Output('nivel-manual-3', 'figure'),
        Output('nivel-manual-4', 'figure'),
        Output('voltajes-manual', 'figure'),
        Input('interval-update', 'n_intervals')
    )
    def update_niveles(_n):
        try:
            t_rel = _rel_time()

            h1 = opc_client_instance.read_tank_level(1)
            h2 = opc_client_instance.read_tank_level(2)
            h3 = opc_client_instance.read_tank_level(3)
            h4 = opc_client_instance.read_tank_level(4)

            v1 = opc_client_instance.read_valve_voltage(1)
            v2 = opc_client_instance.read_valve_voltage(2)

            try:
                g1 = opc_client_instance.read_flow_ratio(1)
                g2 = opc_client_instance.read_flow_ratio(2)
            except Exception:
                g1 = g2 = None

            if None in (h1, h2, h3, h4, v1, v2):
                raise ValueError("Datos no disponibles")

            historial['t'].append(t_rel)
            historial['h1'].append(h1)
            historial['h2'].append(h2)
            historial['h3'].append(h3)
            historial['h4'].append(h4)
            historial['v1'].append(v1)
            historial['v2'].append(v2)
            if g1 is not None: historial['g1'].append(g1)
            if g2 is not None: historial['g2'].append(g2)

            return (
                build_fig(historial['t'], historial['h1'], 'Nivel Tanque 1 (cm)'),
                build_fig(historial['t'], historial['h2'], 'Nivel Tanque 2 (cm)'),
                build_fig(historial['t'], historial['h3'], 'Nivel Tanque 3 (cm)'),
                build_fig(historial['t'], historial['h4'], 'Nivel Tanque 4 (cm)'),
                build_dual_u(historial['t'], historial['v1'], historial['v2']),
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
                    }],
                    margin=dict(l=20, r=20, t=40, b=20), height=260
                )
            return (
                error_fig('Nivel Tanque 1 (cm)'),
                error_fig('Nivel Tanque 2 (cm)'),
                error_fig('Nivel Tanque 3 (cm)'),
                error_fig('Nivel Tanque 4 (cm)'),
                error_fig('Voltajes aplicados'),
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
    # MODO AUTOMÁTICO: PID (ejecución en lazo cerrado)
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

            v1 = pid_h1.compute(h1)
            v2 = pid_h2.compute(h2)

            opc_client_instance.escribir("valvula1", float(v1))
            opc_client_instance.escribir("valvula2", float(v2))

            if switch_value:
                return (f"✅ PID ejecutado: V1={v1:.2f}, V2={v2:.2f} | "
                        "Sugerencia: para FASE NO MÍNIMA ajusta γ en Modo Manual a γ1+γ2<1.")
            else:
                return f"✅ PID ejecutado: V1={v1:.2f}, V2={v2:.2f}"

        except Exception as e:
            return f"❌ Error en lazo cerrado PID: {e}"

    # -----------------------------
    # MODO AUTOMÁTICO: figuras con referencia
    # -----------------------------
    @app.callback(
        Output('auto-h1-fig', 'figure'),
        Output('auto-h2-fig', 'figure'),
        Input('intervalo-automatico', 'n_intervals')
    )
    def actualizar_figs_auto(_n):
        try:
            t_rel = _rel_time()
            h1 = opc_client_instance.read_tank_level(1)
            h2 = opc_client_instance.read_tank_level(2)
            if h1 is None or h2 is None:
                raise ValueError("Datos no disponibles")

            historial['t'].append(t_rel)
            historial['h1'].append(h1)
            historial['h2'].append(h2)

            delta = 0.01  # banda ±0.01
            f1 = build_fig(historial['t'], historial['h1'], 'h1 (cm)', yref=getattr(pid_h1, 'setpoint', None), band=delta)
            f2 = build_fig(historial['t'], historial['h2'], 'h2 (cm)', yref=getattr(pid_h2, 'setpoint', None), band=delta)
            return f1, f2
        except Exception as e:
            msg = f"Error: {e}"
            def err(title):
                return go.Figure().update_layout(
                    title=title,
                    annotations=[{'text': msg, 'xref':'paper','yref':'paper',
                                  'showarrow': False, 'font': {'color':'red'}}]
                )
            return err('h1 (cm)'), err('h2 (cm)')

    # -----------------------------
    # Actualizar parámetros del PID (por lazo)
    # -----------------------------
    @app.callback(
        Output('modo-automatico', 'children', allow_duplicate=True),
        Input('aplicar-PID', 'n_clicks'),
        # Referencias
        State('auto-h1-ref', 'value'),
        State('auto-h2-ref', 'value'),
        # PID h1
        State('auto-h1-kp', 'value'),
        State('auto-h1-ki', 'value'),
        State('auto-h1-kd', 'value'),
        State('auto-h1-aw', 'value'),
        # PID h2
        State('auto-h2-kp', 'value'),
        State('auto-h2-ki', 'value'),
        State('auto-h2-kd', 'value'),
        State('auto-h2-aw', 'value'),
        prevent_initial_call=True
    )
    def aplicarPID(n_clicks,
                   h1ref, h2ref,
                   kp1, ki1, kd1, aw1,
                   kp2, ki2, kd2, aw2):
        if not n_clicks:
            return "⚠️ No se aplicaron cambios."
        try:
            _apply_one_pid(
                pid_h1,
                kp=kp1 if kp1 is not None else getattr(pid_h1, 'Kp', None),
                ki=ki1 if ki1 is not None else getattr(pid_h1, 'Ki', None),
                kd=kd1 if kd1 is not None else getattr(pid_h1, 'Kd', None),
                aw=aw1 if aw1 is not None else getattr(pid_h1, 'anti_windup_gain', getattr(pid_h1, 'aw', None)),
                sp=h1ref if h1ref is not None else getattr(pid_h1, 'setpoint', None)
            )
            _apply_one_pid(
                pid_h2,
                kp=kp2 if kp2 is not None else getattr(pid_h2, 'Kp', None),
                ki=ki2 if ki2 is not None else getattr(pid_h2, 'Ki', None),
                kd=kd2 if kd2 is not None else getattr(pid_h2, 'Kd', None),
                aw=aw2 if aw2 is not None else getattr(pid_h2, 'anti_windup_gain', getattr(pid_h2, 'aw', None)),
                sp=h2ref if h2ref is not None else getattr(pid_h2, 'setpoint', None)
            )

            msg_h1 = f"h1: Kp={getattr(pid_h1,'Kp',None):.4g}, Ki={getattr(pid_h1,'Ki',None):.4g}, Kd={getattr(pid_h1,'Kd',None):.4g}, AW={getattr(pid_h1,'anti_windup_gain', getattr(pid_h1,'aw', None))}, ref={getattr(pid_h1,'setpoint',None)}"
            msg_h2 = f"h2: Kp={getattr(pid_h2,'Kp',None):.4g}, Ki={getattr(pid_h2,'Ki',None):.4g}, Kd={getattr(pid_h2,'Kd',None):.4g}, AW={getattr(pid_h2,'anti_windup_gain', getattr(pid_h2,'aw', None))}, ref={getattr(pid_h2,'setpoint',None)}"
            return f"✅ PID actualizados.\n{msg_h1}\n{msg_h2}"
        except Exception as e:
            return f"❌ Error al actualizar PID: {e}"

    # -----------------------------
    # Alarmas
    # -----------------------------
    @app.callback(
        Output('estado-conexion', 'children'),
        Input('intervalo-alarmas', 'n_intervals')
    )
    def actualizar_estado_conexion(_n):
        try:
            ok = opc_client_instance.is_connected() if hasattr(opc_client_instance, "is_connected") else True
            return f"Estado OPC UA: {'Conectado' if ok else 'Desconectado'}"
        except Exception:
            return "Estado OPC UA: Desconectado"

    @app.callback(
        Output('subscripcion-estado', 'children'),
        Input('opc-alarm-sub-switch', 'value'),
        State('umbral-h1', 'value'),
        State('umbral-h2', 'value'),
        State('umbral-h3', 'value'),
        State('umbral-h4', 'value'),
        prevent_initial_call=False
    )
    def gestionar_suscripcion(sub_on, u1, u2, u3, u4):
        try:
            opc_client_instance.set_alarm_thresholds(u1, u2, u3, u4)
        except Exception:
            pass
        try:
            if sub_on:
                ok = opc_client_instance.enable_level_subscription()
                return "Subscripción: Activa" if ok else "Subscripción: Error al activar"
            else:
                opc_client_instance.disable_level_subscription()
                return "Subscripción: Inactiva"
        except Exception as e:
            return f"Subscripción: Error ({e})"

    @app.callback(
        Output('alarma-estado', 'children'),
        Output('alarma-estado', 'color'),
        Output('alarma-lista', 'children'),
        Input('intervalo-alarmas', 'n_intervals'),
    )
    def refrescar_alarmas(_n):
        try:
            niveles, umbrales, alarmas = opc_client_instance.get_alarm_snapshot()
            activos = [i for i in ('H1','H2','H3','H4') if alarmas.get(i, False)]
            if activos:
                items = []
                for key in activos:
                    h = niveles.get(key)
                    thr = umbrales.get(key)
                    h_txt = f"{h:.2f}" if isinstance(h,(int,float)) else "N/A"
                    thr_txt = f"{thr:.2f}" if isinstance(thr,(int,float)) else "N/A"
                    items.append(html.Li(f"⚠️ {key}: h={h_txt} cm < umbral={thr_txt} cm"))
                return ("Alarma: ACTIVA", "danger", html.Ul(items, style={"margin":"0"}))
            else:
                return ("Alarma: Inactiva", "secondary", "")
        except Exception as e:
            return (f"Alarma: Error ({e})", "warning", "")

    # ============================================================
    #  REGISTRO / EXPORTAR  (NUEVA SECCIÓN)
    # ============================================================
    def _slice_list(lst, start_idx):
        """Devuelve lst[start_idx:] como lista normal."""
        return list(lst)[start_idx:] if lst else []

    def _build_export_dataframe(selected_blocks, n_last):
        """Construye el DataFrame a exportar desde los buffers y estados actuales."""
        L = len(historial['t'])
        if L == 0:
            raise ValueError("No hay datos en el buffer")

        # Calcular inicio en base a n_last
        start = max(0, L - int(n_last)) if (n_last is not None and n_last > 0) else 0

        data = {'t_s': _slice_list(historial['t'], start)}

        if 'niveles' in selected_blocks:
            data['h1_cm'] = _slice_list(historial['h1'], start)
            data['h2_cm'] = _slice_list(historial['h2'], start)
            data['h3_cm'] = _slice_list(historial['h3'], start)
            data['h4_cm'] = _slice_list(historial['h4'], start)

        if 'voltajes' in selected_blocks:
            data['u1_V'] = _slice_list(historial['v1'], start)
            data['u2_V'] = _slice_list(historial['v2'], start)

        # Longitud objetivo
        N = len(data['t_s'])

        # Referencias actuales (constantes por fila)
        if 'refs' in selected_blocks:
            r1 = getattr(pid_h1, 'setpoint', None)
            r2 = getattr(pid_h2, 'setpoint', None)
            data['h1_ref_cm'] = [r1] * N
            data['h2_ref_cm'] = [r2] * N

        # Parámetros actuales PID (constantes por fila)
        if 'pid' in selected_blocks:
            def _g(pid, name, alt=None):  # getter seguro
                if hasattr(pid, name):
                    return getattr(pid, name)
                if alt and hasattr(pid, alt):
                    return getattr(pid, alt)
                return None
            data['h1_Kp'] = [_g(pid_h1, 'Kp')] * N
            data['h1_Ki'] = [_g(pid_h1, 'Ki')] * N
            data['h1_Kd'] = [_g(pid_h1, 'Kd')] * N
            data['h1_AW'] = [_g(pid_h1, 'anti_windup_gain', 'aw')] * N

            data['h2_Kp'] = [_g(pid_h2, 'Kp')] * N
            data['h2_Ki'] = [_g(pid_h2, 'Ki')] * N
            data['h2_Kd'] = [_g(pid_h2, 'Kd')] * N
            data['h2_AW'] = [_g(pid_h2, 'anti_windup_gain', 'aw')] * N

        # Razones de flujo: usa historial si hay, si no, rellena con valor actual
        if 'razones' in selected_blocks:
            g1_hist = _slice_list(historial['g1'], start)
            g2_hist = _slice_list(historial['g2'], start)
            if len(g1_hist) == N and len(g2_hist) == N and N > 0:
                data['gamma1'] = g1_hist
                data['gamma2'] = g2_hist
            else:
                try:
                    g1_now = opc_client_instance.read_flow_ratio(1)
                    g2_now = opc_client_instance.read_flow_ratio(2)
                except Exception:
                    g1_now = g2_now = None
                data['gamma1'] = [g1_now] * N
                data['gamma2'] = [g2_now] * N

        df = pd.DataFrame(data)
        return df

    @app.callback(
        Output('download-datos', 'data'),
        Output('export-status', 'children'),
        Output('export-status', 'color'),
        Output('export-preview', 'children'),
        Input('btn-exportar', 'n_clicks'),
        State('export-signals', 'value'),
        State('export-format', 'value'),
        State('export-filename', 'value'),
        State('export-n-samples', 'value'),
        prevent_initial_call=True
    )
    def exportar_datos(n_clicks, signals, fmt, filename, n_samples):
        if not n_clicks:
            return no_update, "Esperando acción de exportación…", "secondary", no_update
        try:
            selected = signals or []
            df = _build_export_dataframe(selected, n_samples)

            base = (filename or "export")
            if fmt == 'csv':
                # CSV como texto
                data = dcc.send_data_frame(df.to_csv, f"{base}.csv", index=False)
                status = f"✅ Exportado {len(df)} filas a {base}.csv"
                color = "success"
                preview = html.Pre(df.head(8).to_string(index=False))
                return data, status, color, preview

            elif fmt == 'txt':
                # TXT tabulado
                buf = io.StringIO()
                df.to_csv(buf, sep='\t', index=False)
                content = buf.getvalue().encode('utf-8')
                def _send_bytes():
                    return content
                data = dcc.send_bytes(_send_bytes, f"{base}.txt")
                status = f"✅ Exportado {len(df)} filas a {base}.txt (tabulado)"
                color = "success"
                preview = html.Pre(df.head(8).to_string(index=False))
                return data, status, color, preview

            elif fmt == 'npy':
                # NPY con dict {col: ndarray}
                buf = io.BytesIO()
                np.save(buf, {c: df[c].to_numpy() for c in df.columns}, allow_pickle=True)
                raw = buf.getvalue()
                def _send_bytes():
                    return raw
                data = dcc.send_bytes(_send_bytes, f"{base}.npy")
                status = f"✅ Exportado {len(df)} filas a {base}.npy"
                color = "success"
                preview = html.Pre(df.head(8).to_string(index=False))
                return data, status, color, preview

            else:
                return no_update, f"❌ Formato no soportado: {fmt}", "danger", no_update

        except Exception as e:
            return no_update, f"❌ Error al exportar: {e}", "danger", no_update

    @app.callback(
        Output('export-status', 'children', allow_duplicate=True),
        Output('export-status', 'color', allow_duplicate=True),
        Input('btn-limpiar-registro', 'n_clicks'),
        prevent_initial_call=True
    )
    def limpiar_registro(n_clicks):
        if not n_clicks:
            return no_update, no_update
        try:
            for k in ('t','h1','h2','h3','h4','v1','v2','g1','g2'):
                historial[k].clear()
            historial['t0'] = None
            return "🧹 Registro en memoria limpiado.", "warning"
        except Exception as e:
            return f"❌ Error al limpiar registro: {e}", "danger"
