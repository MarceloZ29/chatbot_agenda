import json
from datetime import datetime, date, timedelta

class AgendaManager:
    def __init__(self, filepath='./data/agenda.json'):
        self.filepath = filepath
        self.cargar_agenda()

    def cargar_agenda(self):
        try:
            with open(self.filepath, 'r') as f:
                self.agenda = json.load(f)
                # Ensure 'eventos' key exists
                if "eventos" not in self.agenda:
                    self.agenda["eventos"] = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.agenda = {"eventos": []}

    def guardar_agenda(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.agenda, f, indent=2, ensure_ascii=False)

    def agregar_evento(self, descripcion, fecha, hora=None):
        if not self.agenda["eventos"]:
            nuevo_id = 1
        else:
            nuevo_id = max(evento.get("id", 0) for evento in self.agenda["eventos"]) + 1
        
        # Combine fecha and hora if hora is provided
        fecha_evento = fecha
        if hora:
            fecha_evento = f"{fecha} {hora}"

        nuevo_evento = {
            "id": nuevo_id,
            "descripcion": descripcion,
            "fecha": fecha_evento, # Stores as "YYYY-MM-DD" or "YYYY-MM-DD HH:MM"
            "creado_en": datetime.now().isoformat()
        }
        self.agenda["eventos"].append(nuevo_evento)
        self.guardar_agenda()
        return {"status": "success", "message": "Evento agregado.", "evento": nuevo_evento}

    def consultar_eventos(self, fecha_consulta=None, dia_consulta=None):
        eventos_filtrados = []
        target_date_str = None

        if fecha_consulta:
            target_date_str = fecha_consulta # Expects "YYYY-MM-DD"
        elif dia_consulta:
            dia_consulta_lower = dia_consulta.lower()
            if dia_consulta_lower == "hoy":
                target_date_str = date.today().strftime("%Y-%m-%d")
            elif dia_consulta_lower == "mañana":
                target_date_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            # Add handling for specific day names like "lunes", "martes" if necessary in the future
            # For now, only "hoy", "mañana" and direct date strings are supported for dia_consulta
            elif dia_consulta_lower in ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]:
                # This part requires a more complex utility to find the next occurrence of a given weekday.
                # For now, we'll return an empty list or indicate not supported for these day names if not a direct date.
                # Or, if we assume dia_consulta can also be a date string like "2024-07-30"
                try:
                    datetime.strptime(dia_consulta, "%Y-%m-%d")
                    target_date_str = dia_consulta
                except ValueError:
                    # It's a day name we don't fully support yet for future dates beyond tomorrow
                    # Return empty or a specific message, or try to parse it if it's a full date
                    pass # Handled by target_date_str remaining None or being set

        if not target_date_str and not fecha_consulta and not dia_consulta:
            return self.agenda["eventos"] # Return all events

        if not target_date_str: # If date parsing from dia_consulta failed for specific day names
            return []

        for evento in self.agenda["eventos"]:
            # Event fecha can be "YYYY-MM-DD" or "YYYY-MM-DD HH:MM..."
            # We compare only the date part.
            event_date_str_part = evento["fecha"].split(" ")[0]
            if event_date_str_part == target_date_str:
                eventos_filtrados.append(evento)
        
        return eventos_filtrados

    def eliminar_evento(self, event_id=None, event_description=None):
        evento_eliminado = False
        message = "" # Initialize message to ensure it's always defined
        if event_id is not None:
            try:
                event_id_int = int(event_id)
                original_count = len(self.agenda["eventos"])
                self.agenda["eventos"] = [e for e in self.agenda["eventos"] if e.get("id") != event_id_int]
                if len(self.agenda["eventos"]) < original_count:
                    evento_eliminado = True
                    message = f"Evento con ID {event_id_int} eliminado."
                else:
                    message = f"Evento con ID {event_id_int} no encontrado."
            except ValueError:
                 return {"status": "error", "message": "ID de evento inválido. Debe ser un número."}
        
        elif event_description is not None:
            original_count = len(self.agenda["eventos"])
            # Delete first match by description
            found_event_to_delete_idx = -1 # Use index to avoid issues with modifying list while iterating
            for i, evento in enumerate(self.agenda["eventos"]):
                if evento.get("descripcion") == event_description:
                    found_event_to_delete_idx = i
                    break
            
            if found_event_to_delete_idx != -1:
                del self.agenda["eventos"][found_event_to_delete_idx]
                evento_eliminado = True
                message = f"Evento '{event_description}' eliminado."
            else:
                message = f"Evento con descripción '{event_description}' no encontrado."
        else:
            return {"status": "error", "message": "Se requiere ID o descripción del evento para eliminar."}

        if evento_eliminado:
            self.guardar_agenda()
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    def obtener_todos_los_eventos(self):
        return self.agenda["eventos"]