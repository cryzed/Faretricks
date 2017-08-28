import collections
import functools


class _Selector(collections.namedtuple('Selector', ('type', 'value', 'root', 'target'))):
    def __str__(self):
        return self.value


def _get_best_selector(root, target, recursive=True):
    id_ = target.get('id', None)
    if id_:
        if len(root(id=id_, recursive=recursive)) == 1:
            return _Selector('id', f'#{id_}', root, target)
        if len(root(target.name, id=id_, recursive=recursive)) == 1:
            return _Selector('id', f'{target.name}#{id_}', root, target)

    for class_ in target.get('class', ()):
        if len(root(class_=class_, recursive=recursive)) == 1:
            return _Selector('class', f'.{class_}', root, target)
        if len(root(target.name, class_=class_, recursive=recursive)) == 1:
            return _Selector('class', f'{target.name}.{class_}', root, target)

    if len(root(target.name, recursive=recursive)) == 1:
        return _Selector('target', target.name, root, target)

    siblings = root(target.name, recursive=recursive)
    nth = siblings.index(target) + 1
    return _Selector('nth-of-type', f'{target.name}:nth-of-type({nth:d})', root, target)


def get_unique_selector_chain(root, target):
    if root is target:
        return []

    path = [target]
    for parent in target.parents:
        path.append(parent)
        if parent is root:
            break
    else:
        raise ValueError('target not contained in root')

    # Try to find the best selector, starting from target and navigating up
    for tag in path[:-1]:
        selector = _get_best_selector(root, tag)

        # Selector is sub-optimal, nth-of-type can always be found if recursive=True, but it's not very robust. If the
        # site layout changes by a single element of the same type the selector breaks.
        if selector.type == 'nth-of-type':
            continue

        # We found a good selector somewhere on the path leading from target to root
        selectors = [selector]

        # If we found a direct selector from root to target this will return [], else it will return the best selector
        # for the sub-path from the current tag to the target.
        next_selectors = get_unique_selector_chain(tag, target)

        # Extend the current list of selectors with the rest of the path
        selectors.extend(next_selectors)
        return selectors

    # Failed to find a good selector. Now we advance one level down inside the DOM, to the child of root of which the
    # target is a descendant of.
    selectors = [
        _Selector('>', '>', None, None),
        _get_best_selector(root, path[-2], False)
    ]

    # Attempt to get a good selector for the rest of the path.
    selectors.extend(get_unique_selector_chain(path[-2], target))
    return selectors


@functools.lru_cache(None)
def get_unique_selector_string(root, target):
    return ' '.join(str(s) for s in get_unique_selector_chain(root, target))
