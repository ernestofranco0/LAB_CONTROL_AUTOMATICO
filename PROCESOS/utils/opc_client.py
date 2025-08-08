from opcua import Client, ua
import logging


class OPCClient:
    def __init__(self, url="opc.tcp://localhost:4840/freeopcua/server/"):
        self.url = url
        self.client = Client(self.url)
        self.objects_node = None
        self.connected = False

    def connect(self):
        try:
            self.client.connect()
            self.objects_node = self.client.get_objects_node()
            self.connected = True
            print("✅ Conectado al servidor OPC UA")
        except Exception as e:
            logging.error(f"Error al conectar: {e}")
            self.connected = False

    def disconnect(self):
        try:
            self.client.disconnect()
            self.connected = False
            print("Desconectado del servidor OPC UA")
        except Exception as e:
            logging.error(f"Error al desconectar: {e}")

    def read_tank_level(self, tank_id):
        """
        Lee el nivel del tanque especificado (1 a 4).
        """
        try:
            path = [f"1:Proceso Tanques", "1:Tanques", f"1:Tanque{tank_id}", "1:h"]
            node = self.objects_node.get_child(path)
            return node.get_value()
        except Exception as e:
            logging.warning(f"Error al leer nivel del Tanque {tank_id}: {e}")
            return None

    def write_valve_voltage(self, valve_id, voltage):
        """
        Escribe el voltaje (0-10V) a una válvula (1 o 2).
        """
        try:
            path = [f"1:Proceso Tanques", "1:Valvulas", f"1:Valvula{valve_id}", "1:u"]
            node = self.objects_node.get_child(path)
            node.set_value(ua.Variant(voltage, ua.VariantType.Float))
        except Exception as e:
            logging.warning(f"Error al escribir voltaje en Válvula {valve_id}: {e}")

    def write_flow_ratio(self, ratio_id, value):
        """
        Escribe una razón de flujo gamma (1 o 2).
        """
        try:
            path = [f"1:Proceso Tanques", "1:Razones", f"1:Razon{ratio_id}", "1:gamma"]
            node = self.objects_node.get_child(path)
            node.set_value(ua.Variant(value, ua.VariantType.Float))
        except Exception as e:
            logging.warning(f"Error al escribir razón gamma {ratio_id}: {e}")


# DEBUGG (solo si se ejecuta directamente)
if __name__ == "__main__":
    opc = OPCClient()
    opc.connect()
    print("Nivel tanque 1:", opc.read_tank_level(1))
    opc.write_valve_voltage(1, 5.0)
    opc.write_flow_ratio(1, 0.7)
    opc.disconnect()
