install:
	test -d `git rev-parse --show-toplevel`/.git && git pull || true
	( echo "try:"; echo "  import pyzfscmds"; echo "except ImportError:"; echo "  exit('Module pyzfscmds is not installed')" ) | python3.6
	python3.6 -m ensurepip
	cd `git rev-parse --show-toplevel` && python3.6 setup.py install

uninstall:
	python3.6 -m pip uninstall -y zedenv

help:
	@echo "    install"
	@echo "        Installs zedenv."
	@echo "    uninstall"
	@echo "        Removes zedenv."
