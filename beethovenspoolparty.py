#!/usr/bin/env python3.5

import sys
import os
import argparse
import re
import mido
import numpy as np
import matplotlib.pyplot as plt

from typing import List, Optional


def main():
    args = get_args()

    midi_files = get_files(args.directory)

    if len(midi_files) == 0:
        print('Error: Must input midi files.')
        sys.exit(0)
    elif len(midi_files) > 10:
        print('Too many files. Just examining the first 10.')
        midi_files = sorted(midi_files)[:10]

    messages = get_messages(midi_files)

    # at this point we have a ton of vectors from each midi file
    # we can now /theoretically/ train an RNN
    #print(sum([len(m) for m in messages]))
    # TODO: This...
    model = GenerateMusic()
    model.train(messages)

    write_output(model.predict(1000))


class GenerateMusic(object):
    """
    Let's try a Markov Chain
    """
    def __init__(self):
        self.chain1 = {}
        self.chain2 = {}

    def train(self, messages: List[np.ndarray]):
        for filemessages in messages:
            for i in range(len(filemessages) - 2):
                try:
                    self.chain1[(filemessages[i, 2],
                                 filemessages[i + 1, 2])].append(filemessages[i + 2, 2])
                except KeyError:
                    self.chain1[(filemessages[i, 2],
                                 filemessages[i + 1, 2])] = [filemessages[i + 2, 2]]

            for i in range(len(filemessages) - 1):
                try:
                    self.chain2[filemessages[i, 2]].append(filemessages[i + 1, 2])
                except KeyError:
                    self.chain2[filemessages[i, 2]] = [filemessages[i + 1, 2]]

    def predict(self, length: int):
        note1 = int(np.random.uniform(30, 100, 1)[0])
        note2 = int(np.random.uniform(30, 100, 1)[0])
        notes = np.zeros(length)
        for i in range(length):
            try:
                notes[i] = np.random.choice(self.chain1[(note1, note2)])
            except KeyError:
                notes[i] = np.random.choice(self.chain2[note2])
            note1 = note2
            note2 = notes[i]
        messages = np.zeros((length, 4))
        messages[:] = [0.15, 1, 0, 100]
        messages[:, 2] = notes
        return messages


def write_output(messages: np.ndarray) -> None:
    """
    Write the resulting series of notes to output file
    """
    # TODO: Make this output filename adjustable
    # TODO: the tempo isn't quite working yet....
    with mido.MidiFile() as mid:
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.Message('program_change', program=12))

        for message in messages:
            duration = int(message[0] * 500)
            track.append(mido.Message('note_on', note=int(message[2]),
                                      velocity=int(message[3]), time=duration))
            track.append(mido.Message('note_off', note=int(message[2]),
                                      velocity=int(message[3]), time=duration))
        mid.save('output.mid')


def get_messages(midi_files: List[str]) -> List[np.ndarray]:
    messages = []
    for file in midi_files:
        print('\t{}'.format(file))

        mid = mido.MidiFile(file)

        midfile = []
        for message in mid:
            if not isinstance(message, mido.MetaMessage):
                byte_repr = []
                if message.type not in ['program_change', 'control_change', 'pitchwheel']:
                    byte_repr.append(message.time)
                    byte_repr.append(message.channel)
                    byte_repr.append(message.note)
                    byte_repr.append(message.velocity)

                    midfile.append(byte_repr)
        messages.append(np.array(midfile))
        #print(sorted(list(set(np.array(midfile)[:, 2]))))
    return messages


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
    midi_files = sorted(list(set(midi_files) - {'./output.mid'}))
    return midi_files


def check_hidden(path: str) -> bool:
    hidden = False
    for directory in path.split('/'):
        if re.match('\..+', directory):
            hidden = True
    return hidden


if __name__ == '__main__':
    sys.exit(main())