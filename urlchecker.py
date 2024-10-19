#!/usr/bin/env python3

from difflib import HtmlDiff
from pathlib import Path
from time import strftime
import hashlib
import os
import requests
import sys

SCRIPT_DIR = Path(__file__).absolute().parent


def load_env_vars():
    env_file_path = Path(__file__).absolute().parent / ".env"
    with open(env_file_path) as env_file:
        lines = [line for line in env_file.read().splitlines()
                 if not line.startswith("#") and "=" in line]
        vars = dict(tuple(s.strip() for s in line.split("=")) for line in lines)
        os.environ.update(vars)


class Messenger:
    def __init__(self, telegram_token, telegram_chat_id):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

    def send_message(self, message, document_path=None):
        data = { "chat_id": self.telegram_chat_id }

        if document_path:
            api_method = "sendDocument"
            files = { "document": open(document_path, "rb") }
            data["caption"] = message
        else:
            api_method = "sendMessage"
            files = None
            data["text"] = message

        response = requests.post(
            f"https://api.telegram.org/bot{self.telegram_token}/{api_method}",
            data=data,
            files=files,
            timeout=10
        )
        response.raise_for_status()
        print(response.json())


class URLChecker:
    def __init__(self, url):
        self.url = url
        self.last_response = None
        self.previous_response = None
        self.cache_dir = SCRIPT_DIR / "cache"
    
    def first_check(self):
        return self.previous_response is None

    def response_changed(self):
        return self.previous_response and self.previous_response != self.last_response

    def _get_cache_filepath(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        return self.cache_dir / hashlib.md5(self.url.encode("utf8")).hexdigest()[:10]
    
    def check(self):
        print(f"Checking {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response = response.text

        self.previous_response = self.last_response
        self.last_response = response

        if self.last_response != self.previous_response:
            self._dump_response(response)

    def load_cache(self):
        filepath = self._get_cache_filepath()
        if os.path.exists(filepath):
            with open(filepath) as f:
                self.last_response = f.read()

    def _dump_response(self, response):
        filepath = self._get_cache_filepath()
        with open(filepath, "w") as f:
            print(f"Dumping response in {filepath}")
            f.write(response)

    def dump_diff(self):
        if not self.last_response or not self.previous_response:
            return RuntimeError("Two checks are needed for a diff.")
        
        diff = HtmlDiff()
        timestamp = strftime("%Y%m%d-%H%M%S")
        filepath = f"{self._get_cache_filepath()}-diff-{timestamp}.html"
        with open(filepath, "w") as diff_file:
            diff_file.write(diff.make_file(
                self.previous_response.splitlines(),
                self.last_response.splitlines()
            ))

        return filepath


if __name__ == "__main__":
    url = sys.argv[1]

    load_env_vars()
    telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_chat_id = os.environ["TELEGRAM_CHAT_ID"]
    messenger = Messenger(telegram_token, telegram_chat_id)

    checker = URLChecker(url)
    checker.load_cache()

    checker.check()

    if checker.first_check():
        messenger.send_message(f"Monitoring {url}")
    elif checker.response_changed():
        diff_path = checker.dump_diff()
        messenger.send_message(message=f"URL changed: {url}", document_path=diff_path)
    else:
        print(f"URL didn't change.")
