# Flyer Tools

Generate multiple SVG flyers by transforming a template. Resources (paths to images, texts, etc.) are given as a JSON file.

## Usage
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
