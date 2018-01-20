#!/usr/bin/python3
import sys

from db_engine.constants import DEFAULT_ENGINE_PORT, DEFAULT_TORNADO_PORT
from db_engine.engine import DBEngine


def parse_args(args):
    # TODO: Parse arguments
    return {}


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    engine = DBEngine(args.get('port', DEFAULT_ENGINE_PORT))
    if args.get('interactive'):
        engine.run_interactive()
    else:
        engine.start_work(args.get('tornado_port', DEFAULT_TORNADO_PORT))
