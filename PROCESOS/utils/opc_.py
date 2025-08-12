from opcua import Client
from opcua import ua

client = Client("opc.tcp://192.168.1.115:4840/freeopcua/server/")
try:
 client.connect()
 objectsNode = client.get_objects_node()
 print("contecto cts")
except:
 print("no conecto")
 client.disconnect()