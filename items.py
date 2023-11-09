import urllib.parse

from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from src import settings


@dataclass_json
@dataclass
class GithubSearchItem:
    """
    Item for the scraped GitHub search entity
    """
    url: str
    extras: dict = field(default_factory=dict)

    def __post_init__(self):
        self.url = urllib.parse.urljoin(settings.HOST, self.url)

    def __str__(self):
        return f'GithubSearchItem(url={self.url}, extras={self.extras})'
