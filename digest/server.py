#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A webserver to get access to digests"""
import http.server
import socketserver
import os
import logging
from urllib.parse import unquote
import markdown

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d.%m.%Y %H:%M:%S')

PORT = 8000

HTML_TEMPLATE = """
<!doctype html>

<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>Daily digest: {source}</title>
  <meta name="description" content="GPT-generated biotech news digest.">
  <meta name="author" content="Pavel Yakovlev">

  <meta property="og:title" content="Bio Neural News">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://bio.chat">
  <meta property="og:description" content="GPT-generated biotech news digest.">
</head>

<body>
    {content}
</body>
</html>
"""

class MarkdownRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Renders markdown digests"""
    def _send_response(self, content, content_type="text/html"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
        source = None
        file_path = None
        language = None
        if self.path.startswith("/en/"):
            language = 'en'
            source = unquote(self.path[len("/en/"):])
            file_path = f"/markdown/en/{source}.md"
        elif self.path.startswith('/ru/'):
            language = 'ru'
            source = unquote(self.path[len("/ru/"):])
            file_path = f"/markdown/ru/{source}.md"

        logging.info(f"File path is: {file_path}")
        if not file_path or not os.path.exists(file_path):
            logging.info("Requested file was not fould")
            self.send_error(404, "File was not found")
            return

        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()
            content = markdown.markdown(md_content)
            html_content = HTML_TEMPLATE.format(language=language, source=source, content=content)
            self._send_response(html_content)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MarkdownRequestHandler) as httpd:
        print("Serving on port", PORT)
        httpd.serve_forever()
