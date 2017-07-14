import sys
from ext import ShellApi
import argparse


parser = argparse.ArgumentParser(description="""
Proccess API Search from Keywords stored in keywords.json.
""")
parser.add_argument(
    '--keywords',
    help="Look this keywords object in keywords.json. Default=keywords",
    default='keywords')
parser.add_argument(
    '--until',
    help="Define the max date to search. Default None",
    default=None)
parser.add_argument(
    '--limit',
    help="Limit of returned tweets / 100. Default 10, will return 1000 tweets",
    default=10)
parser.add_argument(
    '--method',
    help="Specify wich methods and parameters should be used.\nDefault: search.\nAvailable: search, timeline",
    default='search')
args = parser.parse_args()
print(args)

api = ShellApi(args.keywords)
api.searchkeywords(until=args.until, limit=args.limit, method=args.method)
