
"""
Placeholder

class that accepts MidiParser.list_of_notes

class attribute that controls which key all pieces are shifted into

has simple method for some kind of music playback
"""

class InputLayerExtractor(object):

    key_signature_center = 48

    def __init__(self, list_of_notes, original_key_signature):
        self.list_of_notes = list_of_notes
        self.original_key_signature = original_key_signature

    def output_playback_stream(self):
        """
        returns something that can be played as audio
        maybe put this in a utility
        """
        pass

    @property
    def input_layer_array(self):
        """
        Returns 2d array where each row corresponds to a beat
        each row also covers the entire notespace
        """
        pass

    def _shift_key(self,):
        pass
