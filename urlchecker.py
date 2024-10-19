#!/usr/bin/env python3


from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import hashlib
import os
import sys

SCRIPT_DIR = Path(__file__).absolute().parent
CACHE_DIR = SCRIPT_DIR / "cache"


def get_cache_filepath_from(url):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR / hashlib.md5(url.encode("utf8")).hexdigest()


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


def send_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    data = urlencode(params).encode("utf8")
    req = Request(url, data)
    with urlopen(req) as response:
        print(response.read())


def load_env_vars():
    env_file_path = Path(__file__).absolute().parent / ".env"
    with open(env_file_path) as env_file:
        lines = [line for line in env_file.read().splitlines()
                 if not line.startswith("#") and "=" in line]
        vars = dict(tuple(s.strip() for s in line.split("=")) for line in lines)
        os.environ.update(vars)

if __name__ == "__main__":
    url = sys.argv[1]

    load_env_vars()
    telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_chat_id = os.environ["TELEGRAM_CHAT_ID"]

    print(f"Checking {url}")
    response = urlopen(url, timeout=10).read().decode("utf-8")
    previous_response = read_cache_response(url)

    if previous_response != response:
        write_cache_response(url, response)
        send_message(telegram_token, telegram_chat_id, f"URL changed: {url}")
    else:
        print(f"URL didn't change.")
