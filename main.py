from chat import ChatbotAgenda
from agenda_manager import AgendaManager

class ChatbotCompleto:
    def __init__(self):
        self.chatbot = ChatbotAgenda()
        self.agenda = AgendaManager()

    def iniciar(self):
        print("Chatbot de Agenda - Comandos: agenda, agregar, salir")
        while True:
            mensaje = input("Tú: ")
            
            if mensaje.lower() == 'salir':
                break
                
            respuesta = self.procesar_mensaje(mensaje)
            print("Bot:", respuesta)

    def procesar_mensaje(self, mensaje):
        intencion = self.chatbot.predecir_intencion(mensaje)
        
        if intencion == "agregar_evento":
            return self.manejar_agregar_evento(mensaje)
        elif intencion == "consultar_evento":
            return f"Tienes {len(self.agenda.agenda['eventos'])} eventos en tu agenda"
        else:
            return self.chatbot.generar_respuesta(mensaje)

    def manejar_agregar_evento(self, mensaje):
        # Implementar lógica para extraer fecha y descripción
        descripcion = input("Bot: ¿Qué evento quieres agregar? ")
        fecha = input("Bot: ¿Para qué fecha? (ej: 15/05/2023) ")
        self.agenda.agregar_evento(descripcion, fecha)
        return "Evento agregado correctamente"

if __name__ == "__main__":
    bot = ChatbotCompleto()
    bot.iniciar()