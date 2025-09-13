from typing import Iterable
from mido import Message, MidiTrack, MidiFile

from .. import parser as p
from .common import TuneSegment


class MidiMessenger:
    """
    Convenience class for producing MIDI events. Also
    keeps track of time in the synthesized music.
    """
    def __init__ (self, shruti: int):
        self.shruti = shruti
        self.gap_ticks = 0
        self.current_note = None

    def advance (self, ticks: int):
        """
        Move forward in time by `ticks` ticks.
        """
        self.gap_ticks += ticks

    def make_message (self, *pargs, **kargs) -> Message:
        """
        Generate a `Message` and ensure that its `time`
        attribute is set correctly.

        All arguments are forwarded to the `Message`
        constructor. Note that `time` SHOULD NOT be specified
        -- i.e. don't do `make_message (..., time = ...)`.
        """
        assert "time" not in kargs
        msg = Message (*pargs, time = self.gap_ticks, **kargs)
        self.gap_ticks = 0
        return msg

    def stop_note (self):
        """
        Stop playing the current note.
        """
        res = self.make_message ("note_off", self.current_note)
        self.current_note = None
        return res

    def play_note (self, rel_note: int) -> Iterable[Message]:
        """
        Return a MIDI message that has the effect of playing
        the note indicated by `rel_note`.
        """
        # `self.current_note` is being played, and
        # `new_note` is about to be played.
        new_note = rel_note + self.shruti
        if self.current_note != new_note:
            yield self.make_message (
                "note_on", note = new_note
            )
            if self.current_note is not None:
                yield self.make_message (
                    "note_off", note = self.current_note
                )
        self.current_note = new_note

    def bend_pitch (self, rel_offset) -> Message:
        bend = (rel_offset / 12) * 8192
        return self.make_message (
            "pitchwheel", pitch = int (bend)
        )

def set_pitchbend_range () -> Iterable[Message]:
    """
    Emit messages to set the pitch bend range to +-1 octave.
    """
    cc = Message ("control_change")
    pb_1 = cc.copy (control = 0x64)
    pb_2 = cc.copy (control = 0x65)
    # "This is a pitchbend sensitivity change sequence"
    yield pb_1.copy (value = 0x0)
    yield pb_2.copy (value = 0x0)
    # "Set sensitivity: coarse = 12 semitones"
    yield cc.copy (control = 0x06, value = 12)
    # "Set sensitivity: fine = 0 cents"
    yield cc.copy (control = 0x26, value = 0)
    # "Pitchbend change sequence ends here"
    yield pb_1.copy (value = 0x7F)
    yield pb_2.copy (value = 0x7f)

def render (segments: Iterable[TuneSegment], outfile: str):
    messenger = MidiMessenger (shruti = 64)

    msgs = []
    msgs.append (Message ("program_change", program = 40))
    msgs.extend (set_pitchbend_range ())
    for seg in segments:
        msgs.extend (messenger.play_note (seg.start_svara))
        #messenger.advance (ticks = 200)
        dur_ticks = 200 * seg.duration
        for tick in range (dur_ticks):
            t = (tick / dur_ticks) ** 5
            offset = seg.gamaka.sample (
                t, (seg.start_svara, seg.end_svara)
            )
            msgs.append (messenger.bend_pitch (offset))
            messenger.advance (ticks = 1)
    msgs.append (messenger.stop_note ())

    # Write the messages to a track in a MIDI file
    file = MidiFile ()
    track = MidiTrack (msgs)
    file.tracks.append (track)
    file.save (outfile)
