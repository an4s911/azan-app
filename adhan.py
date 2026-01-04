import json
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

import requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load cities from json file
CITIES_FILE_PATH = "cities.json"

if not os.path.exists(CITIES_FILE_PATH):
    print(f"Error: {CITIES_FILE_PATH} not found.")
    exit(1)

with open(CITIES_FILE_PATH, "r") as f:
    try:
        my_cities = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode {CITIES_FILE_PATH}.")
        exit(1)

API_URL = "https://api.aladhan.com/v1/timingsByCity"


PRAYERS = [
    "Fajr",
    "Sunrise",
    "Dhuhr",
    "Asr",
    "Maghrib",
    "Isha",
]

PRAYER_TIMES_FILE_PATH = "/tmp/prayer_times.json"


# params = tomorrow: bool and **kwargs
def get_url(tomorrow=False, **kwargs):
    if tomorrow:
        dateStr = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    else:
        dateStr = datetime.now().strftime("%d-%m-%Y")

    url_params = []

    # Format kwargs to add to url
    for key, value in kwargs.items():
        if key == "tune":
            value = "0,0,0,0,0,0,0,0,0"

        url_params.append(f"{key}={quote(str(value), safe='')}")

    return f"{API_URL}/{dateStr}?{'&'.join(url_params)}"


def get_prayer_times(city_index=0):
    # For aligning prayer times to be more accurate
    additional_minutes = my_cities[city_index].get("tune", {})

    # Ensure file exists
    if not os.path.exists(PRAYER_TIMES_FILE_PATH):
        with open(PRAYER_TIMES_FILE_PATH, "w") as f:
            json.dump([], f)

    with open(PRAYER_TIMES_FILE_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    today_str_api = datetime.now().strftime("%d-%m-%Y")

    today_data = None
    for entry in data:
        # API returns date like "01-01-2025" in data.date.gregorian.date
        # We stored the whole 'data' object from api response
        try:
            if entry["date"]["gregorian"]["date"] == today_str_api:
                today_data = entry
                break
        except KeyError:
            continue

    if not today_data:
        try:
            url = get_url(**my_cities[city_index])
            response = requests.get(url)
            response.raise_for_status()
            api_response = response.json()

            if api_response["code"] == 200:
                today_data = api_response["data"]
                data.append(today_data)

                with open(PRAYER_TIMES_FILE_PATH, "w") as f:
                    json.dump(data, f, indent=2)
            else:
                print(f"API Error: {api_response['status']}")
                return None

        except Exception as e:
            print(f"Network error or api error: {e}")
            return None

    if not today_data:
        return None

    prayer_times = {}
    timings = today_data["timings"]
    # Timings format is HH:MM (e.g. "06:03")

    # We need a date component for datetime objects.
    # Use today's date from system or from the entry?
    # The existing logic used datetime.now() mostly for comparison.
    # We'll use the date from the entry to be safe or just today's date.
    # The script compares with datetime.now() later, so using current date is aligned.

    date_str = datetime.now().strftime("%Y-%m-%d")

    for prayer in PRAYERS:
        # Use only HH:MM part if there's timezone etc, though example shows just HH:MM
        time_str = timings[prayer].split(" ")[0]
        prayer_times[prayer] = datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
        ) + timedelta(minutes=int(additional_minutes.get(prayer, 0)))

    return prayer_times, today_data["date"]["hijri"]


def print_string_array_in_length(string_array, length, filler="-"):
    """
    Print all items in string_array on one line,
    padding each with filler characters so that each block (string + filler)
    has total width == length, except the last string which is printed as is.
    """
    for idx, s in enumerate(string_array):
        # print the string itself
        print(s, end=" ")
        # if not the last item, compute and print filler to pad to `length`
        if idx < len(string_array) - 1:
            gap = length - len(s)
            if gap > 0:
                # repeat the filler enough times and truncate to exactly `gap`
                seg = (filler * ((gap // len(filler)) + 1))[:gap]
                print(seg, end=" ")
    print()


if __name__ == "__main__":
    # Get city index from command line argument
    city_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    result = get_prayer_times(city_index)

    if not result:
        exit()

    prayer_times, hijri_data = result

    for i in range(len(PRAYERS) - 1):
        prev = prayer_times[PRAYERS[i]]  # previous prayer time
        next = prayer_times[PRAYERS[i + 1]]  # next prayer time
        if prev < datetime.now() < next:
            next_prayer = PRAYERS[i + 1]
            break
    #
    else:
        next_prayer = PRAYERS[0]

    difference_in_minutes = int(
        ((prayer_times[next_prayer] - datetime.now()).seconds) / 60
    )
    hours, sub_minutes = divmod(difference_in_minutes, 60)
    sub_seconds = (prayer_times[next_prayer] - datetime.now()).seconds % 60

    next_prayers_time_formatted = prayer_times[next_prayer].strftime("%H:%M")
    print(f"{next_prayer}: {next_prayers_time_formatted}")
    print(
        f"Time Remaing: {f"{hours:02}:" if hours > 0 else ''}{
            sub_minutes:02}:{sub_seconds:02}"
    )
    print()
    for prayer in PRAYERS:
        # print(f"{prayer} ----- \t{prayer_times[prayer].strftime('%H:%M')}")
        print_string_array_in_length(
            [f"{prayer}", f"{prayer_times[prayer].strftime('%H:%M')}"],
            13,
        )

    # Print Hijri Date
    day = hijri_data["day"]
    month_en = hijri_data["month"]["en"]
    month_num = str(hijri_data["month"]["number"])
    year = hijri_data["year"]
    print(f"\n{day} {month_en} ({month_num}) {year}")
