#Dash
from dash import Dash
import dash_bootstrap_components as dbc
#Layouts
from layouts.layout import create_layout
#Callbacks
from callbacks.callbacks import register_callbacks
#OPC
from utils.opc_client import opc_client_instance

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = create_layout()

register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
