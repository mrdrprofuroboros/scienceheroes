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


def randint3(mid):
    return random.randint(mid-1, mid+1)


def make_scientist(card, areas, perks, actions):
    rename_image(card['name'], actions)

    area = areas[card['idList']]

    perk = _.get(card, 'labels.0.name')
    if perk:
        text = _.find(perks[area], lambda x: perk in x)
    else:
        print(f"no perk on scientist card: {card['name']}")
        text = perks[area].pop()

    text = text.split('-', 1)
    text = f"<b> {text[0]} </b> - {text[1]}"

    link, n, desc = card['desc'].partition('\n')

    return {
        'name': card['name'],
        'area': area,
        'comp': [randint3(4), randint3(6), randint3(8)],
        'perk': perk,
        'text': text,
        'desc': desc,
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


def get_stats(level, areas):
    """returns stars, comp, cost"""
    if {'MATH', 'PHIL'} & set(areas):
        return 4, randint3(9), randint3(5)
    if 'INT2' in areas:
        return 6, randint3(15), randint3(7)
    if 'INT3' in areas:
        return 8, randint3(21), randint3(9)

    lvl2comp = {1: 4, 2: 9, 3: 15, 4: 21}
    lvl2cost = {1: 3, 2: 5, 3: 7, 4: 9}
    stars = 2 * level - 1 + int('ENVI' in areas)
    return stars, randint3(lvl2comp[level]), randint3(lvl2cost[level])


def make_invention(card, perks):
    areas = []
    for label in card['labels']:
        if label['name'] in AREAS:
            areas.append(label['name'])
        else:
            level = int(label['name'])

    year, desc = card['name'].split(' ', 1)
    try:
        desc, who = desc[:-1].rsplit('(', 1)
    except:
        print(desc)
        who = ''
    stars, comp, cost = get_stats(level, areas)

    return {
        'year': year,
        'desc': desc,
        'who': who,
        'areas': sorted(areas),
        'colors': sorted(areas * (6//len(areas))),
        'level': level,
        'stars': stars,
        'comp': comp,
        'cost': cost,
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