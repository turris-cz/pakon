def timestr_to_seconds(text):
    ret = 0
    if text[-1:].upper() == 'M':
        ret = int(text[:-1]) * 60
    elif text[-1:].upper() == 'H':
        ret = int(text[:-1]) * 3600
    elif text[-1:].upper() == 'D':
        ret = int(text[:-1]) * 24 * 3600
    elif text[-1:].upper() == 'W':
        ret = int(text[:-1]) * 7 * 24 * 3600
    else:
        ret = int(text)
    return ret
