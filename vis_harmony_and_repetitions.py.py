import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pygame
import threading
import random

def lz77_compress(data, window_size):
    compressed = []
    index = 0

    while index < len(data):
        best_offset = -1
        best_length = -1 
        best_match = []

        #search for the longest match in the sliding window
        for length in range(1, min(len(data) - index, window_size)):
            subarray = data[index:index + length]
            offset = find_subarray_match(data, subarray, max(0, index - window_size), index)

            if offset != -1 and length >= best_length:
                best_offset = index - offset
                best_length = length
                best_match = subarray

        if best_match:
            #add the (offset, length, next_element_index) tuple to the compressed data
            next_element_index = index + len(best_match) if index + len(best_match) < len(data) else None
            compressed.append((best_offset, len(best_match), next_element_index))
            index += len(best_match)
        else:
            #no match found, add a zero-offset tuple
            next_element_index = index + 1 if index + 1 < len(data) else None
            compressed.append((0, 0, next_element_index))
            index += 1

    return compressed

def find_subarray_match(array, subarray, start, end):
    for i in range(start, end):
        if array[i:i+len(subarray)] == subarray:
            return i
    return -1

class MusicPlayer(threading.Thread):
    def __init__(self, midi_file_path):
        super().__init__()
        self.midi_file_path = midi_file_path
        self.playing = False
        self.paused = False
        self.stopped = False

    def run(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.midi_file_path)
        self.playing = True
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and not self.stopped:
            if self.paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            pygame.time.Clock().tick(10)

    def stop(self):
        self.stopped = True
        pygame.mixer.music.stop()

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

class App:
    def __init__(self, master, file_name):
        self.master = master
        master.title("Visualisation")

        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

        file = file_name + '.txt'
        column_names = ['Order', 'End', 'Chord', 'Root', 'Key', 'Function', 'Sequence', 'File']
        self.df = pd.read_csv(file, sep=':', names=column_names)
        self.df.replace({'null': None, np.nan: None, ' null':None}, inplace=True)
        self.df['Sequence'] = self.df['Sequence'].apply(lambda x: x.strip('[]').split(', ') if x is not None else None)

        self.midi_file_path =  file_name + '.mid'

        self.chord_mapping = {'MAJOR_TRIAD': (0, 4, 7), 
                              'MINOR_TRIAD': (0, 3, 7),
                              'AUGMENTED_TRIAD': (0, 4, 8), 
                              'DIMINISHED_TRIAD': (0, 3, 6), 
                              'DOMINANT_SEVENTH': (0, 4, 7, 10), 
                              'DIMINISHED_SEVENTH': (0, 3, 6, 9), 
                              'DIMINISHED_MINOR_SEVENTH': (0, 3, 6, 10), 
                              'MAJOR_SEVENTH': (0, 4, 7, 11), 
                              'MINOR_SEVENTH': (0, 3, 7, 10), 
                              'AUGMENTED_SEVENTH': (0, 4, 8, 11), 
                              'MINOR_MAJOR_SEVENTH': (0, 3, 7, 11), 
                              'DOMINANT_SEVENTH_INCOMPLETE': (0, 4, 10), 
                              'DOMINANT_SEVENTH_ALT_INCOMPLETE':(0, 7, 10), 
                              'MAJOR_SEVENTH_INCOMPLETE': (0, 4, 11),
                              'DIMINISHED_SEVENTH_INCOMPLETE': (0, 3, 9),
                              'DIMINISHED_MINOR_SEVENTH_INCOMPLETE': (0, 3, 10),
                              'MINOR_MAJOR_SEVENTH_INCOMPLETE': (0, 3, 11)}

        self.note_mapping = {'C': 0, 'H#': 0,
                             'C#': 1, 'Db': 1, 
                             'D': 2, 
                             'D#': 3, 'Eb': 3, 
                             'E': 4, 'Fb': 4, 
                             'F': 5, 'E#': 5,
                             'F#': 6, 'Gb': 6, 
                             'G': 7, 
                             'G#':8, 'Ab': 8, 
                             'A': 9, 
                             'A#': 10, 'Bb': 10, 
                             'B': 11, 'Cb': 11}

        key, mood = self.df.loc[self.df['Key'].notna()].iloc[0]['Key'].split()
        self.new_note_mapping = self.shift_note_mapping(key)
        self.tonic_sequence = []
        self.sequence_marker = []

        pygame.init()
        self.music_player = MusicPlayer(self.midi_file_path)

        self.create_widgets()

    def create_widgets(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.start_restart_button = tk.Button(self.master, text="Start/Restart", command=self.start_restart_music)
        self.start_restart_button.pack(side=tk.LEFT, pady=5)

        self.pause_unpause_button = tk.Button(self.master, text="Pause/Unpause", command=self.pause_unpause_music)
        self.pause_unpause_button.pack(side=tk.LEFT, pady=5)

        self.get_x_value()
        self.plot_data()
        self.plot_compression()

    def get_x_value(self):
        self.x_value = []
        actual_position = 0
        previous_order = ''
        previous_end = 0
        for index, row in self.df.iterrows():
            if previous_order == row['Order']:
                actual_position += (row['End']-previous_end)
            else:
                actual_position += row['End']
            self.x_value.append(actual_position)
            previous_order = row['Order']
            previous_end = row['End']

    def get_tonic_sequence(self, mood):
        if mood == 'MOLL':
            self.tonic_sequence = [0, 2, 3, 5, 7, 8, 10]
        elif mood == 'DUR':
            self.tonic_sequence = [0, 2, 4, 5, 7, 9, 11]

    def plot_data(self):
        tonic_x = []
        tonic_y = []
        for index, row in self.df.iterrows():
            if isinstance(row['Key'], str):
                key, mood = row['Key'].split()
            if row['Chord'] is None:
                continue
            x_value = self.x_value[index]
            chord_tone, chord_type = row['Chord'].split()
            chord_value = self.chord_mapping.get(chord_type, None)
            if chord_value is not None:
                if chord_tone[-1] == '!':
                    chord_tone = chord_tone[:-1]
                y_value = [(self.new_note_mapping[chord_tone] + i) % 12 for i in chord_value]
                color = 'green' if row['Function'] == 'T (I)' else \
                        'yellow' if row['Function'] == 'D (V)' else \
                        'blue' if row['Function'] == 'S (IV)' else \
                        'gray' if row['Function'] is None else 'pink'
                s = 5 if color == 'gray' else 20
                marker = "o" if mood == 'DUR' else "v"
                if color == 'green':
                    tonic_x.append(x_value)
                    tonic_y.append(self.new_note_mapping[chord_tone])
                for i in y_value:
                    if mood != None:
                        self.get_tonic_sequence(mood)
                        self.tonic_sequence = [(self.new_note_mapping[key] + i) % 12 for i in self.tonic_sequence]
                    if i in self.tonic_sequence or self.tonic_sequence == [] or color == 'green' or color == 'yellow' or color == 'blue':
                        self.ax1.scatter([x_value], i, marker=marker, color=color, s=s)
                    else:
                        self.ax1.scatter([x_value], i, marker=marker, color='red', s=s)
            
            if row['Sequence'] != None:
                if len(self.sequence_marker) > 0:
                    if self.df.loc[self.sequence_marker[-1], 'Function'] != row['Function']:
                        self.sequence_marker.append(index)
                else:
                    self.sequence_marker.append(index)
                if len(self.sequence_marker) > 3 and row['Sequence'][-1] == row['Function']:
                    x1, x2 = self.x_value[self.sequence_marker[0]], self.x_value[self.sequence_marker[-1]]
                    rect = plt.Rectangle((x1, 0), x2-x1, 11, linewidth=0.5, edgecolor='black', facecolor='none')
                    self.ax1.add_patch(rect)
                    self.sequence_marker = []


                
        self.ax1.set_ylim(-1, 12)
        self.ax1.set_xlim(-5, self.x_value[-1]+5)

        self.inverse_note_mapping = {}
        for key, value in self.new_note_mapping.items():
            if value not in self.inverse_note_mapping:
                self.inverse_note_mapping[value] = [key]
            else:
                self.inverse_note_mapping[value].append(key)
        y = [f'{order} {note}' for order, note in self.inverse_note_mapping.items()]
        self.ax1.set_yticks(list(self.inverse_note_mapping.keys()))
        self.ax1.set_yticklabels(y)
        self.ax1.set_title('Harmonic Functions Analysis Visualization')
        self.ax1.set_xticks([])
        self.ax1.set_ylabel('Harmony') 
        self.ax1.plot(tonic_x, tonic_y, color='orange', linewidth=1)

        self.canvas.draw()

    def plot_compression(self):
        data = []
        for index, row in self.df.iterrows():
            cleaned_line = ':'.join(str(value) for value in row.values[1:])
            data.append(cleaned_line)
        data.append(None)

        compressed_data = lz77_compress(data, len(data))

        len_data = len(compressed_data)
        repetitions = dict()

        for i in (compressed_data):
            offset, length, next_ind = i
            if next_ind == None:
                next_ind = len_data
            if next_ind-offset > next_ind-length: #ensuring that two found repeated segments are distant from each other and have no common elements
                continue
            tuple_sequence = tuple(data[next_ind-length: next_ind])
            if length > 2:
                if tuple_sequence in repetitions.keys():
                    repetitions[tuple_sequence].add((next_ind-length, next_ind))
                    repetitions[tuple_sequence].add((next_ind-offset-length, next_ind-offset))
                else:
                    repetitions[tuple_sequence] = {(next_ind-length, next_ind), (next_ind-offset-length, next_ind-offset)}
                color = (random.uniform(0, 0.7), random.uniform(0, 0.7), random.uniform(0, 0.7))
                x1_value = [self.x_value[next_ind-length], self.x_value[next_ind-1]]
                x2_value = [self.x_value[next_ind-offset-length], self.x_value[next_ind-offset-1]]
                self.ax2.hlines(length, x1_value[0], x1_value[1], color=color, linewidth=3)
                self.ax2.hlines(length, x2_value[0], x2_value[1], color=color, linewidth=3)

        self.ax2.set_xlim(-5, self.x_value[-1]+5)
        self.ax2.set_title('Repetitions')
        self.ax2.set_xlabel('Beats')
        self.ax2.set_ylabel('Length')
    
        self.canvas.draw()


    def start_restart_music(self):
        if not self.music_player.is_alive() or self.music_player.stopped:
            self.music_player = MusicPlayer(self.midi_file_path)
            self.music_player.start()
        else:
            self.music_player.stop()
            self.music_player.join()
            self.music_player = MusicPlayer(self.midi_file_path)
            self.music_player.start()

    def pause_unpause_music(self):
        if not hasattr(self, "music_playing") or self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False
        else:
            pygame.mixer.music.unpause()
            self.music_playing = True

    def shift_note_mapping(self, key):
        res_dict = dict()
        shift = self.note_mapping[key] % 12
        for key, value in self.note_mapping.items():
            res_dict[key] = (value - shift) % 12
        return res_dict

    def on_close(self):
        #stop the music player when the window is closed
        self.music_player.stop()
        self.master.destroy()

root = tk.Tk()
app = App(root, 'turca')
root.protocol("WM_DELETE_WINDOW", app.on_close)
root.mainloop()
