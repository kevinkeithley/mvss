def extract_and_format_end_date(date_range):
    months = {
        "January": "01",
        "February": "02",
        "March": "03",
        "April": "04",
        "May": "05",
        "June": "06",
        "July": "07",
        "August": "08",
        "September": "09",
        "October": "10",
        "November": "11",
        "December": "12",
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }

    parts = date_range.split(" - ")
    if len(parts) == 2:
        _, end = parts
    else:
        end = parts[0]

    end_parts = end.split()

    if len(end_parts) == 3:  # Full date
        month, day, year = end_parts
    elif len(end_parts) == 2:  # Day and year only
        day, year = end_parts
        month = parts[0].split()[0]
    else:
        return None  # Unhandled format

    # Remove comma from day if present
    day = day.rstrip(",")

    # Convert month name to number
    month_num = months.get(month)
    if not month_num:
        return None  # Unrecognized month

    # Ensure day and year are in correct format
    day = day.zfill(2)
    if len(year) == 2:
        year = "20" + year

    return f"{year}-{month_num}-{day}"
