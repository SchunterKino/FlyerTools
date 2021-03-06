#!/bin/bash

# check params
if [ -z "$1" ]; then
    echo "Usage: $0 <files>"
    exit 1
fi

for FILE in "$@"; do
  if [ -f "$FILE" ]; then
    PDFFILE="${FILE%.*} - Druck.pdf"
    SVGFILE="${FILE%.*} - Druck.svg"

    # change width to A4 landscape
    sed 's/width=\"148mm\"/width=\"297mm\"/' "$FILE" > "$SVGFILE"
    # two page layout without background
    inkscape -f="$SVGFILE" --select=bg_gradient --verb=EditDelete \
                           --verb=EditSelectAll --verb=SelectionGroup --verb=AlignHorizontalLeft \
                           --verb=EditClone --verb=AlignHorizontalRight \
                           --verb=FileSave --verb=FileQuit
    # export pdf
    inkscape "$SVGFILE" --export-pdf="$PDFFILE"
    # remove temp svg file
    rm "$SVGFILE"

    PDFNAME=$(basename "$PDFFILE")
    echo "Exported to: $PDFNAME"
  else
    echo "File $FILE does not exists"
  fi
done
