#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module helps to prepare a RSS feed by downloading and filtering by keywords"""

import os
import csv
import re
import logging
from collections import namedtuple

import requests
import feedparser
from dateutil.parser import parse as parsedate

logger = logging.getLogger()

SOURCES_DIR = 'sources'
KEYWORDS_DIR = 'keywords'
MATCHES = 2

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/112.0.0.0 Safari/537.36'}

FeedEntrie = namedtuple('FeedEntrie', ['title', 'content', 'date', 'url'])

class FeedLoader:
    """Loads and filters RSS feeds"""
    def __init__(self, sources=None):
        self.sources = {}
        self.regexps = []
        self.fixed_sources = False
        self._reload_regexps()

        if sources:
            self.sources = sources
            self.fixed_sources = True
            logging.info("Using specified fixed sources")
        else:
            self._reload_sources()

        self.feeds = {}

    def reload(self):
        """Reloads sources and keywords"""
        self._reload_regexps()
        if not self.fixed_sources:
            self._reload_sources()
        else:
            logging.info("Sources reloading skipped")

    def download(self):
        """Downloads recent feeds"""
        self.feeds = {}
        for feed_name, feed_url in self.sources.items():
            try:
                logging.info(f"Loading {feed_name} feed")
                response = requests.get(feed_url, headers=HEADERS, timeout=10)
                feed = feedparser.parse(response.text)
                if len(feed.entries) > 0:
                    self.feeds[feed_name] = feed
            except requests.ReadTimeout: 
                logging.warning(f"Error while loading {feed_name} feed")

    def logentries(self):
        """Log total number of entries"""
        total = sum(len(feed.entries) for feed in self.feeds.values())
        logging.info(f"Total entries: {total}")

    def cleanup(self):
        """Removes all feeds with zero entries"""
        logging.info("Cleaning empty feeds")
        new_feeds = {}
        for feed_name, feed in self.feeds.items():
            if len(feed.entries) > 0:
                new_feeds[feed_name] = feed
        self.feeds = new_feeds

    def keepfresh(self, date):
        """Keeps only fresh entries"""
        logging.info("Filtering feeds by date")
        for _, feed in self.feeds.items():
            entries = []
            for entrie in feed.entries:
                try:
                    entrie_date = parsedate(entrie['published']).date()
                    if entrie_date > date:
                        entries.append(entrie)
                except KeyError:
                    entries.append(entrie)
            feed.entries = entries

    def keepactual(self):
        """Keeps only entries that contain keywords"""
        logging.info("Filtering feeds by keywords")
        for _, feed in self.feeds.items():
            entries = []
            for entrie in feed.entries:
                matches = sum(1 for regexp in self.regexps if regexp.search(entrie.title) or \
                                                              regexp.search(entrie.description))
                if matches >= MATCHES:
                    entries.append(entrie)
            feed.entries = entries

    def dump(self):
        """Dumps feed entries"""
        result = []
        for feed in self.feeds.values():
            for entrie in feed.entries:
                result.append(make_entrie(entrie))
        result_contents = set()
        result_dedup = []
        for entrie in result:
            if entrie.content not in result_contents:
                result_contents.add(entrie.content)
                result_dedup.append(entrie)
        logging.info(f"Total deduplicated entries dumped: {len(result_dedup)}")
        return result_dedup

    def _reload_sources(self):
        self.sources = {}
        for root, _, files in os.walk(SOURCES_DIR):
            for file in files:
                if file.endswith('.csv') and not file.startswith("_"):
                    logging.info(f"Loading sources from '{file}'")
                    self.sources.update(load_sourcefile(os.path.join(root, file)))

    def _reload_regexps(self):
        self.regexps = []
        for root, _, files in os.walk(KEYWORDS_DIR):
            for file in files:
                if file.endswith('.txt'):
                    logging.info(f"Loading keywords from '{file}'")
                    self.regexps.extend(load_keywordsfile(os.path.join(root, file)))

def make_entrie(entrie):
    """Converts feedparser entries to FeedEntrie structure"""
    title = entrie.title
    try:
        content = clear_content(entrie.content[0]['value'])
    except AttributeError:
        content = clear_content(entrie.description)
    try:
        date = parsedate(entrie.published).date()
    except AttributeError:
        date = None
    url = entrie.link
    return FeedEntrie(title, content, date, url)

def dict_entrie(entrie):
    """Convers FeedEntrie to a dict"""
    return {'title': entrie.title, 'content': entrie.content, 
            'date': entrie.date, 'url': entrie.url}

def load_sourcefile(filepath):
    """Loads sources from specified file"""
    sources = {}
    with open(filepath, 'r', encoding='utf8') as fd:
        reader = csv.reader(fd, delimiter=';')
        for row in reader:
            feed_name, feed_url = row
            sources[feed_name] = feed_url
    return sources

def load_keywordsfile(filepath):
    """Loads keywords from specified file"""
    regexps = []
    with open(filepath, 'r', encoding='utf8') as fd:
        for line in fd:
            if not line.startswith("#") and line.strip():
                regexps.append(re.compile(line.strip()))
    return regexps

def clear_content(text):
    """Cleans content from comments and other staff"""
    newlines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith('<') and not line.startswith('<p>'):
            continue
        newlines.append(line)
    return " ".join(newlines)

def deduplicate_entries(entries):
    """Deduplicate entries by simple heuristic"""
    capitals= set(chr(i) for i in range(ord('A'), ord('Z') + 1))

    keywords = []
    for entrie in entries:
        keywords.append(set(word for word in entrie.content.split() if word[0] in capitals))

    duplicates = set()
    for i in range(len(entries)):
        for j in range(i+1, len(entries)):
            least = min(len(keywords[i]), len(keywords[j]))
            union = len(keywords[i].intersection(keywords[j]))
            if union >= 0.8 * least:
                duplicates.add(j)

    return [entrie for i, entrie in enumerate(entries) if i not in duplicates]

def change_content(entrie, content):
    """Change the content, keep other"""
    return FeedEntrie(entrie.title, content, entrie.date, entrie.url)

def algorithmic_digest(clusters: dict[str, list[FeedEntrie]], summaries: list[str] = None):
    """Make digest from clusters"""
    result = []
    for topic, entries in clusters.items():
        result.append(f"## {topic}\n")
        if summaries:
            result.append(f"{summaries[topic]}\n")
        for i, entrie in enumerate(entries, start=1):
            result.append(f"{i}. {entrie.content} [link]({entrie.url})")
        result.append("\n")
    return "\n".join(result)
