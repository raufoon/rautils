from setuptools import setup, find_packages

setup(
    name='rautils',
    version='0.11',
    py_modules=['rautils'],
    description='A library containing utility functions for personal projects',
    packages=find_packages(), 
    install_requires=[
        'ipywidgets>=7.0.0',
        'jupyter-ui-poll',
        'lxml',
    ],
    python_requires='>=3.6', 
)
