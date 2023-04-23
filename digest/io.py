#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common IO functions"""

import os
import logging

logger = logging.getLogger()

PROMPTS_DIR = 'prompts'
DIGEST_DOMAIN = os.getenv("DIGEST_DOMAIN")
ENGLISH_DIGEST = '.last-digest-en.md'
RUSSIAN_DIGEST = '.last-digest-ru.md'

def load_prompt(name: str):
    """Loads prompt from text file"""
    prompt = None
    path = os.path.join(PROMPTS_DIR, f'{name}.txt')
    try:
        with open(path, 'r', encoding='utf8') as descriptor:
            prompt = descriptor.read()
    except FileNotFoundError:
        logging.error("Prompt file was not found")
    return prompt

def load_digest(russian_digest: bool = False, custom_path: str = None):
    """Loads pre-saved digest from file"""
    path = custom_path if custom_path else RUSSIAN_DIGEST if russian_digest else ENGLISH_DIGEST
    text = ''
    try:
        with open(path, 'rt', encoding='utf8') as descriptor:
            text = descriptor.read()
    except FileNotFoundError:
        logging.error(f"File was not found: {path}")
    return text

def dump_digest(digest: str, russian_digest: bool = False, custom_path: str = None):
    """Dumps digest to tempfile"""
    path = custom_path if custom_path else RUSSIAN_DIGEST if russian_digest else ENGLISH_DIGEST
    with open(path, 'wt', encoding='utf8') as descriptor:
        descriptor.write(digest)

def url_from_path(filepath: str):
    """Generate valid URL from filepath"""
    lastparts = os.path.abspath(filepath).split("/")[-2:]
    language = lastparts[0]
    date = lastparts[1]
    if language not in ['ru', 'en']:
        logging.error('Not a Russian or English language')
        return None
    date = date[:-3]
    return f"https://{DIGEST_DOMAIN}/{language}/{date}"
