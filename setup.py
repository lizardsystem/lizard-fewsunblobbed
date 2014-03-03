from setuptools import setup
import os.path

version = '2.5.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('USAGE.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django',
    'django-compositepk',
    'django-extensions',
    'django-nose',
    'django-staticfiles',
    'django-treebeard >= 1.61',
    'lizard-map >= 4.0a1',
    'lizard-security',
    'lizard-ui >= 4.0a1',
    'lizard-task',
    'South',
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
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
          ],
          'lizard_map.adapter_class': [
            ('adapter_fews = lizard_fewsunblobbed.layers:' +
             'WorkspaceItemAdapterFewsUnblobbed'),
            ],
          },
      )
