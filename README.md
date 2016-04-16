# Flyer Tools

A collection of scripts to generate the SchunterKino flyers.

## Flyer Generator
Generates multiple SVG flyers by transforming a template. Resources (paths to images, texts, etc.) are given as a JSON file.

### Usage
Simple:
```sh
    python flyer_generator.py program.json
```
Choosing a different template file:
```sh
    python flyer_generator.py -t template.svg program.json
```
Changing the output directory:
```sh
    python flyer_generator.py -o flyers program.json
```
Overwriting existing files:
```sh
    python flyer_generator.py -f program.json
```

## Print Version
 Generates a A4 two page layout PDF from a A5 flyer SVG. Suitable for black and white printing (no background)

### Notice
 Requires Inkscape v0.91+. Also due to how Inkscapes command line tool interacts with the GUI, the dropdown menu in "Align and Distribute" (ctrl+shift+A) must be  set to "Relative to: Page" or the result will be incorrect.

### Usage
This will create the file "Flyer - Druck.pdf":
```sh
    ./druck_version Flyer.svg
```
To create the PDFs for all flyers in a folder:
```sh
for f in flyers/*.svg; do ./druck_version.sh "$f"; done
```
