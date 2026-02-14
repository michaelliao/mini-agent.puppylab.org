# Convert File

Convert file between the formats.

## description

Use pandoc to convert between the formats, support "asciidoc", "docx", "html", "markdown", "pdf".

## usage

pandoc -f {input_format} -t {output_format} -o {output_file} {input_file}

- input_format: specify input format, can be "asciidoc", "docx", "html", "markdown"
- output_format: specify output format, can be "asciidoc", "docx", "html", "markdown", "pdf"
- output_file: the output file name
- input_file: the input file name

## author

Crypto Michael

## Reference

- https://pandoc.org/
