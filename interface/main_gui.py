import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import json
import os
import random
from datetime import datetime
from utils.date_utils import extract_datetime, extract_event_description
import re

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        try:
            from model.predict_intent import IntentPredictor
            self.predictor = IntentPredictor()
            self.load_agenda()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el chatbot:\n{str(e)}")
            self.root.destroy()

    def setup_ui(self):
        self.root.title("Chatbot de Agenda Inteligente")
        self.root.geometry("1100x650")
        
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel de chat (60% del ancho)
        chat_frame = tk.LabelFrame(main_frame, text="Chat", padx=5, pady=5)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.chat_history = scrolledtext.ScrolledText(
            chat_frame, 
            state='disabled',
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        
        # Panel de agenda (40% del ancho)
        agenda_frame = tk.LabelFrame(main_frame, text="Citas Agendadas", padx=5, pady=5)
        agenda_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        self.agenda_tree = ttk.Treeview(
            agenda_frame,
            columns=('Fecha', 'Evento'),
            show='headings',
            height=25
        )
        self.agenda_tree.heading('Fecha', text='Fecha')
        self.agenda_tree.heading('Evento', text='Evento')
        self.agenda_tree.column('Fecha', width=150, anchor='w')
        self.agenda_tree.column('Evento', width=300, anchor='w')
        self.agenda_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar para agenda
        scrollbar = ttk.Scrollbar(agenda_frame, orient="vertical", command=self.agenda_tree.yview)
        self.agenda_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel de entrada
        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.user_input = tk.Entry(
            input_frame,
            font=('Arial', 10)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", lambda e: self.process_input())
        
        send_btn = tk.Button(
            input_frame,
            text="Enviar",
            command=self.process_input,
            bg='#4CAF50',
            fg='white'
        )
        send_btn.pack(side=tk.RIGHT)

    def process_input(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
            
        self.display_message(f"Tú: {user_text}", 'user')
        self.user_input.delete(0, tk.END)
        
        try:
            intent, confidence = self.predictor.predict(user_text)
            
            if intent == "agregar_evento":
                self.handle_add_event(user_text)
            elif intent == "consultar_evento":
                self.handle_consult_events()
            elif intent == "eliminar_evento":
                self.handle_delete_event(user_text)
            else:
                response = self.predictor.get_response(intent)
                self.display_message(f"Bot: {response}", 'bot')
                
        except Exception as e:
            self.display_message(f"Bot: Error procesando tu mensaje - {str(e)}", 'error')

    def handle_add_event(self, user_text):
        """Maneja la adición automática de eventos"""
        try:
        # Extraer fecha y descripción
            date_str = extract_datetime(user_text)
            desc = extract_event_description(user_text, date_str) if date_str else None
        
            if not date_str:
                self.display_message("Bot: No pude entender la fecha. Por favor usa formato: '25 de mayo a las 3pm'", 'bot')
                return
        
        # Limpieza de la descripción
            desc = re.sub(r'\b(?:agenda|agendar|programa|crea|reserva)\b', '', desc or '', flags=re.IGNORECASE)
            desc = re.sub(r'\s+', ' ', desc).strip()
            desc = desc.capitalize() or "Evento sin descripción"
        
        # Agregar a la agenda
            self.add_event(desc, date_str)
            response = random.choice([
                f"Evento agregado: {desc} el {date_str}",
                f"Agendado: {desc} para {date_str}",
                f"Listo: {desc} - {date_str}"
            ])
            self.display_message(f"Bot: {response}", 'bot')
        
        except Exception as e:
            self.display_message(f"Bot: Error al procesar - {str(e)}", 'error')

    def handle_consult_events(self):
        """Muestra los eventos agendados"""
        if not self.agenda_tree.get_children():
            self.display_message("Bot: No tienes eventos agendados aún.", 'bot')
        else:
            self.display_message("Bot: Estos son tus eventos:", 'bot')

    def handle_delete_event(self, user_text):
        """Maneja la eliminación de eventos"""
        selected = self.agenda_tree.selection()
        if selected:
            self.agenda_tree.delete(selected)
            self.save_agenda()
            self.display_message("Bot: Evento eliminado correctamente", 'bot')
        else:
            self.display_message("Bot: Selecciona un evento de la lista para eliminar", 'bot')

    def show_event_dialog(self, user_text=""):
        """Muestra diálogo para confirmar/editar eventos"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirmar Evento")
        
        tk.Label(dialog, text="Descripción:").pack()
        desc_entry = tk.Entry(dialog, width=50)
        desc_entry.insert(0, user_text)
        desc_entry.pack()
        
        tk.Label(dialog, text="Fecha (ej: 25/05 14:00):").pack()
        date_entry = tk.Entry(dialog, width=50)
        date_entry.pack()
        
        def save_and_close():
            desc = desc_entry.get()
            date = date_entry.get()
            if desc and date:
                self.add_event(desc, date)
                self.display_message(f"Bot: Confirmado: {desc} - {date}", 'bot')
            dialog.destroy()
        
        tk.Button(dialog, text="Guardar", command=save_and_close).pack(pady=5)

    def add_event(self, description, date_str):
        """Añade evento a la agenda"""
        try:
            agenda_file = os.path.join(BASE_DIR, 'data', 'agenda.json')
            
            if os.path.exists(agenda_file):
                with open(agenda_file, 'r', encoding='utf-8') as f:
                    agenda = json.load(f)
            else:
                agenda = {"eventos": []}
            
            agenda["eventos"].append({
                "descripcion": description,
                "fecha": date_str,
                "creado_en": datetime.now().isoformat()
            })
            
            with open(agenda_file, 'w', encoding='utf-8') as f:
                json.dump(agenda, f, indent=2, ensure_ascii=False)
            
            self.load_agenda()
            
        except Exception as e:
            self.display_message(f"Bot: Error al guardar - {str(e)}", 'error')

    def load_agenda(self):
        """Carga los eventos en el Treeview"""
        self.agenda_tree.delete(*self.agenda_tree.get_children())
        
        try:
            agenda_file = os.path.join(BASE_DIR, 'data', 'agenda.json')
            if os.path.exists(agenda_file):
                with open(agenda_file, 'r', encoding='utf-8') as f:
                    agenda = json.load(f)
                
                for evento in agenda.get("eventos", []):
                    self.agenda_tree.insert('', 'end', values=(
                        evento.get("fecha", "Sin fecha"),
                        evento.get("descripcion", "Sin descripción")
                    ))
        except Exception as e:
            print(f"Error cargando agenda: {str(e)}")

    def save_agenda(self):
        """Guarda los cambios en agenda.json"""
        try:
            agenda_file = os.path.join(BASE_DIR, 'data', 'agenda.json')
            eventos = []
            
            for item in self.agenda_tree.get_children():
                valores = self.agenda_tree.item(item)['values']
                eventos.append({
                    "descripcion": valores[1],
                    "fecha": valores[0]
                })
            
            with open(agenda_file, 'w', encoding='utf-8') as f:
                json.dump({"eventos": eventos}, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.display_message(f"Bot: Error guardando agenda - {str(e)}", 'error')

    def display_message(self, message, sender):
        """Muestra mensaje en el chat con estilo"""
        self.chat_history.config(state='normal')
        
        # Configurar tags para diferentes remitentes
        tag_colors = {
            'user': 'blue',
            'bot': 'green',
            'error': 'red'
        }
        
        if sender not in self.chat_history.tag_names():
            self.chat_history.tag_config(sender, foreground=tag_colors.get(sender, 'black'))
        
        self.chat_history.insert(tk.END, message + "\n", sender)
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent
    
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()