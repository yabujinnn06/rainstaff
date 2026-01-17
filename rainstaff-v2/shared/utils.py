"""
Rainstaff v2 - Shared Utilities
Common helper functions
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, Tuple


def normalize_date(value: str) -> str:
    """
    Normalize date to ISO format (YYYY-MM-DD)
    Accepts: DD.MM.YYYY or YYYY-MM-DD
    """
    if not value:
        return ""
    
    value = value.strip()
    
    # Try DD.MM.YYYY
    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', value):
        day, month, year = value.split('.')
        return f"{year}-{month}-{day}"
    
    # Try YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        return value
    
    raise ValueError(f"Geçersiz tarih formatı: {value}. Beklenen: DD.MM.YYYY veya YYYY-MM-DD")


def normalize_time(value: str) -> str:
    """
    Normalize time to HH:MM format
    """
    if not value:
        return ""
    
    value = value.strip()
    
    # HH:MM format
    if re.match(r'^\d{1,2}:\d{2}$', value):
        hour, minute = value.split(':')
        hour = int(hour)
        minute = int(minute)
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Geçersiz saat: {value}")
        
        return f"{hour:02d}:{minute:02d}"
    
    raise ValueError(f"Geçersiz saat formatı: {value}. Beklenen: HH:MM")


def parse_date(value: str) -> date:
    """Parse date string to date object"""
    normalized = normalize_date(value)
    return datetime.strptime(normalized, "%Y-%m-%d").date()


def parse_time(value: str) -> Tuple[int, int]:
    """Parse time string to (hour, minute) tuple"""
    normalized = normalize_time(value)
    hour, minute = normalized.split(':')
    return int(hour), int(minute)


def format_date_display(value: date) -> str:
    """Format date for display (DD.MM.YYYY)"""
    return value.strftime("%d.%m.%Y")


def week_start_monday(target_date: date) -> date:
    """Get Monday of the week containing target_date"""
    return target_date - timedelta(days=target_date.weekday())


def week_end_sunday(week_start: date) -> date:
    """Get Sunday of the week starting on week_start (Monday)"""
    return week_start + timedelta(days=6)


def is_weekend(target_date: date) -> bool:
    """Check if date is weekend (Saturday or Sunday)"""
    return target_date.weekday() in (5, 6)


def calculate_hours_between(start_time: str, end_time: str, break_minutes: int = 0) -> float:
    """
    Calculate hours between two times, accounting for break and overnight shifts
    """
    start_hour, start_min = parse_time(start_time)
    end_hour, end_min = parse_time(end_time)
    
    start_total = start_hour * 60 + start_min
    end_total = end_hour * 60 + end_min
    
    # Handle overnight shift (end < start means next day)
    if end_total <= start_total:
        end_total += 24 * 60
    
    worked_minutes = end_total - start_total - break_minutes
    return round(worked_minutes / 60.0, 2)


def validate_range(value: int, min_val: int, max_val: int, field_name: str) -> None:
    """Validate integer is within range"""
    if not (min_val <= value <= max_val):
        raise ValueError(f"{field_name} {min_val} ile {max_val} arasında olmalıdır. Girilen: {value}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized or "unnamed"


def format_currency(amount: float, currency: str = "TRY") -> str:
    """Format currency for display"""
    if currency == "TRY":
        return f"{amount:,.2f} ₺"
    return f"{amount:,.2f} {currency}"


def format_km(km: int) -> str:
    """Format kilometer for display"""
    return f"{km:,} km"
