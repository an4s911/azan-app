import csv
import os
import re
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

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
    else:
        content = response.text

        # Regex pattern to extract prayer names and times
        prayer_pattern = re.compile(r"<td>(.*?)</td><td>(\d{2}:\d{2})</td>")
        prayer_times = prayer_pattern.findall(content)

        prayer_times_dict = {}
        prayer_times_dict["Date"] = datetime.today().strftime("%Y-%m-%d")

        for prayer, time in prayer_times:
            if prayer.startswith("Isha"):
                prayer = "Isha"
            if prayer in PRAYERS:
                prayer_times_dict[prayer] = time

        with open(PRAYER_TIMES_FILE_PATH, "a") as prayer_times_file:
            csv_writer = csv.writer(prayer_times_file)
            row = (
                prayer_times_dict.values()
            )  # In order: Date, Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha
            csv_writer.writerow(row)

        return prayer_times_dict


def get_prayer_times():
    # For aligning prayer times to be more accurate
    additonal_minutes = {
        "Fajr": 2,
        "Sunrise": 2,
        "Dhuhr": 2,
        "Asr": 1,
        "Maghrib": 1,
        "Isha": 1,
    }

    with open(PRAYER_TIMES_FILE_PATH, "r") as prayer_times_file:
        csv_reader = csv.DictReader(prayer_times_file)

        for line in csv_reader:
            pass

        try:
            last_line = line
        except UnboundLocalError:
            last_line = get_and_store_prayer_times()

        prayer_times = {}
        for prayer in PRAYERS:
            prayer_times[prayer] = datetime.strptime(
                f"{last_line['Date']} {last_line[prayer]}", "%Y-%m-%d %H:%M"
            ) + timedelta(minutes=additonal_minutes[prayer])

        last_prayer_date = datetime.strptime(last_line["Date"], "%Y-%m-%d").date()

        if datetime.today().date() > last_prayer_date:
            get_and_store_prayer_times()

        return prayer_times


if __name__ == "__main__":
    prayer_times = get_prayer_times()

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
    print(next_prayer)
    print(f"{hours}hrs {sub_minutes}mins left")
