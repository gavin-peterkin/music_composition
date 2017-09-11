from __future__ import division

from scipy.io import wavfile as scipywf

import datetime as dt
import numpy as np
import pyaudio
import wave

class ToneGenerator(object):


    def __init__(self, freq, sample_rate):
        self.freq = freq
        self.current_time = 0.
        self.tau = 2 * np.pi
        self.sample_rate = sample_rate

    def _wave_generator(self, time):
        return (
            0.7 * (np.sin(self.tau * self.freq * time)
            + 0.5 * np.sin(self.tau * self.freq * 0.5 * time)
            + 0.3 * np.sin(self.tau * self.freq * 2 * time)
            + 0.3 * np.sin(self.tau * self.freq * 3 * time)
            + 0.125 * np.sin(self.tau * self.freq * 4 * time))
            # exponential decay
            * np.exp(-time/4)
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
        self.pa = pyaudio.PyAudio()
        self.list_of_notes = list_of_notes
        self.sample_rate = sample_rate
        self.tempo = tempo

    def get_note_freq(self, note):
        """A5 is note 69: 440 Hz"""
        return 440 * 2 ** ((note - 69) / 12)

    def get_wavfile_output(self, filename):
        waveFile = wave.open(filename, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
        waveFile.setframerate(self.sample_rate)
        # waveFile.setnframes(int(self.sample_rate * len(self.list_of_notes) * 100))  # This doesn't do anything
        return waveFile

    def get_playback_output(self):
        stream = self.pa.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True
        )
        return stream

    def _float2pcm(self, sig):
        # import pdb; pdb.set_trace()
        return (sig * 32767 + np.random.rand(sig.size)).clip(-32768, 32767).astype(np.int16)

    def output_playback_stream(self, filename = None):
        """
        This plays back a demo of what will be recorded. The actual recording
        should be better though.
        """
        if not filename:
            stream = self.get_playback_output()
        else:
            wavefile = self.get_wavfile_output(filename)
            frames = []
            # pass

        current_tones = dict()
        previous_active_notes = set()
        beat_per_sec = self.tempo * 4 / 60
        beat_length = int(self.sample_rate / beat_per_sec)
        for beat in self.list_of_notes:
            active_notes = set()
            for note, sustain in beat:
                active_notes.add(note)
                if (note not in previous_active_notes):
                    current_tones.update({note: ToneGenerator(self.get_note_freq(note), self.sample_rate)})
            for note in (previous_active_notes - active_notes):
                _ = current_tones.pop(note)
            # Add all the tone generators together and write to audio out
            output = np.zeros(beat_length, dtype=np.float32)
            for tone_generator in current_tones.values():
                output += tone_generator.get_next_samples(beat_length)
            previous_active_notes = active_notes

            if not filename:
                stream.write(output / 20)
            else:
                frames.extend(self._float2pcm(output / 20))
                # wavefile.writeframes(self._float2pcm(output / 12))

        if not filename:
            stream.stop_stream()
        else:
            # import pdb; pdb.set_trace()
            scipywf.write(filename, self.sample_rate, np.hstack(frames))
            # wavefile.writeframes(np.hstack(frames))
            # wavefile.close()

    def play(self):
        try:
            self.output_playback_stream()
            self.terminate()
        except KeyboardInterrupt:
            self.terminate()

    def save(self, filename):
        self.output_playback_stream(filename)

    def terminate(self):
        self.pa.terminate()
