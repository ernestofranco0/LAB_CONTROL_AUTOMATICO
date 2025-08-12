# from opcua import Client, ua
# from opcua.common.subscription import SubHandler
# from threading import Lock # hilos
# import logging


# class OPCClient:
#     def __init__(self, url="opc.tcp://192.168.1.115:4840/freeopcua/server/"):
#         self.url = url
#         self.client = Client(self.url)
#         self.root = self.client.get_objects_node()
#         self.objects_node = self.client.get_objects_node()
#         self.connected = False
#         # Alarmas
#         self.subscriptions = {} 
#         self.alarm_states = {1: False, 2: False, 3: False, 4: False}
#         self._lock = Lock()

#     def connect(self):
#         try:
#             self.client.connect()
#             self.objects_node = self.client.get_objects_node()
#             self.connected = True
#             print("✅ Conectado al servidor OPC UA")
#         except Exception as e:
#             logging.error(f"Error al conectar: {e}")
#             self.connected = False

#     def disconnect(self):
#         try:
#             for sub in self.subscriptions.values(): # eliminar subscripciones.
#                 sub["subscription"].delete()
#             self.client.disconnect()
#             self.connected = False
#             print("Desconectado del servidor OPC UA")
#         except Exception as e:
#             logging.error(f"Error al desconectar: {e}")

#     def read_tank_level(self, tank_id):
#         """
#         Lee el nivel del tanque especificado (1 a 4).
#         """
#         try:
#             path = [f"1:Proceso_Tanques", "1:Tanques", f"1:Tanque{tank_id}", "1:h"]
#             node = self.objects_node.get_child(path)
#             return node
#         except Exception as e:
#             logging.warning(f"Error al leer nivel del Tanque {tank_id}: {e}")
#             return None

#     def write_valve_voltage(self, valve_id, voltage):
#         """
#         Escribe el voltaje (0-10V) a una válvula (1 o 2).
#         """
#         try:
#             path = [f"1:Proceso Tanques", "1:Valvulas", f"1:Valvula{valve_id}", "1:u"]
#             node = self.objects_node.get_child(path)
#             node.set_value(ua.Variant(voltage, ua.VariantType.Float))
#         except Exception as e:
#             logging.warning(f"Error al escribir voltaje en Válvula {valve_id}: {e}")

#     def write_flow_ratio(self, ratio_id, value):
#         """
#         Escribe una razón de flujo gamma (1 o 2).
#         """
#         try:
#             path = [f"1:Proceso Tanques", "1:Razones", f"1:Razon{ratio_id}", "1:gamma"]
#             node = self.objects_node.get_child(path)
#             node.set_value(ua.Variant(value, ua.VariantType.Float))
#         except Exception as e:
#             logging.warning(f"Error al escribir razón gamma {ratio_id}: {e}")

#     def read_valve_voltage(self, valve_id):
#         try:
#             path = [f"1:Proceso Tanques", "1:Valvulas", f"1:Valvula{valve_id}", "1:u"]
#             node = self.objects_node.get_child(path)
#             return node.get_value()
#         except Exception as e:
#             logging.warning(f"Error al leer voltaje de válvula {valve_id}: {e}")
#             return None

#     def read_flow_ratio(self, ratio_id):
#         try:
#             path = [f"1:Proceso Tanques", "1:Razones", f"1:Razon{ratio_id}", "1:gamma"]
#             node = self.objects_node.get_child(path)
#             return node.get_value()
#         except Exception as e:
#             logging.warning(f"Error al leer razón de flujo {ratio_id}: {e}")
#             return None

#     def subscribe_to_tank_level(self, tank_id, threshold=10.0):
#         """
#         Se suscribe a los cambios de nivel del tanque `tank_id`.
#         Si el nivel baja del `threshold`, lanza una alarma.
#         """
#         try:
#             path = [f"1:Proceso Tanques", "1:Tanques", f"1:Tanque{tank_id}", "1:h"]
#             node = self.objects_node.get_child(path)
#             handler = AlarmHandler(threshold=threshold, tank_id=tank_id)
#             subscription_obj = self.client.create_subscription(1000, handler)
#             handle = subscription_obj.subscribe_data_change(node)

#             self.subscriptions[tank_id] = {
#                 "subscription": subscription_obj,
#                 "handle": handle,
#                 "node": node
#             }

#             print(f"🟢 Subscrito a Tanque {tank_id} (umbral = {threshold} cm)")
#         except Exception as e:
#             logging.warning(f"Error al subscribirse al Tanque {tank_id}: {e}")

# # Clase que maneja los eventos de suscripción
# class AlarmHandler:
#     def __init__(self, threshold=10.0, tank_id=1, client_ref=None):
#         self.threshold = threshold
#         self.tank_id = tank_id
#         self.client_ref = client_ref

#     def datachange_notification(self, node, val, data):
#         if self.client_ref:
#             with self.client_ref._lock:
#                 self.client_ref.alarm_states[self.tank_id] = (val < self.threshold)

# #opc_client_instance = OPCClient()
# # DEBUGG (solo si se ejecuta directamente)
# if __name__ == "__main__":
#     opc = OPCClient()
#     opc.connect()
#     print("Nivel tanque 1:", opc.read_tank_level(1))
#     opc.write_valve_voltage(1, 5.0)
#     opc.write_flow_ratio(1, 0.7)
#     opc.disconnect()


from opcua import ua, Client
import threading
import time

def funcion_handler(node, val):
    key = node.get_parent().get_display_name().Text
    print('key: {} | val: {}'.format(key, val))

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=funcion_handler, args=(node, val))  # Se realiza la descarga por un thread
        thread_handler.start()

    def event_notification(self, event):
        print("Python: New event", event)


class Cliente():
    def __init__(self, direccion, suscribir_eventos, SubHandler):
        self.direccion = direccion
        self.client = Client(direccion)
        self.alturas = {'H1': 0, 'H2': 0, 'H3':0, 'H4':0}
        self.temperaturas = {'T1': 0, 'T2': 0, 'T3':0, 'T4':0}
        self.valvulas = {'valvula1':0, 'valvula2':0}
        self.razones = {'razon1':0, 'razon2': 0}
        self.subscribir_eventos = suscribir_eventos
        self.periodo = 100 # cantidad de milisegundos para revisar las variables subscritas
        self.SubHandlerClass = SubHandler

    def Instanciacion(self):
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques','2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])


        # Obtención de las alturas
        self.alturas['H1'] = self.Tanques.get_child(['2:Tanque1', '2:h'])
        self.alturas['H2'] = self.Tanques.get_child(['2:Tanque2', '2:h'])
        self.alturas['H3'] = self.Tanques.get_child(['2:Tanque3', '2:h'])
        self.alturas['H4'] = self.Tanques.get_child(['2:Tanque4', '2:h'])

        # Obtención de temperaturas
        self.temperaturas['T1'] = self.Tanques.get_child(['2:Tanque1', '2:T'])
        self.temperaturas['T2'] = self.Tanques.get_child(['2:Tanque2', '2:T'])
        self.temperaturas['T3'] = self.Tanques.get_child(['2:Tanque3', '2:T'])
        self.temperaturas['T4'] = self.Tanques.get_child(['2:Tanque4', '2:T'])

        # Obtención de los pumps
        self.valvulas['valvula1'] = self.Valvulas.get_child(['2:Valvula1', '2:u'])
        self.valvulas['valvula2'] = self.Valvulas.get_child(['2:Valvula2', '2:u'])

        # Obtención de los switches
        self.razones['razon1'] = self.Razones.get_child(['2:Razon1', '2:gamma'])
        self.razones['razon2'] = self.Razones.get_child(['2:Razon2', '2:gamma'])

        # Evento (alarma en este caso)
        if self.subscribir_eventos:
            self.myevent = self.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:Alarma_nivel"])#Tipo de evento
            self.obj_event = self.objects.get_child(['2:Proceso_Tanques', '2:Alarmas', '2:Alarma_nivel'])#Objeto Evento
            self.handler_event = self.SubHandlerClass()
            self.sub_event = self.client.create_subscription(self.periodo, self.handler_event)#Subscripción al evento
            self.handle_event = self.sub_event.subscribe_events(self.obj_event, self.myevent)


    def escribir(self, mv, valor):
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques','2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])
        

        # setear pumps
        # 1. Accede al nodo
        if mv == "valvula1":
            valvula1_node = self.Valvulas.get_child(['2:Valvula1', '2:u'])
            # 2. Escribe el valor
            valvula1_node.set_value(ua.Variant(valor, ua.VariantType.Float))
        elif mv == "valvula2": 
            valvula2_node = self.Valvulas.get_child(['2:Valvula2', '2:u'])
            # 2. Escribe el valor
            valvula2_node.set_value(ua.Variant(valor, ua.VariantType.Float))
        elif mv == "razones1":
            razones1_node = self.Razones.get_child(['2:Razon1', '2:gamma'])
            razones1_node.set_value(ua.Variant(valor, ua.VariantType.Float))
        elif mv == "razones2":
            razones2_node = self.Razones.get_child(['2:Razon2', '2:gamma'])
            razones2_node.set_value(ua.Variant(valor, ua.VariantType.Float))  
                      
    def subscribir_cv(self): # Subscripción a las variables controladas
        self.handler_cv = self.SubHandlerClass()
        self.sub_cv = self.client.create_subscription(self.periodo, self.handler_cv)
        for key, var in self.alturas.items():
            self.sub_cv.subscribe_data_change(var)
        for key, var in self.temperaturas.items():
            self.sub_cv.subscribe_data_change(var)


    def subscribir_mv(self): # Subscripación a las variables manipuladas
        self.handler_mv = self.SubHandlerClass()
        self.sub_mv = self.client.create_subscription(self.periodo, self.handler_mv)
        for key, var in self.valvulas.items():
            self.sub_mv.subscribe_data_change(var)
        for key, var in self.razones.items():
            self.sub_mv.subscribe_data_change(var)


    def conectar(self):
        try:
            self.client.connect()
            self.objects = self.client.get_objects_node()
            print('Cliente OPCUA se ha conectado')
            self.Instanciacion()

        except:
            self.client.disconnect()
            print('Cliente no se ha podido conectar')

if __name__ == "__main__":
    cliente = Cliente("opc.tcp://192.168.1.115:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
    cliente.conectar()
    cliente.subscribir_mv() # Se subscribe a las variables manipuladas
    cliente.escribir("razones1", 0.2)
    cliente.escribir("valvula1", 0.7)