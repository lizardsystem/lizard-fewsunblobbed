from setuptools import setup
import os.path

version = '1.25'

long_description = '\n\n'.join([
    open('README.txt').read(),
    open(os.path.join('lizard_fewsunblobbed', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django',
    'django-compositepk',
    'django-extensions',
    'django-extensions',
    'django-nose',
    'django-staticfiles',
    'django-treebeard >= 1.61',
    'lizard-map >= 3.3',
    'lizard-ui >= 3.6',
    ],

tests_require = [
    ]

setup(name='lizard-fewsunblobbed',
      version=version,
      description=("Lizard-map plugin for showing FEWS data from a " +
                   "so-called 'unblobbed' database"),
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='Jack Ha',
      author_email='jack.ha@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['lizard_fewsunblobbed'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      entry_points={
          'console_scripts': [
          ],
          'lizard_map.adapter_class': [
            'adapter_fews = lizard_fewsunblobbed.layers:WorkspaceItemAdapterFewsUnblobbed',
            ],
          },
      )
