# SVEx Crawler

This software lists all TSV threads currently open on [r/SVExchange](https://reddit.com/r/SVExchange).
The code is run every three hours and the results are pushed to the `gh-pages` branch.
They are available [here](https://cu3po42.github.io/SVEx-Crawler/tsvs.json).

If you want to run it yourself, create a 'script' application on Reddit, accept the API terms and set the environment variables `CLIENT_ID` and `CLIENT_SECRET`.
Install dependencies with `pip install -r requirements.txt` before running `crawl.py`.