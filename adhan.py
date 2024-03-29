import csv
import os
from datetime import datetime, timedelta

import requests

# Change directory to this script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PRAYERS = [
    "Fajr",
    "Fajr Iqamah",
    "Dhuhr",
    "Dhuhr Iqamah",
    "Asr",
    "Asr Iqamah",
    "Maghrib",
    "Maghrib Iqamah",
    "Isha",
    "Isha Iqamah",
]
IQAMAH_TIMINGS = {"Fajr": 0, "Dhuhr": 0, "Asr": 0, "Maghrib": 0, "Isha": 0}

try:
    open("prayer_times.csv", "r").close()
except FileNotFoundError:
    with open("prayer_times.csv", "w") as prayer_times_file:
        prayer_times_file.write("Date," + ",".join(PRAYERS[::2]) + "\n")


def get_time_for_prayer(prayer: str, request):
    lines = request.iter_lines()

    additonal_minutes = {"Fajr": 6, "Dhuhr": 0, "Asr": 0, "Maghrib": 3, "Isha": 0}

    for i in lines:
        if prayer.capitalize() in i.decode("utf-8"):
            lines.__next__()
            time_span_elem = lines.__next__().decode("utf-8").split()[0]
            period = time_span_elem[-2:]
            time_span_elem = time_span_elem[:-2]
            prayer_time = time_span_elem[6 : time_span_elem.find("</")] + period

            # today = datetime.now()
            # prayer_time += f" {today.date()}"

            # return datetime.strptime(prayer_time, '%I:%M%p')
            return (
                datetime.strptime(prayer_time, "%I:%M%p")
                + timedelta(minutes=additonal_minutes[prayer])
            ).strftime("%I:%M%p")


def get_and_store_prayer_times():
    try:
        request = requests.get("https://salah.com")
    except Exception:
        print("No network!")
    else:
        prayer_times = {}
        for prayer in PRAYERS[::2]:
            prayer_times[prayer] = get_time_for_prayer(prayer, request)

        with open("prayer_times.csv", "a") as prayer_times_file:
            csv_writer = csv.writer(prayer_times_file)
            csv_writer.writerow([datetime.today().date(), *prayer_times.values()])


def get_prayer_times():
    with open("prayer_times.csv", "r") as prayer_times_file:
        csv_reader = csv.DictReader(prayer_times_file)

        for line in csv_reader:
            pass

        try:
            last_line = line
        except UnboundLocalError:
            get_and_store_prayer_times()
            return

        prayer_times = {}
        for prayer in PRAYERS[::2]:
            prayer_times[prayer] = datetime.strptime(
                f"{last_line['Date']} {last_line[prayer]}", "%Y-%m-%d %I:%M%p"
            )
            prayer_times[f"{prayer} Iqamah"] = prayer_times[prayer] + timedelta(
                minutes=IQAMAH_TIMINGS[prayer]
            )

        last_prayer_date = datetime.strptime(last_line["Date"], "%Y-%m-%d").date()

        if datetime.today().date() > last_prayer_date:
            get_and_store_prayer_times()

        return prayer_times


prayer_times = get_prayer_times()

for i in range(len(PRAYERS) - 1):
    p = prayer_times[PRAYERS[i]]
    n = prayer_times[PRAYERS[i + 1]]
    if p < datetime.now() < n:
        next_prayer = PRAYERS[i + 1]
        break

else:
    next_prayer = PRAYERS[0]


if __name__ == "__main__":
    difference_in_minutes = int(
        ((prayer_times[next_prayer] - datetime.now()).seconds) / 60
    )
    # print(int(difference_in_seconds/60))
    print(next_prayer, "in", difference_in_minutes, "mins")

# # while True:
# #     difference_in_seconds = (prayer_times[next_prayer] - datetime.now()).seconds
# #     print(next_prayer, "in",timedelta(seconds=difference_in_seconds))
# #     sleep(3)

# # pprint(prayer_times, sort_dicts=False)
# # print(prayer_times)
