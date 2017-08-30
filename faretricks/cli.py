import argparse
import collections
import sys

import requests

from faretricks.scrape import yield_headings, get_text, find_deepest_node, make_beautifulsoup
from faretricks.spoon import get_unique_selector_string
from faretricks.utils import make_requests_session, sort_by_shared_similarity, yield_sorted_by_indices, \
    select_indices_from_list, interruptable

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0'
TIMEOUT = 60
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 10
ERROR_EXIT_CODE = 1

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('url')
argument_parser.add_argument('--user-agent', '-u', default=USER_AGENT)
argument_parser.add_argument('--connect-timeout', '-c', type=float, default=TIMEOUT)
argument_parser.add_argument('--read-timeout', '-r', type=float, default=TIMEOUT)
argument_parser.add_argument('--connect-retries', '-R', type=int, default=CONNECT_RETRIES)
argument_parser.add_argument('--connect-retry-delay', '-d', type=float, default=CONNECT_RETRY_DELAY)


@interruptable
def _find_heading(soup, url):
    headings = list(yield_headings(soup))
    if not headings:
        return

    # Sort headings by shared similarity, the title is likely to appear more often and thus be further up
    texts = [get_text(heading) for heading in headings]
    similarity_indices = sort_by_shared_similarity(texts)
    headings = list(yield_sorted_by_indices(headings, similarity_indices))
    texts = yield_sorted_by_indices(texts, similarity_indices)

    # Create string representations of elements and their selectors for the selection
    items = [f'{text!r}: {get_unique_selector_string(soup, heading)!r}' for heading, text in zip(headings, texts)]
    index = select_indices_from_list(items, 'Please choose heading: ')[0]
    return headings[index]


def find_toc_heading(soup, url):
    return _find_heading(soup, url)


@interruptable
def find_toc_links(soup, url):
    candidates = soup('a', href=True)
    texts = [get_text(candidate) for candidate in candidates]
    items = [repr(text) for text in texts]
    indices = select_indices_from_list(items, 'Select a number of links to be included: ')

    candidates = list(yield_sorted_by_indices(candidates, indices))
    parent = candidates[0].parent
    while not set(candidates).issubset(set(parent('a', href=True))):
        parent = parent.parent

    return parent


def find_chapter_heading(soup, url):
    return _find_heading(soup, url)


@interruptable
def find_chapter_content(soup, url):
    beginning = input('Enter excerpt of the chapter beginning: ').lower()
    ending = input('Enter excerpt of the chapter ending: ').lower()
    return find_deepest_node(soup, lambda text: beginning in text and ending in text)


def find_custom(soup, url):
    pass


def _main(arguments):
    session = make_requests_session(arguments)
    response = requests.get(arguments.url)
    soup = make_beautifulsoup(response.text)

    selectors = collections.OrderedDict()
    for find in [find_toc_heading, find_toc_links]:
        element = find(soup, response.url) or find_custom(soup, response.url)
        selectors[find] = get_unique_selector_string(soup, element)
        print()

    url = input('Please enter chapter URL: ')
    response = requests.get(url)
    soup = make_beautifulsoup(response.text)
    for find in [find_chapter_heading, find_chapter_content]:
        element = find(soup, response.url) or find_custom(soup, response.url)
        selectors[find] = get_unique_selector_string(soup, element)
        print()

    for function_, selector in selectors.items():
        print(f'{function_.__name__}: {selector!r}')


def main():
    arguments = argument_parser.parse_args()
    try:
        return _main(arguments)
    except KeyboardInterrupt:
        print('Aborted.', file=sys.stderr)
        return ERROR_EXIT_CODE


if __name__ == '__main__':
    sys.exit(main())
