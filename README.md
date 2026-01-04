# Adhan App

A Python script that prints the time remaining for the next Adhan (prayer), primarily designed for triggering notifications (e.g., using `notify-send` or similar tools).

> **Note**: While the default output is multi-line and suitable for notifications, the script can be easily modified to output a single line if you wish to use it with status bars like i3blocks or polybar.

## Features
- **Accurate Prayer Times**: Fetches data from the [Aladhan API](https://aladhan.com/prayer-times-api).
- **Caching**: Stores daily prayer times in a local JSON file to reduce network requests.
- **Multiple Cities Support**: Configure multiple locations and switch between them via command-line arguments.
- **Hijri Date**: Displays the current Hijri date.
- **Customizable**: Adjustable prayer time offsets (tuning).

## How It Works
1. **Configuration**: The script reads city configuration from `cities.json`.
2. **Caching**: It checks `/tmp/prayer_times.json` for today's prayer times.
3. **Fetching**: If data is missing or outdated, it fetches new data from the API and updates the cache.
4. **Output**: It calculates the remaining time to the next prayer and prints it along with the schedule for the day and the Hijri date.

## Installation & Setup

1. **Clone or Download**:
   ```bash
   git clone https://github.com/an4s911/azan-app.git
   cd azan-app
   ```

2. **Install Dependencies**:
   This script requires the `requests` library.
   ```bash
   pip install requests
   ```

3. **Configure Cities**:
   - `cities.json` is git-ignored to protect your privacy.
   - Copy the example file to create your configuration:
     ```bash
     cp cities.example.json cities.json
     ```
   - Edit `cities.json` to add your location(s).
   - **Reference**: You can check parameter values (like method, school, etc.) at the [Aladhan API Documentation](https://aladhan.com/prayer-times-api#get-/timingsByCity/-date-).
   - **Tuning**: You can adjust time offsets for each prayer using the `tune` dictionary (values in minutes).

## Usage

Run the script using Python:

```bash
python3 adhan.py
```

### Multiple Cities
If you have configured multiple cities in `cities.json`, you can select one using its index (0-based):

```bash
python3 adhan.py 0  # First city (Default)
python3 adhan.py 1  # Second city
```

## OS Compatibility
This script is designed for **Unix-based systems** (Linux, macOS) as it uses `/tmp/prayer_times.json` for caching.

**Windows Users**:
To make this work on Windows, modify `adhan.py` and change the `PRAYER_TIMES_FILE_PATH` variable to a valid Windows path (e.g., using `tempfile.gettempdir()` or a local file path).

```python
# adhan.py
PRAYER_TIMES_FILE_PATH = "prayer_times.json" # Store in current directory for example
```

## Output Format
The script outputs:
1. Next Prayer Name: Time
2. Time Remaining: HH:MM:SS
3. (Empty Line)
4. List of all prayer times for the day
5. Hijri Date (DD Month (MM) YYYY)
