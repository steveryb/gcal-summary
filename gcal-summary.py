import argparse
import csv
import datetime
import math
import os
import os.path
import pickle
from collections import defaultdict
from enum import Enum
from typing import Dict, List, DefaultDict, Optional, Tuple

import iso8601
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GOOGLE_CALENDAR_CREDENTIALS_PATH = os.path.expanduser('~/credentials.json')
# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'


class RSVP(Enum):
    UNKNOWN = ""
    NEEDS_ACTION = "needsAction"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    ACCEPTED = "accepted"

    @staticmethod
    def api_value_to_enum(api_value: str):
        for rsvp in RSVP:
            if rsvp.value == api_value:
                return rsvp
        return RSVP.UNKNOWN


class CalendarEvent(object):
    def __init__(self, event_id: str, name: str, start: datetime.datetime, end: datetime.datetime,
                 attendees: List[Dict]):
        self.event_id: str = event_id
        self.name: str = name
        self.start: datetime.datetime = start
        self.end: datetime.datetime = end
        self.rsvps: Dict[str, RSVP] = {}
        for attendee in attendees:
            self.rsvps[attendee["email"]] = RSVP.api_value_to_enum(attendee["responseStatus"])

    @property
    def duration(self) -> int:
        """
        :return: the duration in minutes of the event
        """
        return (self.end - self.start).seconds // 60

    def __repr__(self):
        return f"<CalendarEvent(" \
               f"event_id={self.event_id}, " \
               f"name={self.name}, " \
               f"start={self.start}, " \
               f"end={self.end}, " \
               f"duration={self.duration}, " \
               f"rsvps={self.rsvps})>"


def get_calendar(start: datetime.datetime, end: datetime.datetime, credentials_path: str) -> List[CalendarEvent]:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    print("Starting to fetch google calendar events for", start, "to", end)
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    start_string = start.isoformat() + "Z"
    end_string = end.isoformat() + "Z"
    events_result = service.events().list(calendarId='primary',
                                          timeMin=start_string,
                                          timeMax=end_string,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    get_date = lambda e: e["dateTime"]
    has_date_time = lambda e: "dateTime" in e
    print("Finished fetching google calendar events")
    return [CalendarEvent(
        event_id=e["id"],
        name=e["summary"],
        start=iso8601.parse_date(get_date(e["start"])),
        end=iso8601.parse_date(get_date(e["end"])),
        attendees=e["attendees"] if "attendees" in e else [],
    ) for e in events if
        has_date_time(e["start"]) and has_date_time(e["end"])]


def get_midnight_on_day(day: datetime.date):
    return datetime.datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)


def day_to_google_cal_day(day: datetime.datetime):
    utc_now = datetime.datetime.utcnow()
    now = datetime.datetime.now()
    utc_correction = utc_now - now
    return get_midnight_on_day(day) + utc_correction


def get_calendar_events_for_period(start: datetime.datetime, end: datetime.datetime, credentials_path: str):
    return get_calendar(day_to_google_cal_day(start), day_to_google_cal_day(end), credentials_path)


def pick_from_list(options: List[str]) -> int:
    print("\n".join(f"{a}:{b}" for a, b in zip(range(1, len(options) + 1), options)))
    return get_int_input("", len(options) + 1) - 1


def get_int_input(msg: str, max_number: int = math.inf, min_number: int = 0) -> int:
    while True:
        try:
            user_input = int(input(msg))
            if min_number < user_input < max_number:
                return user_input
        except ValueError:
            pass
        print("Invalid input, try again")


def categorise_time(email: Optional[str],
                    categories: Optional[List[str]],
                    calendar_events: List[CalendarEvent]) -> List[Tuple[str, str, str]]:
    has_categories: bool = len(categories) > 1
    event_name_to_duration: DefaultDict = defaultdict(int)
    for event in calendar_events:
        if not email or (email in event.rsvps and event.rsvps[email] != RSVP.DECLINED):
            event_name_to_duration[event.name] += event.duration

    if has_categories:
        print("Categorising", len(event_name_to_duration), "events")

    categorised_events: List[Tuple[str, str, str]] = []
    for event_name, duration in event_name_to_duration.items():
        category = ""
        if has_categories:
            print("Category for:", event_name)
            category = categories[pick_from_list(categories)]
        categorised_events.append((event_name, category, str(duration)))

    return categorised_events


def write_categorised_events(path: str, lines=List[Tuple[str, str, str]],
                             header: Tuple[str, str, str]=("Event Name", "Category", "Duration")):
    print("Writing events to {}".format(path))
    with open(path, 'w') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL, )
        writer.writerow(header)

        for event_name, category, duration in lines:
            writer.writerow((event_name, category, duration))

description = \
"""
 

"""

if __name__ == "__main__":
    default_credentials_directory = "./credentials.json"
    default_categories = ""
    default_start_date = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    default_end_date = datetime.date.today().isoformat()
    default_output_path = "./calendar.csv"

    parser = argparse.ArgumentParser(
        description="A script that lets you summarize what is taking your time up in meetings")
    parser.add_argument("--email",
                        help="Your email address - used for filtering out events you responded no to." +
                             " Defaults to no filtering",
                        default=None)
    parser.add_argument("--credentials",
                        help="Path to your credentials file. Defaults to {}".format(default_credentials_directory),
                        default=default_credentials_directory)
    parser.add_argument("--categories",
                        help="CSV string list of what categories you want to categorise your entries into." +
                             " Defaults to no categories." +
                             " E.g. 'Important and Urgent, Urgent, Important, Neither'",
                        default=default_categories)
    parser.add_argument("--start",
                        help="ISO formatted date for the start of date range we're loading events from. " +
                             "Defaults to 7 days ago. E.g. {}".format(
                                 default_start_date),
                        default=default_start_date)
    parser.add_argument("--end",
                        help="ISO formatted date for the end of date range we're loading events from." +
                             " Defaults to today." +
                             " E.g. {}".format(
                                 default_end_date), default=default_end_date)

    parser.add_argument("--output",
                        help="Path to output the CSV summary to. " +
                             "Defaults to {}".format(default_output_path), default=default_output_path)

    args = parser.parse_args()

    start_time = get_midnight_on_day(datetime.date.fromisoformat(args.start))
    end_time = get_midnight_on_day(datetime.date.fromisoformat(args.end))
    events = get_calendar_events_for_period(start_time, end_time, args.credentials)
    lines = categorise_time(email=args.email, categories=args.categories.split(","), calendar_events=events)
    write_categorised_events(path=args.output, lines=lines)

