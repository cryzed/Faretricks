import collections
import difflib
import itertools
import operator
import types

import bs4
import requests
import retrying


def make_requests_session(arguments):
    session = requests.session()
    session.headers['User-Agent'] = arguments.user_agent

    original_request = session.request

    # Patch request method with default-timeout and retries
    @retrying.retry(stop_max_attempt_number=arguments.connect_retries, wait_fixed=arguments.connect_retry_delay)
    def request(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = arguments.connect_timeout, arguments.read_timeout

        return original_request(*args, **kwargs)

    # noinspection PyArgumentList
    session.request = types.MethodType(request, session)
    return session


def select_from_list(items, text='Please choose: '):
    count = len(items)
    for index, item in enumerate(items, start=1):
        print(f'{index}.\t{item}')

    return input(text)


# TODO: Ranges
def select_indices_from_list(items, text='Please choose: '):
    count = len(items)
    while True:
        values = select_from_list(items, text).split()

        try:
            indices = [int(value.strip()) - 1 for value in values]
        except ValueError:
            print(f'{values!r} contains an invalud number, please try again.')
            continue

        if any(index < 0 or index > count for index in indices):
            print(f'{indices!r} contains an index not within range (1-{count+1}), please try again.')
            continue

        return indices


def make_beautifulsoup(text, parser='html5lib'):
    return bs4.BeautifulSoup(text, parser)


def sort_by_shared_similarity(strings):
    similarity = collections.defaultdict(float)

    # TODO: n * log(n)
    for (index, a), b in itertools.product(enumerate(strings), strings):
        if a is not b:
            matcher = difflib.SequenceMatcher(a=a, b=b)
            similarity[index] += matcher.ratio()

    return [index for index, _ in sorted(similarity.items(), key=operator.itemgetter(1), reverse=True)]


def yield_sorted_by_indices(items, indices):
    return (items[index] for index in indices)
