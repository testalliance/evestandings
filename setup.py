#!/usr/bin/env python
 
from distutils.core import setup
from standings import __version__
 
setup(name = "standings",
    version = __version__,
    description = "EVE API Standings Page Generator",
    author = "Andrew Willaims",
    author_email = "andy@tensixtyone.com",
    url = "https://dev.pleaseignore.com/",
    keywords = "eveapi",
    packages = ['standings',],
    scripts = ['scripts/evestandings'],
    package_data={'standings': ['templates/*.html']},

    classifiers = [
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
    ]
)
