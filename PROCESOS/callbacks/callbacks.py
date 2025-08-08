from dash import Input, Output, State
import plotly.graph_objs as go

def register_callbacks(app):
    
    # 🧪 Ejemplo: actualizar gráfico del nivel del tanque 1
    @app.callback(
        Output('nivel-tanque-1', 'figure'),
        Input('manual-v1', 'value')  # solo a modo de prueba
    )
    def update_tanque_1_graph(v1):
        # Simulación básica: nivel constante según voltaje
        x = list(range(10))  # tiempo ficticio
        y = [v1 or 0] * 10   # nivel constante simulado
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Nivel T1'))
        fig.update_layout(title='Nivel Tanque 1', xaxis_title='Tiempo [s]', yaxis_title='Nivel [cm]')
        return fig

    # Aquí puedes agregar los demás callbacks para:
    # - actualizar todos los gráficos
    # - leer niveles desde OPC UA
    # - escribir valores de válvulas
    # - activar alarmas
    # - guardar datos
