
"""
Placeholder

class that accepts MidiParser.list_of_notes

class attribute that controls which key all pieces are shifted into

has simple method for some kind of music playback
"""

class InputLayerExtractor(object):

    midi_middle_c = 60
    transposition_table = {
        ('F-sharp-major', 'G-flat-major', 'E-flat-minor', 'D-sharp-minor'): 6,
        ('G--major', 'E--minor'): 5,
        ('A-flat-major', 'G-sharp-major', 'F--minor'): 4,
        ('A--major', 'F-sharp-minor'): 3,
        ('B-flat-major', 'G--minor'): 2,
        ('B--major', 'G-sharp-minor'): 1,
        ('C--major', 'A--minor'): 0,
        ('C-sharp-major', 'D-flat-major', 'A-sharp-minor', 'B-flat-minor'): -1,
        ('D--major', 'B--minor'): -2,
        ('E-flat-major', 'C--minor'): -3,
        ('E--major', 'C-sharp-minor'): -4,
        ('F--major', 'D--minor'): -5
    }

    def __init__(self, list_of_notes, original_key_signature):
        """
        Expects list_of_notes in the format [[(64, 'b')], [(76, 'b'), (64, 's')], ...]
        where each element in the list is a beat
        """
        self.original_key_signature = original_key_signature
        self.list_of_notes = self._transpose(list_of_notes, original_key_signature)


    def _transpose(self, list_of_notes, original_key_signature):
        """
        Private method that transposes list_of_notes attribute into C major/A minor
        """
        for key_signatures, shift in self.transposition_table.iteritems():
            if self.original_key_signature in key_signatures:
                return self._shift_key(list_of_notes, shift)

    def _shift_key(self, list_of_notes, shift):
        """
        Given a list of notes and an int shift, translates notes up/down by shift
        """
        def shift_each_note(lst):
            return [(note + shift, sustain) for note, sustain in lst]

        return map(shift_each_note, list_of_notes)

    @property
    def input_layer_array(self):
        """
        Returns 2d array where each row corresponds to a beat
        each row also covers the entire notespace
        """
        pass
