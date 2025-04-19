from setuptools import setup, find_packages

setup(
    name="wa-business-agent",
    version="0.1.0",
    description="AI-powered Washington State business advisor",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.0",
        "uvicorn==0.27.0",
        "pydantic==2.5.3",
        "python-dotenv==1.0.0",
        "openai==1.75.0",
        "semantic-kernel==1.28.1",
        "azure-identity==1.15.0",
        "azure-search-documents==11.4.0",
        "requests==2.31.0",
        "beautifulsoup4==4.12.0",
        "lxml==5.1.0",
        "cachetools==5.3.0",
        "jinja2==3.1.2",
    ],
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest==7.4.4",
        ],
    },
) 