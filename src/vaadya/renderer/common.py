"""
Common functionality for renderers.

Svaras are represented as _relative notes_. A relative note
specifies a svara's position with respect to the shruti (i.e.
reference note).

Gamakas are represented as _samplers_. A sampler is a function
that maps a point in time to a relative note (which can be
non-integral); and time is given as a fraction of elapsed
time in a `TuneSegment`.
"""

from .. import parser as p
from typing import Iterable

class MusicError (Exception):
    def __init__ (self, line, col, msg):
        super ().__init__ (
            f"Line {line}, column {col}: "
            + msg
        )

SvaraIndices = (
    # The index of a svara in this tuple is the
    # offset of that note from the shruti (i.e.
    # reference note). "Offset" here refers to
    # the difference on the MIDI note scale.
    #
    # For instance, when shruti is set to MIDI
    # note 60, svara "ri2" corresponds to MIDI
    # note 62.
    "sa",
    "ri1", "ri2",
    "ga1", "ga2",
    "ma1", "ma2",
    "pa",
    "da1", "da2",
    "ni1", "ni2",
)
def svara_to_rel_note (svara: p.SVARA):
    "Find the relative note for svara `svara`"
    sname = svara.name
    if sname == ",":
        return None

    if sname.endswith ("+"):
        name = svara [:-1]
        octave = +1
    elif sname.endswith ("-"):
        name = svara [:-1]
        octave = -1
    else:
        name = sname
        octave = 0
    try:
        offset = SvaraIndices.index (name)
    except ValueError:
        raise MusicError (
            svara.line, svara.col,
            f"Not a svara: {sname}"
        )
    return offset + (octave * 12)

class GamakaSampler:
    def __init__ (self, checkpoints):
        self.checkpoints = checkpoints
        self.positions = sorted (checkpoints.keys ())
        assert self.positions [0] == 0
        assert self.positions [-1] == 1

    def sample (self, t, params):
        assert t >= 0 and t <= 1
        # Find s, e such that s <= t <= e
        s, e = None, None
        for i in range (len (self.positions) - 1):
            s, e = self.positions [i], self.positions [i + 1]
            assert s <= t
            if e >= t:
                break
        assert s is not None, e is not None
        low, high = self.checkpoints [s], self.checkpoints [e]
        return (
            (params [high] - params [low])
            * t
        )

    def __call__ (self, t, params):
        return self.sample (t, params)

GamakaCheckpoints = {
    ":": GamakaSampler ({0: 0, 1: 0}),
    ":/": GamakaSampler ({0: 0, 1: 1}),
}
def gamaka_to_sampler (gamaka: p.GAMAKA):
    name = gamaka.name
    sampler = GamakaCheckpoints.get (name)
    if sampler is None:
        raise MusicError (
            gamaka.line, gamaka.col,
            f"Not a gamaka: {name}"
        )
    return sampler

class TuneSegment:
    """
    Class capturing one "segment" of music.

    Chronologically, a svara occurs at a _point_ in
    time, while a gamaka determines what happens between
    two svaras. Thus, a `TuneSegment` can also be thought
    of as capturing a gamaka along with the adjacent svaras.

    A `TuneSegment` is characterised by
    * a starting svara
    * an ending svara
    * the gamaka associated with the starting svara

    `TuneSegment`s are consumed by a backend when
    rendering music.
    """
    def __init__ (self, start_svara, end_svara, gamaka):
        self.gamaka = gamaka
        self.start_svara = start_svara
        self.end_svara = end_svara
        self.gamaka = gamaka

    def __repr__ (self):
        cons = self.__class__.__name__
        start = repr (self.start_svara)
        end = repr (self.end_svara)
        gamaka = repr (self.gamaka)
        return f'{cons}({start}, {end}, {gamaka})'

def song_to_tunesegments (song: p.SONG) -> Iterable[TuneSegment]:
    rel_notes = [
        svara_to_rel_note (s)
        for s in song.get_svaras ()
    ]
    for n in range (1, len (rel_notes)):
        if rel_notes [n] is None:
            rel_notes [n] = rel_notes [n - 1]
    gamakas = [
        gamaka_to_sampler (g)
        for g in song.get_gamakas ()
    ]
    for n in range (len (rel_notes) - 1):
        start = rel_notes [n]
        end = rel_notes [n + 1]
        gamaka = gamakas [n]
        yield TuneSegment (start, end, gamaka)
    yield TuneSegment (
        rel_notes [-1], rel_notes [-1], gamakas [-1]
    )
