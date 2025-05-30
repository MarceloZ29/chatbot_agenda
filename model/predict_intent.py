import pickle
import numpy as np
import tensorflow as tf
from pathlib import Path
import json
import os
import random
import re
from datetime import datetime
import dateparser
from utils.preprocessing import tokenize, stem, bag_of_words

class IntentPredictor:
    def __init__(self, model_path=None, words_path=None, tags_path=None):
        # Cargar rutas por defecto si no se especifican
        base_dir = Path(__file__).parent.parent
        self.model_path = model_path or os.path.join(base_dir, 'model', 'modelo_chatbot.h5')
        self.words_path = words_path or os.path.join(base_dir, 'model', 'palabras.pkl')
        self.tags_path = tags_path or os.path.join(base_dir, 'model', 'tags.pkl')
        self.intents_path = os.path.join(base_dir, 'data', 'intents.json')
        
        # Cargar recursos
        self.load_model()
        self.load_resources()

    def load_model(self):
        """Carga el modelo de TensorFlow"""
        self.model = tf.keras.models.load_model(self.model_path)

    def load_resources(self):
        """Carga vocabulario y etiquetas"""
        with open(self.words_path, 'rb') as f:
            self.words = pickle.load(f)
        
        with open(self.tags_path, 'rb') as f:
            self.tags = pickle.load(f)
        
        with open(self.intents_path, 'r', encoding='utf-8') as f:
            self.intents = json.load(f)

    def predict(self, sentence, confidence_threshold=0.7):
        """
        Predice la intención de un mensaje
        Args:
            sentence (str): Mensaje del usuario
            confidence_threshold (float): Umbral de confianza mínimo
        Returns:
            tuple: (intención, confianza) o (None, 0) si no supera el umbral
        """
        # Preprocesamiento
        tokens = tokenize(sentence)
        bow = bag_of_words(tokens, self.words)
        bow = np.array([bow])
        
        # Predicción
        prediction = self.model.predict(bow)[0]
        intent_idx = np.argmax(prediction)
        intent = self.tags[intent_idx]
        confidence = prediction[intent_idx]
        
        return (intent, confidence) if confidence >= confidence_threshold else (None, 0)

    def get_response(self, intent, event_details=None):
        """Obtiene una respuesta aleatoria para la intención"""
        for intent_data in self.intents['intents']:
            if intent_data['tag'] == intent:
                response = random.choice(intent_data['responses'])
                if event_details and '{descripcion}' in response:
                    desc, fecha = event_details
                    return response.format(descripcion=desc, fecha=fecha)
                return response
        return "No entendí eso. ¿Puedes reformularlo?"

    def parse_spanish_date(self, text):
        """Analiza fechas en español con dateparser"""
        settings = {
            'DATE_ORDER': 'DMY',
            'LANGUAGE': 'es',
            'PREFER_DAY_OF_MONTH': 'first',
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now()
        }
        return dateparser.parse(text, settings=settings)

    def extract_datetime(self, text):
        """Extrae fecha y hora de un texto en español"""
        try:
            date = self.parse_spanish_date(text)
            if date:
                # Ajustar formato de 12h a 24h si es necesario
                if "pm" in text.lower() and date.hour < 12:
                    date = date.replace(hour=date.hour+12)
                elif "am" in text.lower() and date.hour == 12:
                    date = date.replace(hour=0)
                return date.strftime("%d/%m/%Y %H:%M")
            return None
        except Exception as e:
            print(f"Error parseando fecha: {str(e)}")
            return None

    def extract_event_description(self, text, date_str):
        """Extrae la descripción del evento eliminando componentes de fecha"""
        try:
            if not date_str:
                return text.capitalize()
                
            date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            
            # Palabras y patrones a eliminar
            remove_patterns = [
                r'\b(?:el|para|a las?|el día|el|la|los|mi|una|agenda|crea|programa)\b',
                date_str,
                date_obj.strftime("%d de %B").lower(),
                date_obj.strftime("%A").lower(),
                r'\d{1,2}(?::\d{2})?\s?(?:am|pm|de la mañana|de la tarde)?',
                r'\b(?:próximo|próxima|siguiente)\b'
            ]
            
            clean_text = text.lower()
            for pattern in remove_patterns:
                clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
            
            # Limpieza final
            clean_text = re.sub(r'[^\w\s]', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            return clean_text.capitalize() if clean_text else "Evento sin descripción"
        
        except Exception as e:
            print(f"Error extrayendo descripción: {str(e)}")
            return text.capitalize()

    def extract_event_details(self, message):
        """
        Extrae descripción y fecha de un mensaje para eventos
        Returns:
            tuple: (descripción, fecha_str) o (None, None) si no se detecta
        """
        try:
            # Primero intenta extraer la fecha
            date_str = self.extract_datetime(message)
            if not date_str:
                return None, None
                
            # Luego extrae la descripción
            description = self.extract_event_description(message, date_str)
            
            return description, date_str
            
        except Exception as e:
            print(f"Error extrayendo detalles del evento: {str(e)}")
            return None, None

if __name__ == "__main__":
    # Ejemplo de uso mejorado
    predictor = IntentPredictor()
    test_phrases = [
        "Hola, cómo estás?",
        "Agenda una reunión para mañana a las 3pm",
        "Qué tengo programado para el viernes?",
        "Crea una cita para el dentista el 31 de mayo a las 3 de la tarde",
        "Reserva hora con el doctor para el 15 de junio a las 10:30",
        "crea una cita para el dentista el 31 de mayo a las 3 de la tarde",
        "agenda reunión importante para el 25 de junio",
        "reserva hora con el doctor para mañana a las 10am",
        "quiero una cita de spa el viernes a las 4pm"
    ]
    
    print("=== Prueba del sistema ===")
    for phrase in test_phrases:
        print(f"\nFrase: '{phrase}'")
        
        # 1. Predecir intención
        intent, confidence = predictor.predict(phrase)
        print(f"Intención detectada: {intent} (confianza: {confidence:.2f})")
        
        if intent:
            # 2. Extraer detalles si es un evento
            event_details = None
            if intent == "agregar_evento":
                event_details = predictor.extract_event_details(phrase)
                print(f"Detalles extraídos: {event_details}")
            
            # 3. Obtener respuesta contextual
            response = predictor.get_response(intent, event_details)
            print(f"Respuesta: {response}")