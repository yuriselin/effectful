import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="effectful",
    version="0.0.1",
    author="Yuri Selin",
    author_email="selin.gsoc@gmail.com",
    description="TODO",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yuriselin/effectful",
    project_urls={
        "Bug Tracker": "https://github.com/yuriselin/effectful/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
    install_requires = [
        'decorator',
        'toolz'
    ]
)
