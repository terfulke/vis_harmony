import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyArrowPatch
import numpy as np
import pandas as pd
import mido
from mido import MidiFile
import threading
import time

class ScatterPlotApp:
    def __init__(self, master):
        self.master = master
        master.title("Visualisation")

        # Read data from file
        file = 'turca.txt'
        column_names = ['Order', 'End', 'Chord', 'Root', 'Key', 'Function', 'Sequence', 'File']
        self.df = pd.read_csv(file, sep=':', names=column_names)
        self.df.replace({'null': None, np.nan: None, ' null':None}, inplace=True)

        # MIDI file
        self.midi_file = MidiFile('turca.mid')
        self.total_ticks = sum([msg.time for msg in self.midi_file if msg.type == 'note_on'])
        self.ticks_per_beat = self.midi_file.ticks_per_beat

        # Chord and note mappings
        self.chord_mapping = {'MAJOR_TRIAD': (0, 4, 7), 
                              'MINOR_TRIAD': (0, 3, 7),
                              'AUGMENTED_TRIAD': (0, 4, 8), 
                              'DIMINISHED_TRIAD': (0, 3, 6), 
                              'DOMINANT_SEVENTH': (0, 4, 7, 10), 
                              'DIMINISHED_SEVENTH': (0, 3, 6, 9), 
                              'DIMINISHED_MINOR_SEVENTH': (0, 3, 6, 10), 
                              'MAJOR_SEVENTH': (0, 4, 7, 11), 
                              'MINOR_SEVENTH': (0, 3, 7, 10), 
                              'AUGMENTED_SEVENTH': (0, 4, 8, 10), 
                              'MINOR_MAJOR_SEVENTH': (0, 3, 7, 11), 
                              'DOMINANT_SEVENTH_INCOMPLETE': (0, 4, 10), 
                              'DOMINANT_SEVENTH_ALT_INCOMPLETE':(0, 4, 9), 
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
        self.bpm = 120

        # Initialize tkinter window
        self.create_widgets()

        # Variables for triangle animation
        self.position = 0
        self.moving = False

    def create_widgets(self):
        # Create figure and axis for scatter plot
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas for embedding matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create buttons
        self.start_button = tk.Button(self.master, text="Start", command=self.start)
        self.start_button.pack(side=tk.LEFT)

        self.restart_button = tk.Button(self.master, text="Restart", command=self.restart)
        self.restart_button.pack(side=tk.LEFT)

        # Plot MIDI and scatter data
        self.plot_data()
        
        self.arrow = FancyArrowPatch((0, -1), (0, -0.2), mutation_scale=20, color='black')
        self.ax.add_patch(self.arrow)


    def plot_data(self):
        self.ax.clear()

        tonic_x = []
        tonic_y = []
        for index, row in self.df.iterrows():
            if isinstance(row['Key'], str):
                key, mood = row['Key'].split()
            if row['Chord'] is None:
                continue
            x_value = row['Order'] * 4 + row['End']
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
                self.ax.scatter([x_value] * len(y_value), y_value, marker=marker, color=color, s=s)
        self.ax.set_ylim(-1, 12)


        inverse_note_mapping = {}
        for key, value in self.new_note_mapping.items():
            if value not in inverse_note_mapping:
                inverse_note_mapping[value] = [key]
            else:
                inverse_note_mapping[value].append(key)
        y = [f'{order} {note}' for order, note in inverse_note_mapping.items()]
        self.ax.set_yticks(list(inverse_note_mapping.keys()))
        self.ax.set_yticklabels(y)
        self.ax.set_title('Harmonic Functions Analysis Visualization')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Harmony') 
        self.ax.plot(tonic_x, tonic_y, color='lightgreen', linestyle='dashed', linewidth=1)

        self.canvas.draw()


    # def stop(self, event=None):
    #     self.moving = False
    #     self.playing = False

    def play_midi(self):
        self.playing = True
        with mido.open_output() as output:
            for msg in self.midi_file.play():
                if not self.playing:
                    break
                output.send(msg)
                # Do not update the arrow position here
        self.moving = False

    def start(self, event=None):
        self.moving = True 
        threading.Thread(target=self.play_midi).start()
        self.animate_arrow()

    def animate_arrow(self):
        if self.moving:
            self.update_arrow_position()
            self.master.after(10, self.animate_arrow)  # Schedule the method to be called again after 10 milliseconds

    def update_arrow_position(self):
        self.adjust_animation_speed()
        self.position += self.animation_speed  # Use adjusted animation speed
        self.arrow.set_positions((self.position, -1), (self.position, -0.2))
        self.canvas.draw()

    # def calculate_tempo(self):
    #     # Calculate tempo of the MIDI file
    #     try:
    #         ticks_per_beat = self.midi_file.ticks_per_beat
    #         tick_times = [msg.time for msg in self.midi_file if msg.type == 'note_on']
    #         total_ticks = sum(tick_times)
    #         total_beats = total_ticks / ticks_per_beat
    #         return (total_beats / (self.midi_file.length / 60.0))  # Tempo in BPM
    #     except Exception as e:
    #         print(f"Error calculating tempo: {e}")
    #         return None

    def adjust_animation_speed(self):
        # Adjust animation speed dynamically based on tempo
        target_speed = 1.0  # Baseline speed
        if self.bpm > 0:
            target_speed *= 60.0 / self.bpm  # Scale animation speed based on tempo
        self.animation_speed = target_speed
            

    def restart(self, event=None):
        self.playing = False
        self.moving = False
        self.position = 0
        self.arrow.set_positions((self.position, -1), (self.position, -0.2))
        self.canvas.draw()

    def shift_note_mapping(self, key):
        res_dict = dict()
        shift = self.note_mapping[key] % 12
        for key, value in self.note_mapping.items():
            res_dict[key] = (value - shift) % 12
        return res_dict

root = tk.Tk()
app = ScatterPlotApp(root)
root.mainloop()