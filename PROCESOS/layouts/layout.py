from dash import html, dcc
import dash_bootstrap_components as dbc

def create_layout():
    return html.Div([
        html.H1("Sistema SCADA - Control de Cuatro Tanques", style={'textAlign': 'center'}),

        # --- Stores para estado global (usados por callbacks) ---
        dcc.Store(id='store-pid-params'),       # Kp, Ki, Kd, aw, refs h1/h2
        dcc.Store(id='store-manual'),           # u1, u2, gamma1, gamma2 actuales
        dcc.Store(id='store-config'),           # max_samples, nivel_critico, etc.
        dcc.Store(id='store-system-state'),     # buffers de series, flags de alarma, conexión
        dcc.Store(id='store-fase'),             # flag fase no mínima (solo informativo)

        dcc.Tabs([

            # 1) Visualización
            dcc.Tab(label='Visualización', children=[
                html.Br(),
                html.H4("Niveles de los Tanques"),
                dcc.Graph(id='nivel-tanque-1'),
                dcc.Graph(id='nivel-tanque-2'),
                dcc.Graph(id='nivel-tanque-3'),
                dcc.Graph(id='nivel-tanque-4'),

                html.H4("Voltajes aplicados a las válvulas"),
                dcc.Graph(id='voltaje-valvula-1'),
                dcc.Graph(id='voltaje-valvula-2'),

                html.H4("Razones de flujo"),
                dcc.Graph(id='razon-flujo-1'),
                dcc.Graph(id='razon-flujo-2'),

                html.Hr(),

                # Alarmas
                html.Div(id='alarma-tanques',
                         style={'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'}),

                # Intervalos de refresco
                dcc.Interval(id='intervalo-alarmas', interval=1000, n_intervals=0),
                dcc.Interval(id='interval-update', interval=1000, n_intervals=0),
            ]),

            # 2) Modo Manual (γ solo aquí)
            dcc.Tab(label='Modo Manual', children=[
                html.Br(),
                html.H4("Control manual de válvulas y razones de flujo"),

                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-v1', type='number',
                                      placeholder='Voltaje V1 (V)', min=0, max=10, step=0.01), width=6),
                    dbc.Col(dbc.Input(id='manual-v2', type='number',
                                      placeholder='Voltaje V2 (V)', min=0, max=10, step=0.01), width=6),
                ], className="g-2"),

                html.Br(),

                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-gamma1', type='number',
                                      placeholder='Razón γ1 (0–1)', min=0, max=1, step=0.01), width=6),
                    dbc.Col(dbc.Input(id='manual-gamma2', type='number',
                                      placeholder='Razón γ2 (0–1)', min=0, max=1, step=0.01), width=6),
                ], className="g-2"),

                html.Small(
                    "Nota: γ1 y γ2 se ajustan manualmente. En fase no mínima se requiere γ1 + γ2 < 1; "
                    "en fase mínima, γ1 + γ2 > 1.",
                    style={'display': 'block', 'textAlign': 'center', 'color': 'gray'}
                ),

                html.Br(),

                html.Div(id='valores-actuales-manual',
                         style={'textAlign': 'center', 'color': 'gray'}),

                dcc.Interval(id='intervalo-manual', interval=1000, n_intervals=0),

                html.Img(
                    src='/assets/sistema.png',
                    style={'width': '30%', 'display': 'block', 'margin': '0 auto'}
                ),

                html.Br(),

                dbc.Row([
                    dbc.Col(dbc.Button("Aplicar", id='aplicar-manual',
                                       color='primary', n_clicks=0), width=6),
                ], className="g-2", justify="center"),

                html.Br(),
                html.Div(id='mensaje-manual',
                         style={'color': 'green', 'textAlign': 'center'}),
            ]),

            # 3) Modo Automático (PID SOLO sobre u1, u2)
            dcc.Tab(label='Modo Automático', children=[

                dcc.Interval(id='intervalo-automatico', interval=1000, n_intervals=0),

                html.Br(),
                html.H4("Control automático con PID (u1, u2)"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-h1-ref', type='number',
                                      placeholder='Referencia h1 (cm)', min=0, step=0.1), width=6),
                    dbc.Col(dbc.Input(id='auto-h2-ref', type='number',
                                      placeholder='Referencia h2 (cm)', min=0, step=0.1), width=6),
                ], className="g-2"),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-kp', type='number',
                                      placeholder='Kp', step=0.001), width=4),
                    dbc.Col(dbc.Input(id='auto-ki', type='number',
                                      placeholder='Ki', step=0.001), width=4),
                    dbc.Col(dbc.Input(id='auto-kd', type='number',
                                      placeholder='Kd', step=0.001), width=4),
                ], className="g-2"),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-aw', type='number',
                                      placeholder='Anti-Windup Gain', step=0.001), width=6),
                ], className="g-2"),

                html.Br(),
                dbc.Row([
                    dbc.Col(html.Button('Aplicar PID', id='aplicar-PID', n_clicks=0), width=6),
                ], className="g-2", justify="center"),

                html.Br(),
                html.Div(id='modo-automatico',
                         style={'color': 'green', 'textAlign': 'center'}),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Switch(id='modo-switch',
                                       label='Activar fase no mínima (informativo)',
                                       value=False), width=6),
                ], className="g-2"),
                html.Small(
                    "Este switch no modifica γ automáticamente: úsalo como guía y ajusta γ1, γ2 en el Modo Manual.",
                    style={'display': 'block', 'textAlign': 'center', 'color': 'gray'}
                ),
            ]),

            # 4) Configuración y Alarmas
            dcc.Tab(label='Configuración y Alarmas', children=[
                html.Br(),
                html.H4("Configuración general y alarmas"),

                dbc.Row([
                    dbc.Col(dbc.Input(id='max-samples', type='number',
                                      placeholder='Máx. muestras en RAM', min=100), width=6),
                    dbc.Col(html.Button("Guardar datos", id='guardar-datos', n_clicks=0), width=6),
                ], className="g-2"),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='nivel-critico', type='number',
                                      placeholder='Nivel crítico para alarma (cm)', min=0), width=6),
                    dbc.Col(html.Div(id='alarma-estado', children='Alarma: Inactiva'), width=6),
                ], className="g-2"),

                html.Br(),
                html.Div(id='estado-conexion', children='Estado OPC UA: Desconectado'),
            ]),
        ])
    ])
