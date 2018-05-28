# Remembrall
Remembrall is a simple mkv tagger that tags 
mkv files with its current name

## Requirements
    python3

## Installation
    git clone https://github.com/johnelliotbaker/Remembrall.git

## Usage
    python3 Remebrall.py "path/to/directory/with/mkv/files"
The prompt will ask for a choice to "save" or "restore"
If you want to save the current file names of mkv to it's tags,
enter "save" and enter.
If you want to restore the current filenames to what's contained
in the file's "OriginalFilename" tag, enter "restore" and enter.

Alternatively, you can add a switch with the command.
e.g.
    python3 Remebrall.py -c save "path/to/directory/with/mkv/files"
    python3 Remebrall.py -c restore "path/to/directory/with/mkv/files"

To recurse through inner directories, use the -R switch.
    python3 Remebrall.py -R -c save "path/to/directory/with/mkv/files"
