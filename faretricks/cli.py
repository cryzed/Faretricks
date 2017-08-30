import argparse
import sys
import urllib.parse

import requests

from faretricks.fanficfare import render_fanficfare_adapter_template
from faretricks.scrape import yield_headings, get_text, find_deepest_node, make_beautifulsoup
from faretricks.spoon import get_unique_selector
from faretricks.utils import make_requests_session, sort_by_shared_similarity, yield_sorted_by_indices, \
    select_indices_from_list, interruptable, input_while_empty

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0'
TIMEOUT = 60
CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 10
ERROR_EXIT_CODE = 1
ENCODING = 'UTF-8'

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
    items = [f'{text!r}: {get_unique_selector(soup, heading)!r}' for heading, text in zip(headings, texts)]
    index = select_indices_from_list(items, 'Please choose heading: ')[0]
    return get_unique_selector(soup, headings[index])


def find_toc_title(soup, url):
    return _find_heading(soup, url)


# TODO: Figure out changing part of chapter URLs using difflib and turn it into a regex/fnmatch pattern
@interruptable
def find_toc_links(soup, url):
    candidates = soup('a', href=True)
    texts = [get_text(candidate) for candidate in candidates]
    items = [repr(text) for text in texts]
    indices = select_indices_from_list(items, 'Select a number of links to be included: ')

    # Search upwards for first element that includes all candidate links
    candidates = list(yield_sorted_by_indices(candidates, indices))
    parent = candidates[0].parent
    while not set(candidates).issubset(set(parent('a', href=True))):
        parent = parent.parent

    return get_unique_selector(soup, parent) + ' a'


@interruptable
def find_chapter_content(soup, url):
    beginning = input_while_empty('Enter excerpt of the chapter beginning: ').lower()
    ending = input_while_empty('Enter excerpt of the chapter ending: ').lower()

    def predicate(element):
        text = get_text(element).lower()
        return beginning in text and ending in text

    element = find_deepest_node(soup, predicate)
    return get_unique_selector(soup, element)


def find_custom(soup, url):
    return input_while_empty('Enter custom BeautifulSoup4-compatible CSS selector: ')


def _main(arguments):
    session = make_requests_session(arguments)
    response = requests.get(arguments.url)
    soup = make_beautifulsoup(response.text)

    # Scrape table of contents
    selectors = {}
    for find in [find_toc_title, find_toc_links]:
        selector = find(soup, response.url) or find_custom(soup, response.url)
        selectors[find] = selector
        print()

    # Scrape chapter
    chapter_url = input('Please enter chapter URL: ')
    chapter_response = requests.get(chapter_url)
    chapter_soup = make_beautifulsoup(chapter_response.text)
    selector = (
        find_chapter_content(chapter_soup, chapter_response.url) or
        find_custom(chapter_soup, chapter_response.url))
    selectors[find_chapter_content] = selector

    # Write adapter code
    adapter_code = render_fanficfare_adapter_template(
        response.url,
        toc_title_pattern=selectors[find_toc_title],
        toc_links_pattern=selectors[find_toc_links],
        chapter_content_pattern=selectors[find_chapter_content])
    netloc = urllib.parse.urlsplit(chapter_url).netloc
    with open(f'adapter_{netloc.replace(".", "")}.py', 'w', encoding=ENCODING) as file:
        file.write(adapter_code)


def main():
    arguments = argument_parser.parse_args()
    try:
        return _main(arguments)
    except KeyboardInterrupt:
        print('Aborted.', file=sys.stderr)
        return ERROR_EXIT_CODE


if __name__ == '__main__':
    sys.exit(main())
