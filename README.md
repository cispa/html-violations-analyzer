# HTML Violations Analyzer

This repository contains the code base used to measure security-relevant HTML violations on the web.
The results of this work can be found in the [IMC 2022 paper](https://swag.cispa.saarland/papers/hantke2022violations.pdf) "HTML Violations and Where to Find Them: A Longitudinal Analysis of Specification Violations in HTML."

## General

This tool leverages the [Common Crawl](https://commoncrawl.org/) (CC) project to analyze websites and validate their HTML content with pre-defined checks.
While we decided to base our work on CC, the program is easily expandable to work with other archives or sources (crawler modules).
All checks the tool performs are defined in the checker module, e.g., the correct number of body elements.
A user can easily extend the crawler with new checks.

## Setup

Before starting the tool, you must set up a data set and configure the tool accordingly.

### Install requirements.

```
pip install -r requirements.txt
```

### Generate a data set.

Before starting the checks, you must generate a data set to analyze. The format of the data set depends on the crawling module that is used. Since we based our research on the CC module, we describe how to generate a data set for CC.

If you use the `commonCrawlCrawler` module, the data set consists of one file with one JSON object per line. This JSON contains the information from which CC file and at which location the HTML content of an URL can be loaded. These information are call CC WARC file information and can be loaded via [AWS Athena](https://commoncrawl.org/2018/03/index-to-warc-files-and-urls-in-columnar-format/). See an example below.

```
{"urlkey": "com,github)/", "timestamp": "20200702224725", "url": "https://github.com/", "mime": "text/html", "mime-detected": "text/html", "status": "200", "digest": "H2FUTQEE5RLUDMETSE3FUSVCXCKWHXTV", "length": "36197", "offset": "333179634", "filename": "crawl-data/CC-MAIN-2020-29/segments/1593655880243.25/warc/CC-MAIN-20200702205206-20200702235206-00457.warc.gz", "languages": "eng", "encoding": "UTF-8"}
```

To receive the WARC file information from AWS Athena, we provide all scripts we used in [misc](misc).

### Set up a database.

To store the final results the program uses a database. We recommend to use [PostgreSQL](https://www.postgresql.org/) or the official [PostgreSQL Docker](https://hub.docker.com/_/postgres/) as database for this project. The following command starts a fresh database instance.

```
docker run -d \
	-e POSTGRES_USER=crawl_user \
	-e POSTGRES_PASSWORD=secret \
	-e POSTGRES_DB=checker_database \
	-e PGDATA=/var/lib/postgresql/data/pgdata \
	-v ./data:/var/lib/postgresql/data \
	postgres
```

Change the database URL in [database.py](database.py) to your database (e.g. `postgresql+psycopg2://crawl_user:secret@localhost/checker_database`).

### Adjust [config.yml](config.yml).

In the [config file](config.yml), you can configure the log output directory, the source the crawling modules takes as the base, and the rules the checker runs.

## Usage

To start the tool, run `main.py` and name the module you want to run.
```
python main.py --module common_crawl
```

## Misc

The [misc folder](misc) contains scripts we used to generate our data set using Common Crawl's AWS Athena database.


# License

Copyright 2022 Florian Hantke

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

