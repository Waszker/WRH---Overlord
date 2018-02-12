#!/usr/bin/python3
import argparse
import os
import sys

from db_engine.constants import DEFAULT_ENGINE_PORT, DEFAULT_TORNADO_PORT, ARGS_PORT, ARGS_TORNADO_PORT, ARGS_PATH, \
    ARGS_INTERACTIVE
from db_engine.engine import DBEngine
from utils.io import log, Color


def parse_args(args):
    parser = argparse.ArgumentParser(description='WRH Overlord module for storing measurements.')
    parser.add_argument('--path', '-p', type=str, help='system path at which this module should be run')
    parser.add_argument('--port', '-P', type=int, help='specifies listening port')
    parser.add_argument('--tornado_port', '-T', type=int, help='specifies Tornado port')
    parser.add_argument('--interactive', '-i', nargs='?', const=True,
                        help='whether system should start in interactive mode')
    pargs = parser.parse_args(args)
    return {ARGS_PORT: pargs.port or DEFAULT_ENGINE_PORT, ARGS_TORNADO_PORT: pargs.tornado_port or DEFAULT_TORNADO_PORT,
            ARGS_PATH: pargs.path or os.os.getcwd(), ARGS_INTERACTIVE: pargs.interactive or False}


if __name__ == '__main__':
    try:
        parsed = parse_args(sys.argv[1:])
        os.chdir(parsed[ARGS_PATH])
        engine = DBEngine(parsed[ARGS_PORT])
        if parsed[ARGS_INTERACTIVE]:
            engine.run_interactive()
        else:
            engine.start_work(parsed[ARGS_TORNADO_PORT])
    except Exception as e:
        log(e, Color.FAIL)
        raise
