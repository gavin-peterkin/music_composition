from __future__ import print_function, division

from collections import defaultdict
from mido import MidiFile, merge_tracks, tempo2bpm

from operator import itemgetter

class MidiParser(object):
    """
    Go from raw midi data -> unicode text file organized as follows:

    smallest beat increments (1/16th notes, things smaller are dropped)
    notes initiated in this increment
    notes continued from previously (must have been initiated and not stopped)

    NOTE:
    "beat" is defined as the smallest unit that will be perceptible to the RNN
    which is one 16th note or 1/4 of a quarter note regardless of midi time_signature
    """

    beat_sep = '\n'
    note_sep = '_'
    extra_trailing_beats = 20

    def __init__(self, midi_byte_stream):
        self.midi = MidiFile(file=midi_byte_stream)

        self.meta_messages = self._get_meta_messages()
        # abs_tempo is the number of ticks per beat
        self.abs_tempo = self._get_approx_meta_attr(
            self.meta_messages, 'set_tempo', 'tempo'
        )
        self.key = self._get_approx_meta_attr(
            self.meta_messages, 'key_signature', 'key'
        )

        self.master_track = self._get_master_track()
        # ticks per 16th note
        self.beat_delta = self._get_beat_delta()

        # Sets attribute note_activity_dict
        self._parse_into_dict()

    def _get_meta_messages(self):
        messages = []
        for track in self.midi.tracks:
            messages.extend([
                msg for msg in track if msg.is_meta
            ])
        return messages

    def _get_approx_meta_attr(self, messages, midi_type, midi_value):
        filtered_msgs = (
            [msg for msg in messages if msg.type == midi_type]
        )
        return max(filtered_msgs, key=lambda x: x.time).dict()[midi_value]

    def _get_master_track(self):
        return [
            msg for msg in merge_tracks(self.midi.tracks) if msg.type in ['note_on', 'note_off']
        ]

    def _get_beat_delta(self):
        return self.midi.ticks_per_beat / 4.

    @property
    def all_note_events(self):
        for msg in self.master_track:
            yield msg.note, msg.time

    def increment_beat(self, time_delta):
        """Find the number of beats corresponding to a time_delta"""
        if time_delta > 0:
            result = int(round(time_delta / self.beat_delta))
            return max(1, result)
        else:
            return 0

    def increment_beat_difference(self, old_time_delta, current_time_delta):
        """
        This isn't being used. find beats elapsed in difference in time deltas
        """
        result = round(abs(current_time_delta - old_time_delta) / self.beat_delta)
        return max(int(result), 1)

    def get_complete_song_attrs(self):
        """
        Returns set of all notes that appear and the total number of beats
        in the midi file for initializing variables in initialize_message_variables
        """
        all_notes = set()  # A set containing every note ever played
        beat_counter = 0  # Increment beats as they're "detected"
        for note, time_delta in self.all_note_events:
            all_notes.add(note)  # include note in set
            if time_delta > 0:
                # at least one new beat
                beat_counter += self.increment_beat(time_delta)

        # For wiggle room and trailing emptiness add a constant
        total_beat_count = int(beat_counter) + self.extra_trailing_beats  # Total number of beats in the song
        return all_notes, total_beat_count

    def initialize_message_variables(self):
        """
        Initializes attribute note_activity_dict and returns empty initialized
        variables for method _parse_into_dict
        """
        all_notes, total_beat_count = self.get_complete_song_attrs()
        # Initialize an empty dictionary with keys corresponding to notes
        # and values that are a list of zeros corresponding to beats
        # if the note is played during that beat the value is 1 for continuation
        # and 2 for initiation
        self.note_activity_dict = {
            note: [0] * total_beat_count
            for note in all_notes
        }
        # a running memory of notes that are currently being played in the loop
        # the key is the note and the value is the time_delta at which the note started
        note_memory_bank = dict()
        beat_incrementer = 0  # beat index
        last_seen_nonzero_time_delta = None
        return note_memory_bank, beat_incrementer, last_seen_nonzero_time_delta

    def insert_note(self, note, on_beat, off_beat):
        # Insert note corresponding to beats from turn_on_time through absolute time
        beat_duration = off_beat - on_beat
        self.note_activity_dict[note][on_beat:off_beat] = [1] *  beat_duration
        self.note_activity_dict[note][on_beat] = 2
        # print("Inserting note", note, "at", on_beat, "thru", off_beat)


    def _parse_into_dict(self):
        """
        Returns a dict with the following structure:
        {note -> list of beats}
        In list of beats, 1 corresponds to a note continuing, and 2 to a note start.
        0 means the note is not active for that beat.
        """
        (
            note_memory_bank,
            beat_incrementer, last_seen_nonzero_time_delta
        ) = self.initialize_message_variables()
        # FIXME: get rid of abs_time?
        abs_time = 0  # track time as we move through messages
        abs_beat = 0
        last_nonnegative_time_delta = None
        for note, time_delta in self.all_note_events:
            if time_delta > 1:
                abs_time += time_delta
                abs_beat += self.increment_beat(time_delta)
            # print('Abs time', abs_time)
            # print('Abs beat', abs_beat)
            if note in note_memory_bank:
                on_beat = note_memory_bank.pop(note)
                self.insert_note(note, on_beat, abs_beat)
            else:
                note_memory_bank[note] = abs_beat
            # _ = raw_input()

    def get_str_translation(self, note, action):
        """
        Given integer note and integer action returns a string encoding
        """
        if action > 1:
            return str(note)
        elif action > 0:
            return str(note) + 'c'
        else:
            return ''

    @property
    def list_of_notes(self):
        """
        Returns list of beats where each element is a list of notes
        """
        # Make sure these are all the same
        beat_len = [len(v) for v in self.note_activity_dict.values()][0]
        beat_list = [[] for _ in range(beat_len)]

        for note, beats in self.note_activity_dict.iteritems():
            for i, action in enumerate(beats):
                if action > 0:
                    beat_list[i].append(self.get_str_translation(note, action))
        return beat_list
