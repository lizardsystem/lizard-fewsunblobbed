from setuptools import setup
import os.path

version = '0.4dev'

long_description = '\n\n'.join([
    open('README.txt').read(),
    open(os.path.join('lizard_fewsunblobbed', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django',
    'django-staticfiles',
    'django-compositepk',
    'django-treebeard',
    'lizard-map',
    ],

tests_require = [
    ]

setup(name='lizard-fewsunblobbed',
      version=version,
      description="TODO",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='TODO',
      author_email='TODO@nelen-schuurmans.nl',
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
          'lizard_map.layer_method': [
            'fews_points_layer = lizard_fewsunblobbed.layers:fews_points_layer',
            ],
          'lizard_map.search_method': [
            'fews_points_layer = lizard_fewsunblobbed.layers:fews_points_layer_search',
            ],
          },
      )
