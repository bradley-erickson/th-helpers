from . import utils

def fetch_row_info(row):
    """ given a row, fetch information """
    cells = row.findAll('td')
    placement = int(cells[0].get_text())
    name = cells[1].get_text().strip()
    country = cells[2].find('img')['alt']
    decklist_cell = cells[-1].find('a')
    decklist_url = decklist_cell['href'] if decklist_cell else None
    archetype = cells[-2].find('span')['data-tooltip']
    archetype_icons = [i['alt'] for i in cells[-2].findAll('img')]
    return placement, archetype, archetype_icons, decklist_url, name, country


def fetch_events():
    base_url = 'https://limitlesstcg.com/tournaments?show=300&time=all'
    page_html = utils.get_html(base_url)
    rows = utils.extract_table_rows(page_html, 'completed-tournaments')
    events = []
    for row in rows:
        name = row.findAll('a')[0]
        url = name['href'].split('/')[-1]
        events.append((name.text, url))
    return events


def fetch_decklists(tour_id):
    base_url = 'https://limitlesstcg.com'
    tour_url = f'{base_url}/tournaments/{tour_id}'

    html = utils.get_html(tour_url)
    rows = utils.extract_table_rows(html, 'data-table')
    decklists = [fetch_row_info(row) for row in rows]
    return decklists


def fetch_decklist(url):
    """ fetch a decklist from a given url """
    html = utils.get_html(url)
    soup_cards = html.findAll('div', {'class': 'decklist-card'})
    cards = []
    for soup_card in soup_cards:
        cards.append(
            {
                'number': soup_card['data-number'],
                'set': soup_card['data-set'],
                'count': int(soup_card.find('span', {'class': 'card-count'}).get_text()),
                'name': soup_card.find('span', {'class': 'card-name'}).get_text()
            }
        )
    return cards


def prompt_to_get_limitless_tour_id():
    print('* Finding Tournaments on Limitless')
    events = fetch_events()
    ids = {}
    for i, row in enumerate(events[:10]):
        ids[i] = row[1]
        print(f'[{i}] {row[0]}')
    selected_id = input('Select tournament: ')
    print('')
    return ids[int(selected_id)]


if __name__ == '__main__':
    out = prompt_to_get_limitless_tour_id()
    print(out)
    decks = fetch_decklists(out)
    print(decks[0])
