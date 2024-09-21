import os
from unittest import mock

import pytest
from click.testing import CliRunner

from hoc.cli import TreeNode, create_structure_from_tree, main, parse_tree_structure


@pytest.fixture
def simple_tree_str():
    return """
root/
├── folder1/
│   ├── file1.txt
│   └── file2.txt
└── folder2/
    └── file3.txt
    """


@pytest.fixture
def complex_tree_str():
    return """
etc/
├── apache2/
│   ├── apache2.conf
│   ├── envvars
│   ├── mods-available/
│   │   ├── alias.conf
│   │   └── dir.conf
├── network/
│   ├── if-up.d/
│   └── interfaces
└── hosts
    """


@pytest.fixture
def invalid_tree_str():
    return """
├── README.md
├── whatever/
│   ├── __init__.py
│   ├── __pycache__/
│   │   ├── __init__.cpython-312.pyc
│   │   └── cli.cpython-312.pyc
│   └── cli.py*
├── yeet/
│   └── root/
    """


def test_parse_tree_structure_simple(simple_tree_str):
    roots = parse_tree_structure(simple_tree_str)
    assert len(roots) == 1
    root = roots[0]
    assert root.name == "root/"
    assert root.is_dir
    assert len(root.children) == 2


def test_parse_tree_structure_complex(complex_tree_str):
    roots = parse_tree_structure(complex_tree_str)
    assert len(roots) == 1
    etc = roots[0]
    assert etc.name == "etc/"
    assert etc.is_dir
    assert len(etc.children) == 3  # apache2/, network/, hosts


def test_parse_tree_structure_invalid(invalid_tree_str):
    with pytest.raises(ValueError) as excinfo:
        parse_tree_structure(invalid_tree_str)
    assert "Inconsistent indentation" in str(excinfo.value)


def test_parse_tree_structure_empty():
    with pytest.raises(ValueError) as excinfo:
        parse_tree_structure("")
    assert "The input tree structure is empty" in str(excinfo.value)


def test_create_structure_from_tree(tmp_path, simple_tree_str):
    roots = parse_tree_structure(simple_tree_str)

    # Define custom permissions
    dir_permissions = 0o755
    file_permissions = 0o644

    # Create the structure with custom permissions
    create_structure_from_tree(str(tmp_path), roots, dir_permissions, file_permissions)

    # Verify directories and files
    assert (tmp_path / "root" / "folder1").is_dir()
    assert (tmp_path / "root" / "folder1" / "file1.txt").is_file()
    assert (tmp_path / "root" / "folder1" / "file2.txt").is_file()
    assert (tmp_path / "root" / "folder2").is_dir()
    assert (tmp_path / "root" / "folder2" / "file3.txt").is_file()

    # Verify permissions
    assert oct((tmp_path / "root" / "folder1").stat().st_mode & 0o777) == oct(dir_permissions)
    assert oct((tmp_path / "root" / "folder1" / "file1.txt").stat().st_mode & 0o777) == oct(file_permissions)
    assert oct((tmp_path / "root" / "folder1" / "file2.txt").stat().st_mode & 0o777) == oct(file_permissions)
    assert oct((tmp_path / "root" / "folder2").stat().st_mode & 0o777) == oct(dir_permissions)
    assert oct((tmp_path / "root" / "folder2" / "file3.txt").stat().st_mode & 0o777) == oct(file_permissions)


def test_treenode():
    root = TreeNode("root/", is_dir=True)
    child = TreeNode("child.txt", parent=root)
    assert root.children[0] == child
    assert child.parent == root
    assert root.is_dir
    assert not child.is_dir
    assert root.get_path() == "root/"
    assert child.get_path() == os.path.join("root/", "child.txt")


def test_main_cli(tmp_path, monkeypatch, simple_tree_str):
    # Mock clipboard content
    with mock.patch("pyperclip.paste", return_value=simple_tree_str):
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])
        assert result.exit_code == 0
        assert "Directory structure created at" in result.output
        # Verify the structure
        assert (tmp_path / "root" / "folder1" / "file1.txt").is_file()


def test_main_cli_with_file(tmp_path, tmpdir, simple_tree_str):
    # Write the tree string to a temporary file
    tree_file = tmpdir.join("tree.txt")
    tree_file.write(simple_tree_str)
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "-f", str(tree_file)])
    assert result.exit_code == 0
    assert "Directory structure created at" in result.output
    # Verify the structure
    assert (tmp_path / "root" / "folder1" / "file1.txt").is_file()


def test_main_cli_invalid_input(tmp_path, invalid_tree_str):
    # Mock clipboard content
    with mock.patch("pyperclip.paste", return_value=invalid_tree_str):
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])
        assert result.exit_code != 0
        assert "Parsing Error" in result.output


def test_main_cli_empty_input(tmp_path):
    # Mock clipboard with empty content
    with mock.patch("pyperclip.paste", return_value=""):
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])
        assert result.exit_code != 0
        assert "The clipboard is empty" in result.output


def test_main_cli_no_arguments(tmp_path, simple_tree_str):
    # Change current directory to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with mock.patch("pyperclip.paste", return_value=simple_tree_str):
            runner = CliRunner()
            result = runner.invoke(main, [])
            assert result.exit_code == 0
            assert "Directory structure created at" in result.output
            # Verify the structure
            assert (tmp_path / "root" / "folder1" / "file1.txt").is_file()
    finally:
        os.chdir(original_cwd)


def test_main_cli_invalid_path(tmp_path, simple_tree_str):
    # Mock clipboard content
    with mock.patch("pyperclip.paste", return_value=simple_tree_str):
        runner = CliRunner()
        # Use an invalid path (file instead of directory)
        invalid_path = tmp_path / "file.txt"
        invalid_path.touch()
        result = runner.invoke(main, [str(invalid_path)])
        assert result.exit_code != 0
        assert f"Error: The path '{invalid_path}' is not a directory" in result.output
