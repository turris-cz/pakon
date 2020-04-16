import subprocess


# TODO: replace with uci bindings - once available
def uci_get(opt):
    delimiter = '__uci__delimiter__'
    child = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = child.communicate()
    out = out.strip().decode('ascii', 'ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out
