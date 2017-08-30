import itertools
import urllib.parse

_TEMPLATE = '''
import itertools
import json
import re

from base_adapter import BaseSiteAdapter


def get_text(element):
    return element.get_text(separator=' ', strip=True)


class {class_name}Adapter(BaseSiteAdapter):
    _SITE_DOMAIN = '{domain}'
    _SITE_URL_PATTERN = r'{site_url_pattern}'

    def __init__(self, configuration, url):
        super({class_name}Adapter, self).__init__(configuration, url)
        self.story.setMetadata('storyId', re.match(self._SITE_URL_PATTERN, url).group(1))
        self.story.setMetadata('siteabbrev', '{domain}')

    @staticmethod
    def getSiteDomain():
        return {class_name}Adapter._SITE_DOMAIN

    def getSiteURLPattern(self):
        return self._SITE_URL_PATTERN

    @classmethod
    def getSiteExampleURLs(cls):
        return [{site_example_url}]

    def doExtractChapterUrlsAndMetadata(self, get_cover=True):
        soup = self.make_soup(self._fetchUrl(self.url))
        self.story.setMetadata('title', get_text(soup.select_one('{toc_title_pattern}')))

    def getChapterText(self, url):
        soup = self.make_soup(self._fetchUrl(self.url))
        return soup


def getClass():
    return {class_name}Adapter
'''


def _netloc_to_camelcase(netloc):
    first_character = netloc[0].upper()
    characters = [first_character]
    previous_character = first_character

    for character in itertools.islice(netloc, 1, None):
        if previous_character == '.':
            character = character.upper()

        if character != '.':
            characters.append(character)

        previous_character = character
    return ''.join(characters)


def render_fanficfare_adapter_template(url, toc_title_pattern, toc_links_pattern, chapter_title_pattern,
                                       chapter_content_pattern):
    netloc = urllib.parse.urlsplit(url).netloc
    class_name = _netloc_to_camelcase(netloc)
    return _TEMPLATE.format(
        class_name=class_name,
        domain=netloc,
        site_url_pattern='...',
        site_example_url=url,
        toc_title_pattern=toc_title_pattern,
        toc_links_pattern=toc_links_pattern,
        chapter_title_pattern=chapter_title_pattern,
        chapter_content_pattern=chapter_content_pattern
    )
