import json
import random
import numpy as np
import pickle
import nltk
from nltk.stem import PorterStemmer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
import sys
from pathlib import Path

# Configuración de paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from utils.preprocessing import tokenize, stem, bag_of_words, clean_text  # Nueva función clean_text

# Descargar recursos de NLTK
nltk.download('punkt', quiet=True)

def load_and_preprocess_data():
    """Carga y preprocesa los datos de entrenamiento"""
    # Cargar datos
    with open(BASE_DIR/'data'/'intents.json', encoding='utf-8') as file:
        data = json.load(file)
    
    palabras = []
    tags = []
    xy = []
    
    # Preprocesamiento mejorado
    for intent in data['intents']:
        tag = intent['tag']
        tags.append(tag)
        for pattern in intent['patterns']:
            # Limpieza adicional del texto
            cleaned_text = clean_text(pattern)
            tokens = tokenize(cleaned_text)
            palabras.extend(tokens)
            xy.append((tokens, tag))
    
    # Stemming y filtrado
    palabras = [stem(w) for w in palabras if w not in ["?", "!", ".", ","]]
    palabras = sorted(list(set(palabras)))
    tags = sorted(list(set(tags)))
    
    return palabras, tags, xy

def create_model(input_shape, output_shape):
    """Crea un modelo mejorado de red neuronal"""
    model = Sequential([
        Dense(256, input_shape=input_shape, activation='relu'),
        BatchNormalization(),
        Dropout(0.6),
        Dense(128, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        Dense(output_shape, activation='softmax')
    ])
    
    optimizer = Adam(learning_rate=0.001)
    model.compile(loss='categorical_crossentropy',
                 optimizer=optimizer,
                 metrics=['accuracy'])
    
    return model

def main():
    # 1. Cargar y preprocesar datos
    palabras, tags, xy = load_and_preprocess_data()
    
    # 2. Preparar datos de entrenamiento
    X = []
    y = []
    
    for (pattern_sentence, tag) in xy:
        bow = bag_of_words(pattern_sentence, palabras)
        X.append(bow)
        y.append(tags.index(tag))
    
    X = np.array(X)
    y = np.eye(len(tags))[y]  # One-hot encoding
    
    # 3. Dividir en train y validation
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # 4. Crear y entrenar el modelo
    model = create_model((X_train.shape[1],), y_train.shape[1])
    
    callbacks = [
        EarlyStopping(patience=10, restore_best_weights=True),
        ModelCheckpoint(
            str(BASE_DIR/'model'/'best_model.h5'),
            save_best_only=True,
            monitor='val_accuracy'
        )
    ]
    
    history = model.fit(
        X_train, y_train,
        epochs=300,
        batch_size=16,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        verbose=1
    )
    
    # 5. Guardar recursos finales
    model.save(BASE_DIR/'model'/'modelo_chatbot.h5')
    
    with open(BASE_DIR/'model'/'palabras.pkl', 'wb') as f:
        pickle.dump(palabras, f)
    
    with open(BASE_DIR/'model'/'tags.pkl', 'wb') as f:
        pickle.dump(tags, f)
    
    print("\n✅ Entrenamiento completado:")
    print(f"- Vocabulario: {len(palabras)} palabras")
    print(f"- Intenciones: {len(tags)} tags")
    print(f"- Mejor val_accuracy: {max(history.history['val_accuracy']):.4f}")

if __name__ == "__main__":
    main()