from setuptools import setup, find_packages
import os

version = '2.1.0'

tests_require = [
    'ftw.builder',
    'ftw.testing',
    'path.py',
    'plone.app.testing',
]

setup(name='ftw.publisher.receiver',
      version=version,
      description="Staging and publishing addon for Plone contents.",
      long_description=open("README.rst").read() + "\n" +
      open(os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
          'Framework :: Plone',
          'Framework :: Plone :: 4.3',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],

      keywords='ftw publisher receiver',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.publisher.receiver',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', 'ftw.publisher'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'setuptools',
          'ftw.publisher.core',
          'Plone',
      ],

      extras_require={
          'tests': tests_require,
          'PloneFormGen': ['Products.PloneFormGen'],
      },

      tests_require=tests_require,

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """)
