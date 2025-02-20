coverage-run:
    coverage run -m pytest tests

coverage-xml:
    coverage xml

coverage-html:
    coverage html

coverage-report:
    coverage report

coverage-open:
    open htmlcov/index.html

coverage: coverage-run coverage-xml coverage-report

doc:
    mkdocs serve

doc-build:
    mkdocs build
