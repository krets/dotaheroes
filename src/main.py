import urllib.parse

import npcheroes

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

def hero_details():
    default_name = 'npc_dota_hero_base'
    veto = ['npc_dota_hero_target_dummy', default_name]
    rows = []
    data = npcheroes.get()
    heroes = data['DOTAHeroes']
    default = {k:v for k, v in heroes[default_name].items() if isinstance(v, str)}
    for k, v in default.items():
        if isinstance(v, (str)):
            try:
                default[k] = float(v)
            except ValueError:
                default[k] = v
    for key, val in heroes.items():
        if key in veto or not key.startswith('npc_dota_hero'):
            continue
        row = default.copy()
        row['_key'] = key
        for k, v in val.items():
            if isinstance(v, (str)):
                try:
                    row[k] = float(v)
                except ValueError:
                    row[k] = v
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

if __name__ == '__main__':
    main()