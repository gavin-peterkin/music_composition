from utility.playback import Playback

import numpy as np


class OutputLayerExtractor(object):

    # Number of one hot encodings for number of notes at the end
    note_count_len = 10

    def __init__(self, output_logits_list, raw_output_layer_lst=None, raw_output_layer=None):
        if raw_output_layer is not None:
            self.raw_output_layer = raw_output_layer
            self.pred_out_layer = np.mean(np.vstack([r for r in self.raw_output_layer]), axis=0)
        elif raw_output_layer_lst is not None:
            # From tensorflow
            self.raw_output_layer_lst = raw_output_layer_lst
            self.pred_out_layer_lst = [
                np.mean(np.vstack([r for r in ele]), axis=0)
                for ele in self.raw_output_layer_lst
            ]
        elif output_logits_list is not None:
            self.raw_logits = output_logits_list
            self.list_of_notes = self._convert_output_list_to_beats(self.raw_logits)



    def _convert_output_list_to_beats(self, pred_out_layer_lst):
        beats = list()
        for pred_out_layer in pred_out_layer_lst:
            new_beat = self._convert_output_layer_to_beat(pred_out_layer)
            beats.append(new_beat)
        return beats

    def _convert_output_layer_to_beat(self, pred_out_layer):
        note_count = pred_out_layer[:,-self.note_count_len:].argmax()
        if note_count > 0:
            notes = pred_out_layer[:,:-self.note_count_len].argsort()[:,-note_count:][::-1]
            beat = [(note, 'b') for note in list(*notes)]
        else:
            beat = []
        # if len(beat) > 9:
        #     import pdb; pdb.set_trace()
        return beat

    def _note_count_index(self, note_count):
        if note_count >= 9:
            return 9
        elif note_count <= 0:
            return 0
        else:
            return note_count

    def _get_note_count_hot(self, note_count):
        """
        Given a note_count int returns an array of len 10 to append to the end
        of the input layer so the number of notes to select can be determined during playback
        """
        result = np.zeros(10)
        result[self._note_count_index(note_count).astype(int)] = 1
        return result

    def _convert_to_input_layer(self, input_size, pred_out_layer):
        result = np.zeros(128)
        note_count = pred_out_layer[:,-self.note_count_len:].argmax()
        notes = pred_out_layer[:,:-self.note_count_len].argsort(axis=1)[:,-note_count:][::-1]
        result[notes] = 1
        num_result = self._get_note_count_hot(note_count)
        result = np.hstack([result, num_result])
        return result
