# EJecutar la API
```
source env/bin/activate
pip install flask paramiko pysnmp matplotlib networkx
python3 app.py
```

# Monitoreo de octetos en interfaces de los routers.
## Solicitud GET.

```
curl http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/octetos
```

## Solicitud POST

```
curl -X POST http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/octetos/10?duration=60
```

## Solicitud DELETE

```
curl -X DELETE http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/octetos
```

# Generar gráfica del monitoreo

```
curl http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/grafica --output grafica.png
```

# Traps
## Solicitud GET
```
curl http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/estado
```

## Solucitud POST
```
curl -X POST http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/estado
```

## Solicitud DELETE
```
curl -X DELETE http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/estado
```

## Grafica
```
curl http://localhost:5000/routers/192.168.100.5/interfaces/Fa1/1/grafica_traps --output grafica_traps.png
```

## Correr el programa con permisos sudo por el puerto UDP
sudo env "PATH=$PATH" python3 app.py
