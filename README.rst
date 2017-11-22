.. image:: https://travis-ci.com/johnramsden/zedenv.svg?token=4X1vWwTyHTHCUwBTudyN&branch=master
    :target: https://travis-ci.com/johnramsden/zedenv

zedenv
======

ZFS boot environment manager


Testing
-------

To test using pytest, run it from the tests directory with a zfs dataset.::
    pytest --root-dataset="zpool/ROOT/default"

To test coverage run pytest wuth the pytest-cov plugin.

pytest --root-dataset="zpool/ROOT/default" --cov=zedenv
