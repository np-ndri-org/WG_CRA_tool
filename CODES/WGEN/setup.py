import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="WGEN",
    version="0.1.0",
    author="Dibesh Shrestha",
    author_email="dibeshshrestha@live.com",
    py_modules= ['wg'],
    description="Weather Generator for Climate Risk Assessment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
