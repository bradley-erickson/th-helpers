import dash_bootstrap_components as dbc
from dash import dcc

import utils.constants as c

_RESULT_RATES = [
    (c.RESULT_RATE_STRATEGY.IGNORE_TIES,
     'Ignore Ties',
     r'% = $\frac{W}{W+L}$',
     lambda w, l, t: (w, w + l)),
    (c.RESULT_RATE_STRATEGY.TIES_COUNT_AS_LOSSES,
     'Count Ties as Losses',
     r'% = $\frac{W}{W+L+T}$',
     lambda w, l, t: (w, w + l + t)),
    (c.RESULT_RATE_STRATEGY.TIES_COUNT_AS_HALF_WIN,
     'Count Ties as 1/2 Win',
     r'% = $\frac{W + \frac{T}{2}}{W+L+T}$',
     lambda w, l, t: (w + t / 2, w + l + t)),
    (c.RESULT_RATE_STRATEGY.TIES_COUNT_AS_THIRD_WIN,
     'Count Ties as 1/3 Win',
     r'% = $\frac{W + \frac{T}{3}}{W+L+T}$',
     lambda w, l, t: (w + t / 3, w + l + t)),
    (c.RESULT_RATE_STRATEGY.TIES_COUNT_AS_WINS,
     'Count Ties as Wins',
     r'% = $\frac{W + T}{W+L+T}$',
     lambda w, l, t: (w + t, w + l + t)),
]
RESULT_RATE_STRATEGY_DETAILS = {
    v[0]: {
        c.RESULT_RATE_FIELD.LABEL: v[1],
        c.RESULT_RATE_FIELD.FORMULA: v[2],
        c.RESULT_RATE_FIELD.CALCULATE: v[3],
    } for v in _RESULT_RATES
}


def create_result_rate_label(strategy, formula_only=False):
    if strategy not in RESULT_RATE_STRATEGY_DETAILS:
        return None
    label = f'{RESULT_RATE_STRATEGY_DETAILS[strategy][c.RESULT_RATE_FIELD.FORMULA]}'
    if not formula_only:
        label = f'{RESULT_RATE_STRATEGY_DETAILS[strategy][c.RESULT_RATE_FIELD.LABEL]}: {label}'
    return dcc.Markdown(
        label,
        className='m-0', mathjax=True
    )


def create_result_rate_selector(id, value=c.RESULT_RATE_STRATEGY.IGNORE_TIES):
    '''Return a radio item group allowing selection of the result rate formula.

    Each option includes a small markdown snippet describing the formula used.
    '''
    options = [
        {
            c.DASH.VALUE: key,
            c.DASH.LABEL: create_result_rate_label(key)
        }
        for key in RESULT_RATE_STRATEGY_DETAILS
    ]
    return dcc.Dropdown(id=id, options=options, value=value, clearable=False)


def calculate_result_rate(strategy, wins, losses, ties, percentage=False):
    '''Calculate the result rate for the given strategy.

    Parameters
    ----------
    strategy: str
        One of the keys in :data:`components.result_rate.RESULT_RATE_STRATEGY_DETAILS`.
    wins: int or float
    losses: int or float
    ties: int or float
    percentage: bool, default=False
        If True, return the rate as a percentage in the range [0, 100].
        Otherwise return a value between 0 and 1.
    '''
    try:
        calc = RESULT_RATE_STRATEGY_DETAILS[strategy][c.RESULT_RATE_FIELD.CALCULATE]
        numerator, denominator = calc(wins, losses, ties)
    except KeyError as exc:
        raise ValueError(f'Unknown result rate strategy: {strategy}') from exc

    rate = 0 if denominator == 0 else numerator / denominator
    return round(rate * 100, 1) if percentage else rate
