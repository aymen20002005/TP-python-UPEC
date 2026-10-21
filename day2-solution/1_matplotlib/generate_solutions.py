#!/usr/bin/env python3
"""
Generate *_solution.ipynb for all notebooks in the given directory by:
- Loading the original notebooks
- Sanitizing JetBrains-specific transient fields (e.g., 'jetTransient') and any unknown keys in outputs
- Saving as *_solution.ipynb
- Executing the solution notebooks to verify they run without errors

Usage:
    python generate_solutions.py [notebooks_dir]

Default notebooks_dir is the directory of this script.
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import json
from typing import Any, Dict, List

import nbformat
from nbformat import NotebookNode
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError


def sanitize_notebook(nb: NotebookNode) -> NotebookNode:
    """Remove JetBrains-specific or unknown transient keys from outputs and cells.
    Specifically removes 'jetTransient' from outputs and cells if present.
    """
    # Ensure nbformat v4
    nb.nbformat = 4
    nb.nbformat_minor = max(getattr(nb, 'nbformat_minor', 5), 5)

    for cell in nb.cells:
        # Remove jetTransient from cell-level metadata if present
        if isinstance(cell.get('metadata'), dict) and 'jetTransient' in cell.metadata:
            try:
                del cell.metadata['jetTransient']
            except Exception:
                pass

        # Clean outputs
        outputs: List[Dict[str, Any]] = cell.get('outputs', []) or []
        for output in outputs:
            if isinstance(output, dict) and 'jetTransient' in output:
                try:
                    del output['jetTransient']
                except Exception:
                    pass
            # Also make sure output has only allowed keys; leave standard ones untouched
            # We won't aggressively prune unknown keys except jetTransient to avoid losing data

    # Clean top-level metadata if necessary
    if isinstance(nb.get('metadata'), dict) and 'jetTransient' in nb.metadata:
        try:
            del nb.metadata['jetTransient']
        except Exception:
            pass

    return nb


def create_solution_path(src: Path) -> Path:
    stem = src.stem
    if stem.endswith('_solution'):
        return src
    return src.with_name(f"{stem}_solution{src.suffix}")


def is_notebook(path: Path) -> bool:
    return path.suffix == '.ipynb' and not path.name.endswith('-executed.ipynb') and not path.name.endswith('_solution.ipynb')


def main():
    if len(sys.argv) > 1:
        nb_dir = Path(sys.argv[1]).expanduser().resolve()
    else:
        nb_dir = Path(__file__).parent.resolve()

    if not nb_dir.exists():
        print(f"Directory not found: {nb_dir}", file=sys.stderr)
        sys.exit(1)

    notebooks = sorted([p for p in nb_dir.iterdir() if is_notebook(p)])
    if not notebooks:
        print(f"No notebooks found in {nb_dir}")
        return

    print(f"Found {len(notebooks)} notebooks in {nb_dir}")

    # Prepare executor
    ep = ExecutePreprocessor(timeout=300, kernel_name='python3')

    successes = []
    failures = []

    for nb_path in notebooks:
        print(f"\nProcessing: {nb_path.name}")
        try:
            nb = nbformat.read(nb_path, as_version=4)
        except Exception as e:
            # Try raw JSON load and then convert to nbformat, to bypass validation issues
            try:
                with open(nb_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                nb = nbformat.from_dict(raw)
            except Exception as e2:
                msg = f"Failed to read notebook {nb_path}: {e2}"
                print(msg)
                failures.append((nb_path.name, msg))
                continue

        nb = sanitize_notebook(nb)

        sol_path = create_solution_path(nb_path)
        # If a solution already exists, prefer it (it may have been patched) and execute that one.
        if sol_path.exists():
            try:
                nb = nbformat.read(sol_path, as_version=4)
                nb = sanitize_notebook(nb)
                print(f"Using existing solution notebook: {sol_path.name}")
            except Exception as e:
                print(f"Failed to read existing solution {sol_path.name}: {e}, will overwrite with sanitized copy of original.")
                try:
                    nbformat.write(nb, sol_path)
                    print(f"Saved solution notebook: {sol_path.name}")
                except Exception as e2:
                    msg = f"Failed to write solution notebook {sol_path}: {e2}"
                    print(msg)
                    failures.append((nb_path.name, msg))
                    continue
        else:
            try:
                nbformat.write(nb, sol_path)
                print(f"Saved solution notebook: {sol_path.name}")
            except Exception as e:
                msg = f"Failed to write solution notebook {sol_path}: {e}"
                print(msg)
                failures.append((nb_path.name, msg))
                continue

        # Execute the solution notebook in-place and overwrite
        try:
            print("Executing...")
            ep.preprocess(nb, {'metadata': {'path': str(nb_dir)}})
            nbformat.write(nb, sol_path)
            print(f"Executed successfully: {sol_path.name}")
            successes.append(sol_path.name)
        except CellExecutionError as e:
            msg = f"Execution error in {sol_path.name}: {e}"
            print(msg)
            failures.append((sol_path.name, msg))
        except Exception as e:
            msg = f"Unexpected error executing {sol_path.name}: {e}"
            print(msg)
            failures.append((sol_path.name, msg))

    print("\nSummary:")
    print(f"  Success: {len(successes)}")
    for s in successes:
        print(f"   - {s}")
    print(f"  Failures: {len(failures)}")
    for name, msg in failures:
        print(f"   - {name}: {msg}")

    # Exit code reflects success/failure
    if failures:
        sys.exit(2)


if __name__ == '__main__':
    main()
