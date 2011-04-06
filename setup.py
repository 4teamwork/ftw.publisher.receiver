from setuptools import setup, find_packages
import os

version = open(os.path.join('ftw', 'publisher', 'receiver',
                            'version.txt')).read().strip()
maintainer = 'Jonas Baumann'

tests_require=[
    'collective.testcaselayer',
    ]

setup(name='ftw.publisher.receiver',
      version=version,
      description="Staging and publishing addon for Plone contents.",
      long_description=open("README.rst").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),

      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],

      keywords='ftw publisher receiver',
      author='%s, 4teamwork GmbH' % maintainer,
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.publisher.core',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', 'ftw.publisher'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'setuptools',
        'ftw.publisher.core',
        ],

      extras_require={
        'tests': tests_require,
        'PloneFormGen': ['Products.PloneFormGen'],
        'python2.4': ['simplejson']
        },

      tests_require=tests_require,

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
