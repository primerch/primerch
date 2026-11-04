"""Collect only public-profile calendar aggregates, including anonymous private work."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LOGIN = 'primerch'


def query_github(token, query):
    request = Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': LOGIN}}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'User-Agent': 'primerch-anonymous-activity'},
    )
    with urlopen(request, timeout=45) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError('Unable to read public-profile contribution aggregates')
    return result['data']['user']


def validate_activity(activity):
    expected = {'schemaVersion', 'asOf', 'lifetimeContributions', 'lastYearContributions', 'anonymousPrivateLastYear', 'days'}
    if set(activity) != expected or activity['schemaVersion'] != 1:
        raise ValueError('Activity output must contain only the approved anonymous aggregate schema')
    for key in ('lifetimeContributions', 'lastYearContributions', 'anonymousPrivateLastYear'):
        if type(activity[key]) is not int or activity[key] < 0:
            raise ValueError('Contribution totals must be nonnegative integers')
    if not activity['anonymousPrivateLastYear'] <= activity['lastYearContributions'] <= activity['lifetimeContributions']:
        raise ValueError('Contribution totals use inconsistent scopes')
    datetime.fromisoformat(activity['asOf'])
    dates = set()
    for item in activity['days']:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError('Calendar entries may contain only a date and count')
        day, count = item
        datetime.strptime(day, '%Y-%m-%d')
        if day in dates or type(count) is not int or count < 0:
            raise ValueError('Invalid or repeated calendar entry')
        dates.add(day)


def collect(token):
    user = query_github(token, '''query($login:String!) {
      user(login:$login) { contributionsCollection {
        contributionYears restrictedContributionsCount
        contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
      } }
    }''')
    collection = user['contributionsCollection']
    years = collection['contributionYears']
    fields = '\n'.join(
        f'y{year}: contributionsCollection(from:"{year}-01-01T00:00:00Z",to:"{year}-12-31T23:59:59Z") {{ contributionCalendar {{ totalContributions }} }}'
        for year in years
    )
    history = query_github(token, 'query($login:String!) { user(login:$login) {' + fields + '} }')
    activity = {
        'schemaVersion': 1,
        'asOf': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'lifetimeContributions': sum(history[f'y{year}']['contributionCalendar']['totalContributions'] for year in years),
        'lastYearContributions': collection['contributionCalendar']['totalContributions'],
        'anonymousPrivateLastYear': collection['restrictedContributionsCount'],
        'days': [[day['date'], day['contributionCount']] for week in collection['contributionCalendar']['weeks'] for day in week['contributionDays']],
    }
    validate_activity(activity)
    return activity


if __name__ == '__main__':
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        raise SystemExit('A GitHub workflow token is required')
    activity = collect(token)
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/activity.json').write_text(json.dumps(activity, indent=2) + '\n')
    print(f"Anonymous activity verified: {activity['lifetimeContributions']:,} lifetime; {activity['anonymousPrivateLastYear']:,} private in the past year")
