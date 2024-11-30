# pwd : /Users/anggitrestu/code/ms-jarvis/chainable-llm

from setuptools import setup, find_packages

setup(
    name="chainable_llm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "anthropic>=0.3.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
        "structlog>=23.1.0",
    ],
    author="Anggit Restu",
    author_email="anggitrestu60@gmail.com",
    description="A chainable LLM framework for building AI applications",
    url="https://github.com/bot-brigade-studio/chainable-llm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
