#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import json
import re
import os

# dates
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
import dateutil.parser

# image encoding and compression
import base64
from PIL import Image
from cStringIO import StringIO

# inkscape/svg
# TODO pure xml parser without inkscape dependency?
sys.path.append('/usr/share/inkscape/extensions')
import inkex # inkscape effects


class FlyerEffect(inkex.Effect):

    def __init__(self, program, movie, next_movies, output_folder):
        inkex.Effect.__init__(self)
        self.program= program
        self.movie = movie
        self.next_movies = next_movies
        self.output_folder = output_folder

    def effect(self):
        # title
        title = self.movie['Titel']
        self.getElementById('titel').text = title

        # text
        folder = self.movie['Dateien']['Ordner']
        textfile_path = os.path.join(folder, self.movie['Dateien']['Text']);
        with open(textfile_path) as text_file:
            text = text_file.read().decode('utf-8')
        self.getElementById('kurztext').text = text

        # info (year, director, ...)
        year = self.movie['Jahr']
        genre = self.movie['Genre']
        length = self.movie['Laenge']
        info = ', '.join([year, genre, length])
        self.getElementById('zusatzinfo').text = info
        director = 'Regie: ' + self.movie['Regie']
        self.getElementById('regie').text = director

        # dates + start time
        combined_dates = []
        for date in self.movie['Termine']:
            parsed_date = dateutil.parser.parse(date, dayfirst=True)
            weekday = parsed_date.strftime('%A')
            short_date = parsed_date.strftime('%d.%m.')
            # Donnerstag 29.10.
            combined_dates.append(weekday + ' ' + short_date)
        # Donnerstag 29.10. + Dienstag 03.11.
        combined_dates = ' + '.join(combined_dates)
        self.getElementById('termineDatum').text = combined_dates
        start_time = 'Beginn: ' + self.program['Beginn']
        self.getElementById('termineZeit').text = start_time

        # prices
        price = 'Eintritt: ' + self.program['Eintritt']
        self.getElementById('eintrittPreis').text = price
        pass_price = 'Filmpass*: ' + self.program['Filmpass']
        self.getElementById('eintrittFilmpass').text = pass_price

        # poster
        poster = os.path.join(folder, self.movie['Dateien']['Poster'])
        self.getElementById('poster').set('{http://www.w3.org/1999/xlink}href', encode_image(poster))

        # screenshots
        screenshot1 = os.path.join(folder, self.movie['Dateien']['Screenshot1'])
        self.getElementById('screenshot1').set('{http://www.w3.org/1999/xlink}href', encode_image(screenshot1))
        screenshot2 = os.path.join(folder, self.movie['Dateien']['Screenshot2'])
        self.getElementById('screenshot2').set('{http://www.w3.org/1999/xlink}href', encode_image(screenshot2))
        screenshot3 = os.path.join(folder, self.movie['Dateien']['Screenshot3'])
        self.getElementById('screenshot3').set('{http://www.w3.org/1999/xlink}href', encode_image(screenshot3))

        # posters and dates for next movies
        has_next_movies = False
        for index, next_movie in enumerate(self.next_movies):
            element_id = index+1
            next_poster_element = self.getElementById('folgeposter' + str(element_id))
            if next_movie is None:
                # clear field, poster and shadow
                next_dates = ''
                next_title = ''
                shadow = self.getElementById('schatten' + str(element_id))
                shadow.getparent().remove(shadow)
                next_poster_element.getparent().remove(next_poster_element)
            else:
                has_next_movies = True
                next_dates = []
                for date in next_movie['Termine']:
                    parsed_date = dateutil.parser.parse(date, dayfirst=True)
                    short_date = parsed_date.strftime('%d.%m.')
                    next_dates.append(short_date)
                next_dates = ' + '.join(next_dates)
                next_title = next_movie['Titel']
                next_poster = os.path.join(next_movie['Dateien']['Ordner'], next_movie['Dateien']['Poster']);
                next_poster_element.set('{http://www.w3.org/1999/xlink}href', encode_image(next_poster))
            self.getElementById('folgeDatum' + str(element_id)).text = next_dates
            self.getElementById('folgeTitel' + str(element_id)).text = next_title

        if not has_next_movies:
            # remove next movies title ("Bald im SchunterKino")
            self.getElementById('vorschauTitel').text = ''

        # save to file
        path = title_to_filepath(title, self.output_folder)
        with open(path, 'w') as output_file:
            self.document.write(output_file)


def encode_image(image_path):
    # compress first
    compressed_image = compress(image_path)

    # images are embed as base64 in svg files
    return 'data:image/jpeg;base64,' + base64.encodestring(compressed_image)


def compress(image_path):
    # fixed resolution
    image = Image.open(image_path)
    image.thumbnail((1024,1024), Image.ANTIALIAS)

    # store in temporary memory file
    temp_file = StringIO()
    image.save(temp_file, 'JPEG', omptimize=True, quality=90)

    # rewind and return image content as string
    temp_file.seek(0)
    return temp_file.getvalue()


def title_to_filepath(titel, output_folder):
    # filter special chars
    filename = re.sub('[^\w\-_\. ]', '_', titel)
    return os.path.join(output_folder, filename + '.svg')


if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    # TODO Print version?
    # TODO Program
    #parser.add_argument('-p', '--program', help='Programm Flyer erstellen', action='store_true')
    parser.add_argument('-f', '--force', help='Bestehende Flyer überschreiben', action='store_true')
    parser.add_argument('-o', '--output', help='Ausgabe Ordner', action='store', default='woechentliche Flyer')
    parser.add_argument('Datei', type=argparse.FileType('r'), help='JSON Datei mit dem aktuellen Programm')
    args = parser.parse_args()

    # load json file
    program = json.load(args.Datei)['Programm']

    # templates
    template = program['Vorlage']

    # generate flyers
    movies = program['Filme']
    for index, movie in enumerate(movies):
        filepath = title_to_filepath(movie['Titel'], args.output)

        # Skip existing flyers
        if not args.force and os.path.isfile(filepath):
            print 'Flyer existiert bereits:\t' + filepath
            continue

        # create folder if not exists
        if not os.path.exists(args.output):
            os.makedirs(args.output)

        # collect next 3 movies (or None) for preview
        next_movies = movies[index+1:index+4]
        next_movies = next_movies + [None]*(3 - len(next_movies))

        # generate
        print 'Generiere Flyer:\t' + filepath
        # TODO Create only 1 Effect, with parameters in affect() instead of constructor?
        flyer_effect = FlyerEffect(program, movie, next_movies, args.output)
        flyer_effect.affect(args=[template], output=False)
