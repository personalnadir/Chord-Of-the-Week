import os
#required for python 2.7 & >=3.3
import json
from jinja2 import Template
from PIL import Image
import operator

directory_path = os.getcwd()
DATA_DIR = 'data'
RML_DIR = 'rml'

class Chord(object):
    "Empty class to hold parsed chord attributes"
    pass

def parse_chords(filename):
    chords = []
    with open(filename, 'r') as infile:
        content = json.loads(infile.read())
        for chord in content:
            fret = os.path.join(directory_path, chord['chord'])
            info_file = os.path.join(directory_path, chord['info'])

            c = Chord()
            c.fret = fret
            c.info = info_file
            c.root = chord['root']
            c.notes = chord['notes']
            c.width = 150
            chords.append(c)
    chords.sort(key=operator.attrgetter('root', 'notes'))
    return chords

def create_html(chords, template):
    """Creates PDF as a binary stream in memory, and returns it

    This can then be used to write to disk from management commands or crons,
    or returned to caller via Django views.
    """
    template_name = os.path.join(RML_DIR, template)
    namespace = {
        'chords':chords,
    }

    with open(template_name, 'r') as template_file:
        template = Template(template_file.read())
        xmlstring = template.render(**namespace)
        return xmlstring

def main():
    filename = os.path.join(DATA_DIR, 'chord-files.json')

    print('\n'+'#'*20)
    print('\nabout to parse file: ', filename)
    chords = parse_chords(filename)
    print('file parsed OK \n')

    html = create_html(chords, 'book_template.prep')
    filename = 'output/chord-of-the-week.html'
    open(filename, 'w').write(html)
    print('Created %s' % filename)

if __name__ == '__main__':
    main()
