from datetime import date, timedelta
from decimal import Decimal as D
from re import sub as substitute
import re


def fallback(value, default):
    return value if is_set(value) else default


def is_set(value):
    return value != "" and value != ""


builtins = {
    "D": D,
    "date": date,
    "fallback": fallback,
    "is_set": is_set,
    "timedelta": timedelta,
    "re": re,
    "substitute": substitute,
}
