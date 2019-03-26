#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

# parameters
import argparse
import json

# dates
import locale
import dateutil.parser

# image encoding and compression
import base64
from PIL import Image
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

# xml parser
from lxml import etree

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


class FlyerTransformation(object):

    def __init__(self, resources_dir, program, movie, next_movies):
        self.resources_dir = resources_dir
        self.program = program
        self.movie = movie
        self.next_movies = next_movies

    def parse(self, file):
        stream = open(file, 'r')
        self.document = etree.parse(stream)
        stream.close()

    def getElementById(self, id):
        path = '//*[@id="%s"]' % id
        el_list = self.document.xpath(path)
        if el_list:
            return el_list[0]
        else:
            return None

    def apply(self, template):
        self.parse(template)
        movie_dir = os.path.join(self.resources_dir, self.movie['Dateien']['Ordner'])

        # title
        title = self.movie['Titel']
        self.getElementById('titel').text = title

        # text
        textfile_path = os.path.join(movie_dir, self.movie['Dateien']['Text'])
        with open(textfile_path, encoding='utf-8') as text_file:
            text = text_file.read()
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
        poster = os.path.join(movie_dir, self.movie['Dateien']['Poster'])
        self.getElementById('poster').set('{http://www.w3.org/1999/xlink}href', encode_image(poster))

        # screenshots
        screenshot1 = os.path.join(movie_dir, self.movie['Dateien']['Screenshot1'])
        self.getElementById('screenshot1').set('{http://www.w3.org/1999/xlink}href', encode_image(screenshot1))
        screenshot2 = os.path.join(movie_dir, self.movie['Dateien']['Screenshot2'])
        self.getElementById('screenshot2').set('{http://www.w3.org/1999/xlink}href', encode_image(screenshot2))
        screenshot3 = os.path.join(movie_dir, self.movie['Dateien']['Screenshot3'])
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
                next_poster = os.path.join(self.resources_dir,
                                           next_movie['Dateien']['Ordner'],
                                           next_movie['Dateien']['Poster'])
                next_poster_element.set('{http://www.w3.org/1999/xlink}href', encode_image(next_poster))
            self.getElementById('folgeDatum' + str(element_id)).text = next_dates
            self.getElementById('folgeTitel' + str(element_id)).text = next_title

        if not has_next_movies:
            # remove next movies title ("Bald im SchunterKino")
            self.getElementById('vorschauTitel').text = ''

        return self.document


def encode_image(image_path):
    # compress first
    compressed_image = compress(image_path)

    # images are embed as base64 in svg files
    return b'data:image/jpeg;base64,' + base64.encodestring(compressed_image)


def compress(image_path):
    # fixed resolution
    image = Image.open(image_path)
    image.thumbnail((1024, 1024), Image.ANTIALIAS)

    # use rgb
    if image.mode is not "RGB":
        image = image.convert("RGB")

    # store in temporary memory file
    temp_file = BytesIO()
    image.save(temp_file, 'JPEG', optimize=True, quality=90)

    # rewind and return image content as string
    temp_file.seek(0)
    return temp_file.getvalue()


def title_to_filepath(titel, output_dir):
    # filter special chars
    filename = re.sub(r'[^\w\-_\. ]', '_', titel)
    return os.path.join(output_dir, filename + '.svg')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', help=u'Bestehende Flyer überschreiben', action='store_true')
    parser.add_argument('-o', '--output', help='Ausgabe Ordner', action='store', default='woechentliche Flyer')
    parser.add_argument('-t', '--template', help='Vorlage Datei', action='store', default='vorlage.svg')
    parser.add_argument('json', metavar='program.json', type=argparse.FileType('r', encoding='utf-8'), help='JSON Datei mit dem aktuellen Programm')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    template = args.template
    resources_dir = os.path.dirname(args.json.name)  # resources are relative to the program file
    program = json.load(args.json)['Programm']

    # generate flyers
    movies = program['Filme']
    for index, movie in enumerate(movies):
        filepath = title_to_filepath(movie['Titel'], args.output)

        # skip existing flyers
        if not args.force and os.path.isfile(filepath):
            print('Flyer existiert bereits:\t' + os.path.basename(filepath))
            continue

        try:
            # collect next 3 movies (or None) for preview
            next_movies = movies[index+1:index+4]
            next_movies = next_movies + [None]*(3 - len(next_movies))

            # generate
            print('Generiere Flyer:\t' + os.path.basename(filepath))
            transformation = FlyerTransformation(resources_dir, program, movie, next_movies)
            document = transformation.apply(template)

            # create output directory if not exists
            if not os.path.exists(args.output):
                os.makedirs(args.output)

            # save to file
            with open(filepath, 'wb') as output_file:
                document.write(output_file, encoding='utf-8')
        except Exception as e:
            print('Fehler bei Flyer {}:'.format(filepath), repr(e))
