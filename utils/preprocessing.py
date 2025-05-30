import re
import nltk
import numpy as np
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except Exception: # More general exception to catch download issues
    nltk.download('punkt', quiet=True)

stemmer = PorterStemmer() # Consider SnowballStemmer for Spanish: nltk.stem.SnowballStemmer('spanish')

def clean_text(text: str) -> str:
    """
    Limpia el texto para el modelado Bag-of-Words y NLU:
    - Convierte a minúsculas.
    - Elimina puntuación específica no esencial (¡!?,.;'").
    - Reemplaza otros caracteres no alfanuméricos (excepto acentos, :, -) con espacio.
    - Conserva letras, números, espacios, dos puntos (para horas como 10:30), 
      guiones (para palabras compuestas o fechas).
    - Normaliza espacios múltiples a uno solo.
    """
    if not isinstance(text, str):
        return "" # Handle non-string input gracefully
        
    text = text.lower()
    
    # Eliminar puntuación específica como comillas, puntos y comas (si no son parte de números), etc.
    # Cuidado con no eliminar ':' o '-' si son parte de entidades como horas o nombres compuestos.
    # For NLU, some punctuation might be part of the description.
    # This regex removes common sentence delimiters.
    text = re.sub(r'[¿¡!?,.;\'"]', '', text)
    
    # Conservar caracteres alfanuméricos (incluyendo acentos españoles), espacios, dos puntos y guiones.
    # Reemplazar cualquier otra cosa con un espacio para evitar concatenar palabras.
    text = re.sub(r'[^\w\s:\-áéíóúüñÁÉÍÓÚÜÑ]', ' ', text)
    
    # Normalizar espacios múltiples a uno solo y quitar espacios al inicio/final.
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize(sentence: str) -> list[str]:
    """Tokeniza una oración (que ya debería estar preprocesada/limpia)."""
    # clean_text ya convierte a minúsculas.
    return word_tokenize(sentence)

def stem(word: str) -> str:
    """Realiza stemming de una palabra (que ya debería estar en minúsculas)."""
    # clean_text ya convierte a minúsculas.
    return stemmer.stem(word)

def bag_of_words(tokenized_sentence: list[str], all_words: list[str]) -> np.ndarray:
    """
    Genera un vector Bag-of-Words.
    'all_words' (vocabulario) debe estar pre-procesado (ej. stemmizado) si las palabras en 
    'tokenized_sentence' lo están.
    """
    # Asumimos que tokenized_sentence ya está stemmizada si es necesario.
    # Y que all_words (el vocabulario) también está stemmizado.
    # Si no, se debería hacer aquí consistentemente.
    # La implementación original stemmizaba tokenized_sentence aquí,
    # y luego stemmizaba cada palabra del vocabulario al vuelo para comparar.
    
    stemmed_sentence = [stem(w) for w in tokenized_sentence]
    # Ensure all_words are also stemmed for comparison
    # This assumes all_words is a list of unique stemmed words forming the vocabulary
    return np.array([1 if w_stemmed in stemmed_sentence else 0 for w_stemmed in all_words])