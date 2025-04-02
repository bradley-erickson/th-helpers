from dash import html
import dash_bootstrap_components as dbc

DEFAULT_OPTIONS = [
    {'label': html.I(className='fas fa-xmark text-danger'), 'value': -1},
    {'label': html.I(className='far fa-circle'), 'value': 0},
    {'label': html.I(className='fas fa-check text-success'), 'value': 1},
]

TURN_OPTIONS = [
    {'label': html.I(className='fas fa-1 text-info'), 'value': 1},
    {'label': html.I(className='far fa-circle'), 'value': 0},
    {'label': html.I(className='fas fa-2 text-warning'), 'value': 2},
]

def create_ternary_switch(id, label, options=DEFAULT_OPTIONS):
    return html.Div([
        dbc.RadioItems(
            id=id,
            className='btn-group btn-group-sm me-1',
            inputClassName='btn-check',
            labelClassName='btn btn-outline-primary ternary-switch',
            labelCheckedClassName='active',
            options=options,
            value=0,
        ),
        dbc.Label(label)
    ], className='radio-group')
