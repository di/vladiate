BINDIR = $(PWD)/.state/env/bin

test: .state/env/pyvenv.cfg
	$(BINDIR)/coverage run --source=vladiate setup.py test
	$(BINDIR)/coverage report -m

lint: .state/env/pyvenv.cfg
	$(BINDIR)/flake8 .

.state/env/pyvenv.cfg:
	# Create our Python 3.5 virtual environment
	rm -rf .state/env
	python3.5 -m venv .state/env

	# install/upgrade general requirements
	.state/env/bin/python -m pip install --upgrade pip setuptools wheel

	# install various types of requirements
	.state/env/bin/python -m pip install coverage
	.state/env/bin/python -m pip install flake8
