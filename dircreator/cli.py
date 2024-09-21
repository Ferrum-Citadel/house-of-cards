import argparse
import os
import re
import sys


def parse_tree_structure(tree_str):
    tree = {}
    path_stack = []
    lines = tree_str.strip().split("\n")

    base_name = ""
    for idx, line in enumerate(lines):
        # Ignore empty lines
        if not line.strip():
            continue

        # For the first line, set the base name (root directory)
        if idx == 0:
            base_name = line.strip()
            if not base_name.endswith("/"):
                base_name += "/"
            path_stack = [base_name]
            tree[base_name] = {"type": "dir"}
            continue

        # Regular expression to match indentation and name
        match = re.match(r"^(?P<indent>(?:    |\│   )*)(?P<connector>[├└]── )(?P<name>.+)$", line)
        if not match:
            continue

        indent = match.group("indent")
        name = match.group("name").strip()

        # Calculate depth (number of indentation levels)
        depth = (len(indent.replace("│", " ")) // 4) + 1  # '+1' because root is depth 0

        # Adjust path_stack based on depth
        while len(path_stack) > depth:
            path_stack.pop()

        # Add current name to path_stack
        path_stack.append(name)

        # Build current path
        current_path = os.path.join(*path_stack)

        # Determine if it's a directory (if it ends with '/')
        is_dir = name.endswith("/")

        # Store in tree
        tree[current_path] = {"type": "dir" if is_dir else "file"}

    return tree


def set_permissions(full_path, item_type):
    if item_type == "dir":
        os.chmod(full_path, 0o755)
    else:
        ext = os.path.splitext(full_path)[1]
        if ext == ".py":
            os.chmod(full_path, 0o755)  # Executable for Python scripts
        else:
            os.chmod(full_path, 0o644)  # Read/write for text files


def create_structure(base_path, tree):
    for path, info in tree.items():
        full_path = os.path.join(base_path, path)
        if info["type"] == "dir":
            os.makedirs(full_path, exist_ok=True)
            set_permissions(full_path, "dir")
        else:
            dir_path = os.path.dirname(full_path)
            os.makedirs(dir_path, exist_ok=True)
            # Create an empty file
            open(full_path, "w").close()
            set_permissions(full_path, "file")


def main():
    parser = argparse.ArgumentParser(description="Create directory structure from tree-like input.")
    parser.add_argument("path", help="Base path to create the directory structure.")
    parser.add_argument(
        "input_file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="File containing the tree structure. If not provided, defaults to stdin.",
    )
    args = parser.parse_args()

    # Ensure the base path exists or create it
    if not os.path.exists(args.path):
        os.makedirs(args.path)
    elif not os.path.isdir(args.path):
        print(f"Error: The path '{args.path}' is not a directory.")
        sys.exit(1)

    # Read and validate the input file content
    try:
        tree_str = args.input_file.read()
        if not tree_str.strip():
            raise ValueError("The input file is empty.")
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    try:
        tree = parse_tree_structure(tree_str)
        create_structure(args.path, tree)
        print(f"Directory structure created at {args.path}")
    except Exception as e:
        print(f"Error: {e}")
        print("The provided directory structure could not be parsed. Please check the input for inconsistencies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
