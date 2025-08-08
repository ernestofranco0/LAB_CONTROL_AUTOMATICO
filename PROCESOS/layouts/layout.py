from dash import html, dcc
import dash_bootstrap_components as dbc

def create_layout():
    return html.Div([
        html.H1("Sistema SCADA - Control de Cuatro Tanques", style={'textAlign': 'center'}),

        dcc.Tabs([
            # 1. Visualización
            dcc.Tab(label='Visualización', children=[
                html.Br(),
                html.H4("Niveles de los Tanques"),
                
                dcc.Graph(
                    id='nivel-tanque-1',
                    figure={
                        'layout': {
                            'title': 'Nivel Tanque 1',
                            'xaxis': {'title': 'Tiempo [s]'},
                            'yaxis': {'title': 'Nivel [cm]'}
                        }
                    }
                ),
                dcc.Graph(
                    id='nivel-tanque-2',
                    figure={
                        'layout': {
                            'title': 'Nivel Tanque 2',
                            'xaxis': {'title': 'Tiempo [s]'},
                            'yaxis': {'title': 'Nivel [cm]'}
                        }
                    }
                ),
                dcc.Graph(
                    id='nivel-tanque-3',
                    figure={
                        'layout': {
                            'title': 'Nivel Tanque 3',
                            'xaxis': {'title': 'Tiempo [s]'},
                            'yaxis': {'title': 'Nivel [cm]'}
                        }
                    }
                ),
                dcc.Graph(
                    id='nivel-tanque-4',
                    figure={
                        'layout': {
                            'title': 'Nivel Tanque 4',
                            'xaxis': {'title': 'Tiempo [s]'},
                            'yaxis': {'title': 'Nivel [cm]'}
                        }
                    }
                ),
                # Alarmas
                html.Div(id='alarma-tanques', style={'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'}),
                dcc.Interval(id='intervalo-alarmas', interval=1000, n_intervals=0),

                html.H4("Voltajes Aplicados a las Válvulas"),
                dcc.Graph(
                    id='voltajes-valvulas',
                    figure={
                        'layout': {
                            'title': 'Voltajes en Válvulas 1 y 2',
                            'xaxis': {'title': 'Tiempo [s]'},
                            'yaxis': {'title': 'Voltaje [V]'}
                        }
                    }
                ),
                # Intervalo de actualización automática
                dcc.Interval(
                    id='interval-update',
                    interval=1000,  # 1 segundo
                    n_intervals=0
                )
            ]),

            # 2. Modo Manual
            dcc.Tab(label='Modo Manual', children=[
                html.Br(),
                html.H4("Control Manual de Válvulas y Flujo"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-v1', type='number', placeholder='Voltaje V1 (V)'), width=6),
                    dbc.Col(dbc.Input(id='manual-v2', type='number', placeholder='Voltaje V2 (V)'), width=6),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-gamma1', type='number', placeholder='Razón γ1'), width=6),
                    dbc.Col(dbc.Input(id='manual-gamma2', type='number', placeholder='Razón γ2'), width=6),
                ]),
            ]),

            # 3. Modo Automático
            dcc.Tab(label='Modo Automático', children=[
                html.Br(),
                html.H4("Control Automático con PID"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-h1-ref', type='number', placeholder='Referencia h1 (cm)'), width=6),
                    dbc.Col(dbc.Input(id='auto-h2-ref', type='number', placeholder='Referencia h2 (cm)'), width=6),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-kp', type='number', placeholder='Kp'), width=4),
                    dbc.Col(dbc.Input(id='auto-ki', type='number', placeholder='Ki'), width=4),
                    dbc.Col(dbc.Input(id='auto-kd', type='number', placeholder='Kd'), width=4),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-aw', type='number', placeholder='Anti-Windup Gain'), width=6),
                ])
            ]),

            # 4. Configuración y Alarmas
            dcc.Tab(label='Configuración y Alarmas', children=[
                html.Br(),
                html.H4("Configuración General y Alarmas"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='max-samples', type='number', placeholder='Máx. muestras en RAM'), width=6),
                    dbc.Col(html.Button("Guardar Datos", id='guardar-datos', n_clicks=0), width=6)
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='nivel-critico', type='number', placeholder='Nivel Crítico para Alarma (cm)'), width=6),
                    dbc.Col(html.Div(id='alarma-estado', children='Alarma: Inactiva'), width=6)
                ]),
                html.Br(),
                html.Div(id='estado-conexion', children='Estado OPC UA: Desconectado'),
            ])
        ])
    ])
