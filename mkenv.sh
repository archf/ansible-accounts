rm -rf env filter_plugins.egg-info

# create env
virtualenv --system-site-packages -p /usr/bin/python env

# activate
source env/bin/activate

unalias python
unalias pip

# install current package
\pip install -e .

# install pytest
\pip install pytest
