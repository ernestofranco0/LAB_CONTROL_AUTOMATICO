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

            # 1) Modo Manual
            dcc.Tab(label='Modo Manual', children=[
                html.Br(),
                html.H4("Control Manual de Válvulas y Razones"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-v1', type='number', placeholder='Voltaje V1 (V)', min=0, max=10, step=0.01), width=6),
                    dbc.Col(dbc.Input(id='manual-v2', type='number', placeholder='Voltaje V2 (V)', min=0, max=10, step=0.01), width=6),
                ], className="g-2"),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Input(id='manual-gamma1', type='number', placeholder='Razón γ1 (0–1)', min=0, max=1, step=0.01), width=6),
                    dbc.Col(dbc.Input(id='manual-gamma2', type='number', placeholder='Razón γ2 (0–1)', min=0, max=1, step=0.01), width=6),
                ], className="g-2"),
                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Button("Aplicar", id='aplicar-manual', color='primary', n_clicks=0), width=6),
                ], className="g-2", justify="center"),
                html.Br(),
                html.Div(id='mensaje-manual', style={'color': 'green', 'textAlign': 'center'}),

                html.Hr(),
                html.H4("Niveles (gráficos separados)"),
                dcc.Graph(id='nivel-manual-1'),
                dcc.Graph(id='nivel-manual-2'),
                dcc.Graph(id='nivel-manual-3'),
                dcc.Graph(id='nivel-manual-4'),

                html.H4("Voltajes aplicados (u1 y u2)"),
                dcc.Graph(id='voltajes-manual'),

                # Intervalo de refresco
                dcc.Interval(id='interval-update', interval=1000, n_intervals=0),
            ]),

            # 2) Modo Automático
            dcc.Tab(label='Modo Automático', children=[
                dcc.Interval(id='intervalo-automatico', interval=1000, n_intervals=0),
                html.Br(),
                html.H4("Control automático con PID (u1, u2)"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='auto-h1-ref', type='number', placeholder='Referencia h1 (cm)', min=0, step=0.1), width=6),
                    dbc.Col(dbc.Input(id='auto-h2-ref', type='number', placeholder='Referencia h2 (cm)', min=0, step=0.1), width=6),
                ], className="g-2"),

                html.Br(),
                # ---- Parámetros PID por lazo ----
                dbc.Row([
                    # --- PID h1 ---
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader("PID para h1"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(dbc.Input(id='auto-h1-kp', type='number', placeholder='Kp (h1)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h1-ki', type='number', placeholder='Ki (h1)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h1-kd', type='number', placeholder='Kd (h1)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h1-aw', type='number', placeholder='Anti-Windup (h1)', step=0.001), width=3),
                                ], className="g-2"),
                            ])
                        ], className="h-100"),
                        width=12, lg=6
                    ),
                    # --- PID h2 ---
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader("PID para h2"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(dbc.Input(id='auto-h2-kp', type='number', placeholder='Kp (h2)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h2-ki', type='number', placeholder='Ki (h2)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h2-kd', type='number', placeholder='Kd (h2)', step=0.001), width=3),
                                    dbc.Col(dbc.Input(id='auto-h2-aw', type='number', placeholder='Anti-Windup (h2)', step=0.001), width=3),
                                ], className="g-2"),
                            ])
                        ], className="h-100"),
                        width=12, lg=6
                    ),
                ], className="g-3"),

                html.Br(),
                dbc.Row([
                    dbc.Col(html.Button('Aplicar PID', id='aplicar-PID', n_clicks=0, className='btn btn-primary'), width=6),
                ], className="g-2", justify="center"),
                html.Br(),
                html.Div(id='modo-automatico', style={'color': 'green', 'textAlign': 'center'}),

                html.Hr(),
                html.H4("Niveles con referencia"),
                dcc.Graph(id='auto-h1-fig'),
                dcc.Graph(id='auto-h2-fig'),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Switch(id='modo-switch', label='Activar fase no mínima (informativo)', value=False), width=6),
                ], className="g-2"),
                html.Small(
                    "Este switch no modifica γ automáticamente: ajústalas en Modo Manual (γ1+γ2<1 no mínima; >1 mínima).",
                    style={'display': 'block', 'textAlign': 'center', 'color': 'gray'}
                ),
            ]),

            # 3) Configuración y Alarmas
            dcc.Tab(label='Configuración y Alarmas', children=[
                html.Br(),
                html.H4("Configuración general y alarmas"),

                # Switch de suscripción a OPC (DataChange) para niveles
                dbc.Row([
                    dbc.Col(dbc.Switch(id='opc-alarm-sub-switch', label='Suscribirse a alarmas OPC (niveles)', value=False), width=6),
                    dbc.Col(html.Div(id='subscripcion-estado', children='Subscripción: Inactiva'), width=6),
                ], className="g-2"),

                html.Hr(),
                html.H5("Umbrales por estanque (cm)"),
                dbc.Row([
                    dbc.Col(dbc.Input(id='umbral-h1', type='number', placeholder='h1 crítico', min=0, step=0.1), width=3),
                    dbc.Col(dbc.Input(id='umbral-h2', type='number', placeholder='h2 crítico', min=0, step=0.1), width=3),
                    dbc.Col(dbc.Input(id='umbral-h3', type='number', placeholder='h3 crítico', min=0, step=0.1), width=3),
                    dbc.Col(dbc.Input(id='umbral-h4', type='number', placeholder='h4 crítico', min=0, step=0.1), width=3),
                ], className="g-2"),

                html.Br(),
                # Indicador visual de alarmas (no bloqueante)
                dbc.Alert(id='alarma-estado', children='Alarma: Inactiva', color='secondary', dismissable=False, is_open=True),
                html.Div(id='alarma-lista', style={'textAlign': 'left'}),

                html.Hr(),
                # Estado de conexión opcional
                html.Div(id='estado-conexion', children='Estado OPC UA: Desconectado'),

                # Intervalo para refrescar indicadores de alarmas/estado
                dcc.Interval(id='intervalo-alarmas', interval=1000, n_intervals=0),
            ]),

            # 4) Registro / Exportar
            dcc.Tab(label='Registro / Exportar', children=[
                html.Br(),
                html.H4("Guardar series de tiempo y metadatos"),
                dcc.Markdown(
                    "- Puedes exportar una **secuencia finita** de datos en formato CSV.\n"
                    "- Selecciona las señales a incluir y cuántas muestras tomar desde el buffer en memoria.\n"
                    "- Los callbacks deberán encargarse de empaquetar y disparar la descarga."
                ),

                dbc.Row([
                    dbc.Col(dbc.Checklist(
                        id='export-signals',
                        options=[
                            {'label': 'Niveles h1–h4', 'value': 'niveles'},
                            {'label': 'Referencias (h1_ref, h2_ref)', 'value': 'refs'},
                            {'label': 'Voltajes (u1, u2)', 'value': 'voltajes'},
                            {'label': 'Parámetros PID (Kp, Ki, Kd, AW)', 'value': 'pid'},
                            {'label': 'Razones de flujo (γ1, γ2)', 'value': 'razones'},
                        ],
                        value=['niveles', 'refs', 'voltajes', 'pid', 'razones'],
                        inline=False
                    ), width=12, lg=6),

                    dbc.Col([
                        dbc.Label("Formato de exportación"),
                        dcc.Dropdown(
                            id='export-format',
                            options=[
                                {'label': 'CSV (texto separado por comas)', 'value': 'csv'},
                                {'label': 'NPY (No disponible)', 'value': 'npy'},
                                {'label': 'TXT (No disponible)', 'value': 'txt'},
                            ],
                            value='csv',
                            clearable=False
                        ),
                        html.Br(),
                        dbc.Label("Nombre de archivo (sin extensión)"),
                        dbc.Input(id='export-filename', type='text', placeholder='ej: experimento_s1'),
                        html.Small("La extensión se añade automáticamente según el formato elegido.", className="text-muted"),
                        html.Br(), html.Br(),
                        dbc.Label("Cantidad de muestras a exportar"),
                        dbc.Input(id='export-n-samples', type='number', min=1, step=1, placeholder='ej: 500'),
                        html.Small("Si se deja vacío, se exporta todo el buffer disponible.", className="text-muted"),
                    ], width=12, lg=6),
                ], className="g-3"),

                html.Br(),
                dbc.Row([
                    dbc.Col(dbc.Button("Exportar datos", id='btn-exportar', color='success', n_clicks=0), width=6),
                    dbc.Col(dbc.Button("Limpiar registro (opcional)", id='btn-limpiar-registro', color='secondary', n_clicks=0), width=6),
                ], className="g-2"),

                html.Br(),
                dbc.Alert(id='export-status', children='Esperando acción de exportación…', color='secondary', dismissable=False, is_open=True),

                # Componente para descarga
                dcc.Download(id='download-datos'),

                html.Hr(),
                html.H5("Vista previa"),
                html.Div(id='export-preview', children=html.Small("El callback puede poblar una tabla/resumen aquí.")),
            ]),
        ])
    ])
