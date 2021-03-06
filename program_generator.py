#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

# parameters
import argparse
import json

# dates
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
import copy


class ProgramTransformation(object):

    def __init__(self, resources_dir, program):
        self.resources_dir = resources_dir
        self.program = program

    def parse(self, file):
        stream = open(file, 'r', encoding='utf-8')
        self.document = etree.parse(stream)
        stream.close()

    def getElementById(self, id):
        path = '//*[@id="{}"]'.format(id)
        el_list = self.document.xpath(path)
        if el_list:
            return el_list[0]
        else:
            return None

    def apply(self, template):
        self.parse(template)

        # semester
        self.getElementById('semester_title').text = program['Semester']

        # times
        self.getElementById('einlass').text = program['Einlass']
        self.getElementById('beginn').text = program['Beginn']

        # prices
        self.getElementById('eintritt').text = program['Eintritt']
        self.getElementById('filmpass').text = program['Filmpass']

        # dates + titles
        list_item_template = self.getElementById('termine_item')
        date_list = list_item_template.getparent()
        # remove template lines
        for line in date_list.iter('{*}flowPara'):
            line.getparent().remove(line)
        movies = program['Filme']
        for movie in movies:
            combined_dates = []
            for date in movie['Termine']:
                parsed_date = dateutil.parser.parse(date, dayfirst=True)
                short_date = parsed_date.strftime('%d.%m.')
                # 29.10.
                combined_dates.append(short_date)
            # 29.10. + 03.11.
            combined_dates = ' + '.join(combined_dates)
            # 29.10. + 03.11. Das brandneue Testament
            dates_with_title = combined_dates + " " + movie['Titel']
            # append line
            line = copy.copy(list_item_template)
            line.text = dates_with_title
            date_list.append(line)

        # posters
        poster_template = self.getElementById('poster_links')
        page = poster_template.getparent()
        x_left = float(poster_template.attrib['x'])
        x_right = float(self.getElementById('poster_rechts').attrib['x'])
        y_base = float(poster_template.attrib['y'])
        height = float(poster_template.attrib['height'])
        # remove template posters
        for poster in page.iter('{*}image'):
            poster.getparent().remove(poster)
        for index, movie in enumerate(movies):
            # calculate position
            if index % 2 == 0:
                x = x_left
            else:
                x = x_right
            y_index = index // 2  # integer division -> 0,0,1,1,2,2,3,3,...
            y = y_base + height * y_index
            # append poster
            poster = copy.copy(poster_template)
            movie_dir = os.path.join(self.resources_dir, movie['Dateien']['Ordner'])
            image = os.path.join(movie_dir, movie['Dateien']['Poster'])
            poster.set('{http://www.w3.org/1999/xlink}href', encode_image(image))
            poster.attrib['x'] = str(x)
            poster.attrib['y'] = str(y)
            page.append(poster)

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', help=u'Bestehenden Flyer überschreiben', action='store_true')
    parser.add_argument('-o', '--output', help='Ausgabe Datei', action='store', default='Programm.svg')
    parser.add_argument('-t', '--template', help='Vorlage Datei', action='store', default='vorlage_programm.svg')
    parser.add_argument('json', metavar='program.json', type=argparse.FileType('r', encoding='utf-8'), help='JSON Datei mit dem aktuellen Programm')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    template = args.template
    resources_dir = os.path.dirname(args.json.name)  # resources are relative to the program file
    program = json.load(args.json)['Programm']
    outfile = args.output
    outdir = os.path.dirname(outfile)

    if not args.force and os.path.isfile(outfile):
        # skip existing flyer
        print('Flyer existiert bereits:\t' + os.path.basename(outfile))
    else:
        # generate flyer
        print('Generiere Flyer:\t' + os.path.basename(outfile))
        try:
            transformation = ProgramTransformation(resources_dir, program)
            document = transformation.apply(template)
        
            # create output directory if not exists
            if outdir and not os.path.exists(outdir):
                os.makedirs(outdir)

            # save to file
            with open(outfile, 'wb') as f:
                document.write(f, encoding='utf-8')

        except Exception as e:
            print('Fehler:', repr(e))
