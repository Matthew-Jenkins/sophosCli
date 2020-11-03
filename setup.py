from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

long_description = 'Sophos Cli. Github is a private repo. Ping me to be added.'

setup(
    name='sophosCli',
    version='1.0.0',
    author='Matthew Jenkins',
    author_email='matt.jenkins@dataprise.com',
    url='https://github.com/Matthew-Jenkins/sophosCli',
    description='Cli for sophos.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sophosCli = sophosCli.sophosCli:main'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3.8",
        "License :: None :: Property of Dataprise",
        "Operating System :: OS Independent",
    ),
    keywords='sophos cli automation',
    install_requires=requirements,
    zip_safe=False
)
