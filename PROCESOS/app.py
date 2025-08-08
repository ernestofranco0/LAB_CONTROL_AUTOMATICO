from dash import Dash
from layouts.layout import create_layout
from callbacks.callbacks import register_callbacks
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = create_layout()

register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
