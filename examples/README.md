# Running Examples
Examples are provided in two ways:
1. Jupyter notebooks.  These are provided with inline comments, somewhat as a user guide. Make sure you have run `poetry install`, which will install jupyter as a development dependency.  You can then launch the jupyter server with: `poetry run jupyter notebook`
1. Scripts - run and enter into scripts interactively: `poetry run python -i examples/scripts/templates-01.py`

_Note: Since Tasty uses some class methods and variables, make sure to restart your Jupyter Python kernel to clear out instances if you are getting unexpected results_
