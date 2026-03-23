from setuptools import setup, find_packages

setup(
    name="doc-gen",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "click>=8.1",
        "pydantic>=2.0",
        "pyyaml>=6.0",
        "httpx>=0.25",
    ],
    entry_points={
        "console_scripts": [
            "doc-gen=doc_gen.cli.main:cli",
        ],
    },
    python_requires=">=3.9",
)
