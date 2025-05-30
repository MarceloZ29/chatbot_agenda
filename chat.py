import random
import json
import pickle
import numpy as np
import tensorflow as tf
import re # Moved from __main__ to top-level
from utils.preprocessing import tokenize, stem, bag_of_words, clean_text
from agenda_manager import AgendaManager
from utils.entity_extractor import extract_event_details

class ChatbotAgenda:
    def __init__(self):
        # Cargar modelo y recursos
        self.model = tf.keras.models.load_model('./model/modelo_chatbot.h5')
        with open('./model/palabras.pkl', 'rb') as f:
            self.palabras = pickle.load(f)
        with open('./model/tags.pkl', 'rb') as f:
            self.tags = pickle.load(f)
        with open('./data/intents.json', 'r', encoding='utf-8') as f:
            self.intents = json.load(f)
        self.agenda_manager = AgendaManager()

    def predecir_intencion(self, mensaje):
        cleaned_mensaje = clean_text(mensaje) # Use clean_text for consistency with training
        tokens = tokenize(cleaned_mensaje)
        X = bag_of_words(tokens, self.palabras)
        X = np.array([X])
        
        # Suppress TensorFlow logging for prediction
        tf.get_logger().setLevel('ERROR')
        prediccion = self.model.predict(X, verbose=0)[0]
        tf.get_logger().setLevel('INFO') # Restore logger level

        intencion_idx = np.argmax(prediccion)
        intencion = self.tags[intencion_idx]
        confianza = prediccion[intencion_idx]
        
        # print(f"Input: '{mensaje}' -> Cleaned: '{cleaned_mensaje}' -> Tokens: {tokens} -> Intent: {intencion} (Conf: {confianza:.4f})") # Debug
        return intencion if confianza > 0.7 else None

    def generar_respuesta(self, mensaje):
        intencion = self.predecir_intencion(mensaje)
        
        if not intencion:
            return "No entendí bien. ¿Puedes reformularlo?"

        if intencion == "agregar_evento":
            details = extract_event_details(mensaje)
            descripcion = details.get("descripcion")
            fecha = details.get("fecha")
            hora = details.get("hora")

            if not descripcion and not fecha: # Both missing
                 return "Necesito más detalles. ¿Qué evento quieres agregar y para cuándo?"
            elif not fecha:
                return f"Entendido. ¿Para qué fecha quieres agendar '{descripcion}'?" if descripcion else "Necesito una fecha para agendar el evento. ¿Cuándo sería?"
            elif not descripcion:
                return f"Entendido. Agendaré algo para el {fecha}. ¿Cuál es la descripción del evento?"
            else:
                # Have description and date, hora is optional
                response_data = self.agenda_manager.agregar_evento(descripcion=descripcion, fecha=fecha, hora=hora)
                if response_data.get("status") == "success" and response_data.get("evento"):
                    evento = response_data["evento"]
                    hora_str = f" a las {evento['hora']}" if evento.get('hora') else ""
                    return f"¡Evento agregado! '{evento['descripcion']}' para el {evento['fecha']}{hora_str}."
                else:
                    return response_data.get("message", "No pude agregar el evento, hubo un problema.")

        elif intencion == "consultar_evento":
            details = extract_event_details(mensaje)
            fecha_consulta = details.get("fecha") 
            # dia_consulta is not explicitly extracted by extract_event_details yet,
            # but AgendaManager's consultar_eventos can handle "hoy", "mañana" if passed as dia_consulta.
            # For now, we rely on dateparser in extract_event_details to resolve these to a specific fecha.
            # We will pass fecha_consulta to both arguments in AgendaManager to cover direct date and parsed "hoy"/"mañana"
            
            eventos = self.agenda_manager.consultar_eventos(fecha_consulta=fecha_consulta, dia_consulta=fecha_consulta)

            if eventos:
                response_parts = []
                if fecha_consulta:
                    response_parts.append(f"Aquí están tus eventos para {fecha_consulta}:")
                else:
                    response_parts.append("Aquí están todos tus eventos:")
                
                for e in eventos:
                    hora_str = f" a las {e.get('hora')}" if e.get('hora') else ""
                    response_parts.append(f"- '{e['descripcion']}' el {e['fecha']}{hora_str} (ID: {e['id']})")
                return "\n".join(response_parts)
            else:
                return f"No tienes eventos programados {'para esa fecha.' if fecha_consulta else 'en tu agenda.'}"

        elif intencion == "eliminar_evento":
            details = extract_event_details(mensaje) # Tries to get description primarily
            event_description_to_delete = details.get("descripcion")
            
            # Simple ID extraction attempt (e.g., "borra evento 3", "elimina id 5")
            # This is very basic and can be improved with more robust regex or NER
            id_match = re.search(r'\b(?:id|evento)\s+(\d+)\b', mensaje, re.IGNORECASE)
            event_id_to_delete = None
            if id_match:
                event_id_to_delete = id_match.group(1)

            if event_id_to_delete:
                response_data = self.agenda_manager.eliminar_evento(event_id=event_id_to_delete)
                return response_data.get("message", "Error al procesar eliminación por ID.")
            elif event_description_to_delete:
                # Try to remove some keywords if the description is too generic like "el evento"
                if event_description_to_delete.lower() in ["evento", "el evento", "la reunion", "reunion", "la cita", "cita"]:
                    return "Para eliminar por descripción, por favor dame una descripción más específica del evento que quieres borrar."
                response_data = self.agenda_manager.eliminar_evento(event_description=event_description_to_delete)
                return response_data.get("message", "Error al procesar eliminación por descripción.")
            else:
                return "No entendí qué evento quieres eliminar. Puedes decir 'elimina evento con ID X' o 'borra el evento llamado YYY'."
        
        else: # Fallback for other intents like saludo, despedida, ayuda, agradecimiento
            for intent_data in self.intents['intents']:
                if intent_data['tag'] == intencion:
                    return random.choice(intent_data['responses'])
            
            # Should not be reached if all intents in JSON have handlers or are covered by the loop above
            return f"Entendí que quieres '{intencion}', pero aún no sé cómo manejar eso."

if __name__ == "__main__":
    bot = ChatbotAgenda()
    print("Chatbot de Agenda (escribe 'salir' para terminar)")
    
    while True:
        mensaje = input("Tú: ")
        if mensaje.lower() == 'salir':
            break
        print("Bot:", bot.generar_respuesta(mensaje))