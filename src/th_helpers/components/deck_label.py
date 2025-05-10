from dash import html


pokemon_url = 'https://raw.githubusercontent.com/bradley-erickson/pokesprite/master/pokemon/regular'

pokemon_mapping = {
    'ogerpon': 'ogerpon-teal-mask',
    'squawkabilly': 'squawkabilly-green',
    'regieleki-a': 'regieleki',
    'ogerpon-cornerstone': 'ogerpon-cornerstone-mask',
    'ogerpon-wellspring': 'ogerpon-wellspring-mask',
    'ogerpon-hearthflame': 'ogerpon-hearthflame-mask',
    'terapagos': 'terapagos-terastal'
}


# TODO add game
def format_label(deck, hide_text=False, hide_text_small=False):
    if deck is None:
        return ''
    children = [
        html.Img(
            src=i,
            style={'maxHeight': '35px'}
        ) for i in deck.get('icons', [])
    ]
    name = deck.get('name')
    children.append(html.Span(name, className='d-none' if hide_text else 'd-none d-md-inline-block' if hide_text_small else 'ms-1'))
    return html.Div(
        children, title=name,
        className='d-flex flex-row align-items-center'
    )


def get_pokemon_icon(pokemon):
    if not pokemon:
        return ''
    if pokemon == 'substitute':
        source = '/assets/substitute.png'
    else:
        mon = pokemon_mapping[pokemon] if pokemon in pokemon_mapping else pokemon
        source = f'{pokemon_url}/{mon}.png'
    return source


def create_default_deck(id):
    id_fix = 'other' if id is None else id
    return {'id': id_fix, 'name': id_fix.title(), 'icons': ['substitute']}
