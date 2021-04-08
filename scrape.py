import urllib.request
import re
import json
from bs4 import BeautifulSoup

CHORD_PATTERN = re.compile(r'(([A-Ga-g][#b]?[mM]?[1-2]?[0-9]?(([sS]us|[Aa]dd|[Mm]aj|[Dd]im|[Dd]om)[1-9]?[0-9]?)?)(/[A-Ga-g][#b]?)?\s?(\(?([nN]o3rd|[nN]o[rR]oot|[nN]o5th)\)?)?(\(?[A-Ga-g]-shape\)?)?):?\s?(([12]?[0-9x][ \t]?){6,6})')
IS_CHORD_OF_THE_WEEK_LINK = re.compile(r'chord-of-the-week')

def scrape_address(address):
    print('Scraping {0}'.format(address))
    page = urllib.request.urlopen(address)

    soup = BeautifulSoup(page.read(), features="html.parser")

    chords = []
    for element in soup.find_all(attrs={'class': 'Message'}):
        for descendant in element.descendants:
            text = descendant.string
            if text:
                for m in CHORD_PATTERN.findall(str(text)):
                    chords.append({'name': m[0], 'pattern': m[8]})
    return chords


def find_chord_of_week_links(root_page):
    page = urllib.request.urlopen(root_page)
    soup = BeautifulSoup(page.read(), features="html.parser")

    urls = []
    for element in soup.find_all(attrs={'class': 'Message'}):
        for link in element.find_all('a'):
            href = str(link['href'])
            if IS_CHORD_OF_THE_WEEK_LINK.search(href):
                urls.append(href)
    return urls

def write_chord_file():
    links = find_chord_of_week_links('https://thefretboard.co.uk/discussion/598/chord-of-the-week-index#latest')

    chords = [scrape_address(url) for url in links]
    results = []

    for cl in chords:
        results += cl

    for x in results:
        print(x)

    with open('patterns.json', 'w') as outfile:
        json.dump(results, outfile)

if __name__ == '__main__':
    write_chord_file()