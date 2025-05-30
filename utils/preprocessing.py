import re
import nltk
import numpy as np  # <-- Esta importación faltaba
from nltk.stem import PorterStemmer

nltk.download('punkt')
stemmer = PorterStemmer()

def clean_text(text):
    """Limpia el texto conservando información importante para fechas"""
    # Conserva palabras clave de tiempo
    time_words = ['enero','febrero','marzo','abril','mayo','junio',
                'julio','agosto','septiembre','octubre','noviembre','diciembre',
                'lunes','martes','miércoles','jueves','viernes','sábado','domingo',
                'am','pm','próximo','próxima','mañana','tarde']
    
    words = tokenize(text)
    words = [w for w in words if w.lower() in time_words or w.isalpha()]
    return ' '.join(words)

def tokenize(sentence):
    return nltk.word_tokenize(sentence.lower())

def stem(word):
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, all_words):
    tokenized_sentence = [stem(w) for w in tokenized_sentence]
    return np.array([1 if w in tokenized_sentence else 0 for w in all_words])  # <-- Aquí se usa np.array