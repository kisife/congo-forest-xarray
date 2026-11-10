"""Execute both portfolio notebooks in place from the repository root."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook, timeout=600, kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    nbformat.write(notebook, path)
    print(f"Executed {path.relative_to(ROOT)}")
