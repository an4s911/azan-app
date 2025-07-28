import csv
import os
import re
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(".env")

city_id = os.getenv("CITY_ID")

# For details on how to get this link for your city, see
# https://support.muslimpro.com/hc/en-us/articles/202886274-How-do-I-add-Muslim-Pro-prayer-times-on-my-own-web-page
URL = f"https://prayer-times.muslimpro.com/muslimprowidget.js?cityid={city_id}"

PRAYERS = [
    "Fajr",
    "Sunrise",
    "Dhuhr",
    "Asr",
    "Maghrib",
    "Isha",
]

PRAYER_TIMES_FILE_PATH = "/tmp/prayer_times.csv"

try:
    open(PRAYER_TIMES_FILE_PATH, "r").close()
except FileNotFoundError:
    with open(PRAYER_TIMES_FILE_PATH, "w") as prayer_times_file:
        prayer_times_file.write("Date," + ",".join(PRAYERS) + "\n")


def get_and_store_prayer_times():
    try:
        # Fetch the JavaScript response
        response = requests.get(URL)
        response.raise_for_status()
    except Exception:
        print("No network!")
        return None
    else:
        content = response.text

        # Regex pattern to extract prayer names and times

        # 24 hours format
        # prayer_pattern = re.compile(r"<td>(.*?)</td><td>(\d{2}:\d{2})</td>")

        # 12 hours format (with AM/PM)
        # prayer_pattern = re.compile(r"<td>(.*?)</td><td>(\d{2}:\d{2} AM)</td>")

        prayer_pattern = re.compile(
            r"<td>(.*?)</td><td>((?:0[1-9]|1[0-2]):[0-5][0-9]\s?(?:AM|PM))</td>",
            re.IGNORECASE,
        )

        prayer_times = prayer_pattern.findall(content)

        prayer_times_dict = {}
        prayer_times_dict["Date"] = datetime.today().strftime("%Y-%m-%d")

        for prayer, time in prayer_times:
            if prayer.startswith("Isha"):
                prayer = "Isha"
            if prayer in PRAYERS:
                t = time.strip()
                # decide format based on presence of AM/PM
                if t.upper().endswith(("AM", "PM")):
                    fmt = "%I:%M %p"
                else:
                    fmt = "%H:%M"
                # parse then re‑format to HH:MM
                dt = datetime.strptime(t, fmt)
                prayer_times_dict[prayer] = dt.strftime("%H:%M")

        with open(PRAYER_TIMES_FILE_PATH, "a") as prayer_times_file:
            csv_writer = csv.writer(prayer_times_file)
            row = (
                prayer_times_dict.values()
            )  # In order: Date, Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha
            csv_writer.writerow(row)

        loc_pattern = re.compile(
            r"/Prayer-times-([A-Za-z0-9\-]+)-([A-Za-z0-9\-]+)-\d+", re.IGNORECASE
        )

        loc = loc_pattern.search(content)
        if loc:
            city = loc.group(1).replace("-", " ")
            country = loc.group(2).replace("-", " ")
            print(city, country)

        return prayer_times_dict


def get_prayer_times():
    # For aligning prayer times to be more accurate
    additonal_minutes = {
        "Fajr": 2,
        "Sunrise": 0,
        "Dhuhr": 1,
        "Asr": 1,
        "Maghrib": 2,
        "Isha": 2,
    }

    with open(PRAYER_TIMES_FILE_PATH, "r") as prayer_times_file:
        csv_reader = csv.DictReader(prayer_times_file)

        for line in csv_reader:
            pass

        try:
            last_line = line
        except UnboundLocalError:
            last_line = get_and_store_prayer_times()

        last_prayer_date = datetime.strptime(last_line["Date"], "%Y-%m-%d").date()
        if datetime.today().date() > last_prayer_date:
            last_line = get_and_store_prayer_times()

        prayer_times = {}
        for prayer in PRAYERS:
            prayer_times[prayer] = datetime.strptime(
                f"{last_line['Date']} {last_line[prayer]}", "%Y-%m-%d %H:%M"
            ) + timedelta(minutes=additonal_minutes[prayer])

        return prayer_times


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
    prayer_times = get_prayer_times()

    if not prayer_times:
        exit()

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
