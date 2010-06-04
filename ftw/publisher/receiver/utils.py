
def recursive_encode(value, enc='utf8'):
    # str
    if isinstance(value, str):
        return value

    # unicode
    if isinstance(value, unicode):
        return value.encode(enc)

    # lists, sets, tuples
    if type(value) in (list, set, tuple):
        nval = []
        for sval in value:
            nval.append(recursive_encode(sval, enc=enc))
        return type(value)(nval)

    # dicts
    if isinstance(value, dict):
        nval = {}
        for key, sval in value.items():
            key = recursive_encode(key, enc=enc)
            sval = recursive_encode(sval, enc=enc)
            nval[key] = sval
        return nval

    return value
        
