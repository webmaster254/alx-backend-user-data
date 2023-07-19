#!/usr/bin/env python3
"""
    This script demonstrates obfuscation and log formatting.
    It creates a logger and filters sensitive data fields.
"""

import os
import logging
import mysql.connector
from re import sub
from typing import List, Tuple


# Sensitive data fields to be obfuscated
PII_FIELDS = ("name", "email", "phone", "ssn", "password")


def get_db() -> mysql.connector.connection.MySQLConnection:
    """
    Establishes a connection to the database.

    Returns:
        A connection to the database.
    """
    username = os.getenv('PERSONAL_DATA_DB_USERNAME', 'root')
    password = os.getenv('PERSONAL_DATA_DB_PASSWORD', '')
    host = os.getenv('PERSONAL_DATA_DB_HOST', 'localhost')
    db_name = os.getenv('PERSONAL_DATA_DB_NAME')

    db = mysql.connector.connect(
        host=host,
        username=username,
        password=password,
        database=db_name
    )

    return db


def get_logger() -> logging.Logger:
    """
    Configures the log formatter and creates a logger.

    Returns:
        A configured logger.
    """
    logger: logging.Logger = logging.getLogger('user_data')
    logger.propagate = False

    stream_handler: logging.StreamHandler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter((RedactingFormatter(fields=PII_FIELDS)))
    stream_handler.formatter = formatter

    logger.addHandler(stream_handler)

    return logger


def filter_datum(fields: List[str], redaction: str,
                 message: str, separator: str) -> str:
    """
    Filters and obfuscates the sensitive data fields in a log message.

    Args:
        fields: A list of strings representing the fields to obfuscate.
        redaction: A string representing the obfuscation pattern.
        message: A string representing the log line.
        separator: A string representing the field separator in the log line.

    Returns:
        The obfuscated log message.
    """
    for field in fields:
        message = sub(f'{field}=.+?{separator}',
                      f'{field}={redaction}{separator}', message)

    return message


class RedactingFormatter(logging.Formatter):
    """
    Custom log formatter that obfuscates sensitive data fields.
    """

    REDACTION = "***"
    FORMAT = "[HOLBERTON] %(name)s %(levelname)s %(asctime)-15s: %(message)s"
    SEPARATOR = ";"

    def __init__(self, fields: List[str]):
        super(RedactingFormatter, self).__init__(self.FORMAT)
        self.fields = fields

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record by obfuscating sensitive data fields.

        Args:
            record: The log record.

        Returns:
            The formatted log message.
        """
        record.msg = filter_datum(self.fields, self.REDACTION,
                                  record.getMessage(), self.SEPARATOR)

        return super(RedactingFormatter, self).format(record)


def main():
    """Entry Point"""
    db: mysql.connector.connection.MySQLConnection = get_db()
    cursor = db.cursor()
    headers: Tuple = (head[0] for head in cursor.description)
    cursor.execute("SELECT name, email, phone, ssn, password FROM users;")
    log: logging.Logger = get_logger()

    for row in cursor:
        data_row: str = ''
        for key, value in zip(headers, row):
            data_row = ''.join(f'{key}={str(value)};')

        log.info(data_row)

    cursor
