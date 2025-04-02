from dash import html
import dash_bootstrap_components as dbc


def create_help_icon(id, children, className='', big=False):
    return html.Div([
        html.I(className='far fa-circle-question', id=id),
        dbc.Popover(children, body=True, target=id, trigger='click hover', placement='bottom', class_name=f'help-icon-popover {"big" if big else ""}')
    ], className=f'd-inline-block {className}')
