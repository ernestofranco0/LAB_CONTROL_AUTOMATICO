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

                dcc.Graph(id='nivel-tanque-1'),
                dcc.Graph(id='nivel-tanque-2'),
                dcc.Graph(id='nivel-tanque-3'),
                dcc.Graph(id='nivel-tanque-4'),

                html.H4("Voltajes Aplicados a las Válvulas"),
                dcc.Graph(id='voltaje-valvula-1'),
                dcc.Graph(id='voltaje-valvula-2'),

                html.H4("Razones de Flujo"),
                dcc.Graph(id='razon-flujo-1'),
                dcc.Graph(id='razon-flujo-2'),

                html.Hr(),

                # Alarmas
                html.Div(id='alarma-tanques', style={'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'}),
                dcc.Interval(id='intervalo-alarmas', interval=1000, n_intervals=0),

                # Intervalo general de actualización automática
                dcc.Interval(id='interval-update', interval=1000, n_intervals=0)
            ]),

            # 2. Modo Manual
            dcc.Tab(label='Modo Manual', children=[
                html.Br(),
                html.H4("Control Manual de Válvulas y Flujo"),
                
                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-v1', type='number', placeholder='Voltaje V1 (V)', min=0, max=10), width=6),
                    dbc.Col(dbc.Input(id='manual-v2', type='number', placeholder='Voltaje V2 (V)', min=0, max=10), width=6),
                ]),
                
                html.Br(),

                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-gamma1', type='number', placeholder='Razón γ1', min=0, max=1, step=0.01), width=6),
                    dbc.Col(dbc.Input(id='manual-gamma2', type='number', placeholder='Razón γ2', min=0, max=1, step=0.01), width=6),
                ]),

                html.Br(),

                html.Div(id='valores-actuales-manual', style={'textAlign': 'center', 'color': 'gray'}),
                dcc.Interval(id='intervalo-manual', interval=1000, n_intervals=0),

                html.Img(
                    src='/assets/sistema.png',
                    style={
                        'width': '30%',
                        'display': 'block',
                        'margin': '0 auto'
                    }
                ),

                html.Br(),

                dbc.Row([
                    dbc.Col(dbc.Button("Aplicar", id='aplicar-manual', color='primary', n_clicks=0), width=6),
                ]),
                
                html.Br(),

                html.Div(id='mensaje-manual', style={'color': 'green', 'textAlign': 'center'})
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
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(html.Button('Aplicar PID', id='aplicar-PID', n_clicks=0), width=6)
                ]),
                html.Br(),
                html.Div(id='modo-automatico', style={'color': 'green', 'textAlign': 'center'}),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Switch(id='modo-switch', label='Activar fase no mínima',value=False), width=6)
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
