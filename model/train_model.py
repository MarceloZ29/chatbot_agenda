import json
import random
import numpy as np
import pickle

import nltk
from nltk.stem import PorterStemmer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD

from utils.preprocessing import tokenize, stem, bag_of_words

# Descargar recursos de NLTK
nltk.download('punkt')

# Inicializamos el stemmer
stemmer = PorterStemmer()

# Cargar datos del archivo intents.json
with open('./data/intents.json', encoding='utf-8') as file:
    data = json.load(file)

palabras = []
tags = []
xy = []

# Preprocesamiento
for intent in data['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        palabras.extend(w)
        xy.append((w, tag))

# Aplicamos stemming y ordenamos
palabras = [stem(w) for w in palabras if w != "?"]
palabras = sorted(list(set(palabras)))
tags = sorted(list(set(tags)))

# Crear training data
X_train = []
y_train = []

for (pattern_sentence, tag) in xy:
    bow = bag_of_words(pattern_sentence, palabras)
    X_train.append(bow)

    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.eye(len(tags))[y_train]  # One-hot encoding

# Crear el modelo (MLP)
model = Sequential()
model.add(Dense(128, input_shape=(len(X_train[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(y_train[0]), activation='softmax'))

# Compilar
sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Entrenar
model.fit(X_train, y_train, epochs=200, batch_size=8, verbose=1)

# Guardar modelo y recursos
model.save("./model/modelo_chatbot.h5")
with open('./model/palabras.pkl', 'wb') as f:
    pickle.dump(palabras, f)
with open('./model/tags.pkl', 'wb') as f:
    pickle.dump(tags, f)

print("✅ Modelo entrenado y guardado exitosamente.")
