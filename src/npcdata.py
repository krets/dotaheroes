import logging
import io

import vpk
import vdf

from config import CONFIG

LOG = logging.getLogger('krets')

_TYPES = {
    'FIElD_INTEGER': int,
    'FIELD_FLOAT': float,
}
_SPECIAL_IGNORE = [
    'LinkedSpecialBonus',
    'ad_linked_ability',
    'ad_linked_abilities',
    'linked_ad_abilities',
    'LinkedSpecialBonusField',
    'LinkedSpecialBonusOperation',
    'levelkey',
    'var_type',
    'DamageTypeTooltip'
]

_PAK_CACHE = {}

def _game_version():
    data = _pak("resource/localization/patchnotes/patchnotes_english.txt")
    parts = [_.split('_') for _ in data['patch']]
    versions = list(sorted(set([tuple(_[2:4]) for _ in parts])))
    return '.'.join(versions[-1])

def _pak(key):
    pak_obj_key = '_pak_obj'
    pak = _PAK_CACHE.get(pak_obj_key)
    if pak is None:
        pak = _PAK_CACHE[pak_obj_key] = vpk.open(CONFIG['pak01_dir'])
    data = _PAK_CACHE.get(key)
    if data is None:
        data = _PAK_CACHE[key] = vdf.parse(io.StringIO(pak[key].read().decode('utf8')))
    return data

def get(npc_type='npc_heroes'):
    data = _pak(CONFIG['npc_file'] % npc_type)
    return _clean(data)

def _clean(data):
    """ Expecting string keys for any level of the npc data
    """
    if data and all([_.isdigit() for _ in data.keys()]) and 'var_type' in list(data.values())[0]:
        return _special_vars(data)

    for key, val in data.items():
        if isinstance(val, dict):
            data[key] = _clean(val)
    return data

def _special_vars(data):
    result = {}
    for item in data.values():
        convert = _TYPES.get(item.get('var_type', ''), lambda x: x)
        for k, v in item.items():
            if k in _SPECIAL_IGNORE:
                continue
            try:
                result[k] = [convert(_) for _ in v.split()]
            except (ValueError, AttributeError) as error:
                raise
    return result


def main():
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[0].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    version = _game_version()
    data = get()
    pass

if __name__ == '__main__':
    main()