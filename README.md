# vis_harmony
Source codes for the bachelor thesis entitled: Visualisation of harmonic analysis of classical music

Piano Sonata No.17 in Bb, K.570, Allegro od Mozarta, ktorej
MIDI súbor mal časovo 4:49, Piano Sonata No.5 in C-, Op.10, No.1, Allegro molto e
con brio od Beethovena (MIDI prehrávanie má trvanie 3:46) a Keyboard Sonata No.4
in G, Hob.XVI:G1, Allegro

.txt files below are harmonic analysis of .mid files of same name below
beethoven.mid and beethoven.txt are files of his Piano Sonata No.5 in C-, Op.10, No.1, Allegro molto e con brio 
mozart.mid and mozart.txt are files of his Piano Sonata No.17 in Bb, K.570, Allegro
haydn.mid and haydn.txt are files of his Keyboard Sonata No.4 in G, Hob.XVI:G1, Allegro
turca.mid and turca.txt are files of Mozart's Rondo Alla Turca

file vis_harmony_and_repetitions.py contains:
  - class App - for data processing and visualisation
  - class MusicPlayer - for enabling music to play with buttons
  - function lz77_compress and function find_subarray_match - for finding repetitions

file statistics_harmony_vis.ipynb contains tables and interactive plots to display statistics about the (above mentioned) musical pieces:
  - measures in the song
  - key change line
  - chords and their occurence
  - harmonic functions
  - candences
