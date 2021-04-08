"""Script loads guitar chord patterns from patterns.json file and creates SVG images of them.
pattern.json is assumed to contain an array with each pattern being an object in the form
{
    "name": "Am",
    "pattern": "x02210"
}

Where the fret numbers are greater than 9 the pattern should be separated by spaces:
"x 0 10 0 0 0"

The script requires an images directory in the working directory where it will write the files.
It also produces a chord-files.json file which is an array of entries for each chord.

Each entry is in the form:
{"chord": "images/Am.svg", "info": "images/Am_info.svg", "root": "A", "notes": 3}
chord is the fretboard diagram
info is the name and notes of the chord (as fretted)
"""
import json
import re
import fretboard
import drawSvg as draw
from musthe import *
from pychord import Chord, note_to_chord

NOTES_SHARP = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

SLASH_NOTE = re.compile(r'/\s?([a-g])')

# the flats for each scale
FLAT_MAPPING = {
    'F': {'A#':'Bb'},
    'Bb':{'A#':'Bb', 'D#':'Eb'},
    'Eb':{'A#':'Bb', 'D#':'Eb', 'G#':'Ab'},
    'Ab':{'A#':'Bb', 'D#':'Eb', 'G#':'Ab', 'C#': 'Db'},
    'Db':{'A#':'Bb', 'D#':'Eb', 'G#':'Ab', 'C#': 'Db', 'F#': 'Gb'},
    'Gb':{'A#':'Bb', 'D#':'Eb', 'G#':'Ab', 'C#': 'Db', 'F#': 'Gb', 'B': 'Cb'},
    'Cb':{'A#':'Bb', 'D#':'Eb', 'G#':'Ab', 'C#': 'Db', 'F#': 'Gb', 'B': 'Cb', 'E': 'Fb'}
}

FLAT_MAPPING['Dm'] = FLAT_MAPPING['F']
FLAT_MAPPING['Gm'] = FLAT_MAPPING['Bb']
FLAT_MAPPING['Cm'] = FLAT_MAPPING['Eb']
FLAT_MAPPING['Fm'] = FLAT_MAPPING['Ab']
FLAT_MAPPING['Bbm'] = FLAT_MAPPING['Db']
FLAT_MAPPING['Ebm'] = FLAT_MAPPING['Gb']
FLAT_MAPPING['Abm'] = FLAT_MAPPING['Cb']

# chord qualities currently unsupported by the libraries being used
CHORD_RECIPES = {
    'm11': 'R m3 P5 m7 M9 P11',
    'm13': 'R m3 p5 m7 M9 M13',
    'maj9/13': 'R M3 P5 M7 M9 P6',
    '5add9': 'R M2 M3 P5 M7',
    '7sus2':'R M2 P5 m7',
    'maj9/11': 'R M3 P5 M7 M9',
    'maj9#5': 'R M3 A5 M7 M9',
    'dim7': 'R m3 d5 d7',
    'm7#5': 'R m3 A5 m7',
    'mMaj11': 'R m3 P4 P5 M7',
    'mMaj9':'R m3 P5 M7 M9',
    'add4': 'R M3 P4 P5',
    'madd4': 'R m3 P4 P5'
}

# the open note indexes - if you change this, you will need to ensure the patterns reflect this
TUNING_INDEXES = [7, 0, 5, 10, 2, 7]
STANDARD_TUNING = [NOTES_SHARP[i] for i in TUNING_INDEXES]

print('Creating chord patterns using tuning {0}'.format(STANDARD_TUNING))

def create_string(start_index):
    """returns a list of note positions for a guitar string given the starting index. Sharps are used in place of flats"""
    return [NOTES_SHARP[(x + start_index) % 12] for x in range(0, 12)]

FRET_NOTES = [create_string(s) for s in TUNING_INDEXES]

FRET_POSITION = re.compile(r'((\s[1-2])?[0-9x])')
ROOT_CHORD = re.compile(r'^([A-G][#b]?(m(?!aj))?)')
IS_MINOR = re.compile(r'^[A-G][#b]?(m(?!aj))')

def cap_slash(match_object):
    """Captiliase the bass note in a slash chord - should be rewritten as lambda"""
    return match_object.group(0).upper()

def rotate(l, n):
    """Rotate array l by n places"""
    return l[n:] + l[:n]

def pattern_to_notes(pattern):
    """Convert string pattern in a list of notes"""
    pattern_notes = []
    for (i, m) in zip(range(0, 6), FRET_POSITION.findall(pattern)):
        pos = m[0].strip()
        if pos != 'x':
            pattern_notes.append(FRET_NOTES[i][int(pos) % 12])
    return pattern_notes

CREATED_FILES = []

CHORD_DICT = {}
with open('prettychords.json', 'r') as infile:
    chords = json.loads(infile.read())
    for chord in chords:
        for pattern in chords[chord]:
            intPattern = [int(fret) for fret in pattern]
            spacePattern = max(intPattern) > 9
            separator = ' ' if spacePattern else ''
            strPattern = separator.join([str(fret) if fret >= 0 else 'x' for fret in intPattern])
            CHORD_DICT[strPattern] = chord

with open('patterns.json', 'r') as infile:
    content = json.loads(infile.read())
    processed_patterns = {}
    file_names = {}

    for chord in content:
        pattern = chord['pattern'].strip()
        # Skip single note patterns
        if pattern.count('x') == 5:
            continue

        if pattern in processed_patterns:
            continue

        name = chord['name'].strip()
        processed_patterns[pattern] = name

        if pattern in CHORD_DICT:
            if CHORD_DICT[pattern] != name:
                name = CHORD_DICT[pattern].replace('major', '').replace('minor', 'm')

        if ' ' in pattern:
            pattern = pattern.replace(' ', '-')

        notes = pattern_to_notes(pattern)
        uniqueNotes = set(notes)

        name = (name.capitalize()
                .replace('mmaj7', 'mM7')
                .replace('m7add11', 'm11')
                .replace('add13', 'm13')
                .replace('9add13', 'maj9/13')
                .replace('6add9', '6/9')
                .replace('7add11', '11')
                .replace('7m13', '7#5')
                .replace('9add11', 'maj9/11')
                .replace('9add4', 'maj9/11')
                .replace('9m13', 'maj9#5')
                .replace('m7m13', 'm7#5')
                .replace('m7sus4', 'm11')
                .replace('madd11', 'mMaj11')
                .replace('msus4', 'madd4'))

        scale = ROOT_CHORD.match(name).group(0)
        # switch sharps to flats if required
        if scale in FLAT_MAPPING:
            mapping = FLAT_MAPPING[scale]
            uniqueNotes = [mapping[n] if n in mapping else n for n in uniqueNotes]

        try:
            # remove comments from chord name
            if '(' in name:
                name = name.split('(')[0]
            name = name.replace('no3rd', '').replace('no5th', '').strip()

            root_note = notes[0]
            bass = root_note

            if '/' in name:
                slashChord = name.split('/')
                c = Chord(slashChord[0].strip())
                bass = slashChord[1].upper()
                if bass not in notes:
                    print('{0} Bass {1} not in notes {2}'.format(name, bass, notes))
                    bass = root_note
            else:
                c = Chord(name)

            canonicalNotes = c.components()
            canonicalNotes.append(bass)

            # Guitar chord diagrams often ommit notes, so only check that all the fretted notes
            # are a subset of the expected notes
            if not all(note in canonicalNotes for note in uniqueNotes):
                notes = list(uniqueNotes)
                notes.sort(key=lambda x, rn=root_note: 'G' + rn if x < rn else x)
                suggestedChords = note_to_chord(notes)
                if suggestedChords:
                    name = suggestedChords[0].chord
                else:
                    name += '*'
        except ValueError:
            root_note = notes[0]
            add_m = IS_MINOR.match(name)
            s = Scale(Note(root_note), 'natural_minor' if add_m else 'major')

            postfix = ('m' if add_m else '') + name.split(scale)[1]
            postfix = postfix.replace('mm', 'mM')

            recipe = CHORD_RECIPES[postfix]

            computedNotes = [str(Note(root_note) + Interval(i)) for i in recipe.split(' ')[1:]]
            computedNotes.append(root_note)
            if not all(note in computedNotes for note in uniqueNotes):
                name += '*'
                print('{0}: Notes {1} Computed Notes {2}'.format(name, uniqueNotes, computedNotes))

        niceName = (name.replace('#', '♯')
                    .replace('b', '♭')
                    .replace('69', '6/9')
                    .replace('add', ' Add')
                    .replace('sus', ' Sus')
                    .replace('maj', ' Maj'))

        niceName = re.sub(SLASH_NOTE, cap_slash, niceName).strip()

        niceNotes = sorted([n.replace('#', '♯').replace('b', '♭') for n in uniqueNotes])
        root = scale.replace('#', '♯').replace('b', '♭').replace('m', '')
        if root in niceNotes:
            niceNotes = rotate(niceNotes, niceNotes.index(root))

        d = draw.Drawing(300, 100, origin='center', displayInline=False)
        d.draw(draw.Rectangle(-140, -50, 300, 100, fill='white'))
        d.append(draw.Text(niceName, 32, 0, 20 -11, text_anchor='middle', fill='#696969'))  # Text with font size 8
        d.append(draw.Text(', '.join(niceNotes), 32, 0, -20 -11, text_anchor='middle', fill='#696969'))  # Text with font size 8
        safeName = name.replace('/', '_').replace('#', 's').strip()
        proposedName = safeName
        count = 0
        while proposedName in file_names:
            proposedName = '{0}{1}'.format(safeName, count)
            count += 1
        file_names[proposedName] = True
        safeName = proposedName
        infoFileName = 'images/{0}_info.svg'.format(safeName)
        d.saveSvg(infoFileName)
        chordFileName = 'images/{0}.svg'.format(safeName)

        try:
            fretboard.Chord(positions=pattern).save(chordFileName)
            CREATED_FILES.append({'chord': chordFileName, 'info': infoFileName, 'root': root, 'notes': len(niceNotes)})
        except ValueError:
            print('{0}: Could not produce diagram. Pattern:{1}'.format(name, pattern))

with open('chord-files.json', 'w') as outfile:
    json.dump(CREATED_FILES, outfile)
