import random
import json
import pickle
import numpy as np
import tensorflow as tf
from utils.preprocessing import tokenize, stem, bag_of_words

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

    def predecir_intencion(self, mensaje):
        tokens = tokenize(mensaje)
        X = bag_of_words(tokens, self.palabras)
        X = np.array([X])
        
        prediccion = self.model.predict(X)[0]
        intencion_idx = np.argmax(prediccion)
        intencion = self.tags[intencion_idx]
        confianza = prediccion[intencion_idx]
        
        return intencion if confianza > 0.7 else None

    def generar_respuesta(self, mensaje):
        intencion = self.predecir_intencion(mensaje)
        
        if not intencion:
            return "No entendí bien. ¿Puedes reformularlo?"
        
        # Respuestas estándar
        for intent in self.intents['intents']:
            if intent['tag'] == intencion:
                return random.choice(intent['responses'])

if __name__ == "__main__":
    bot = ChatbotAgenda()
    print("Chatbot de Agenda (escribe 'salir' para terminar)")
    
    while True:
        mensaje = input("Tú: ")
        if mensaje.lower() == 'salir':
            break
        print("Bot:", bot.generar_respuesta(mensaje))