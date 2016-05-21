#!/usr/bin/env python3.5

import sys
import os
import argparse
import re
import mido
import theano

from typing import List


def main():
    args = get_args()

    midi_files = get_files(args.directory)

    if len(midi_files) == 0:
        print('Error: Must input midi files.')
        sys.exit(0)

    for file in midi_files:
        mid = mido.MidiFile(file)

        for message in mid.play():
            print(message)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, default='.',
                        help='Directory to load midi files from. Will recursively search.')
    args = parser.parse_args()
    return args


def get_files(input_directory: str) -> List[str]:
    """
    Gets all midi files from directory. Does not search hidden directories
    """
    midi_files = []
    for directory, dirs, files in os.walk(input_directory):
        if not check_hidden(directory):
            for file in files:
                if re.match('.+\.midi?$', file):
                    midi_files.append(os.path.join(directory, file))
    return midi_files


def check_hidden(path: str) -> bool:
    hidden = False
    for directory in path.split('/'):
        if re.match('\..+', directory):
            hidden = True
    return hidden



if __name__ == '__main__':
    sys.exit(main())