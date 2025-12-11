from setuptools import setup, find_packages

setup(
    name="audit-client",
    version="1.0.0",
    description="Client library for the audit logging service",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
    ],
    python_requires=">=3.11",
)
