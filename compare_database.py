# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
from optparse import OptionParser
from utils import create_database_session, collect_table_data
from termcolor import colored


def read_data(filename):
    """
    Read JSON database description from file
    :param filename: string
    :return: dict
    """
    with open(filename, 'r') as f:
        return json.load(f)


def say(text, color):
    """
    Prints out a "debug" message to console.
    :param text: string
    :param color: boolean
    """
    if color:
        text = colored(text, 'blue')
    print(text)


def yay(text, color):
    """
    Prints out a "ok" message to console.
    :param text: string
    :param color: boolean
    """
    if color:
        text = colored(text, 'green')
    print(text)


def nay(text, color):
    """
    Prints out a "not ok" message to console.
    :param text: string
    :param color: boolean
    """
    if color:
        text = colored(text, 'red')
    print(text)


def compare_values(msg, expected, actual, approved_diff=None, diff_only=True, color=False):
    """
    Compare two provided values and report the results
    :param msg: string description of two values to compare
    :param expected: object
    :param actual: object
    :param approved_diff: float fraction of difference we are ok with (ex: 0.1 is 10%)
    :param diff_only: boolean only print out the differences
    :param color: boolean print out colored lines into terminal
    """

    def close_enough(exp, act):
        if not approved_diff:
            return False

        expected_diff = approved_diff * min(exp, act)
        actual_diff = (abs(exp - act))
        return actual_diff < expected_diff

    if expected == actual or close_enough(expected, actual):
        if not diff_only:
            yay('{0}: same: expected {1}, actual {2}.'.format(msg, expected, actual), color)
    else:
        nay('{0}: different: expected {1}, actual {2}.'.format(msg, expected, actual), color)


def compare_data(ref_data, table_data, diff_only, color):
    """
    Compare two dicts with database information
    :param ref_data: dict information about our "good" database
    :param table_data: dict information about the database we want to check
    :param diff_only: boolean only print out the differences
    :param color: boolean print out colored lines into terminal
    """
    compare_values('Number of tables', len(ref_data), len(table_data), diff_only=diff_only, color=color)

    for table_name in sorted(ref_data.keys()):
        say('* Comparing {0}'.format(table_name), color)

        if table_name in table_data:

            compare_values(
                '  rows'.format(table_name),
                ref_data[table_name]['row_count'],
                table_data[table_name]['row_count'],
                approved_diff=0.1,
                diff_only=diff_only,
                color=color
            )

            for col_name in ref_data[table_name]['columns']:
                if col_name in table_data[table_name]['columns']:

                    if ref_data[table_name]['columns'][col_name]['primary_key']:

                        compare_values(
                            '  {0} min'.format(col_name),
                            ref_data[table_name]['columns'][col_name]['min_value'],
                            table_data[table_name]['columns'][col_name]['min_value'],
                            diff_only=diff_only,
                            color=color)

                        compare_values(
                            '  {0} max'.format(col_name),
                            ref_data[table_name]['columns'][col_name]['max_value'],
                            table_data[table_name]['columns'][col_name]['max_value'],
                            diff_only=diff_only,
                            color=color)
                else:
                    nay('  {0} field is missing.'.format(col_name), color)
        else:
            nay('* {0} table is missing.'.format(table_name), color)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        '-d',
        '--database',
        dest='database',
        help='Database URL for SQLAlchemy (required).')
    parser.add_option(
        '-f',
        '--filename',
        dest='filename',
        help='Input JSON filename (required).')
    parser.add_option(
        '-c',
        '--colored',
        action="store_true",
        dest='colored',
        default=False,
        help='Color output (default is false).')
    parser.add_option(
        '--diff-only',
        action="store_true",
        dest='diff_only',
        default=False,
        help='Only print out what is different (default is false).')
    (popts, pargs) = parser.parse_args()

    if not popts.database or not popts.filename:
        parser.print_help()
        exit(1)

    base, session = create_database_session(popts.database)
    reference_data = read_data(popts.filename)
    table_data = collect_table_data(base, session)
    compare_data(reference_data, table_data, popts.diff_only, popts.colored)
