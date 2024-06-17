import th_helpers.scraper.utils as utils

def prompt_to_get_pokedata_tour_id():
    print('* Finding Tournaments on PokeData')
    base_url = 'https://pokedata.ovh/standings/'
    page_html = utils.get_html(base_url)
    buttons = page_html.findAll('button')
    ids = {}
    for i, button in enumerate(buttons[:10]):
        ids[i] = button['onclick'].split('=')[1][1:-2]
        name = button.text.replace("\n", "")
        print(f'[{i}] {name}')
    selected_id = input('Select tournament: ')
    print('')
    return ids[int(selected_id)]
