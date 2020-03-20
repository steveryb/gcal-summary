# gcal-summary
A script that lets you summarize what is taking your time up in meetings

## Installation Mac OS

The instructions for other OSes might be similar, but going to focus on Mac OS here, and using `pipenv` for package management.

1. Clone repo: `git clone git@github.com:steveryb/gcal-summary.git`
1. Install pipenv: `brew install pipenv`
1. Install packages: `cd gcal-summary; pipenv install`
1. Download the `configuration.json` file to get credentials to access google calendar from the [Python Quickstart in Google Calendar Python Guide](https://developers.google.com/calendar/quickstart/python), and put it in the `gcal-summary` directory.

## Running the script
1. Open a pipenv shell: `pipenv shell`
2. Run the script: `python python gcal-summary.py`

Output will be in `calendar.csv` and look like:
```csv
"Event Name","Category","Duration"
"Standup","4","90"
"Think about thinking","2","360"
"Ponder my 401k","3","30"
```

By default, this will output a CSV of meetings in the past week. Some more options:

```
> python gcal-summary.py --help
usage: gcal-summary.py [-h] [--email EMAIL] [--credentials CREDENTIALS]
                       [--categories CATEGORIES] [--start START] [--end END]
                       [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --email EMAIL         Your email address - used for filtering out events you
                        responded no to. Defaults to no filtering
  --credentials CREDENTIALS
                        Path to your credentials file. Defaults to
                        ./credentials.json
  --categories CATEGORIES
                        CSV string list of what categories you want to
                        categorise your entries into. Defaults to no
                        categories. E.g. 'Important and Urgent, Urgent,
                        Important, Neither'
  --start START         ISO formatted date for the start of date range we're
                        loading events from. Defaults to 7 days ago. E.g.
                        2020-03-11
  --end END             ISO formatted date for the end of date range we're
                        loading events from. Defaults to today. E.g.
                        2020-03-18
  --output OUTPUT       Path to output the CSV
```

## Examples:


Output all events from the past week to calendar.csv
```shell script
> python gcal-summary.py  
```

Filter out events that only myname@gmail.com didn't RSVP no to
```shell script
> python gcal-summary.py --email myname@gmail.com  
```

Go through each event and categorize it into a category
```shell script
> python gcal-summary.py --categories "Important and Urgent, Urgent, Important, Neither"
```

Only look at events between these two dates
```shell script
> python gcal-summary.py --start 2020-03-11 --end 2020-03-18 
```

Example of most of the arguments
```shell script
> python gcal-summary.py --email myname@gmail.com --start=2020-03-01 --end=2020-03-15 --output=whoops.csv --credentials=./credentials.json1 --categories=1,2,3,4
```
