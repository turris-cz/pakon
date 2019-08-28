import subprocess


def get(opt):
    delimiter = '__uci__delimiter__'
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = chld.communicate()
    out = out.strip().decode('ascii', 'ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    return out

def get_time(opt, default=None):
    ret = 0
    text = get(opt)
    if not text:
        text = default
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
