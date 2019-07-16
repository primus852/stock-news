import setuptools


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(name='stocknews',
                 version='0.9.11',
                 description='PoC for scraping Yahoo News with sentiment analysis',
                 url='http://github.com/primus852/stock-news.git',
                 author='Torsten Wolter',
                 long_description=readme(),
                 keywords='sentiment news rss stock',
                 long_description_content_type="text/markdown",
                 author_email='tow.berlin@gmail.com',
                 packages=setuptools.find_packages(),
                 classifiers=[
                     'Development Status :: 4 - Beta',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python :: 3.6',
                     'Topic :: Text Processing :: Linguistic',
                 ],
                 license='MIT',
                 include_package_data=True,
                 install_requires=[
                     'pandas',
                     'feedparser',
                     'nltk',
                     'requests',
                     'numpy'
                 ],
                 zip_safe=False,
                 test_suite='nose.collector',
                 tests_require=['nose'],
                 )
