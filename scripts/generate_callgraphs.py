"""Render main.py's Pyan graph with function names or full source signatures.

Requires the pyan3 and Graphviz dot executables on PATH. Does not import or run
main.py. Pyan supplies the nodes and edges; this script only adjusts labels and
presentation, including identifying the bisect_left key callback.
"""

import ast
import json
import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "docs" / "callgraphs"
NODE = re.compile(r'^(\s*"([^"]+)" \[label=)"(?:[^"\\]|\\.)*"(.*)$')


def function_labels(
    source: str,
) -> dict[str, tuple[str, str]]:
    """Map Pyan identifiers to qualified function names and source signatures."""
    lines = source.splitlines()
    labels: dict[str, tuple[str, str]] = {}

    def visit(node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                path = (*scope, child.name)
                header = textwrap.dedent(
                    "\n".join(lines[child.lineno - 1 : child.body[0].lineno - 1])
                ).strip()
                if not header.endswith(":"):
                    raise ValueError(
                        f"Expected a multiline function body: {child.name}"
                    )
                signature = header.removeprefix("async ").removeprefix("def ")[:-1]
                labels["__".join((SOURCE.stem, *path))] = (
                    ".".join(path),
                    signature,
                )
                visit(child, path)
            elif isinstance(child, ast.ClassDef):
                visit(child, (*scope, child.name))
            else:
                visit(child, scope)

    visit(ast.parse(source), ())
    return labels


def render_dot(
    raw: str, labels: dict[str, tuple[str, str]], *, signatures: bool
) -> str:
    variant = "Full function signatures" if signatures else "Function names"
    title = (
        f"main.py - {variant}\n"
        "Pyan static uses graph; external calls are omitted.\n"
        "Dashed edge: callback passed to bisect_left."
    )
    output: list[str] = []
    labeled: set[str] = set()
    for line in raw.splitlines():
        if line == "digraph G {":
            output.extend(
                [
                    line,
                    f"    graph [label={json.dumps(title)}, labelloc=t, "
                    + 'fontname="DejaVu Sans", fontsize=14, bgcolor="white", pad=0.3];',
                    '    node [shape=box, fontname="DejaVu Sans", fontsize=11, margin="0.18,0.12"];',
                    '    edge [fontname="DejaVu Sans", fontsize=10, arrowsize=0.8];',
                ]
            )
            continue
        match = NODE.match(line)
        if match is not None:
            prefix, node_id, suffix = match.groups()
            if node_id in labels:
                name, signature = labels[node_id]
                label = signature if signatures else name
                quoted = json.dumps(label)
                if "\n" in label:
                    quoted = json.dumps(label + "\n").replace(r"\n", r"\l")
                line = prefix + quoted + suffix
                labeled.add(node_id)
            elif node_id == SOURCE.stem:
                line = prefix + json.dumps("main.py (module entry)") + suffix
            line = line.replace('style="filled"', 'style="rounded,filled"')
            line = line.replace('fillcolor="#feccccb2"', 'fillcolor="#e8f1fb"')
            line = line.replace('fillcolor="#ff9999b2"', 'fillcolor="#d5e5f8"')
        # Preserve Pyan's edge, but distinguish a callback reference from a direct call.
        if re.search(r'"main__[^" ]+" -> "main__[^" ]+__is_feasible"', line):
            line = line.replace('style="solid"', 'style="dashed", label="key callback"')
        output.append(line)
    if labeled != labels.keys():
        raise ValueError(f"Pyan did not emit all functions: {labels.keys() - labeled}")
    return "\n".join(output) + "\n"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text()
    labels = function_labels(source)
    generated = subprocess.run(
        [
            "pyan3",
            "main.py",
            "--uses",
            "--no-defines",
            "--colored",
            "--dot",
            "--dot-rankdir",
            "TB",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    for signatures in (False, True):
        name = "main-signatures" if signatures else "main-names"
        dot_path = OUTPUT / f"{name}.dot"
        _ = dot_path.write_text(
            render_dot(generated.stdout, labels, signatures=signatures)
        )
        for extension in ("svg", "png"):
            target = OUTPUT / f"{name}.{extension}"
            _ = subprocess.run(
                ["dot", f"-T{extension}", str(dot_path), "-o", str(target)],
                check=True,
            )
            print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
