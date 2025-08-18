from opcua import ua, Client
import threading
import time

def funcion_handler(node, val):
    key = node.get_parent().get_display_name().Text
    print('key: {} | val: {}'.format(key, val))

class SubHandler(object):
    def __init__(self, owner=None):
        self.owner = owner  # puede ser None (para eventos), o Cliente en datachange

    def datachange_notification(self, node, val, data):
        # logging no bloqueante (opcional)
        try:
            thread_handler = threading.Thread(target=funcion_handler, args=(node, val))
            thread_handler.daemon = True
            thread_handler.start()
        except Exception:
            pass

        # actualizar estados de alarma si tenemos owner
        if self.owner is None:
            return
        try:
            with self.owner._lock:
                # mapear nodeid -> 'H1'...'H4'
                key = self.owner.node_to_tank.get(node.nodeid, None)
                if key is None:
                    return
                self.owner.last_levels[key] = float(val)
                thr = self.owner.thresholds.get(key, None)
                if thr is not None:
                    self.owner.alarm_states[key] = (float(val) < float(thr))
        except Exception:
            pass

    def event_notification(self, event):
        print("Python: New event", event)

class Cliente():
    def __init__(self, direccion, suscribir_eventos, SubHandler):
        self.direccion = direccion
        self.client = Client(direccion)
        self._lock = threading.Lock()  # <--- NUEVO

        self.alturas = {'H1': 0, 'H2': 0, 'H3':0, 'H4':0}
        self.temperaturas = {'T1': 0, 'T2': 0, 'T3':0, 'T4':0}
        self.valvulas = {'valvula1':0, 'valvula2':0}
        self.razones = {'razon1':0, 'razon2': 0}

        # --- NUEVO: estados de alarmas / umbrales / últimos niveles
        self.thresholds  = {'H1': None, 'H2': None, 'H3': None, 'H4': None}
        self.last_levels = {'H1': None, 'H2': None, 'H3': None, 'H4': None}
        self.alarm_states = {'H1': False, 'H2': False, 'H3': False, 'H4': False}
        self.node_to_tank = {}   # NodeId -> 'H1'...'H4'

        self.subscribir_eventos = suscribir_eventos
        self.periodo = 100 # ms
        self.SubHandlerClass = SubHandler

        # --- NUEVO: datos de suscripción a niveles
        self._sub_levels = None
        self._sub_levels_handles = []
        self._subscribed_levels = False

        self._connected = False  # <--- NUEVO

    def is_connected(self):
        return bool(self._connected)

    def Instanciacion(self):

        #aqui tengo que agregar la carpeta de Alarmas
        #self.Alarmas = self.objets.get_child(['2:Proceso_Tanques','2:Alarmas']) #esto me permite acceder a las alarmas de los 4 niveles (por implementar)
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques','2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])

        # Alturas (nodos)
        self.alturas['H1'] = self.Tanques.get_child(['2:Tanque1', '2:h'])
        self.alturas['H2'] = self.Tanques.get_child(['2:Tanque2', '2:h'])
        self.alturas['H3'] = self.Tanques.get_child(['2:Tanque3', '2:h'])
        self.alturas['H4'] = self.Tanques.get_child(['2:Tanque4', '2:h'])

        # --- NUEVO: mapeo nodeid -> 'H#'
        self.node_to_tank[self.alturas['H1'].nodeid] = 'H1'
        self.node_to_tank[self.alturas['H2'].nodeid] = 'H2'
        self.node_to_tank[self.alturas['H3'].nodeid] = 'H3'
        self.node_to_tank[self.alturas['H4'].nodeid] = 'H4'

        # Temperaturas (nodos)
        self.temperaturas['T1'] = self.Tanques.get_child(['2:Tanque1', '2:T'])
        self.temperaturas['T2'] = self.Tanques.get_child(['2:Tanque2', '2:T'])
        self.temperaturas['T3'] = self.Tanques.get_child(['2:Tanque3', '2:T'])
        self.temperaturas['T4'] = self.Tanques.get_child(['2:Tanque4', '2:T'])

        # Válvulas (nodos)
        self.valvulas['valvula1'] = self.Valvulas.get_child(['2:Valvula1', '2:u'])
        self.valvulas['valvula2'] = self.Valvulas.get_child(['2:Valvula2', '2:u'])

        # Razones (nodos)
        self.razones['razon1'] = self.Razones.get_child(['2:Razon1', '2:gamma'])
        self.razones['razon2'] = self.Razones.get_child(['2:Razon2', '2:gamma'])

        # Eventos (si decides mantenerlos)
        if self.subscribir_eventos:
            self.myevent = self.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:Alarma_nivel"])
            self.obj_event = self.objects.get_child(['2:Proceso_Tanques', '2:Alarmas', '2:Alarma_nivel'])
            self.handler_event = self.SubHandlerClass()  # sin owner
            self.sub_event = self.client.create_subscription(self.periodo, self.handler_event)
            self.handle_event = self.sub_event.subscribe_events(self.obj_event, self.myevent)

    def set_alarm_thresholds(self, h1=None, h2=None, h3=None, h4=None):
        with self._lock:
            if h1 is not None: self.thresholds['H1'] = float(h1)
            if h2 is not None: self.thresholds['H2'] = float(h2)
            if h3 is not None: self.thresholds['H3'] = float(h3)
            if h4 is not None: self.thresholds['H4'] = float(h4)

    def enable_level_subscription(self):
        if self._subscribed_levels:
            return True
        handler = self.SubHandlerClass(owner=self)  # ahora con owner
        self._sub_levels = self.client.create_subscription(self.periodo, handler)
        self._sub_levels_handles = []
        # suscribir h1..h4
        for key in ('H1','H2','H3','H4'):
            handle = self._sub_levels.subscribe_data_change(self.alturas[key])
            self._sub_levels_handles.append(handle)
        self._subscribed_levels = True
        return True

    def disable_level_subscription(self):
        try:
            if self._sub_levels:
                for h in self._sub_levels_handles:
                    self._sub_levels.unsubscribe(h)
                self._sub_levels.delete()
        except Exception:
            pass
        self._sub_levels = None
        self._sub_levels_handles = []
        self._subscribed_levels = False
        return True

    def is_level_subscribed(self):
        return bool(self._subscribed_levels)

    # --- NUEVO: snapshot para la UI
    def get_alarm_snapshot(self):
        with self._lock:
            return (self.last_levels.copy(), self.thresholds.copy(), self.alarm_states.copy())

    def escribir(self, mv, valor):
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
        elif mv == "razon1":
            razones1_node = self.Razones.get_child(['2:Razon1', '2:gamma'])
            razones1_node.set_value(ua.Variant(valor, ua.VariantType.Float))
        elif mv == "razon2":
            razones2_node = self.Razones.get_child(['2:Razon2', '2:gamma'])
            razones2_node.set_value(ua.Variant(valor, ua.VariantType.Float))  
        
    def read_tank_level(self, tank_id):
        try:
            key = f"H{tank_id}"
            node = self.alturas[key]
            return float(node.get_value())
        except Exception as e:
            print(f"❌ Error al leer nivel del Tanque {tank_id}: {e}")
            return None

    def read_valve_voltage(self, valvula_id):
        try:
            key = f"valvula{valvula_id}"
            return float(self.valvulas[key].get_value())
        except Exception as e:
            print(f"❌ Error al leer voltaje de válvula {valvula_id}: {e}")
            return None

    def read_flow_ratio(self, razon_id):
        try:
            key = f"razon{razon_id}"
            return float(self.razones[key].get_value())
        except Exception as e:
            print(f"❌ Error al leer razón de flujo {razon_id}: {e}")
            return None

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
            self._connected = True 
            self.Instanciacion()
        except:
            self.client.disconnect()
            self._connected = False 
            print('Cliente no se ha podido conectar')

opc_client_instance = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
opc_client_instance.conectar()
if __name__ == "__main__":
    #cliente = Cliente("opc.tcp://192.168.1.115:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
    cliente = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)

    cliente.conectar()
    cliente.subscribir_mv() # Se subscribe a las variables manipuladas
    cliente.escribir("razon1", 0.2)
    cliente.escribir("valvula1", 0.7)