# URL checker

`urlchecker.py` checks if a URL changed since the last time it was checked and it
sends a message using Telegram if it did.

## Setup

Python 3 and the requests library (`sudo apt install python3-requests`) are required.

To be able to send Telegram messages, rename `.env.template` to `.env` and add 
the Telegram bot token and chat id following the instructions in the file.
They should look something like this: 

```sh
TELEGRAM_BOT_TOKEN=123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
TELEGRAM_CHAT_ID=1234567890
```

## Usage

```sh
./urlchecker.py https://a.url
```

Use cron to run periodic checks:
1. First check that cron is running with `service cron status`.
2. Add a cron rule with `crontab -e`. For example, to run a check every hour:

```sh
0 * * * * /path/to/urlcheker.py https://a.url
```
