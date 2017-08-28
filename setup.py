from distutils.core import setup

setup(
    name='Faretricks',
    version='',
    packages=['faretricks'],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    install_requires=['requests', 'retrying', 'beautifulsoup4', 'html5lib'],
    entry_points={
        'console_scripts': ['faretricks=faretricks.cli:main'],
    }
)
