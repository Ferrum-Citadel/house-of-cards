import os
import re
import sys
from typing import List, Optional

import click
import pyperclip


class TreeNode:
    def __init__(self, name: str, is_dir: Optional[bool] = None, parent: Optional["TreeNode"] = None):
        self.name = name
        self.parent = parent
        self.children: List["TreeNode"] = []
        self.is_dir = is_dir if is_dir is not None else False
        self.full_path = os.path.join(parent.full_path, name) if parent else name

        if parent:
            parent.add_child(self)

    def add_child(self, child: "TreeNode") -> None:
        self.children.append(child)
        self.is_dir = True  # A node with children is a directory

    def get_path(self) -> str:
        return self.full_path

    def __repr__(self):
        return f"TreeNode(name='{self.name}', is_dir={self.is_dir})"


def parse_tree_structure(tree_str: str) -> List[TreeNode]:
    """
    Parses a tree-like string and returns a list of root nodes.

    Args:
        tree_str (str): The tree-like string representation of directories and files.

    Returns:
        List[TreeNode]: A list of root nodes of the tree structure.

    Raises:
        ValueError: If the input tree structure is invalid.
    """
    lines = tree_str.strip().split("\n")
    if not any(line.strip() for line in lines):
        raise ValueError("The input tree structure is empty.")

    # Replace tabs with 4 spaces
    lines = [line.replace("\t", "    ") for line in lines]
    node_stack: List[TreeNode] = []
    roots: List[TreeNode] = []

    pattern = re.compile(r"^(?P<indent>(?: {4}|\│   )*)(?:(?P<connector>[├└])── )?(?P<name>.+)$")

    for line in lines:
        if not line.strip():
            continue
        match = pattern.match(line)
        if not match:
            raise ValueError(f"Invalid line format: '{line}'")

        indent = match.group("indent")
        connector = match.group("connector")
        name = match.group("name")
        indent = indent.replace("│", " ")

        # Adjust the depth calculation to include connectors
        depth = len(indent) // 4 + (1 if connector else 0)
        is_dir = name.endswith("/")

        if depth == 0:
            node = TreeNode(name=name, is_dir=is_dir)
            roots.append(node)
            node_stack = [node]
        else:
            if depth > len(node_stack):
                raise ValueError(f"Inconsistent indentation at line: '{line}'")
            node_stack = node_stack[:depth]
            parent_node = node_stack[-1]
            node = TreeNode(name=name, is_dir=is_dir, parent=parent_node)
            node_stack.append(node)
    return roots


def create_structure_from_tree(
    base_path: str, nodes: List[TreeNode], dir_permissions: Optional[int], file_permissions: Optional[int]
) -> None:
    for node in nodes:
        create_node_structure(base_path, node, dir_permissions, file_permissions)


def create_node_structure(
    base_path: str, node: TreeNode, dir_permissions: Optional[int], file_permissions: Optional[int]
) -> None:
    full_path = os.path.join(base_path, node.get_path())

    if node.is_dir or node.children:
        os.makedirs(full_path, exist_ok=True)
        if dir_permissions is not None:
            set_permissions(full_path, dir_permissions)
        for child in node.children:
            create_node_structure(base_path, child, dir_permissions, file_permissions)
    else:
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(full_path, "w", encoding="utf-8"):
            pass
        if file_permissions is not None:
            set_permissions(full_path, file_permissions)


def set_permissions(full_path: str, permissions: int) -> None:
    try:
        os.chmod(full_path, permissions)
    except OSError as e:
        print(f"Error setting permissions for '{full_path}': {e}")


def validate_permissions(ctx, param, value):
    if value is not None:
        try:
            # Convert the string to an octal integer
            permissions = int(value, 8)
            if not (0 <= permissions <= 0o777):
                raise ValueError
            return permissions
        except ValueError:
            raise click.BadParameter("Permissions must be a valid octal number between 000 and 777.")
    return value


class Command(click.Command):
    def get_help(self, ctx):
        help_message = super().get_help(ctx)
        help_text = f"""
{help_message}

Examples:
  - Create a directory structure from the clipboard content in the current directory:
    hoc

  - Create a directory structure from the clipboard content in a specified directory:
    hoc /path/to/directory

  - Create a directory structure from a file in the current directory:
    hoc -f /path/to/tree_structure.txt

  - Create a directory structure from a file in a specified directory:
    hoc /path/to/directory -f /path/to/tree_structure.txt

  - Create a directory structure with custom permissions:
    hoc -dp 755 -fp 644
"""
        return help_text


@click.command(cls=Command)
@click.help_option("-h", "--help")
@click.argument("path", default=".", required=False)
@click.option(
    "-f", "--file", "input_file", type=click.File("r", encoding="utf-8"), help="File containing the tree structure."
)
@click.option(
    "-dp",
    "--dir-permissions",
    callback=validate_permissions,
    help="Octal permissions for created directories (e.g., 755).",
)
@click.option(
    "-fp", "--file-permissions", callback=validate_permissions, help="Octal permissions for created files (e.g., 644)."
)
def main(
    path: str, input_file: Optional[click.File], dir_permissions: Optional[int], file_permissions: Optional[int]
) -> None:
    """
    Create a directory structure from a tree-like string.

    PATH is the base path where the directory structure will be created. If not
    provided, the current directory ('.') will be used.

    If no input file is provided, the clipboard content will be used by default.

    Options:
      -dp, --dir-permissions: Octal permissions for created directories (e.g., 755).
      -fp, --file-permissions: Octal permissions for created files (e.g., 644).
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            print(f"Error creating base directory '{path}': {e}")
            sys.exit(1)
    elif not os.path.isdir(path):
        print(f"Error: The path '{path}' is not a directory.")
        sys.exit(1)

    try:
        if input_file:
            tree_str = input_file.read()
            if not tree_str.strip():
                raise ValueError("The input file is empty.")
        else:
            tree_str = pyperclip.paste()
            if not tree_str.strip():
                raise ValueError("The clipboard is empty.")
    except Exception as e:
        print(f"Error reading input: {e}")
        sys.exit(1)

    try:
        roots = parse_tree_structure(tree_str)
        create_structure_from_tree(path, roots, dir_permissions, file_permissions)
        print(f"Directory structure created at '{path}'")
    except ValueError as ve:
        print(f"Parsing Error: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        print("An unexpected error occurred. Please check the input for inconsistencies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
