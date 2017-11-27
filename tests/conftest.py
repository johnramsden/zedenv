import pytest


def pytest_addoption(parser):
    parser.addoption("--root-dataset", action="store", default=None,
                     help="Specify a root dataset to use.")


def pytest_runtest_setup(item):
    if 'require_root_dataset' in item.keywords and not item.config.getvalue("root_dataset"):
        pytest.skip("Need --root-dataset option to run")


@pytest.fixture
def root_dataset(request):
    """Specify a root dataset to use."""
    return request.config.getoption("--root-dataset")
