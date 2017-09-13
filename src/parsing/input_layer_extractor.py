import numpy as np


class InputLayerExtractor(object):

    midi_middle_c = 60
    # Some of these key signatures don't actually exist ;)
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

    def __init__(self, list_of_notes, original_key_signature, center_output=False):
        """
        Expects list_of_notes in the format [[(64, 'b')], [(76, 'b'), (64, 's')], ...]
        where each element in the list is a beat
        """
        self.original_key_signature = original_key_signature
        self.list_of_notes = self._transpose(list_of_notes, original_key_signature)
        self.center_output = center_output


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

    def _note_count_index(self, note_count_arr):
        mask_9 = (note_count_arr >= 9)
        mask_0 = (note_count_arr <= 0)
        note_count_arr[mask_9] = 9
        note_count_arr[mask_0] = 0
        return note_count_arr

    def _get_note_count_hot_arr(self, note_count_arr):
        """
        Given a note_count int returns an array of len 10 to append to the end
        of the input layer so the number of notes to select can be determined during playback
        """
        result = np.zeros((note_count_arr.size, 10))
        result[np.arange(note_count_arr.size), self._note_count_index(note_count_arr).astype(int)] = 1
        return result

    def _convert_to_input_layer(self, list_of_notes):
        """
        Takes a list of notes format and transforms it into an array of input
        layer vectors (rows) of size 138. 128 are for the notes and 10 are for
        the number of notes.

        Optionally, the data are centered to have a mean of 0 and a standard
        deviation of 1.
        """
        # Remove empty beats from the end of the list
        tmp_list = list_of_notes
        while not tmp_list[-1]:
            _ = tmp_list.pop()
        input_layer = np.zeros((len(tmp_list), 128))
        for i, beat in enumerate(tmp_list):
            for note, sustain in beat:
                input_layer[i, note] += 1
                # NOTE: sustain treatment makes sense?
                # if sustain == 's':
                #     input_layer[i, note] -= 1
        # FIXME: Think about how to include the number of notes being played
        note_count_arr = input_layer.sum(axis=1)
        array = np.hstack([input_layer, self._get_note_count_hot_arr(note_count_arr)])
        if self.center_output:
            array = (array - np.mean(array)) / np.max(np.std(array), 0)
        return array

    def truncate_music_seed(self, X_seed, input_size, batch_size, truncated_backprop_length):
        assert X_seed.shape[1] == input_size, "Invalid seed shape {}".format(X_seed.shape)
        length_difference = truncated_backprop_length - X_seed.shape[0]

        if length_difference > 0:
            zeros_pad = np.zeros((length_difference, input_size))
            return np.vstack([zeros_pad, X_seed])
        else:
            return X_seed[-truncated_backprop_length:]

    @property
    def c_chord(self):
        # Define C major
        return self._make_seed_chord(60, 64, 67)

    @property
    def a_min_chord(self):
        # Define A minor
        return self._make_seed_chord(57, 60, 64)

    @property
    def excitement_seed(self):
        list_of_notes = []
        list_of_notes.extend([[(60, 'b'), (64, 'b'),  (67, 'b')]] * 2)
        list_of_notes.extend([[]] * 2)
        list_of_notes.extend([[(60, 'b'), (65, 'b'),  (69, 'b')]] * 2)
        list_of_notes.extend([[]] * 2)
        list_of_notes.extend([[(62, 'b'), (67, 'b'),  (71, 'b')]] * 2)
        return list_of_notes

    def _make_seed_chord(self, notea, noteb, notec):
        chord = [[(notea, 'b')]]
        chord.extend([[(notea, 's')]] * 3)
        chord.extend([[(notea, 's'), (noteb, 'b')]])
        chord.extend([[(notea, 's'), (noteb, 's')]] * 3)
        chord.extend([[(notea, 's'), (noteb, 's'), (notec, 'b')]])
        chord.extend([[(notea, 's'), (noteb, 's'), (notec, 's')]] * 3)
        return chord

    def input_layer_seed_chord(self, chord_descr='maj'):
        if chord_descr == 'dyn':
            return self._convert_to_input_layer(self.excitement_seed)
        elif chord_descr == 'min':
            return self._convert_to_input_layer(self.a_min_chord)
        else:
            return self._convert_to_input_layer(self.c_chord)

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
