import collections

import th_helpers.utils.card_cache


ENERGY = {
    'Grass': 'G',
    'Fire': 'R',
    'Water': 'W',
    'Lightning': 'L',
    'Psychic': 'P',
    'Fighting': 'F',
    'Darkness': 'D',
    'Metal': 'M',
    'Fairy': 'Y',
    'Dragon': 'N',
    'Colorless': 'C'
}

card_cache = {}


def _query_card(id):
    card = th_helpers.utils.card_cache.get_card(id)
    return card


def get_card(name, set, number):
    card = {'name': name, 'set': set, 'number': number}
    set_obj = th_helpers.utils.card_cache.get_set_by_ptcgo(set)
    card_set = set_obj['id']
    card_number = card['number']

    obj = _query_card(f'{card_set}-{card_number}')
    if obj is None:
        basic_energy = not any(c.isdigit() for c in card['number']) or ('Energy' in card['name'] and card['name'].split(' ')[0] in ENERGY)
        card['supertype'] = 'Energy' if basic_energy else None
        card['subtype'] = 'Basic' if basic_energy else None
        card['dex'] = None
    else:
        card['supertype'] = obj.get('supertype')
        subtypes = obj.get('subtypes', [])
        card['subtype'] = subtypes[0] if 'Pokémon Tool' not in subtypes else 'Pokémon Tool'
        nat_dex = obj.get('nationalPokedexNumbers')
        card['dex'] = nat_dex[0] if nat_dex else None

    if card['supertype'] == 'Pokémon':
        card_id = f"{card['name']}-{card['set']}-{card['number']}"
        if card_id not in card_cache:
            card['attacks'] = obj.get('attacks', [])
            # TODO check similar cards in cache
            possible_matches = {k: v for k, v in card_cache.items() if k.startswith(card['name'])}
            matched = False
            for k, v in possible_matches.items():
                if v.get('attacks', []) == card['attacks']:
                    matched = True
                    card_cache[card_id] = v
                    break
            if not matched:
                card_cache[card_id] = card
        return card_cache[card_id]
    else:
        if name not in card_cache:
            card_cache[name] = card
        return card_cache[name]


def sort_pokemon(cards):
    if len(cards) == 0:
        return []
    name_counter = {}
    name_dex = {}
    for card in cards:
        card_name = card['name']
        if card_name not in name_dex:
            name_counter[card_name] = 0
            name_dex[card_name] = 0
        name_counter[card_name] += card.get('count', 0)
        if card['dex']:
            name_dex[card_name] = card['dex']

    sort = []
    while len(name_counter.keys()) > 0:
        max_value = max(name_counter.values())
        max_names = [k for k, v in name_counter.items() if v == max_value]
        if max_value == 1:
            sort.extend(sorted(
                (c for c in cards if c['name'] in max_names),
                key=lambda x: x.get('play_rate', 0), reverse=True
            ))
            break
        min_dex = min(v for k, v in name_dex.items() if k in max_names)
        min_name = next(k for k, v in name_dex.items() if v == min_dex and k in max_names)

        named_cards = (c for c in cards if c['name'] == min_name)
        sort.extend(sorted(named_cards, key=lambda x: (x.get('count', 0), x.get('play_rate', 0)), reverse=True))
        del name_counter[min_name]
        evolution_cards = [c for c in cards if (name_dex[c['name']] == min_dex + 1 or name_dex[c['name']] == min_dex + 2) and c['subtype'] in ['Stage 1', 'Stage 2'] and c['name'] in name_counter]
        for evo in evolution_cards:
            if evo['name'] in name_counter:
                del name_counter[evo['name']]

        sort.extend(sorted(evolution_cards, key=lambda x: (name_dex[x['name']], 60-x.get('count', 0), 1-x.get('play_rate', 0))))
    return sort


def sort_trainers(cards):
    if len(cards) == 0:
        return []
    custom_order = {'Supporter': 1, 'Item': 2, 'Pokémon Tool': 3, 'Stadium': 4}
    return sorted(cards, key=lambda x: (custom_order[x['subtype']], 60-x.get('count', 0), 1-x.get('play_rate', 0)))


def sort_energy(cards):
    if len(cards) > 0 and 'count' in cards[0]:
        return sorted(cards, key=lambda x: (x.get('count', 0), x.get('play_rate', 0)), reverse=True)
    return cards


def sort_deck(cards):
    '''
    Sorting requirements:
    - Pokemon
        - Count
    - Trainer
    - Energy
    '''
    pokemon = 'Pokémon'
    trainer = 'Trainer'
    energy = 'Energy'
    types = collections.OrderedDict({
        pokemon: [],
        trainer: [],
        energy: []
    })
    sort_functions = {
        pokemon: sort_pokemon,
        trainer: sort_trainers,
        energy: sort_energy
    }
    for c in cards:
        supertype = c['supertype']
        if supertype not in types:
            supertype = energy
        types[supertype].append(c)

    sorted_cards = []
    for t in types.keys():
        sorted_cards.extend(
            sort_functions[t](types[t])
        )
    return sorted_cards


if __name__ == '__main__':
    c = {'set': 'SVI', 'number': '34'}
    c = get_card(c)
    print(c)

    d = {'set': 'BRS', 'number': 'R'}
    d = get_card(d)
    print(d)
