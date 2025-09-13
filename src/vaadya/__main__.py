from argparse import ArgumentParser

from .tokenizer import tokenize
from .parser import parse
from .renderer.midi import render
from .renderer.common import song_to_tunesegments

# Command-line interface to Vaadya

if __name__ == "__main__":
    ap = ArgumentParser ()
    ap.add_argument ("source", help = "The song file to compile")
    ap.add_argument ("output", help = "Output MIDI file")
    args = ap.parse_args ()

    with open (args.source) as f:
        program = f.read ()
    tokens = [*tokenize (program)]
    ast = parse (tokens)
    segments = song_to_tunesegments (ast)
    render (segments, args.output)
