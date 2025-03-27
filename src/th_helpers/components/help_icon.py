from dash import html
import dash_bootstrap_components as dbc


def create_help_icon(id, children, className=''):
    return html.Div([
        html.I(className='far fa-circle-question', id=id),
        dbc.Popover(children, body=True, target=id, trigger='click hover', placement='bottom')
    ], className=f'd-inline-block {className}')
