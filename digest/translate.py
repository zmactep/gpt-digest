"""Digest generation using GPT"""
import argparse
import logging

from digest.io import dump_digest, load_digest, ENGLISH_DIGEST, RUSSIAN_DIGEST
from digest import gpt

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d.%m.%Y %H:%M:%S')

def get_args():
    """Get command line args"""
    parser = argparse.ArgumentParser("digest.translate")
    parser.add_argument("--input", required=False,
                        dest="input", help="custom path of digest to translate")
    parser.add_argument("--output", required=False,
                        dest="output", help="custom path to write translated digest")
    return parser.parse_args()

def translate(digest: str, output: str):
    """Translates specified digest"""
    ru_digest = gpt.translate(digest)
    dump_digest(ru_digest, custom_path=output)
    return ru_digest

def main():
    """Entrie point"""
    args = get_args()

    input_path = args.input if args.input else ENGLISH_DIGEST
    output_path = args.output if args.output else RUSSIAN_DIGEST

    digest = load_digest(custom_path=input_path)
    if digest:
        print(translate(digest, output_path))

if __name__ == "__main__":
    main()
