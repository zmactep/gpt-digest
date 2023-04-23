"""Digest generation using GPT"""
import argparse
import logging

from digest.feed import FeedLoader, deduplicate_entries, algorithmic_digest
from digest.io import dump_digest, ENGLISH_DIGEST
from digest import gpt

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d.%m.%Y %H:%M:%S')


def get_args():
    """Get command line args"""
    parser = argparse.ArgumentParser("digest.generate")
    parser.add_argument("--output", required=False,
                        dest="output", help="custom path to write digest")
    parser.add_argument('--summaries', action='store_true',
                        dest='summaries', help="add topics summaries")
    parser.add_argument('--highlights', action='store_true',
                        dest='highlights', help="add daily highlights")
    parser.add_argument('--fix-links', action='store_true',
                        dest='fix_links', help="fix meshed up links")
    return parser.parse_args()

def get_entries():
    """Downloads feeds and generates filtered list of entries"""
    loader = FeedLoader()
    loader.download()
    loader.logentries()
    loader.keepactual()
    loader.cleanup()
    loader.logentries()
    return loader.dump()

def generate(output: str, add_summaries: bool = True,
             add_highlights: bool = True, fix_links: bool = True):
    """Generate new digest by entries list"""
    entries = get_entries()
    digest = None

    if len(entries) == 0:
        logging.warning("No fresh news after applying filters")
        return digest

    # Generate summaries for every entrie
    entries = gpt.summarize(entries)

    # Deduplicate entries by simple algorithmic logic 
    entries = deduplicate_entries(entries)

    # Clusterize entries by topics
    clusters = gpt.make_topics(entries)

    # Write a summary for each topic
    summaries = gpt.make_topic_summaries(clusters) if add_summaries else None

    # Generate a digest
    digest = algorithmic_digest(clusters, summaries)
    dump_digest(digest, custom_path=output)

    # Make highlights for the digest
    if add_highlights:
        highlights = gpt.make_highlights(digest)
        digest = f"# Biotech News Report\n\nDaily highlights:\n\n{highlights}\n\n{digest}"
        dump_digest(digest, custom_path=output)

    # Fixes links to sources
    if fix_links:
        digest = gpt.fix_links(digest)
        dump_digest(digest, custom_path=output)

    return digest

def main():
    """Entrie point"""
    args = get_args()
    output_path = args.output if args.output else ENGLISH_DIGEST
    print(generate(output_path, args.summaries, args.highlights, args.fix_links))

if __name__ == "__main__":
    main()
