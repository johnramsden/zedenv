import pytest


def pytest_addoption(parser):
    parser.addoption("--root-dataset", action="store", default=None,
                     help="Specify a root dataset to use.")

    parser.addoption("--zpool", action="store", default=None,
                     help="Specify a pool to use.")


def pytest_runtest_setup(item):
    if 'require_root_dataset' in item.keywords and not item.config.getvalue("root_dataset"):
        pytest.skip("Need --root-dataset option to run")

    if 'require_zpool' in item.keywords and not item.config.getoption("--zpool"):
        pytest.skip("Need --zpool option to run")


@pytest.fixture
def root_dataset(request):
    """Specify a root dataset to use."""
    return request.config.getoption("--root-dataset")


@pytest.fixture
def zpool(request):
    """Specify a root dataset to use."""
    return request.config.getoption("--zpool")
