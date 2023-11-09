# Project settings
DEBUG = True

# Crawler settings
PARAMS_FILE_PATH = 'resources/parameters.json'
OUTPUT_FILE_PATH = 'resources/output.json'
SUPPORTED_GITHUB_TYPES = ('Repositories', 'Issues', 'Wikis')
HOST = 'https://github.com'

PARAMS_SCHEMA = {
    'type': 'object',
    'properties': {
        'keywords': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
            'minItems': 1
        },
        'proxies': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'type': {
            'type': 'string',
        }
    },
    'required': ['keywords', 'type']
}
