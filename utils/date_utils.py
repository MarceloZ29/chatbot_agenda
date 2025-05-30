import dateparser
import re
from datetime import datetime

def extract_datetime_object(text: str) -> datetime | None:
    """
    Extracts a datetime object from a text string using dateparser.
    Returns the datetime object if found, otherwise None.
    """
    try:
        # Settings to prefer dates in the future for ambiguous parsing
        # and to handle relative dates like "next Monday" correctly.
        settings = {'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()}
        parsed_date = dateparser.parse(text, languages=['es'], settings=settings)
        return parsed_date
    except Exception:
        # Log error or handle as needed
        return None

def format_datetime_for_agenda(dt_object: datetime | None) -> dict:
    """
    Formats a datetime object into a dictionary with "fecha" (YYYY-MM-DD)
    and "hora" (HH:MM) suitable for AgendaManager.
    If dt_object is None, returns None for both.
    If time is not present (00:00:00), hora is None.
    """
    if not dt_object:
        return {"fecha": None, "hora": None}

    fecha_str = dt_object.strftime("%Y-%m-%d")
    # Check if time is explicitly set (not default 00:00:00)
    # dateparser might set a default time if only a date is found.
    # We consider time as "provided" if it's not midnight.
    # This might need adjustment based on how dateparser handles "all day" events or dates without specific times.
    if dt_object.hour == 0 and dt_object.minute == 0 and dt_object.second == 0:
        # Let's test how dateparser behaves for phrases like "tomorrow" or "next Monday"
        # It often defaults to midnight. If that's the case, we might want hora to be None.
        # For "tomorrow at 3pm", time will be set.
        hora_str = None # Assume time is not explicitly provided if it's midnight
    else:
        hora_str = dt_object.strftime("%H:%M")
        
    return {"fecha": fecha_str, "hora": hora_str}


def extract_event_description(text: str, parsed_datetime_obj: datetime | None, detected_date_strings: list[str] | None = None) -> str:
    """
    Extracts event description by removing date/time related phrases.
    Relies on dateparser's detected date strings if available, otherwise uses the datetime object
    to generate patterns for removal.
    """
    description = text
    
    # Convert original text to lowercase for case-insensitive matching
    # but keep original text for the final description if possible, or capitalize later.
    # For simplicity in regex, we'll work with lowercase and then process the final result.
    processed_description = description.lower()

    # If dateparser provided the strings it detected, use them directly for removal
    if parsed_datetime_obj and detected_date_strings:
        for date_str_segment in detected_date_strings:
            # Escape the detected string for regex and remove it
            processed_description = processed_description.replace(date_str_segment.lower(), "", 1)

    # Fallback or additional cleaning based on the datetime object
    # This is useful if detected_date_strings isn't perfect or not available
    if parsed_datetime_obj:
        # Generate various string formats that might represent the date/time in text
        possible_date_time_patterns = [
            parsed_datetime_obj.strftime("%d/%m/%Y %H:%M"),
            parsed_datetime_obj.strftime("%d/%m/%Y"),
            parsed_datetime_obj.strftime("%H:%M"),
            parsed_datetime_obj.strftime("%I:%M %p").lower(), # 03:00 pm
            parsed_datetime_obj.strftime("%d de %B de %Y").lower(), # 03 de julio de 2024
            parsed_datetime_obj.strftime("%d de %B").lower(),      # 03 de julio
            parsed_datetime_obj.strftime("%A").lower(),           # miércoles
            str(parsed_datetime_obj.day), # e.g., "3", "15"
            # Add common time expressions that might not be fully covered by detected_date_strings
            r"\b(a las?)\s*" + parsed_datetime_obj.strftime("%I").lstrip('0') + r"\s*(pm|am|de la tarde|de la mañana)?\b", # a las 3 pm
            r"\b(a las?)\s*" + parsed_datetime_obj.strftime("%H") + r"\b", # a las 15
        ]
        # Remove specific time parts like "a las 3pm" if not caught by dateparser segment removal
        time_regex = r"(?:a la(?:s)?|las)\s+(?:[01]?\d|2[0-3])(?::[0-5]\d)?(?:\s*(?:am|pm|de la mañana|de la tarde|de la noche))?"
        processed_description = re.sub(time_regex, "", processed_description, flags=re.IGNORECASE)


        for pattern in possible_date_time_patterns:
            if pattern: # Ensure pattern is not empty
                 # Escape special regex characters in the pattern string
                processed_description = re.sub(re.escape(pattern), "", processed_description, flags=re.IGNORECASE)
    
    # Common keywords to remove
    keywords_to_remove = [
        r'\b(?:programa|agenda|agendar|anota|apunta|crea|recordarme|recordatorio)\b',
        r'\b(?:para el|el día|el|en)\b',
        r'\b(?:de)\b', # "reunión de equipo" vs "3 de la tarde" - be careful
        r'\b(?:mañana|hoy|pasado mañana)\b',
        r'\b(?:próximo|próxima|siguiente)\b',
        r'\s+(?:a|en|con|para|de)\s+$', # Prepositions at the end of string
        r'^\s*(?:a|en|con|para|de)\s+', # Prepositions at the start
    ]

    for kw_pattern in keywords_to_remove:
        processed_description = re.sub(kw_pattern, " ", processed_description, flags=re.IGNORECASE).strip()

    # Normalize spaces
    processed_description = re.sub(r'\s+', ' ', processed_description).strip()
    
    # Remove common connecting words if they are left alone, e.g., " de ", " a ", " con "
    # This is tricky, as "de" can be part of a description.
    # Example: "reunion de equipo" vs "evento de prueba"
    # For now, let's be conservative here or handle it by more intelligent NLP if needed.
    # A simple approach: remove dangling prepositions if they are not part of a larger phrase.
    # This is partly handled by stripping prepositions at start/end.

    # Final cleanup of characters: preserve letters, numbers, spaces, and some essential punctuation.
    # Allow a-z, A-Z, 0-9, spaces, and specific characters like 'áéíóúñÑüÜ', '-', ':'
    # This is less aggressive than removing all non-alphanumerics.
    processed_description = re.sub(r'[^\w\s\dáéíóúñÑüÜ:\-\']', '', processed_description) # Keep accents, numbers, space, colon, hyphen, apostrophe
    processed_description = re.sub(r'\s+', ' ', processed_description).strip()

    return processed_description.capitalize() if processed_description else "Evento sin descripción"