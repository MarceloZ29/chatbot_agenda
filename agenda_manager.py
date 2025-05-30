import json
from datetime import datetime

class AgendaManager:
    def __init__(self, filepath='./data/agenda.json'):
        self.filepath = filepath
        self.cargar_agenda()

    def cargar_agenda(self):
        try:
            with open(self.filepath, 'r') as f:
                self.agenda = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.agenda = {"eventos": []}

    def guardar_agenda(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.agenda, f, indent=2)

    def agregar_evento(self, descripcion, fecha):
        nuevo_evento = {
            "id": len(self.agenda["eventos"]) + 1,
            "descripcion": descripcion,
            "fecha": fecha,
            "creado_en": datetime.now().isoformat()
        }
        self.agenda["eventos"].append(nuevo_evento)
        self.guardar_agenda()
        return True