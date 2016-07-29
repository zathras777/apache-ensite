from setuptools import setup, find_packages
from os import path
from ensite import __version__
import io


here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with io.open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='apache-ensite',
    version=__version__,
    description='Apache 2 Configuration file management utilities',
    long_description=long_description,
    url='https://github.com/zathras777/apache-ensite',
    author='david reid',
    author_email='zathrasorama@gmail.com',
    license='Unlicense',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='apache freebsd configuration',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': ['a2ensite=ensite.ensite:a2ensite',
                            'a2dissite=ensite.ensite:a2dissite']
    },
)
