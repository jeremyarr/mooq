.PHONY: docs
flake8:
	flake8 --ignore=E501,F401,E128,E402,E731,F821 mooq

package:
	rm -rf build dist .egg mooq.egg-info
	python setup.py release sdist bdist_wheel

publish:
	twine upload dist/*
	rm -rf build dist .egg mooq.egg-info

docs:
	cd docs && make html
	@echo -e "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"

