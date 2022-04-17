from main import hero_details

def main():
    heroes = {_['workshop_guide_name']:_ for _ in hero_details()}
    for name, hero in heroes.items():
        for ability_name, details in hero.get('Abilities', {}).items():
            for key, val in details.get('AbilitySpecial', {}).items():
                if 'tick' in key:
                    print("%s %s.%s: %s" % (val, ability_name, key, val))
                    pass
    pass

if __name__ == '__main__':
    main()
