import matplotlib.pyplot as plt
import csv

# --- Leer datos desde el archivo CSV ---
tiempos = []
h1 = []
h2 = []
h3 = []
h4 = []

with open("data/alturas.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)  # Saltar encabezado

    for row in reader:
        tiempos.append(float(row[0]))
        h1.append(float(row[1]))
        h2.append(float(row[2]))
        h3.append(float(row[3]))
        h4.append(float(row[4]))

# --- Graficar las alturas ---
plt.figure(figsize=(10, 6))
plt.plot(tiempos, h1, label='Tanque 1')
plt.plot(tiempos, h2, label='Tanque 2')
plt.plot(tiempos, h3, label='Tanque 3')
plt.plot(tiempos, h4, label='Tanque 4')

plt.xlabel("Tiempo [s]")
plt.ylabel("Altura [cm]")
plt.title("Evolución de Alturas de los Tanques")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
