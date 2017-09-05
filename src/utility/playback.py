from __future__ import division

import numpy as np
import pyaudio


class ToneGenerator(object):


    def __init__(self, freq, sample_rate):
        self.freq = freq
        self.current_time = 0.
        self.tau = 2 * np.pi
        self.sample_rate = sample_rate

    def _wave_generator(self, time):
        return (
            (np.sin(self.tau * self.freq * time)
            + 0.25 * np.sin(self.tau * self.freq * 2 * time)
            + 0.125 * np.sin(self.tau * self.freq * 3 * time)
            + 0.125/2 * np.sin(self.tau * self.freq * 4 * time))
            # exponential decay
            * np.exp(-time/8)
        )

    def get_next_samples(self, num_samples):
        duration = 1.0 * (num_samples - 1) / self.sample_rate
        time = np.linspace(
            self.current_time,
            self.current_time + duration,
            num_samples,
            dtype=np.float32
        )
        y = self._wave_generator(time)
        self.current_time += duration
        return y

class Playback(object):

    sample_rate = 44100.

    def __init__(self, list_of_notes, sample_rate=44100, tempo=60):
        self.p = pyaudio.PyAudio()
        self.list_of_notes = list_of_notes
        self.sample_rate = sample_rate
        self.tempo = tempo

    def get_note_freq(self, note):
        """A5 is note 69: 440 Hz"""
        return 440 * 2 ** ((note - 69) / 12)

    def output_playback_stream(self):
        """
        returns something that can be played as audio
        maybe put this in a utility?
        """
        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True
        )
        current_tones = dict()
        previous_active_notes = set()
        beat_length = int(self.tempo * self.sample_rate / 60)
        for beat in self.list_of_notes:
            active_notes = set()
            for note, sustain in beat:
                active_notes.add(note)
                if sustain == 'b' or (note not in previous_active_notes):
                    current_tones.update({note: ToneGenerator(self.get_note_freq(note), self.sample_rate)})
            for note in (previous_active_notes - active_notes):
                _ = current_tones.pop(note)
            # Add all the tone generators together and write to audio out
            output = np.zeros(beat_length, dtype=np.float32)
            for tone_generator in current_tones.values():
                output += tone_generator.get_next_samples(beat_length)
            stream.write(output / 12)
            previous_active_notes = active_notes
        stream.stop_stream()
        stream.close()

    def terminate(self):
        self.p.terminate()
