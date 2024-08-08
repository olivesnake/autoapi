"""
Oliver 2024
"""

import csv as _csv
import json
import os.path as _op
import re
import sqlite3 as sqlite
from typing import Dict, List, Any, Tuple, Callable

from . import utils

IN_MEMORY = ":memory:"


def echo_callback(stmt):
    print("[statement]: {}".format(stmt))


def progress_callback(status, remaining, total):
    print("{}/{} pages copied..".format(total - remaining, total))


class SQL:
    def __init__(
            self,
            filename: str = IN_MEMORY,
            echo: bool = False,
            timeout: float = 5.0,
            detect_types: int = 0,
            isolation_level: str | None = None,
            check_same_thread: bool = True,
            cached_statements: int = 128,
            optimize: bool = True,
            foreign_keys: bool = True
    ):
        """
        :param filename: path to database file
        :param echo: flag of whether to echo statements and errors
        :param timeout: How many seconds the connection should wait before raising an OperationalError when a table is locked
        :param detect_types: control whether and how data types not natively supported by SQLite are looked up to be converted to Python types
        :param isolation_level: control legacy transaction handling behaviour
        :param check_same_thread: flag for the db connection to check if running on the same thread (on by default)
        :param cached_statements:he number of statements that sqlite3 should internally cache for this connection, to avoid parsing overhead. By default, 128 statements.
        :param optimize: set journal mode to write ahead log and other optimizations (on by default)
        :param foreign_keys: enables foreign key flag (on by default)
        """
        self.file: str = filename
        self.con: sqlite.Connection = sqlite.connect(
            filename,
            timeout=timeout,
            detect_types=detect_types,
            isolation_level=isolation_level,
            check_same_thread=check_same_thread,
            cached_statements=cached_statements,
        )
        if echo:
            self.con.set_trace_callback(echo_callback)
        if foreign_keys:
            self.execute("pragma foreign_keys = on;")
        if optimize and self.file != IN_MEMORY:
            # enabled write ahead log journal mode if not already enabled
            journal_mode = self.fetch("pragma journal_mode;", one=True)
            if journal_mode != 'wal':
                self.executescript(
                    "pragma journal_mode = WAL; pragma synchronous = normal; pragma journal_size_limit = 6144000;"
                )

        self.schema: Dict[str, List[str]] = {}

    def get_table_names(self) -> List[str]:
        """
        returns a list of all table names in the database
        :return: list of strings of table names
        """
        tables = self.fetch(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        return tables

    def get_column_names(self, table_name: str) -> List[str]:
        """
        returns a list of all column names in a given table
        :param table_name: name of table in database
        :return: list of strings
        """
        columns = self.fetch("PRAGMA table_info({});".format(table_name))
        return [col[1] for col in columns]

    def build_schema(self) -> None:
        """
        creates a quick lookup dictionary for
        the basic schema of the database
        with table names and keys and a list of
        column names as values
        :return: None
        """
        self.schema.clear()

        for table in self.get_table_names():
            table_name = table
            # get all of the current tables columns
            self.schema[table_name] = self.get_column_names(table_name)

    def select(self, table_name: str,
               columns: List[str] | None = None,
               distinct: bool = False,
               where: str | None = None,
               order_by: str | None = None,
               asc: bool = True,
               group_by: str | None = None,
               having: str | None = None,
               limit: int = -1,
               offset: int = 0,
               fetch: None | int = None,
               return_as_dict: bool = False,
               ) -> List[Dict[str, Any]] | Dict[str, Any] | List[Tuple[Any]] | List[sqlite.Row] | sqlite.Row | Tuple[
        Any]:
        """
        buildabe select statement shortcut,
        returns a given number of rows that matched the
        given criteria in either dict convertible Row format
        or value tuples
        :param table_name: name of the table to select from
        :param columns: (optional) columns to return in selection, if None then all
        :param distinct: flag whether to select distinct columns
        :param where: (optional) where conditional string statement
        :param order_by: (optional) column name to order results by
        :param asc: flag of where to order in ascending or descending fashion (default: True)
        :param group_by: (optional) group by clause string
        :param having: (optional) having clause string
        :param limit: int to limit rows returned (default: -1 AKA no limit)
        :param offset: offset from where to start rows that are returned (default: 0)
        :param fetch: number of items to fetch from return (default: None/all)
        :param row_factory: return a dict converitable rows or set to None to return tuples
        :param return_as_dict: returns already converted to dictionayr object
        :return: list of items from select
        """
        # format columns
        if columns:
            col_list = ",".join(columns)
        else:
            col_list = "*"

        # build select statement
        core = f"SELECT {'DISTINCT ' if distinct else ''}{col_list} FROM {table_name}"
        where_chunk = '' if not where else f' WHERE {where}'
        group_by_chunk = '' if not group_by else f' GROUP BY {group_by}'
        having_chunk = '' if not having else f' HAVING {having}'
        order_by_chunk = '' if not order_by else f" ORDER BY {order_by} {'ASC' if asc else 'DESC'}"
        limit_offset_chunk = f" LIMIT {limit} OFFSET {offset};"

        stmt = ''.join([core, where_chunk, group_by_chunk, having_chunk, order_by_chunk, limit_offset_chunk])

        result = self.fetch(stmt, one=limit == 1, return_as_dict=return_as_dict)
        return result

    def insert(self,
               table_name: str,
               data: Dict[str, Any],
               replace: bool = False,
               returning: str | None = None) -> bool | List[Tuple[Any]]:
        """
        insert (or replace) new data into a table
        :param table_name: name of table in database
        :param data: a dictionary of column names and the values
        :param replace: flag of whether make it an OR REPLACE statement
        :param returning: optional string input for a returning clause after insertion
        :return: boolean whether execution was successful
        """
        columns, values = utils.process_dict(data)
        core = "INSERT INTO" if not replace else "INSERT OR REPLACE INTO"
        col_list = ','.join(columns)
        val_list = ','.join(['?' for _ in values])
        stmt = f"{core} {table_name} ({col_list}) VALUES ({val_list}){' RETURNING %s' % returning if returning else ''};"
        res = self.execute(stmt, *values, as_transaction=True, has_return=returning is not None)
        return res

    def update(self,
               table_name: str,
               data: Dict[str, Any],
               where: str = "1 = 1",
               returning: str | None = None) -> bool | List[Tuple[Any]]:
        """
        update data within a given table
        :param table_name: table name to update in
        :param data: dictionary of column names and new values
        :param where: conditional clause for updating (default: 1 = 1 / update everything)
        :param returning: optional string input for a returning clause after update
        :return: boolean whether execution was successful
        """
        columns, values = utils.process_dict(data)

        params = ', '.join([f"{c} = ?" for c in columns])
        stmt = f"UPDATE {table_name} SET {params} WHERE {where}{' RETURNING %s' % returning if returning else ''};"

        res = self.execute(stmt, *values, as_transaction=True, has_return=returning is not None)
        return res

    def delete(self,
               table_name: str,
               where: str,
               returning: str | None = None,
               vacuum: bool = False) -> bool | List[Tuple[Any]]:
        """
        delete from a table based on a given conditional
        :param table_name: name of table in database
        :param where: conditional for which item to delete from table
        :param returning: optional string input for a returning clause after update
        :param vacuum: flag to specify whether to vacuum db after this delete operation
        :return: boolean of whether execution was successful
        """

        stmt = f"DELETE FROM {table_name} WHERE {where}{' RETURNING %s' % returning if returning else ''};"

        success = self.execute(stmt, as_transaction=True, has_return=returning is not None)
        if vacuum and success:
            self.vacuum()
        return success

    def table_exists(self, name: str) -> bool:
        """
        return whether a table name is found in database
        :param name: name of table
        :return: True if exists else False
        """
        return name in self.get_table_names()

    def column_exists_in_table(self, table_name: str, column: str) -> bool:
        """
        return if a column name exists within a given table
        :param table_name: name of table
        :param column: column name
        :return: True if column is in table else False
        """
        if len(self.schema) == 0:
            self.build_schema()
        table_cols = self.schema.get(table_name, None)
        if table_cols is None:
            return False
        column_found: bool = column in self.schema[table_name]
        return column_found

    def fetch_first_value(self, __sql: str, *__params) -> Any:
        """
        special case of fetchone where you only want one row and
        the first value of the first selected column of that row
        :param __sql: sql statement
        :param __params: (optional) parameter arguments
        :return: value of first column of rows
        """
        out = self.fetch(__sql, *__params, one=True)
        return out if not out else out[0]

    def aggregate(self, table_name: str, column: str, agg: str) -> Any:
        """
        utility function to perform an
        aggregate function on a column in a table
        :param table_name: name of table
        :param column: name of column
        :param agg: aggregate function (i.e. SUM, AVG)
        :return: result of aggregate
        """
        stmt = f"SELECT {agg}({column}) FROM {table_name};"
        a = self.fetch(stmt, one=True)
        return a

    def count(self, table_name: str, column: str | None = None) -> int | None:
        """
        returns the number of rows in a table
        :param table_name: name of table
        :param column: (optional) defaults to None or '*' and returns
        all rows, or specify to select number of all non-null columns
        :return: number of rows
        """
        count = self.aggregate(table_name, "*" if not column else column, "COUNT")
        return count

    def sum(self, table_name: str, column: str) -> float | None:
        """
        perform sum aggregate on given column in table
        :param table_name: name of table
        :param column: column name
        :return: sum of values in the column
        """
        agg = self.aggregate(table_name, column, "SUM")
        return agg

    def avg(self, table_name: str, column: str, precision=2) -> float | None:
        """
        preform average aggregate on a given column in table
        :param table_name: name of table
        :param column: column name
        :param precision: decimal places in rounding (default: 2)
        :return: average value of values in the column
        """
        agg = self.aggregate(table_name, column, "AVG")
        return agg if agg is None else round(agg, precision)

    def min(self, table_name: str, column: str) -> Any:
        """
        preform min aggregate on a given column in a table
        :param table_name: name of table
        :param column: column name
        :return: minimum value in column
        """
        agg = self.aggregate(table_name, column, "MIN")
        return agg

    def max(self, table_name: str, column: str) -> Any:
        """
        preform max aggregate on a given column in a table
        :param table_name: name of table
        :param column: column name
        :return: maximum value in column
        """
        agg = self.aggregate(table_name, column, "MAX")
        return agg

    def fetch(self,
              sql: str,
              *params,
              one: bool = False,
              return_as_dict: bool = False
              ) -> None | List[Dict[str, Any]] | Dict[str, Any] | List[Tuple] | Tuple:
        """
        fetch statement execution with specificed number of
        rows to fetch
        :param sql: sql statement to be executed
        :param params: (optional) parameter values as arguments to function
        rather than in iterable
        :param one: flag to specify if to fetch exactly one (return single object)
        :param return_as_dict: return already casted to a dictionary object
        return dict convertible Row objects
        :return: result of fetch
        """
        try:
            params = list(params)
            one = one or re.match(r"^.+ LIMIT 1($| |;|\D).*", sql, flags=re.IGNORECASE)
            self.con.row_factory = sqlite.Row if return_as_dict else None
            # select rows from database
            rows = [
                dict(row) if return_as_dict else row for row in self.con.execute(sql, params)
            ]

            if len(rows) == 0:
                return None if one else []

            if one:
                row = rows[0]
                if len(row) == 1 and not return_as_dict:
                    return row[0]
                return row
            else:
                if len(rows[0]) == 1 and not return_as_dict:
                    return [row[0] for row in rows]
                return rows

        except sqlite.Error as e:
            return None

    def execute(self,
                statement: str,
                *params,
                as_transaction: bool = False,
                has_return: bool = False) -> bool | List[Tuple[Any]]:
        """
        execute an sql statement
        :param statement: sql statement
        :param params: (optional) parameter values
        :param as_transaction: flag of whether to run
        the execution as a transaction
        :param has_return: flag of whether statement returns data
        (e.g. UPDATE BOOKS SET isbn = '1234' WHERE id = 1 RETURNING *;
        :return: boolean whether execution was successful
        """
        cur = self.con.cursor()
        try:
            if as_transaction:
                cur.execute("BEGIN TRANSACTION;")
            cur.execute(statement, list(params))
            out = cur.fetchall() if has_return else True
            self.con.commit()
            return out
        except sqlite.Error as e:
            self.con.rollback()
            return False

    def executescript(self, __sql: str) -> bool:
        """
        executes an sql script
        :param __sql: sql script
        :return: boolean whether the execution was successful
        """
        cur = self.con.cursor()
        try:
            cur.executescript(__sql)
            self.con.commit()
        except sqlite.Error as e:
            self.con.rollback()
            return False
        return True

    def executemany(self, __sql: str, __seq_of_params) -> bool:
        """
        executes an sql statement many times on
        a sequence of parameter values
        :param __sql: sql statement
        :param __seq_of_params: sequence of data
        :return: boolean whether execution was successful
        """
        cur = self.con.cursor()
        try:
            cur.executemany(__sql, __seq_of_params)
            self.con.commit()
        except sqlite.Error as e:
            self.con.rollback()
            return False
        return True

    def vacuum(self):
        """utility for vacuuming database"""
        self.execute("VACUUM;")

    def __get_database_name(self):
        """ utility for getting the filename of database """
        if self.file == IN_MEMORY:
            return "memory"
        _, fname = _op.split(self.file)
        name, _ = _op.splitext(fname)
        return name

    def dump(self, out_file: str = None) -> None:
        """
        dump the entire database schema to a
        .sql file
        :param out_file: (optional) name of the destination file
        :return: None
        """
        if not out_file:
            out_file = "%s.sql" % self.__get_database_name()
        dst = open(out_file, 'w', encoding="utf-16")
        lines = '\n'.join(self.con.iterdump())
        dst.writelines(lines)
        dst.close()

    def export_to_csv(self, delimeter: str = ',') -> None:
        """
        exports every table in the database
        to seperate csvs
        :return: None
        """
        for table in self.get_table_names():
            self.export_table_to_csv(table_name=table, delimeter=delimeter)

    def to_json(self, table_name: str, filename: str | None = None) -> bool:
        """
        converts a table in the database to a JSON file
        :param table_name: name of table
        :param filename: filename for output (if None then table_name.json)
        :return: boolean whether export was successful
        """
        if not filename:
            filename = './{}.json'.format(table_name)
        result = self.select(table_name, return_as_dict=True)
        if result is None:
            return False
        try:
            with open(filename, 'w') as file:
                json.dump(result, file)
        except Exception as e:
            return False
        return True

    def export_table_to_csv(self, table_name: str, delimeter: str = ',') -> None:
        """
        exports a table in the database to csv format
        :param table_name: name of table
        :param delimeter: csv file delimeter character
        :return: None
        """
        if not self.table_exists(table_name):
            return
        outfile = f"./{self.__get_database_name()}-{table_name}.csv"
        rows = [row for row in self.select(table_name, return_as_dict=True)]
        if not len(rows):
            return
        headers = list(rows[0].keys())  # extract column header line
        csv_rows = [list(row.values()) for row in rows]
        with open(outfile, 'w', newline='', encoding='UTF-8') as csv_file:
            writer = _csv.writer(csv_file, delimiter=delimeter)
            writer.writerow(headers)
            writer.writerows(csv_rows)

    def register_adapter(self, type: object, adapter: Callable):
        """
        Register an adapter callable to adapt the Python type type into an SQLite type.
        :param type: a custom or Python type
        :param adapter: a callable
        :return: None
        """
        sqlite.register_adapter(type, adapter)

    def register_convert(self, typename: str, converter: Callable):
        """
        Register the converter callable to convert SQLite objects of
        type typename into a Python object of a specific type.
         The converter is invoked for all SQLite values of type typename;
         it is passed a bytes object and should return an object of the desired Python type.
        :param typename: string of the typename
        :param converter: callabe for conversion
        :return: None
        """
        sqlite.register_converter(typename, converter)

    def create_function(self, name: str, narg: int, func: Callable | None, *, deterministic: bool = False):
        """
        Create or remove a user-defined SQL function.
        :param name: name of the function
        :param narg:number of arguments function can accept, -1 for any amount
        :param func: callabe function or None to remove an existing function
        :param deterministic:
        :return: None
        """
        self.con.create_function(
            name, narg, func, deterministic=deterministic
        )

    def backup(self, filename: str, pages: int = -1, quiet: bool = True):
        """
        create backup of current sqlite database
        :param filename: filename for sqlite database
        :param pages:number of pages to copy at a time (default -1/all)
        :param quiet: flag of whether to use copy progress callback
        :return: None
        """
        with sqlite.connect(filename) as dst:
            self.con.backup(
                dst,
                pages=pages,
                progress=None if quiet else progress_callback
            )

    def create_table_from_csv(self, filename: str, name: str | None = None) -> bool:
        """
        create a new table in the current database from a csv file and inserts all data
        assumes that json file is an array of objects with the same keys
        :param filename: name of csv file
        :param name: optional name of table
        :return: boolean of if creation was successful
        """
        if name is None:
            name = utils.extract_filename(filename).lower()
        name = utils.safe_name(name)
        headers, rows = utils.read_csv(filename)
        if len(rows) == 0:
            return False
        columns = []
        for i, v in enumerate(rows[0]):
            col = "{} {}".format(headers[i].replace(' ', '_'), utils.detect_type_csv(v))
            columns.append(col)
        create_stmt = f"CREATE TABLE {name} ({','.join(columns)});"
        if not self.execute(create_stmt):
            return False

        insert_stmt = f"INSERT INTO {name} ({','.join(headers)}) VALUES ({','.join('?' * len(columns))});"

        return self.executemany(insert_stmt, rows)

    def create_table_from_json(self, filename: str, name: str | None = None) -> bool:
        """
        create a new table in the current database from a json file and inserts all data
        assumes that json file is an array of objects with the same keys
        :param filename: name of json file
        :param name: optional name of table
        :return: boolean of if creation was successful
        """
        if name is None:
            name = utils.extract_filename(filename).lower()
        with open(filename, "r") as file:
            data = json.load(file)
            if len(data) == 0:
                return
            if not isinstance(data, list):
                # TODO: implement handling for a single object?
                return False

            # assume all objects have the same key
            item = data[0]
            keys = item.keys()
            cols = ",".join(
                "{} {}".format(
                    k, utils.detect_type_json(item[k])
                )
                for k in keys
            )
            statement = f"CREATE TABLE {name} ({cols});"  # don't check if exists for later handling
            if not self.execute(statement):  # error in creation or table name exists
                return False

            success = True
            for x in data:
                success = success and self.insert(name, x)
            return success

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()
