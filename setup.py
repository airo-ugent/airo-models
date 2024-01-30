import setuptools
from setuptools import find_packages

setuptools.setup(
    name="airo-models",
    version="0.0.1",
    author="Andreas Verleysen",
    author_email="andreas.verleysen@ugent.be",
    description="TODO",
    install_requires=[
        "numpy",
    ],
    packages=find_packages(),
    include_package_data=True,  # Without this URDFs & meshes are not included in non-editable pip install
)
