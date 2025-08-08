from dash import Dash
#Layouts
from layouts.layout import create_layout
#Callbacks
from callbacks.callbacks import register_callbacks
from callbacks.callbacks import register_alarm_callback

import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = create_layout()

register_callbacks(app)
register_alarm_callback(app)

if __name__ == '__main__':
    app.run(debug=True)
