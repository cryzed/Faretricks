import re
import urlparse

from base_adapter import BaseSiteAdapter


def get_text(element):
    return element.get_text(separator=' ', strip=True)


class VolarenovelsComAdapter(BaseSiteAdapter):
    _SITE_DOMAIN = 'volarenovels.com'
    _SITE_URL_PATTERN = r'https?://volarenovels.com/(.+?)(/.*)?'

    def __init__(self, configuration, url):
        super(VolarenovelsComAdapter, self).__init__(configuration, url)
        self.story.setMetadata('storyId', re.match(self._SITE_URL_PATTERN, url).group(1))
        self.story.setMetadata('siteabbrev', self._SITE_DOMAIN)

    @staticmethod
    def getSiteDomain():
        return VolarenovelsComAdapter._SITE_DOMAIN

    def getSiteURLPattern(self):
        return self._SITE_URL_PATTERN

    @classmethod
    def getSiteExampleURLs(cls):
        return ['http://volarenovels.com/adorable-creature-attack/']

    def doExtractChapterUrlsAndMetadata(self, get_cover=True):
        soup = self.make_soup(self._fetchUrl(self.url))
        self.story.setMetadata('title', get_text(soup.select_one('.entry-title')))
        self.story.setMetadata('authorId', self._SITE_DOMAIN)
        for a in soup.select('#content .wrapper a'):
            title = get_text(a)
            url = urlparse.urljoin(self.url, a['href'])
            self.chapterUrls.append((title, url))

    def getChapterText(self, url):
        soup = self.make_soup(self._fetchUrl(url))
        content = soup.select_one('.entry-content')
        return self.utf8FromSoup(url, content)


def getClass():
    return VolarenovelsComAdapter
