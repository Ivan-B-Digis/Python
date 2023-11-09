import json
import logging
import os
import sys

import aiofiles

from src import settings


def get_logger(name):
    """
    Returns a logger instance with added formatting and attached
    stdout handler.

    Returns:
        logging.Logger: logger instance
    """
    logger = logging.getLogger(name)

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    return logger


def _resolve_default_path(default, new=None):
    """
    Resolves a path to a file. If new path is provided, it is returned.

    Args:
        default: default path
        new: new path

    Returns:
        str: path to the file
    """
    if new:
        if not os.path.exists(new):
            raise FileNotFoundError(f'File {new} does not exist')
        return new
    else:
        if not os.path.exists(default):
            raise FileNotFoundError(
                f'File {default} does not exist. Please provide a valid path'
            )
        return default


def read_json_params(file_path=None):
    """
    Reads provided json file and parsed parameters.

    Args:
        file_path: path to the json file

    Returns:
        dict: contents of the json file
    """
    path = _resolve_default_path(settings.PARAMS_FILE_PATH, file_path)

    with open(path, 'r') as f:
        data = json.load(f)

    return data


async def write_items(items, file_path=None):
    """
    Writes provided items to the output file.

    Args:
        items (list): list of items to write
        file_path (str): path to the output file
    """
    path = _resolve_default_path(settings.OUTPUT_FILE_PATH, file_path)

    async with aiofiles.open(path, 'w+') as f:
        await f.write(json.dumps(items, indent=4))
        await f.flush()
