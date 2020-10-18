import logging

from config import CONFIG

LOG = logging.getLogger('krets')

def get():
    """ parser for npc_heroes.txt written without spec. Seems to work.
    """
    data = {}
    key = None
    cursor = data
    stack = []
    comment_marker = '//'
    with open(CONFIG['npc_heroes'], 'rb') as fh:
        for i, raw_line in enumerate(fh):
            line = raw_line.decode().strip()
            if comment_marker in line:
                line, _ = line.split(comment_marker, 2)
            parts = [_.strip() for _ in line.split("\t") if _.strip()]
            if not parts:
                continue
            if len(parts) == 1:
                if parts[0] == '{' and key is not None:
                    cursor[key] = {}
                    stack.append(cursor)
                    cursor = cursor[key]
                elif parts[0] == '}':
                    cursor = stack.pop()
                else:
                    key = parts[0].strip('"')
                continue
            if len(parts) > 2:
                # Seems like the slardar line has a misplaced tab
                LOG.warning("Bad data on line: %s of %s: %s", i+1, CONFIG['npc_heroes'], raw_line)

            key, value = [_.strip('"') for _ in parts[:2]]
            cursor[key] = value
            key = None

    return data

def main():
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[0].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    data = get()
    pass

if __name__ == '__main__':
    main()