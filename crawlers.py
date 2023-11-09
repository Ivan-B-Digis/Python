import asyncio
import random
import urllib.parse
from http import HTTPStatus

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer
from jsonschema import validate

from src import exceptions
from src import settings
from src.abstracts import Crawler
from src.items import GithubSearchItem
from src.utils import read_json_params, write_items, get_logger


_logger = get_logger(__name__)


class GithubSearchCrawler(Crawler):
    def __init__(self, *args, **kwargs):
        # load input date from a json file
        params = read_json_params(kwargs.get('params_file_path'))
        _logger.info(f'Provided parameters: {params}')

        self.validate_params(params)

        # required parameters
        self.keywords = params['keywords']
        self.type_ = params['type']

        # optional parameters
        self.proxies = params.get('proxies', [])

        # collection for storing parsed items
        self.items = []

        self._session = None

        super().__init__()

    @property
    def search_url(self):
        """
        Forms an url based on the input data for the GitHub search.

        Returns:
            str: url for the GitHub search
        """
        query_params = {
            'q': '+'.join(self.keywords),
            'type': self.type_.lower()
        }
        query = urllib.parse.urlencode(query_params, safe='+')

        return urllib.parse.urljoin(settings.HOST, 'search?' + query)

    @property
    def proxy(self):
        """
        Selects a proxy server to use.

        Returns:
            str: selected proxy server
        """
        selected = f"https://{random.choice(self.proxies)}" if self.proxies else None
        _logger.info(f'Using proxy: {selected}')

        return selected

    async def setup(self):
        """
        Initializes dependencies such client
        session to perform web requests.
        """
        self._session = aiohttp.ClientSession()

    @staticmethod
    def validate_params(params):
        """
        Validates input parameters.

        Args:
            params: input parameters from the json
        Raises:
            InvalidSearchType: if the search type is not supported
            jsonschema.exceptions.ValidationError: if the input data does not match the schema
        """
        # check if the input data is valid and matches the schema
        validate(instance=params, schema=settings.PARAMS_SCHEMA)

        # check if the search type is supported
        if params['type'] not in settings.SUPPORTED_GITHUB_TYPES:
            raise exceptions.InvalidSearchType(
                f"Invalid search type: `{params['type']}`. "
                f"Valid types are: {', '.join(settings.SUPPORTED_GITHUB_TYPES)}"
            )

        _logger.info('Parameters are valid')

    async def process(self):
        """
        Contains processing logic for the crawler.
        Sends a request to the GitHub search page and based on
        the search type calls the corresponding parser.
        """
        tasks = []
        # coroutines for parsing different types of search results
        coro = {
            'Repositories': self.parse_repositories,
            'Issues': self.parse_data_hydro_click_elements,
            'Wikis': self.parse_data_hydro_click_elements
        }

        _logger.info(f'Searching for {self.type_} with keywords: {self.keywords}')

        await self.setup()

        async with self._session.get(self.search_url, proxy=self.proxy) as response:
            _logger.info(f'Received response: {response.status}')

            if response.status == HTTPStatus.OK:
                text = await response.text()
                soup = BeautifulSoup(
                    text,
                    'html.parser',
                    parse_only=SoupStrainer('a')
                )
                tasks.append(
                    asyncio.create_task(coro[self.type_](soup))
                )
            else:
                raise exceptions.RequestProcessError(
                    f'Bad response status: {response.status}'
                )
            await asyncio.gather(*tasks)

        # close a crawler
        await self.close()
        # save parsed items to a json file
        _logger.info(f'Parsed {len(self.items)} items. Saving to {settings.OUTPUT_FILE_PATH}')
        await write_items(self.items)

    async def close(self):
        """
        Closes the crawler.
        """
        if not self._session.closed:
            await self._session.close()

    @staticmethod
    async def get_extras(text):
        """
        Parses the owner and language stats from the repository page to
        form extras attribute of the GithubSearchItem's extras attribute.

        Args:
            text: html text of the repository page
        Returns:
            dict: owner and language stats
        """
        soup = BeautifulSoup(text, 'html.parser')
        owner = soup.find(attrs={'rel': 'author'}).text.strip()

        # retrieve elements containing language stats data
        language_elements = [
            lang for lang in soup.find_all(attrs={'data-ga-click': True})
            if 'stats' in lang['data-ga-click']
        ]

        # clear language stats from unnecessary data
        # noinspection PyTypeChecker
        language_stats = dict([
            stat.text.strip().replace('%', '').split('\n')
            for stat in language_elements
        ])

        return {
            'owner': owner,
            'language_stats': language_stats
        }

    async def parse_repositories(self, data):
        """
        Parses repositories from the search page and appends
        formed item into the item collection.

        Args:
            data: html text of the search page
        """
        links = data.find_all(
            attrs={'class': 'v-align-middle'},
            href=True
        )
        for a in links:
            item = GithubSearchItem(url=a['href'])
            _logger.info(f'Processing: {item}')

            async with self._session.get(item.url) as response:
                text = await response.text()

            extras = await self.get_extras(text)

            item.extras = extras
            self.items.append(item.to_dict())

    async def parse_data_hydro_click_elements(self, data):
        """
        Parses issues and wikis from the search page and appends
        into the item collection.

        Args:
            data: html text of the search page
        """
        # issues and wikis have the same data-hydro-click elements
        def match_condition(a):
            """
            Checks if the element is an issue or a wiki.

            Args:
                a: element to check
            Returns:
                bool: True if the element is an issue or a wiki, False otherwise
            """
            return (
                a.has_attr('href') and a.has_attr('data-hydro-click')
                and 'search_result.click' in a['data-hydro-click']
            )

        links = [a for a in data if match_condition(a)]

        for link in links:
            item = GithubSearchItem(url=link['href'])
            _logger.info(f'Processing: {item}')
            self.items.append(item.to_dict())
