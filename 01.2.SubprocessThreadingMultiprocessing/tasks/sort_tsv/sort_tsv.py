from pathlib import Path
import subprocess


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    file_in = Path(file_in)
    file_out = Path(file_out)
    with file_in.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    def sortl(line):
        col1, col2 = line.strip("\n").split("\t")
        return int(col2), col1

    sort = sorted(lines, key=sortl)

    with file_out.open("w", encoding="utf-8") as f:
        f.writelines(sort)


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    subprocess.run(
        ["sort", "-t", "\t", "-k", "2n", "-k", "1,1", "-o",  file_out, file_in],
        check=True,
    )
