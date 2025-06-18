import pandas as pd
import geopandas as gpd
import folium
from folium import FeatureGroup, LayerControl, Marker, Circle, CircleMarker, Popup
from shapely.geometry import Point

# Cargar datos
df_agencias = pd.read_excel("Oficinas - Geolocalización.xlsx")
df_pob = pd.read_csv("centroides_poblacion.csv")

# Preprocesamiento
df_agencias = df_agencias.rename(columns={
    "Oficina": "NOMBRE",
    "Latitud": "LAT",
    "Longitud": "LON",
    "Tamaño agencia": "Tamaño"
})
df_agencias = df_agencias.dropna(subset=["LAT", "LON", "Tamaño"])
df_agencias["Tamaño"] = df_agencias["Tamaño"].str.upper()
df_agencias["Radio_km"] = df_agencias["Tamaño"].map({"CH": 2, "M": 8, "G": 15})

# Crear GeoDataFrames
gdf_agencias = gpd.GeoDataFrame(df_agencias, geometry=gpd.points_from_xy(df_agencias["LON"], df_agencias["LAT"]), crs="EPSG:4326")
gdf_pob = gpd.GeoDataFrame(df_pob, geometry=gpd.points_from_xy(df_pob["X"], df_pob["Y"]), crs="EPSG:4326")

# Proyectar a métrico para calcular buffers
gdf_agencias_m = gdf_agencias.to_crs(epsg=3857)
gdf_pob_m = gdf_pob.to_crs(epsg=3857)

# Crear buffers
buffers = []
props = []
for _, row in gdf_agencias_m.iterrows():
    buffered = row.geometry.buffer(row["Radio_km"] * 1000)
    buffers.append(buffered)
    props.append((row["NOMBRE"], row["Tamaño"]))

gdf_buffers = gpd.GeoDataFrame(props, columns=["NOMBRE", "Tamaño"], geometry=buffers, crs=3857)

# Intersección espacial
join = gpd.sjoin(gdf_pob_m, gdf_buffers, predicate="within", how="left")

# Agrupar cobertura
agencias_por_punto = join.groupby(join.index).agg({
    "NOMBRE": lambda x: list(x.dropna())
})

gdf_pob["Coberturas"] = agencias_por_punto["NOMBRE"].apply(len)
gdf_pob["Agencias_que_cubren"] = agencias_por_punto["NOMBRE"]
gdf_pob["Coberturas"] = gdf_pob["Coberturas"].fillna(0).astype(int)
gdf_pob["Agencias_que_cubren"] = gdf_pob["Agencias_que_cubren"].apply(lambda x: x if isinstance(x, list) else [])

# Volver a EPSG:4326
gdf_pob = gdf_pob.to_crs(epsg=4326)

# Función de color por densidad
def color_por_poblacion(pob, cob):
    if pob > 1000:
        return "red"
    elif pob > 500:
        return "orange"
    elif pob > 100:
        return "yellow"
    elif cob == 0:
        return "gray"
    else:
        return "lightgray"

# Crear mapa
m = folium.Map(location=[-32.5, -56], zoom_start=6)
grupo_g = FeatureGroup(name="Agencias Grandes")
grupo_m = FeatureGroup(name="Agencias Medianas")
grupo_ch = FeatureGroup(name="Agencias Chicas")
grupo_pob = FeatureGroup(name="Población")

# Agencias
for _, row in gdf_agencias.iterrows():
    grupo = grupo_g if row["Tamaño"] == "G" else grupo_m if row["Tamaño"] == "M" else grupo_ch
    Circle(
        location=[row.geometry.y, row.geometry.x],
        radius=row["Radio_km"] * 1000,
        color="blue",
        fill=True,
        fill_opacity=0.05,
        opacity=0.5
    ).add_to(grupo)
    Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=Popup(f"<b>{row['NOMBRE']}</b><br>Tamaño: {row['Tamaño']}"),
        icon=folium.Icon(color="blue", icon="building", prefix="fa")
    ).add_to(grupo)

# Población
for _, row in gdf_pob.iterrows():
    color = color_por_poblacion(row["POB_TOT_23"], row["Coberturas"])
    texto = f"<b>Población:</b> {int(row['POB_TOT_23'])}<br><b>Agencias que cubren:</b> {row['Coberturas']}"
    if row["Coberturas"] > 0:
        texto += "<br>" + "<br>".join(row["Agencias_que_cubren"])
    CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=3,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        color=None,
        popup=Popup(texto, max_width=300)
    ).add_to(grupo_pob)

# Añadir capas al mapa
grupo_g.add_to(m)
grupo_m.add_to(m)
grupo_ch.add_to(m)
grupo_pob.add_to(m)
LayerControl(collapsed=False).add_to(m)

# Guardar mapa
m.save("index.html")
print("Mapa guardado como index.html")
