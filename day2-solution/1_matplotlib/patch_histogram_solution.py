#!/usr/bin/env python3
"""Patch matplotlib_05_histogram_solution.ipynb to fill exercise cells and define df.
"""
from __future__ import annotations
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

nb_path = Path(__file__).parent / 'matplotlib_05_histogram_solution.ipynb'

nb = nbformat.read(nb_path, as_version=4)

# Helper to find cells by marker content
def find_cells_with_marker(nb, marker: str):
    idxs = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code' and marker in ''.join(cell.source):
            idxs.append(i)
    return idxs

marker = '## Insérez votre code ici'
indices = find_cells_with_marker(nb, marker)

# There should be 3 such code cells in this notebook
# Fill them with appropriate solutions
solutions = []

# 1) Random choice histogram
solutions.append(
    """
# Générer 40 nombres aléatoires entre 0 et 10
x = np.random.choice(np.arange(0, 11), size=40, replace=True)
plt.figure(figsize=(10,6))
plt.hist(x, bins=7, rwidth=0.8, color='orange')
plt.title("Histogramme de valeurs aléatoires")
plt.xlabel("Valeurs")
plt.ylabel("Fréquences")
plt.show()
""".strip()
)

# 2) Horizontal histogram with density
solutions.append(
    """
x = [1, 2, 2, 3, 4, 4, 4, 4, 4, 5, 5]
plt.figure(figsize=(10,6))
plt.hist(x, bins=5, range=(1,6), rwidth=0.6, color="#EE3459", orientation='horizontal', density=True)
plt.xlabel('fréquences')
plt.ylabel('valeurs')
plt.title('Histogramme horizontal')
plt.show()
""".strip()
)

# 3) Read CSV and two series histograms (side-by-side and stacked)
solutions.append(
    """
# Lecture du fichier CSV et histogrammes pour Product1 et Product2
df = pd.read_csv('sales_data.csv')
plt.figure(figsize=(10,6))
plt.hist([df['Product1'], df['Product2']], bins=6, color=['#f27750', '#f7bf59'], label=['Product1', 'Product2'])
plt.title('Histogramme 2 series')
plt.xlabel('Ventes')
plt.ylabel('Fréquences')
plt.legend()
plt.show()

plt.figure(figsize=(10,6))
plt.hist([df['Product1'], df['Product2']], bins=6, color=['#961939', '#193996'], label=['Product1', 'Product2'], rwidth=0.8, histtype='barstacked')
plt.title('2 series superposées')
plt.xlabel('Ventes')
plt.ylabel('Frequences')
plt.legend()
plt.show()
""".strip()
)

if len(indices) >= 3:
    for i, code in zip(indices[:3], solutions):
        nb.cells[i].source = code
else:
    # Fallback: append new cells with solutions at the end
    for code in solutions:
        nb.cells.append(nbformat.v4.new_code_cell(code))

nbformat.write(nb, nb_path)

# Execute to verify
ep = ExecutePreprocessor(timeout=300, kernel_name='python3')
ep.preprocess(nb, {'metadata': {'path': str(nb_path.parent)}})
nbformat.write(nb, nb_path)
print("Patched and executed successfully:", nb_path.name)
