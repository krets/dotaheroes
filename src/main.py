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
<div id="title"> Dota Hero Vision <span class="version">(v{DOTA_VERSION})<span></div>
"""
FOOTER = "</body></html>"

_HERO_PREFIX = 'npc_dota_hero_'


def _vision_bonuses(hero):
    bonuses = {}
    name = hero['_key'][len(_HERO_PREFIX):]
    for ability, details in hero['Abilities'].items():
        _ = {}
        for key, v in details.get('AbilitySpecial', {}).items():
            if 'bonus' in key and 'vision' in key:
                _[key] = [int(_) for _ in v]
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
    default = {k:v for k, v in heroes[default_name].items() if isinstance(v, str)}
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
    data = []
    rows = hero_details()
    data.sort(key=lambda x: x['HERO'])

    with open('../out/out.html', 'w') as out:
        out.write(HEADER)

        for row in rows:
            img = 'images/%s_minimap_icon.png' % (urllib.parse.quote(row["workshop_guide_name"].replace(' ', '_')))
            name = row['workshop_guide_name']
            vision_night = row['VisionNighttimeRange']
            vision_day = row['VisionDaytimeRange']

            ## Vision
            # height = width = smallest_vision/10<br/>
            # border = (largest_vision - smallest_vision)/2<br/>

            bonuses = _vision_bonuses(row)
            if bonuses:
                LOG.debug("Yay, bonus vision for %s: %s", name, bonuses)
            smallest_vision, largest_vision = sorted([vision_day, vision_night])
            width = int(smallest_vision/10)
            border = int((largest_vision - smallest_vision)/20)
            padding = int((200 - largest_vision / 10)/2)
            class_name = 'vision'
            if vision_night > vision_day:
                class_name = 'vision-night'
            if vision_day == vision_night:
                class_name = 'vision-slark'
            hero_attr = f"""<div class="hero">
            <img class="icon" src="{img}" title="{name}">
            <div class="{class_name}" title="Vision day: {vision_day:.0f} night: {vision_night:.0f}" style="margin:{padding}px; border-width: {border}px; height: {width}px; width: {width}px">
            </div>
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
        (vision_night, True, False, None),
        (vision_day, False, False, None),
    ]
    if vision_day == vision_night:
        visions = [(vision_night, None, False, None)]

    for bonus, details in bonuses.items():
        _active_key = 'duration'
        requires_active = bool(details.get(_active_key))
        for description, distances in details.items():
            if description == _active_key:
                continue
            night_only = 'night' in description
            for level, amount in enumerate(distances):
                comment = bonus
                if level > 0:
                    comment += " level %d" % (level + 1)
                visions.append((amount + vision_night, True, requires_active, comment))
                if not night_only:
                    comment += " day"
                    visions.append((amount + vision_day, False, requires_active, comment))
    visions.sort(reverse=True)
    if bonuses:
        LOG.debug("Yay, bonus vision for %s: %s", hero['workshop_guide_name'], bonuses)
    return visions


if __name__ == '__main__':
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[-1].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    main()