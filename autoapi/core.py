"""
Oliver Aug 2024
"""

import functools
import json
import os.path
import re
import socket
import threading
from typing import List, Dict

from .sqrl import SQL

GET = "GET"
GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"
SINGLE = 0
ALL = 1
HOMEPAGE = os.path.join(os.path.dirname(__file__), "index.html")


def process_headers(request_lines: List[bytes]) -> Dict:
    request_lines = b'\n'.join(request_lines).replace(b'\r', b'').split(b'\n')
    header_dict = {}
    for line in request_lines:
        line = line.decode()
        line = line.strip()
        res = line.split(":", maxsplit=1)
        if len(res) >= 2:
            key, val = res
            header_dict[key.strip()] = val.strip()
    return header_dict


def read_as_text(filename: str):
    with open(filename, 'r') as file:
        return file.read()


class App:
    def __init__(self, database: str, echo: bool = False):
        """

        :param database: sqlite database file
        :param echo: flag of whether to echo commands on the command line
        """
        self.db = SQL(database, echo=echo, check_same_thread=False)
        self.tables = self.db.get_table_names()
        self.patterns = []
        try:
            self.tables.remove('sqlite_sequence')
            self.tables.remove('sqlite_stat1')
            self.tables.remove('sqlite_master')
        except ValueError:
            pass
        for t in self.tables:
            all_path = rf"\b({re.escape(t)})\b(?!\w+)"
            single_path = rf"{re.escape(t)}/(\w+)"
            self.patterns.extend([(single_path, SINGLE), (all_path, ALL)])

    def read_all(self, table_name):
        """
        reads all items from a given table in a database
        :param table_name: name of table in database
        :return: json stringified result
        """
        return json.dumps(self.db.select(table_name, return_as_dict=True))

    @functools.lru_cache()
    def get_primary_key_column(self, table_name: str) -> str:
        """
        returns the name of the first
        primary key column in a table
        :param table_name: name of table in database
        :return: name of primary key column
        """
        result = self.db.fetch(f"PRAGMA table_info({table_name})")
        primary_key_columns = [col[1] for col in result if col[5] == 1]
        if len(primary_key_columns) < 1:
            raise RuntimeError
        return primary_key_columns[0]

    def read_one(self, table_name, pk):
        """
        reads a single items from a table in the database
        based on a given value assumed to be search with
        the main primary key
        :param table_name: name of the table in the database
        :param pk: value to search for the item by
        :return: json stringified result
        """
        col = self.get_primary_key_column(table_name)

        return json.dumps(
            self.db.select(table_name, limit=1, return_as_dict=True, where="{} = {}".format(col, pk))
        )

    def handle(self, client: socket.socket, addr: tuple):
        """
        handler for client connections to server
        :param client: client socket
        :param addr: client addr
        :return: None
        """
        with client:
            while 1:
                req = client.recv(1024)
                if not req:
                    break
                lines = req.split(b'\n')
                request_line = lines[0].strip().decode()
                # print(request_line)
                headers = process_headers(lines[1:])
                status = ''
                # serve custom generated homepage
                if request_line == "GET / HTTP/1.1":
                    status = "HTTP/1.1 200 OK"

                method = request_line.split(" /", maxsplit=1)[0]

                matched = False
                for pattern, ptype in self.patterns:
                    result = re.search(pattern, request_line)
                    if result is None:
                        continue
                    matched = True
                    if ptype == SINGLE:
                        table = re.search(r"(\w+)/\d+", request_line).group(1)
                        pk = re.search(r"\w+/(\w+)", request_line).group(1)
                        if method == GET:
                            content = self.read_one(table, pk)
                            length = len(content)
                            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {length}\r\n\r\n{content}"
                            client.sendall(response.encode("utf-8"))
                            break
                    else:
                        table = result.group(0)
                        if method == GET:
                            content = self.read_all(table_name=table)
                            length = len(content)
                            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {length}\r\n\r\n{content}"
                            client.sendall(response.encode("utf-8"))
                            break

                if not matched:
                    status = "HTTP/1.1 404 NOT FOUND"
                    data = read_as_text(HOMEPAGE)
                    length = len(data)
                    response = f"{status}\r\nContent-Length: {length}\r\n\r\n{data}"
                    client.sendall(response.encode("utf-8"))

    def run(self, host: str = "localhost", port: int = 5000):
        """
        server initializer and loop
        :param host: host for server (0.0.0.0 for IP addr)
        :param port: port to run server on
        :return: None
        """
        if host == '0.0.0.0':
            host = socket.gethostbyname(socket.gethostname())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
            server.listen()
            print(f"🚀 server listening on http://{host}:{port}")
            while 1:
                sock, addr = server.accept()
                thread = threading.Thread(target=self.handle, args=(sock, addr))
                thread.start()
