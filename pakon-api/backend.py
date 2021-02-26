from utils import Parser
from _cli import _run_show

def fetch_data():
    return Parser.csv_to_json(_run_show())
