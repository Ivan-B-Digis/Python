from abc import ABC, abstractmethod


class Crawler(ABC):
    @abstractmethod
    async def process(self):
        """
        Contains processing logic for the crawler.
        """
        pass

    @abstractmethod
    async def setup(self):
        """
        Initializes crawler's dependencies.
        """
        pass

    @abstractmethod
    def validate_params(self, params):
        """
        Validates the input parameters.
        """
        pass

    @abstractmethod
    async def close(self):
        """
        Closes the crawler.
        """
        pass
