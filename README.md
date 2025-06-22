# EJecutar la API
```
source env/bin/activate
pip install flask paramiko pysnmp matplotlib networkx
python3 app.py
```

# Monitoreo de octetos en interfaces de los routers.
## Solicitud GET.

```
curl http://localhost:5000/routers/192.168.100.4/interfaces/Fa1/1/octetos
```

## Solicitud POST

```
curl -X POST http://localhost:5000/routers/192.168.100.4/interfaces/Fa1/1/octetos/10?duration=60
```

## Solicitud DELETE

```
curl -X DELETE http://localhost:5000/routers/192.168.100.4/interfaces/Fa1/1/octetos
```

# Generar gráfica del monitoreo

```
curl http://localhost:5000/routers/192.168.100.4/interfaces/Fa1/1/grafica --output grafica.png
```