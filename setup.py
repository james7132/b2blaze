import setuptools

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='aiob2',
    version='0.1.0',
    author='James Liu',
    author_email='contact@jamessliu.com',
    description='A asyncio Backblaze B2 client.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/james7132/aiob2',
    packages=setuptools.find_packages(),
    keywords='asyncio backblaze b2 cloud storage',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        'Topic :: Software Development :: Libraries',
        "Operating System :: OS Independent",
    ],
    license='MIT'
)
