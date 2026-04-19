import base64


def _get_base64_encoded_image(path):
    try:
        return base64.b64encode(open(path, 'rb').read())
    except Exception as e:
        print(f'Warning: {path} is missing, unable to load\n{e}')


# Logos
logo_black_path = './assets/logo_black.png'
logo_black_tunel = _get_base64_encoded_image(logo_black_path)
logo_white_path = './assets/logo.png'
logo_white_tunel = _get_base64_encoded_image(logo_white_path)

logo_black_sm_path = './assets/logo_black_small.png'
logo_black_sm_tunel = _get_base64_encoded_image(logo_black_sm_path)
logo_white_sm_path = './assets/logo_small.png'
logo_white_sm_tunel = _get_base64_encoded_image(logo_white_sm_path)

# Cards
ptcg_card_url = 'https://limitlesstcg.nyc3.digitaloceanspaces.com'


def get_card_image(card_code, size='SM', game='PTCG'):
    if not card_code:
        return ''
    card_code = card_code.replace('PR-SW', 'SSP')
    card_code = card_code.replace('PR-SV', 'SVP')
    set_code, number = card_code.split('-', 1)

    is_tpc_sv = (set_code.startswith('SV') and set_code[2].isdigit()) or set_code in ['SVHM', 'SVHK']
    is_tpc_mega = set_code.startswith('M') and set_code[1].isdigit()
    card_origin = 'tpc' if is_tpc_sv or is_tpc_mega else 'tpci'
    lang = 'EN'
    if card_origin == 'tpc':
        lang = 'JP'
        number = number.lstrip('0')
    source = f'{ptcg_card_url}/{card_origin}/{set_code}/{set_code}_{number}_R_{lang}_{size}.png'
    return source

# TODO add in Pocket and dispatch for getting the either PTCG or POCKET
