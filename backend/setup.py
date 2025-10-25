from setuptools import setup, find_packages

setup(
    name='backend',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'sqlalchemy==1.4.52',  # FIXED: Downgraded to match Airflow <2.0
        'psycopg2-binary==2.9.9',
        'requests==2.32.3',
        'tenacity==8.2.3',
        'pydantic==2.5.0',
        'pydantic-settings',  # For BaseSettings
        # Add others from requirements.txt if needed
    ],
)