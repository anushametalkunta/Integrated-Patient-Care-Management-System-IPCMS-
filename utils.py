"""Shared helpers for IPCMS."""
from datetime import date, datetime
from calendar import month_abbr


def compute_bmi(height_cm, weight_kg):
    """Return BMI rounded to 1 decimal, or None if inputs invalid."""
    if not height_cm or not weight_kg or height_cm <= 0:
        return None
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m * height_m), 1)


def bmi_category(bmi):
    if bmi is None:
        return None
    if bmi < 18.5:
        return 'Underweight'
    if bmi < 25:
        return 'Normal'
    if bmi < 30:
        return 'Overweight'
    return 'Obese'


def patient_display_id(patient_id):
    return f'#{1000 + patient_id}'


def generate_mrn(patient_id):
    return f'MRN{10000 + patient_id:05d}'


def month_labels(count=6):
    """Return last N month abbreviations ending with current month."""
    today = date.today()
    labels = []
    for i in range(count - 1, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        labels.append(month_abbr[month])
    return labels


def monthly_counts(items, date_attr, months=6):
    """Count items grouped by month for the last N months."""
    today = date.today()
    buckets = []
    labels = month_labels(months)
    for i in range(months - 1, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        count = 0
        for item in items:
            raw = getattr(item, date_attr, None)
            if raw is None:
                continue
            if isinstance(raw, datetime):
                raw = raw.date()
            if raw.year == year and raw.month == month:
                count += 1
        buckets.append(count)
    return labels, buckets
