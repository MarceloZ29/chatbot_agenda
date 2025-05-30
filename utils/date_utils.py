import dateparser
import re
from datetime import datetime

def extract_datetime(text):
    """Versión simplificada como alternativa"""
    try:
        parsed_date = dateparser.parse(text, languages=['es'])
        if parsed_date:
            return parsed_date.strftime("%d/%m/%Y %H:%M")
        return None
    except:
        return None

def extract_event_description(text, date_str):
    """Extrae descripción eliminando componentes de fecha"""
    try:
        if not date_str:
            return text.capitalize()
            
        date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        
        # Expresiones para eliminar
        patterns = [
            r'\b(?:el|para|a las?|el día|el|la|los|mi|una|agenda|agendar|programa)\b',
            date_str,
            date_obj.strftime("%d de %B").lower(),
            date_obj.strftime("%A").lower(),
            r'\d{1,2}(?::\d{2})?\s?(?:am|pm|de la mañana|de la tarde)?',
            r'\b(?:próximo|próxima|siguiente)\b'
        ]
        
        clean_text = text.lower()
        for pattern in patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Limpieza final
        clean_text = re.sub(r'[^\w\s]', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text.capitalize() if clean_text else "Evento sin descripción"
    
    except Exception as e:
        print(f"Error extrayendo descripción: {str(e)}")
        return text.capitalize()