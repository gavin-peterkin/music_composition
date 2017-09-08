import numpy as np


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

    def _convert_to_input_layer(self, list_of_notes):
        # Remove empty beats from the end of the list
        tmp_list = list_of_notes
        while not tmp_list[-1]:
            _ = tmp_list.pop()
        input_layer = np.zeros((len(tmp_list), 128))
        for i, beat in enumerate(tmp_list):
            for note, sustain in beat:
                input_layer[i, note] += 1
                # FIXME: Need to deal with sustain later
                # if sustain == 's':
                #     input_layer[i, note] += 1
        # FIXME: Think about how to include the number of notes being played
        # np.hstack(input_layer, input_layer.sum(axis=1, keepdims=True))
        return input_layer

    def _inv_convert_output_layer(self, output_layer):
        # Need to figure this out
        pass

    @property
    def input_layer_seed_chord(self):
        # Define C major
        c_chord = [[(60, 'b')]]
        c_chord.extend([[(60, 's')]] * 3)
        c_chord.extend([[(60, 's'), (64, 'b')]])
        c_chord.extend([[(60, 's'), (64, 's')]] * 3)
        c_chord.extend([[(60, 's'), (64, 's'), (67, 'b')]])
        c_chord.extend([[(60, 's'), (64, 's'), (67, 's')]] * 3)
        return self._convert_to_input_layer(c_chord)

    @property
    def input_layer_array(self):
        """
        Returns 2d array where each row corresponds to a beat
        each row also covers the entire notespace

        Reference to the midi standard:
        http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/midi_note_numbers_for_octaves.htm

        There are 128 total possible notes with midi

        the last column, 129, indicates the number of notes being played
        """
        return self._convert_to_input_layer(self.list_of_notes)
