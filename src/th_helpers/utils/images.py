import base64

# Logos
logo_black_path = './assets/logo_black.png'
logo_black_tunel = base64.b64encode(open(logo_black_path, 'rb').read())
logo_white_path = './assets/logo.png'
logo_white_tunel = base64.b64encode(open(logo_white_path, 'rb').read())

logo_black_sm_path = './assets/logo_black_small.png'
logo_black_sm_tunel = base64.b64encode(open(logo_black_sm_path, 'rb').read())
logo_white_sm_path = './assets/logo_small.png'
logo_white_sm_tunel = base64.b64encode(open(logo_white_sm_path, 'rb').read())
