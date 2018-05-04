import pkg_resources


# Import plugins
def get_plugins():
    # https://packaging.python.org/guides/packaging-namespace-packages/
    # https://packaging.python.org/guides/creating-and-discovering-plugins/

    plugins = dict()

    for entry_point in pkg_resources.iter_entry_points('zedenv.plugins'):
        plugins[entry_point.name] = entry_point.load()

    return plugins
