import os
import json
import random
import pydash as _
from collections import defaultdict
from jinja2 import Environment, PackageLoader, select_autoescape

AREAS = {'TECH', 'PHIS', 'BIOM', 'ENVI', 'MATH', 'PHIL'}
INV_LISTS = AREAS | {'INT2', 'INT3'}

restrictions = {
    ('Джонас Солк', 'Карл Ландштайнер'),
    ('Роберт Макартур и Эдвард Уилсон', 'Роберт МакАртур и Эдвард Уилсон'),
    ('Рональд Фишер', 'Андрей Марков'),
}

def rename_image(name, actions):
    for action in actions:
        if action['card'].get('name') == name and _.get(action, 'old.name'):
            old = action['old']['name']
            if old == name:
                continue

            if (old, name) not in restrictions and os.path.exists(f"media/images/scientists/{old}.png"):
                print(f"renaming {old} -> {name}")
                os.rename(f"media/images/scientists/{old}.png", f"media/images/scientists/{name}.png")


def make_scientist(card, areas, perks, actions):
    rename_image(card['name'], actions)

    area = areas[card['idList']]

    perk = _.get(card, 'labels.0.name')
    if perk:
        perk = _.find(perks[area], lambda x: perk in x)
    else:
        print(f"no perk on scientist card: {card['name']}")
        perk = perks[area].pop()

    hint = perk.split('}')
    if len(hint) == 1:
        hint = None
    else:
        hint, perk = hint[0][1:], hint[1]

    perk = perk.split('-', 1)
    perk = f"<b>{perk[0]}</b> - {perk[1]}"

    hint_icons = {
        '[active]': '<div class="hint-circle"><i class="fa-solid fa-arrow-down"></i></div>',
        '[patent]': '<div class="hint-circle"><i class="fa-solid fa-stamp"></i></div>',
    }
    for old, new in hint_icons.items():
        perk = perk.replace(old, new)

    link, n, desc = card['desc'].partition('\n')

    return {
        'name': card['name'],
        'area': area,
        'intuition': [2, 5, 10],
        'perk': perk,
        'desc': desc
    }


def prepare_scientists_data():
    with open('data/scientists.json') as f:
        scientists_raw = json.loads(f.read())

    # load actions to rename images if needed
    actions = defaultdict(list)
    for action in scientists_raw['actions']:
        if not "card" in action['data']:
            continue
        actions[action['data']['card']['id']].append(action['data'])

    areas = {li['id']: li['name'] for li in scientists_raw['lists'] if li['name'] in AREAS}

    perk_lists = {'GG', 'G', 'B'}
    perk_lists = {li['id']: li['name'] for li in scientists_raw['lists'] if li['name'] in perk_lists}

    perks = {area: {q: list() for q in perk_lists.values()} for area in areas.values()}
    for card in scientists_raw['cards']:
        if card['idList'] not in perk_lists or card['closed']:
            continue

        area = card['labels'][0]['name']
        quality = perk_lists[card['idList']]

        perks[area][quality].append(card['name'])

    perks['TECH'] = perks['TECH']['G']*5 + perks['TECH']['GG']*2 + perks['TECH']['B']*5
    perks['BIOM'] = perks['BIOM']['G']*4 + perks['BIOM']['GG']*2 + perks['BIOM']['B']*5
    perks['PHIS'] = perks['PHIS']['G']*4 + perks['PHIS']['GG']*2 + perks['PHIS']['B']*2 + perks['PHIS']['B']
    perks['ENVI'] = perks['ENVI']['G']*5 + perks['ENVI']['GG']*2 + perks['ENVI']['B']*5
    perks['PHIL'] = perks['PHIL']['G']*4 + perks['PHIL']['GG']*2 + perks['PHIL']['B']*2 + perks['PHIL']['B']
    perks['MATH'] = perks['MATH']['G']*5 + perks['MATH']['GG']*2 + perks['MATH']['B']*2 + perks['MATH']['B']

    for a, p in perks.items():
        random.shuffle(p)
    #     for pp in p:
    #         print(a, pp)
    #         print()
        # print(a, len(p))

    return [
        make_scientist(card, areas, perks, actions[card['id']])
        for card in scientists_raw['cards']
        if card['idList'] in areas and not card['closed']
    ]


def make_invention(card, perks):
    areas = []
    for label in card['labels']:
        if label['name'] in AREAS:
            areas.append(label['name'])
        else:
            level = int(label['name'])

    year, desc = card['name'].split(' ', 1)

    return {
        'year': year,
        'desc': desc,
        'areas': areas,
        'level': level,
        'perk': _.map_(areas, lambda a: perks[a]),
    }



def prepare_inventions_data():
    with open('data/inventions.json') as f:
        inventions_raw = json.loads(f.read())

    areas = {li['id']: li['name'] for li in inventions_raw['lists'] if li['name'] in INV_LISTS}
    
    perk_list = _.find(inventions_raw['lists'], lambda li: li['name'] == 'EFFECTS')['id']
    perks = {
        card['labels'][0]['name']: card['name']
        for card in inventions_raw['cards']
        if card['idList'] == perk_list and not card['closed']
    }

    return [
        make_invention(card, perks)
        for card in inventions_raw['cards']
        if card['idList'] in areas and not card['closed']
    ]


def render():
    env = Environment(
        loader=PackageLoader("render"),
        autoescape=select_autoescape()
    )
    template = env.get_template("pnp.html.jinja2")
    with open('pnp.html', 'w') as f:
        f.write(template.render(
            scientists=prepare_scientists_data(),
            inventions=prepare_inventions_data(),
            size='small'
        ))


if __name__ == "__main__":
    render()