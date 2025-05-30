from datetime import datetime
from . import date_utils # Use relative import for utils module

def extract_event_details(text: str) -> dict:
    """
    Extracts event details (description, date, time) from a text string.

    Args:
        text: The input string from the user.

    Returns:
        A dictionary containing:
        - "descripcion": The extracted event description (str|None).
        - "fecha": The extracted date in "YYYY-MM-DD" format (str|None).
        - "hora": The extracted time in "HH:MM" format (str|None).
    """
    if not text:
        return {"descripcion": None, "fecha": None, "hora": None}

    # 1. Extract datetime object
    # For extract_event_description, we might ideally want the raw string segment that dateparser matched.
    # dateparser.parse doesn't directly give this. dateparser.search.search_dates does,
    # but it's a different approach. We'll pass the parsed_datetime_obj for now.
    # The `extract_datetime_object` function in date_utils uses dateparser.parse().
    parsed_datetime_obj = date_utils.extract_datetime_object(text)

    # 2. Format datetime object for agenda
    # This will give {"fecha": "YYYY-MM-DD" or None, "hora": "HH:MM" or None}
    formatted_datetime = date_utils.format_datetime_for_agenda(parsed_datetime_obj)
    extracted_fecha = formatted_datetime.get("fecha")
    extracted_hora = formatted_datetime.get("hora")
    
    # 3. Extract event description
    # The date_utils.extract_event_description function is designed to remove date/time phrases.
    # Passing `parsed_datetime_obj` helps it generate patterns to remove.
    # `detected_date_strings` is None for now, as `extract_datetime_object` doesn't provide it directly.
    extracted_descripcion = date_utils.extract_event_description(
        text=text,
        parsed_datetime_obj=parsed_datetime_obj,
        detected_date_strings=None # search_dates would be needed to populate this effectively
    )

    # Handle cases where description might be empty or a placeholder
    if not extracted_descripcion or extracted_descripcion == "Evento sin descripción":
        # If we have a date/time, we might not want to return None for description,
        # but rather indicate it's missing, or let it be the placeholder.
        # For now, if it's the placeholder and we have a date, let's make it None.
        if extracted_fecha or extracted_hora:
             extracted_descripcion = None # Or keep "Evento sin descripción" if preferred by downstream
        else: # No date, no time, no real description
            extracted_descripcion = None


    # Ensure description is not None if other fields are also None (unless it was truly empty)
    if not extracted_fecha and not extracted_hora and not extracted_descripcion:
        # This means nothing was found. If the original text was not empty,
        # the description could be the original text, or parts of it if cleaning was minimal.
        # However, extract_event_description tries to clean it.
        # If all are None, it implies the input was not an event string or was empty.
        pass # All components can be None if nothing is found.

    return {
        "descripcion": extracted_descripcion,
        "fecha": extracted_fecha,
        "hora": extracted_hora,
    }

if __name__ == '__main__':
    # Quick tests
    test_phrases = [
        "Agenda una reunión con el equipo para el próximo martes a las 3 de la tarde",
        "Recordatorio: dentista mañana a las 10am",
        "Tenemos que hacer la presentación el 25 de diciembre",
        "partido de futbol en dos horas",
        "comprar pan",
        "cena con maria el viernes",
        "Llamar a mamá mañana por la mañana",
        "Revisión del proyecto el 05/08/2024 a las 15:00",
        "Ir al gimnasio hoy",
        "Consulta médica el próximo lunes",
        "Tomar café con Ana el 10 de Agosto a las cinco y media",
        "Nada para el martes que viene", # Should ideally result in low confidence for 'agregar_evento'
        "el dia 15 de este mes una cita importante"
    ]

    # Need to make sure date_utils is accessible for the __main__ block
    # This might require adjusting PYTHONPATH or running as a module if utils is a package
    # For a simple script structure, ensure date_utils.py is in the same directory or accessible.
    # Assuming a package structure like:
    # utils/
    #   __init__.py
    #   date_utils.py
    #   entity_extractor.py
    
    # If running this file directly, relative imports might need adjustment.
    # The `from . import date_utils` implies it's part of a package.
    # To run standalone for testing, you might change it to `import date_utils`
    # and ensure date_utils.py is in the PYTHONPATH.
    
    print("Running entity extraction tests:")
    for phrase in test_phrases:
        details = extract_event_details(phrase)
        print(f"Input: \"{phrase}\"")
        print(f"  -> Extracted: {details}\n")

    # Test with a specific known date to check formatting
    # Assuming date_utils.extract_datetime_object and format_datetime_for_agenda work
    # Test dateparser's behavior for "next Monday at midnight" vs "next Monday"
    print("Testing specific date parsing:")
    dt_obj_midnight = date_utils.extract_datetime_object("next Monday at 00:00")
    formatted_midnight = date_utils.format_datetime_for_agenda(dt_obj_midnight)
    print(f"Input: \"next Monday at 00:00\" -> {formatted_midnight} (Raw: {dt_obj_midnight})")

    dt_obj_no_time = date_utils.extract_datetime_object("next Monday")
    formatted_no_time = date_utils.format_datetime_for_agenda(dt_obj_no_time)
    print(f"Input: \"next Monday\" -> {formatted_no_time} (Raw: {dt_obj_no_time})")
    
    dt_obj_with_time = date_utils.extract_datetime_object("next Monday 3pm")
    formatted_with_time = date_utils.format_datetime_for_agenda(dt_obj_with_time)
    print(f"Input: \"next Monday 3pm\" -> {formatted_with_time} (Raw: {dt_obj_with_time})")

    # Test description extraction
    desc_test_phrase = "Agenda una reunión de seguimiento con Carlos para el jueves a las 2pm"
    desc_dt_obj = date_utils.extract_datetime_object(desc_test_phrase)
    desc_details = date_utils.extract_event_description(desc_test_phrase, desc_dt_obj)
    print(f"Input for description: \"{desc_test_phrase}\" -> Description: \"{desc_details}\"")

    desc_test_phrase_2 = "partido de futbol el viernes por la noche"
    desc_dt_obj_2 = date_utils.extract_datetime_object(desc_test_phrase_2)
    desc_details_2 = date_utils.extract_event_description(desc_test_phrase_2, desc_dt_obj_2)
    print(f"Input for description: \"{desc_test_phrase_2}\" -> Description: \"{desc_details_2}\"")

    desc_test_phrase_3 = "Comprar entradas para el concierto el 15 de mayo"
    desc_dt_obj_3 = date_utils.extract_datetime_object(desc_test_phrase_3)
    desc_details_3 = date_utils.extract_event_description(desc_test_phrase_3, desc_dt_obj_3)
    print(f"Input for description: \"{desc_test_phrase_3}\" -> Description: \"{desc_details_3}\"")
