#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sends generated digest to telegram channel"""
import argparse
import logging
import os
import re
import requests

from digest.io import load_digest, url_from_path

TELEGRAM_KEY = os.getenv("TELEGRAM_DIGEST_KEY")
CHANNEL_EN_ID = os.getenv("TELEGRAM_DIGEST_EN_CHANNEL") 
CHANNEL_RU_ID = os.getenv("TELEGRAM_DIGEST_RU_CHANNEL") 
CHANNEL_TEST_ID = os.getenv("TELEGRAM_DIGEST_TEST_CHANNEL")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d.%m.%Y %H:%M:%S')


def get_args():
    """Get command line args"""
    parser = argparse.ArgumentParser("digest.telegram")
    parser.add_argument('--input', required=True,
                        dest='input_path', help='input path of digest')
    parser.add_argument("--english", action="store_true",
                        dest="english", help="work with english channel")
    parser.add_argument("--russian", action="store_true",
                        dest="russian", help="work with russian channel")
    parser.add_argument('--only-highlights', action='store_true',
                        dest='highlights', help='send ony highlights and a URL')
    return parser.parse_args()

def escape_md_characters(text):
    """Converts text to correct MarkdownV2 format"""
    md_chars = ['_', '*', '[', ']', '(', ')',
                '~', '`', '>', '#', '+', '-',
                '=', '|', '{', '}', '.', '!']
    link_re = re.compile(r'\[([^\[]+)\]\(([^\)]+)\)')
    result = []
    words = text.split(' ')
    for word in words:
        if link_re.match(word):
            result.append(word)
            continue
        escapeword = ''
        for char in word:
            if char in md_chars:
                escapeword += '\\'
            escapeword += char
        result.append(escapeword)
    return " ".join(result)

def line_numbers_to_emoji(text):
    """Converts markdown list to nice emojis"""
    numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣',
               '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    for i, emoji in enumerate(numbers, start=1):
        pattern = f"{i}."
        if text.startswith(pattern):
            text = f"{emoji}{text[len(pattern):]}"
    return text

def convert_markdown(text):
    """Change markdown text to telegram API acceptable"""
    lines = text.split("\n")
    header = False

    result = []
    for line in lines:
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            line = line[3:]
            header = True
        line = line_numbers_to_emoji(line)
        line = escape_md_characters(line)
        if header:
            line = f"*{line}*"
        header = False
        result.append(line)
    return "\n".join(result)

def post_message(message_text: str, channel: int):
    """Posts specifed message in markdown format to the channel"""
    message_text = convert_markdown(message_text)

    logging.info("Sending telegram message")
    result = requests.post(f"https://api.telegram.org/bot{TELEGRAM_KEY}/sendMessage",
                           data = {'chat_id': channel,
                                   'text': message_text, 
                                   'parse_mode': 'MarkdownV2'},
                           timeout=10)
    result = result.json()
    if result['ok']:
        logging.info("Telegram message was sent")
    else:
        logging.error(f"Telegram error: {result['description']}")
    return result

def main():
    """Entrie point"""
    args = get_args()
    if args.english and args.russian:
        logging.error("Inconsistent options: both english and russian channels selected")
        return
    channel = CHANNEL_TEST_ID
    if args.english:
        channel = CHANNEL_EN_ID
    elif args.russian:
        channel = CHANNEL_RU_ID

    digest = load_digest(custom_path=args.input_path)
    if not digest:
        return

    if args.highlights:
        digest = digest.split("\n\n")[2]
    digest += f"\n\n{url_from_path(args.input_path)}"
    post_message(digest, channel)

if __name__ == "__main__":
    main()
