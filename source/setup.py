# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import setuptools

try:
    with open("../README.md") as fp:
        long_description = fp.read()
except IOError as e:
    long_description = ''

setuptools.setup(
    name="sql-based-etl",
    version="2.0.0",

    description="A CDK v2 Python app for SQL-based ETL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="meloyang",

    package_dir={"": "./"},
    packages=setuptools.find_packages(where="./"),

    install_requires=[
        "aws-cdk-lib==2.105.0",
        "aws-cdk.lambda-layer-kubectl-v27==2.1.0",
        "constructs>=10.0.0,<11.0.0",
        "pyyaml==5.4"
    ],

    python_requires=">=3.7",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",   
         
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
