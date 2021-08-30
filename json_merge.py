
def merger(a, b):
    for key in b:
        if key in a:
            if type(b[key]) is dict:
                a[key] = merger(a[key], b[key])
            if type(b[key]) is list and type(a[key]) == list:
                a[key].extend(b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
