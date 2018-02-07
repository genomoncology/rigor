# https://stackoverflow.com/a/3233356
def nested_update(d, u):
    import collections
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = nested_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def overlap(l1, l2):
    return set(l1 or []) & set(l2 or [])


def clean_split(line, delimiter="|"):
    items = [value.strip() for value in line.split(delimiter)]

    # trim empty first item
    if items and not items[0]:
        items = items[1:]

    # trim empty last item
    if items and not items[-1]:
        items = items[:-1]

    # replace empty strings with Nones
    return [None if item == '' else item for item in items]


def parse_into_header_rows(text_table):
    lines = [line.strip() for line in text_table.strip().splitlines()]
    header = clean_split(lines[0])
    rows = [clean_split(line) for line in lines[1:]]
    return header, rows


def to_nested_dict(nested_cols, value):
    top_col, rest_col = nested_cols[0], nested_cols[1:]
    if rest_col:
        return {top_col: to_nested_dict(rest_col, value)}
    else:
        return {top_col: value}


def parse_into_rows_of_dicts(text_table):
    header, rows = parse_into_header_rows(text_table)
    header = [column.split("/") for column in header]
    result = []
    for row in rows:
        d = {}
        for (nested_cols, value) in zip(header, row):
            nested_update(d, to_nested_dict(nested_cols, value))

        result.append(d)
    return result


def parse_into_dicts_of_rows(text_table):
    header, rows = parse_into_header_rows(text_table)
    d = {}
    for col_num in range(len(header)):
        d[header[col_num]] = [row[col_num] for row in rows]
    return d


def download_json_with_headers(suite, path):
    """ Download using a suite profile (such as headers). """
    from . import Requestor, StepState, Step, State, Case
    import requests

    # a little bit painful, but ensures headers are full evaluated w/ globals
    request = Requestor(host=suite.host, path=path)
    state = State(suite=suite, case=Case(scenarios=[], file_path="."))
    step = Step(request=request, description="Download: %s" % path)
    step_state = StepState(state=state, step=step)
    fetch = step_state.get_fetch()
    kw = fetch.get_kwargs(is_aiohttp=False)
    context = requests.request(fetch.method, fetch.url, **kw)

    # hard failure during development.
    assert context.status_code == 200, "%s => %s" % (fetch.url, context)
    return context.json()
