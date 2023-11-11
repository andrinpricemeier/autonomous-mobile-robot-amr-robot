import nox

nox.options.sessions = "lint", "tests", "mypy", "black"


@nox.session(python=["3.6.9"])
def tests(session):
    session.run("pytest", "--cov", "tests", external=True)


@nox.session(python=["3.6.9"])
def lint(session):
    args = session.posargs
    session.run("flake8", *args, external=True)


@nox.session(python="3.6.9")
def black(session):
    args = session.posargs
    session.run("black", *args, external=True)


@nox.session(python="3.6.9")
def mypy(session) -> None:
    args = session.posargs
    session.run("mypy", ".", external=True)
