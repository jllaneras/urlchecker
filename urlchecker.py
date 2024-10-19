#!/usr/bin/env python3

from difflib import HtmlDiff
from pathlib import Path
from time import strftime
import hashlib
import os
import requests
import sys

SCRIPT_DIR = Path(__file__).absolute().parent
CACHE_DIR = SCRIPT_DIR / "cache"


def load_env_vars():
    env_file_path = Path(__file__).absolute().parent / ".env"
    with open(env_file_path) as env_file:
        lines = [line for line in env_file.read().splitlines()
                 if not line.startswith("#") and "=" in line]
        vars = dict(tuple(s.strip() for s in line.split("=")) for line in lines)
        os.environ.update(vars)


def get_cache_filepath_from(url):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR / hashlib.md5(url.encode("utf8")).hexdigest()[:10]


def read_cache_response(url):
    filepath = get_cache_filepath_from(url)
    previous_response = None
    if os.path.exists(filepath):
        with open(filepath) as f:
            previous_response = f.read()
    return previous_response


def write_cache_response(url, response):
    filepath = get_cache_filepath_from(url)
    with open(filepath, "w") as f:
        print(f"Dumping response in {filepath}")
        f.write(response)


def send_message(token, chat_id, message, document=None):
    data = { "chat_id": chat_id }

    if document:
        api_method = "sendDocument"
        files = { "document": open(document, "rb") }
        data["caption"] = message
    else:
        api_method = "sendMessage"
        files = None
        data["text"] = message

    response = requests.post(
        f"https://api.telegram.org/bot{token}/{api_method}",
        data=data,
        files=files,
        timeout=10
    )
    response.raise_for_status()
    print(response.json())


def create_diff(url, old_response, new_response):
    diff = HtmlDiff()
    timestamp = strftime("%Y%m%d-%H%M%S")
    filepath = CACHE_DIR / f"{get_cache_filepath_from(url)}-diff-{timestamp}.html"
    with open(filepath, "w") as diff_file:
        diff_file.write(diff.make_file(old_response.splitlines(), new_response.splitlines()))
    return filepath


if __name__ == "__main__":
    url = sys.argv[1]

    load_env_vars()
    telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_chat_id = os.environ["TELEGRAM_CHAT_ID"]

    print(f"Checking {url}")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response = response.text
    previous_response = read_cache_response(url)

    if previous_response != response:
        write_cache_response(url, response)
        if previous_response:
            diff_path = create_diff(url, previous_response, response)
            send_message(telegram_token, telegram_chat_id, "URL changed: {url}", diff_path)
        else:
            send_message(telegram_token, telegram_chat_id, f"Monitoring {url}")
    else:
        print(f"URL didn't change.")
