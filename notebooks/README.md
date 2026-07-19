# Quickstart notebook

`biophys_interop_quickstart.ipynb` — a 5-minute, runnable tour of the toolkit.

## Run it

- **Google Colab (no install):** open it from the public repository URL and choose *Runtime → Run all*. The first
  cell installs the package directly from GitHub.
- **Locally:** `pip install "biophys_interop[batch] @ git+https://github.com/xingaobio/biophys_interop.git"`, then
  open the notebook in Jupyter and run all.

## Open in Colab

```markdown
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xingaobio/biophys_interop/blob/master/notebooks/biophys_interop_quickstart.ipynb)
```

The notebook ships with its cell outputs already populated, so it reads correctly even before you run it. The batch
cell downloads a 200-row demo CSV from the repo (`examples/demo_input.csv`).
