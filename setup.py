import os, re
from setuptools import setup, find_packages

# Read __version__.py for version information
def read_version():
    with open(os.path.join("br_mongodb_orm", "__version__.py")) as f:
        content = f.read()
    match = re.search(r'__version__ = ["\'](.+)["\']', content)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")

# Read README file for long description
try:
    with open('README.md', 'r', encoding='utf-8') as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = 'ORM for creating a structured MongoDB model with ease.'

setup(
    name='br_mongodb_orm',
    version=read_version(),
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pydantic>=2.8.2',
        'motor>=3.5.1',
        'pymongo>=4.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=5.0.0',
            'mypy>=1.0.0',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
        ],
    },
    entry_points={
        'console_scripts': []
    },
    author='Aasif Rahman M',
    author_email='asifrahman15@gmail.com',
    description='Modern async MongoDB ORM for Python with Pydantic integration.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/asifrahman15/br_mongodb_orm',
    project_urls={
        'Bug Reports': 'https://github.com/asifrahman15/br_mongodb_orm/issues',
        'Source': 'https://github.com/asifrahman15/br_mongodb_orm',
        'Documentation': 'https://github.com/asifrahman15/br_mongodb_orm#readme',
    },
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: AsyncIO',
    ],
    keywords='mongodb orm async motor pydantic database nosql',
)
