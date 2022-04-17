import logging
import io

import vpk

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

def get(npc_type='npc_heroes'):
    data = _read(npc_type)
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

def _extract(handle):
    """ parser for npc_heroes.txt written without spec. Seems to work.

    Builds a stack to allow arbitrary depth of data structure.
    """
    data = {}
    key = None
    cursor = data
    stack = []
    comment_marker = '//'
    for i, raw_line in enumerate(handle):
        if hasattr(raw_line, 'decode'):
            line = raw_line.decode().strip()
        else:
            line = raw_line
        if comment_marker in line:
            line, _ = line.split(comment_marker, 1)
        parts = [_.strip() for _ in line.split("\t") if _.strip()]
        if not parts:
            continue
        if len(parts) == 1:
            if parts[0] == '{' and key is not None:
                cursor[key] = {}
                stack.append(cursor)
                cursor = cursor[key]
            elif parts[0] == '}':
                if stack:
                    cursor = stack.pop()
            else:
                key = parts[0].strip('"')
            continue
        if len(parts) > 2:
            # Seems like the slardar line has a misplaced tab
            LOG.warning("Bad data on line: %s : %s", i + 1, raw_line)

        key, value = [_.strip('"') for _ in parts[:2]]
        cursor[key] = value
        key = None
    return data

def _read(npc_type):
    pak = vpk.open(CONFIG['pak01_dir'])
    return _extract(io.StringIO(pak[CONFIG['npc_file'] % npc_type].read().decode('utf8')))


def main():
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[0].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    data = get()
    pass

if __name__ == '__main__':
    main()