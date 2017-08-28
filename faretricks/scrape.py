def yield_headings(soup):
    for index in range(1, 7):
        for heading in soup(f'h{index}', text=True):
            yield heading


def get_text(soup):
    return soup.get_text(strip=True, separator=' ')


def find_deepest_node(soup, predicate):
    stack = soup(recursive=False)
    last_match = None
    while stack:
        element = stack.pop(0)
        text = get_text(element).lower()
        if predicate(text):
            last_match = element
            stack.extend(element(recursive=False))

        if not stack:
            return last_match
