# Flyer Tools
A collection of scripts to generate the SchunterKino flyers.

## Dependencies
Install Python dependencies once:
```sh
pip install -r requirements.txt
```

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
./print_version.sh Flyer.svg
```
To create the PDFs for all flyers in a folder:
```sh
./print_version.sh flyers/*.svg
```


## Program generator
Generates a single overview SVG flyer from a JSON file and a template.

### Usage
Simple:
```sh
python program_generator.py program.json
```
Choosing a different template file:
```sh
python program_generator.py -t template_overview.svg program.json
```
Changing the output file:
```sh
python program_generator.py -o program.svg program.json
```
Overwriting existing files:
```sh
python program_generator.py -f program.json
```
