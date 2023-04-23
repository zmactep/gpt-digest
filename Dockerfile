FROM python:3.11

RUN pip install markdown
ADD digest/server.py .
RUN chmod a+x server.py

VOLUME /markdown

EXPOSE 8000
ENTRYPOINT ["./server.py"]