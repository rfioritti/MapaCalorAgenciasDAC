import os
import re
from math import ceil

# CONFIG
input_file = "index.html"
output_folder = "js"
chunk_size = 5000

# Crear carpeta js si no existe
os.makedirs(output_folder, exist_ok=True)

# Leer HTML original
with open(input_file, "r", encoding="utf-8") as f:
    html = f.read()

# Extraer todos los circleMarker
match = re.findall(r"L\.circleMarker\([\s\S]+?\.addTo\(poblacionGrupo\);", html)

# Dividir en partes
total_chunks = ceil(len(match) / chunk_size)
script_tags = []

for i in range(total_chunks):
    chunk = match[i * chunk_size : (i + 1) * chunk_size]
    script_name = f"capas_poblacion_{i+1}.js"
    script_path = os.path.join(output_folder, script_name)
    script_tags.append(f'<script src="{output_folder}/{script_name}"></script>')
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(f"// Parte {i+1} de puntos de población\n")
        f.write("var poblacionGrupo = L.layerGroup().addTo(map);\n")
        f.write("\n".join(chunk))

# Reemplazar en el HTML
new_html = re.sub(r'(<script src="js/capas_poblacion.js"></script>|<!-- CAPAS_POBLACION -->)',
                  "\\n".join(script_tags), html)

with open("index_fragmentado.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print(f"Generados {total_chunks} archivos en /{output_folder}/ y archivo index_fragmentado.html")
