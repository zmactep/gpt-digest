#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GPT requests"""

import os
import json
import logging
import openai
import tiktoken

from digest.feed import FeedEntrie, change_content
from digest.io import load_prompt

logger = logging.getLogger()

openai.api_key = os.getenv("OPENAI_API_KEY")

class GPT:
    """Make generic requests using GPT"""
    def __init__(self, prompt: str, model: str = 'gpt-3.5-turbo', allow32k: bool = False):
        self.prompt = prompt
        self.system_prompt = load_prompt(prompt)
        self.model = model
        self.allow32k = allow32k

    def request(self, user_prompt: str):
        """Run request"""
        logging.info(f"Sending {self.prompt} request to GPT")
        response = request(self.system_prompt, user_prompt, 
                           model=self.model, allow32k=self.allow32k)
        content = response['choices'][0]['message']['content']
        logging.info("Response recieved")
        return content

def request(system_prompt: str, user_prompt: str, model: str = 'gpt-4', allow32k: str = False):
    """Runs request to OpenAI GPT API"""
    response = None
    count_tokens = lambda x: len(tiktoken.encoding_for_model('gpt-4').encode(x))
    tokens_size = count_tokens(system_prompt) + count_tokens(user_prompt)
    if model == 'gpt-4' and tokens_size > 8196:
        if allow32k:
            logging.info(f"Text is too long ({tokens_size} tokens), switching request to gpt-4-32k")
            model = 'gpt-4-32k'
        else:
            logging.error(f'Text is too long ({tokens_size} tokens)')
            return response
    logging.info(f"{tokens_size} tokens will be sent to {model} model")
    response = openai.ChatCompletion.create(model=model, messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ])
    return response

def content_prompt(entries: list[FeedEntrie]) -> str:
    """Creates a text of enumerated paragraphs"""
    return "\n".join(f"{idx}\n{entrie.content}\n"
                     for idx, entrie in enumerate(entries, start=1))

# GPT requests

def summarize(entries: list[FeedEntrie]) -> list[FeedEntrie]:
    """Summarizes content of every given entrie"""
    summary = GPT('summary')
    logging.info(f'Running {len(entries)} summary tasks')
    new_entries = [change_content(entrie, summary.request(entrie.content)) for entrie in entries]
    logging.info('All tasks were finished')
    return new_entries

def make_topics(entries: list[FeedEntrie], max_attempts: int = 2) -> dict[str, list[FeedEntrie]]:
    """Detects topics from entries content and clusterie entries by topics"""
    topics = GPT('cluster', model='gpt-4')
    clusters = {}
    for i in range(max_attempts):
        clusters_with_ids = json.loads(topics.request(content_prompt(entries)))
        try:
            clusters = {}
            for topic, entries_ids in clusters_with_ids.items():
                logging.info(f"Topic '{topic}' was detected for {len(entries_ids)} messages")
                clusters[topic] = [entries[idx - 1] for idx in entries_ids]
            break
        except json.JSONDecodeError:
            logging.warning("Clustering ressponse led to incorrect output (non-json)")
        except IndexError:
            logging.warning("Clustering ressponse led to incorrect output (wrong index)")
        if i < max_attempts - 1:
            logging.info(f"Trying again ({i+1}/{max_attempts})")
        else:
            logging.error("All attempts have been exhausted, clustering failed")
    return clusters

def make_topic_summaries(clusters: dict[str, list[FeedEntrie]]) -> list[str]:
    """Writes a summary for each topic"""
    single_summary = GPT('single_summary')
    logging.info(f'Running {len(clusters)} summary tasks')
    return {topic: single_summary.request(content_prompt(entries))
            for topic, entries in clusters.items()}

def make_highlights(digest: str) -> str:
    """Writes highlights block for a digest"""
    highlights = GPT('highlights', model='gpt-4')
    return highlights.request(digest)

def fix_links(digest: str) -> str:
    """Fixes meshed up links to sources"""
    fixer = GPT('links', model='gpt-4')
    return fixer.request(digest)

def translate(digest: str, split_pattern: str = '\n\n## ') -> str:
    """Translates digest topic by topic"""
    translator = GPT('translate', model='gpt-4')
    translated_blocks = []
    for block in digest.split(split_pattern):
        translated_blocks.append(translator.request(block))
    return split_pattern.join(translated_blocks)
