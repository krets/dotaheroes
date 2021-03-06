from collections import Counter
import urllib.parse
import logging

LOG = logging.getLogger('dotaheroes')

import npcdata

DOTA_VERSION = "7.27d"

HEADER = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="main.css">
</head>
<body>
<div id="title"> Dota Hero Vision <span class="version">(v%s)<span></div>
"""
FOOTER = "</body></html>"

_HERO_PREFIX = 'npc_dota_hero_'


def _vision_bonuses(hero):
    bonuses = {}
    name = hero['_key'][len(_HERO_PREFIX):]
    for ability, details in hero['Abilities'].items():
        _ = {}
        if ability in ['templar_assassin_trap', 'templar_assassin_psionic_trap']:
            LOG.debug("Ignoring %s Bonus Vision" % ability)
            continue
        for subvalue_key in ('AbilitySpecial', 'AbilityValues'):
            for key, v in details.get(subvalue_key, {}).items():
                if 'bonus' in key and 'vision' in key:
                    if isinstance(v, (dict)) and 'value' in v:
                        v = v['value']
                    if ' ' in v:
                        v = v.split(' ')
                    _[key] = [int(__) for __ in v]
        if _:
            _['duration'] = details.get('duration')
            bonuses[ability[len(name):].replace('_', ' ').title().strip(' ')] = _

        # talent bonuses
        if 'special_bonus' in ability and 'vision' in ability:
            level = 25
            for key, val in hero.items():
                if val == ability:
                    number = int(''.join([_ for _ in key if _.isdigit()]))
                    if 9 < number < 12:
                        level = 10
                    elif 11 < number < 14:
                        level = 15
                    elif 13 < number < 16:
                        level = 20

            for daynight in ('day', 'night', ''):
                if daynight in ability:
                    break
            bonuses[f"Talent: Level {level} {daynight} vision"] = {ability: [int(details['AbilitySpecial']['value'][0])]}

    return bonuses

def hero_details():
    default_name = 'npc_dota_hero_base'
    veto = ['npc_dota_hero_target_dummy', default_name]
    rows = []
    data = npcdata.get('npc_heroes')
    heroes = data['DOTAHeroes']
    hero_abilities = npcdata.get('npc_abilities')['DOTAAbilities']
    default = {k: v for k, v in heroes[default_name].items() if isinstance(v, str)}
    for k, v in default.items():
        if isinstance(v, (str)):
            try:
                default[k] = float(v)
            except ValueError:
                default[k] = v
    for key, val in heroes.items():
        if key in veto or not key.startswith(_HERO_PREFIX):
            continue
        row = default.copy()
        row['_key'] = key
        row['Abilities'] = {}
        for k, v in val.items():
            if isinstance(v, (str)):
                try:
                    row[k] = float(v)
                except ValueError:
                    row[k] = v
            if k.startswith('Ability') and k[-1].isdigit():
                row['Abilities'][v] = hero_abilities.get(v, {})
        rows.append(row)
    return rows


def main():
    _vision_key_day = 'VisionDaytimeRange'
    _vision_key_night = 'VisionNighttimeRange'
    data = []
    rows = hero_details()
    _visions = [(_[_vision_key_day], _[_vision_key_night]) for _ in rows]
    _visions_day, _visions_night = zip(*_visions)
    _visions_day = Counter(_visions_day)
    _visions_night = Counter(_visions_night)
    vision_day_normal = _visions_day.most_common(1)[0][0]
    vision_night_normal =_visions_night.most_common(1)[0][0]

    data.sort(key=lambda x: x['HERO'])
    version = npcdata._game_version()

    with open('../out/out.html', 'w') as out:
        out.write(HEADER % version)

        for hero in rows:
            img = 'images/%s_minimap_icon.png' % (urllib.parse.quote(hero["workshop_guide_name"].replace(' ', '_')))
            name = hero['workshop_guide_name']
            vision_night = hero[_vision_key_night]
            vision_day = hero[_vision_key_day]
            visions = extract_visions(hero)

            hero_classes = []
            if vision_day != vision_day_normal or vision_night != vision_night_normal:
                hero_classes.append("abnormal_base_vision")

            hero_attr = f'<div class="hero {" ".join(hero_classes)}"><img class="icon" src="{img}" title="{name}">'

            for i, details in enumerate(visions):
                amount, is_night_vision, requires_active, title = details

                classes = ['vision']
                if len([_ for _ in visions if _[1] == is_night_vision]) > 1:
                    classes.append('multiple')
                if title is None:
                    title = 'base vision'
                    classes.append('base')

                if is_night_vision is None:
                    classes.append('slark')
                elif is_night_vision:
                    classes.append('night')
                else:
                    classes.append('day')

                if requires_active:
                    classes.append('active')

                width = int(amount)/10
                margin = (200 - width)/2
                width -=2 # border on all items.
                class_str = ' '.join(classes)
                hero_attr += (
                    f'<div class="{" ".join(classes)}" title="{title}" style="margin:{margin}px; '
                    f'height: {width}px; width: {width}px; z-index: {i}"></div>')

            hero_attr += f"""
            <div class='stats'>
                <span class='hero-name'>{name}</span><br/><span class='value-day'>{vision_day:.0f}</span><span class='value-night'>{vision_night:.0f}</span>
            </div>
    
        </div>
        """
            out.write(hero_attr)
        out.write(FOOTER)


def extract_visions(hero):
    vision_night = hero['VisionNighttimeRange']
    vision_day = hero['VisionDaytimeRange']

    bonuses = _vision_bonuses(hero)
    # vision: amount, is_night_vision, requires_active, description
    visions = [
        (vision_night, True, False, ''),
        (vision_day, False, False, ''),
    ]
    if vision_day == vision_night:
        visions = [(vision_night, None, False, '')]

    for bonus, details in bonuses.items():
        _active_key = 'duration'
        requires_active = bool(details.get(_active_key))
        for description, distances in details.items():
            if description == _active_key:
                continue
            night_only = 'night' in description
            for level, amount in enumerate(distances):
                if amount <= 1:
                    LOG.debug("Ignoring low/no bonus (%s %s %s)", hero['workshop_guide_name'], bonus, level+1)
                    continue
                comment = bonus
                if level > 0:
                    comment += " level %d" % (level + 1)
                visions.append((amount + vision_night, True, requires_active, comment))
                if not night_only:
                    comment += " day"
                    visions.append((amount + vision_day, False, requires_active, comment))
    visions.sort(reverse=True)
    if bonuses and len(visions) > 2:
        LOG.debug("Yay, bonus vision for %s: %s", hero['workshop_guide_name'], bonuses)
    return visions


if __name__ == '__main__':
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[-1].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    main()