import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pymaketool",
    version="2.0.1",
    author="Ericson Joseph",
    author_email="ericsonjoseph@gmail.com",
    description="Python Makefile Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    scripts = ['scripts/pymaketool', 'scripts/pymaketesting', 'scripts/pybuildanalyzer', 'scripts/pybuildanalyzer2', 'scripts/pymakedot'],
    url="https://github.com/ericsonj/pymaketool",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={'': ['*.glade']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
