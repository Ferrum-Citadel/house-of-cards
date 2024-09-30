![build](https://github.com/Ferrum-Citadel/house-of-cards/actions/workflows/python-test.yml/badge.svg)
# House-of-Cards (hoc)

A command-line tool to create real file structures on your system from tree-like representations. Easily replicate directory and file structures from your favorite articles, tutorials, LLM answers, or even from `tree -F` outputs from other users! Just copy the tree  structure to your clipboard and you're ready to recreate it on your system.

## Features

- Parses tree-like representations of file structures like:
```sh
./
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md
```
and creates them in your system.
- Handles directories with or without trailing slashes.
- Compatible with the output of the `tree -F` command.
- Can Automatically set appropriate permissions for directories and files.

## Installation

Install `hoc` from PyPI using `pip`:

```sh
pip install house-of-cards
```
or run it using pipx:
```sh
pipx run house-of-cards
```

or even single runs  with uvx:
```sh
uvx house-of-cards
```

## Usage

`hoc` can be used directly from the command line. It reads the file structure string from the clipboard or a file and creates the corresponding directory and file structure at the specified base path.

```sh
hoc <base_path> [options]
```
- <base_path>: The base directory where the structure will be created. (current directory if not provided)
- [Options]: Optional arguments to customize the behavior of the command.  

> [!NOTE]  
> If the dir that was chosen as base for the generated file structure does not exist it will be created.

### Options
- `-f, --file FILENAME`: File containing the tree structure. If not provided, the clipboard content will be used.
- `-dp, --dir-permissions PERMISSIONS`: Octal permissions for created directories (e.g., 755).
- `-fp, --file-permissions PERMISSIONS`: Octal permissions for created files (e.g., 644).
- `-h, --help`: Show the help message and exit.

## Examples

### Example 1: Generating a file structure from the clipboard contents
You can generate a directory structure based on the contents of your clipboard. Just copy the tree-like structure from your favorite tutorial, LLM answer, documentation or the output of a:
```sh
 `tree -F .`
 ```
  command and run hoc by just specifying the base path.

```sh
hoc /relative/base/path
```

Try it by copying the following structure to your clipboard:

```sh
etc/
├── apache2/
│   ├── apache2.conf
│   ├── envvars
│   ├── magic
│   ├── mods-available/
│   ├── mods-enabled/
│   ├── sites-available/
│   └── sites-enabled/
├── network/
│   ├── if-up.d/
│   ├── if-down.d/
│   └── interfaces
├── passwd
├── shadow
├── group
└── hosts
```
and running:
```sh
hoc ~/hoc_test
```
or
```sh
hoc 
```
If you want to use the current directory as the base path.

### Example 2: Creating a Structure from a File
Create a file named structure.txt with the following content:

```sh
./
├── apache2/
│   ├── apache2.conf
│   ├── envvars
│   ├── magic
│   ├── mods-available/
│   ├── mods-enabled/
│   ├── sites-available/
│   └── sites-enabled/
├── network/
│   ├── if-up.d/
│   ├── if-down.d/
│   └── interfaces
├── passwd
├── shadow
├── group
└── hosts
```
Run hoc to create the structure:
```sh
hoc /relative/base/path -f structure.txt
```

### Example 3: Setting Permissions
You can set the permissions for directories and files using the `-dp` and `-fp` options. For example, to set the permissions for directories to 755 and for files to 644, run:
```sh
hoc /relative/base/path -dp 755 -fp 644
```

### Example 4: Use it to clone file structures to a remote server or share them with other users
You can use hoc to clone file structures to a remote server by copying the structure using:
```sh
tree -F /path/to/directory | pbcopy
or
tree -F /path/to/directory | xclip -selection clipboard
```
and either share the clipboard content with the other user or save it to a file and send it to them. They can then run hoc on their system to create the same structure or run it on the remote server to create the structure there.

## License

This project is licensed under the GNU General Public License version 3. See the [LICENSE](LICENSE) file for details.
  