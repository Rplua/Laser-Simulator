# Asyncio y servidor TCP

Esta guía explica la capa de transporte de la fase 4. El objetivo es conectar
el protocolo ya implementado con una red TCP real, manteniendo la lógica del
láser separada de los sockets.

## Qué añade la fase 4

Hasta la fase 3, el sistema puede recibir un `payload` en memoria, validarlo,
ejecutar un comando y producir una respuesta enmarcada. La fase 4 permite que
esos bytes viajen entre procesos:

```text
Driver Python
    |
    | TCP
    v
LaserTCPServer
    |
    v
FrameParser -> CommandProcessor -> CommandDispatcher -> Laser
```

TCP solo transporta un flujo ordenado de bytes. No conserva los límites de
los mensajes. Por ese motivo, el servidor continúa necesitando el
`FrameParser` desarrollado en la fase 3.

## Qué es `asyncio`

`asyncio` es la biblioteca estándar de Python para ejecutar operaciones
concurrentes basadas principalmente en espera, como conexiones de red.

Cuando una conexión está esperando datos, el servidor puede atender otra en
vez de bloquear todo el proceso:

```text
Cliente A: esperando bytes ----------- recibe bytes
                    |
                    +-> Python atiende al cliente B
```

Esto no implica crear un hilo por cliente. Un bucle de eventos coordina las
tareas y cambia de una a otra cuando alcanzan una operación que debe esperar.

## `async def` y `await`

Una función declarada con `async def` es una corrutina:

```python
async def start(self) -> None:
    ...
```

Dentro de ella, `await` indica un punto donde la tarea puede quedar en pausa
sin bloquear todo el bucle de eventos:

```python
data = await reader.read(4096)
```

La lectura espera bytes para esa conexión. Mientras tanto, `asyncio` puede
continuar ejecutando otras tareas.

## Arrancar el servidor

El servidor se abre una sola vez:

```python
self._server = await asyncio.start_server(
    self._handle_client,
    self._host,
    self._port,
)
```

`asyncio.start_server`:

1. Abre un socket de escucha en el host y puerto indicados.
2. Registra `_handle_client` como manejador de nuevas conexiones.
3. Devuelve el objeto `asyncio.Server` que representa el servidor abierto.

Se pasa `self._handle_client`, sin paréntesis, porque entregamos la función a
`asyncio` para que pueda ejecutarla cuando se conecte un cliente.

## Atender a un cliente

Por cada conexión, `asyncio` invoca el manejador con dos objetos:

```python
async def _handle_client(
    self,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    ...
```

- `reader` permite recibir bytes de ese cliente.
- `writer` permite enviarle bytes y cerrar su conexión.

El manejador no crea otro servidor. Atiende únicamente la conexión que
representan su `reader` y su `writer`.

## Lectura y reconstrucción de mensajes

Esta operación lee como máximo 4096 bytes disponibles:

```python
data = await reader.read(4096)
```

El número 4096 no representa el tamaño de un mensaje. Una lectura puede
contener medio frame, uno completo o varios frames. El resultado se entrega al
parser:

```python
payloads = frame_parser.feed(data)
```

El parser devuelve solamente los payloads completos y conserva internamente
el fragmento incompleto, si existe, hasta la próxima lectura.

Cada conexión necesita su propio `FrameParser`. Compartir uno mezclaría los
bytes enviados por clientes diferentes:

```text
Cliente A -> FrameParser A
Cliente B -> FrameParser B
```

## Procesamiento y respuesta

Cada payload completo se entrega al procesador de la aplicación:

```python
response_frame = self._command_processor.process_payload(payload)
```

El recorrido de entrada es:

```text
TCP bytes
  -> FrameParser
  -> decode_command
  -> CommandRequest
  -> CommandDispatcher
  -> Laser
```

La respuesta realiza el recorrido inverso:

```text
LaserSnapshot
  -> modelo de respuesta
  -> JSON UTF-8
  -> frame con encabezado
  -> TCP bytes
```

El `CommandProcessor` ya realiza esta transformación de vuelta. El servidor
solo debe escribir el frame obtenido:

```python
writer.write(response_frame)
await writer.drain()
```

`write` coloca los bytes en el buffer de salida. `drain` permite esperar si el
buffer está lleno, sin bloquear las demás tareas.

## Cierre de una conexión

Una lectura vacía (`b""`) significa que el cliente cerró la conexión. El
servidor debe liberar siempre sus recursos, incluso cuando ocurre un error:

```python
writer.close()
await writer.wait_closed()
```

Por eso estas operaciones se colocan en un bloque `finally`.

## Construcción de dentro hacia fuera

Al iniciar el proceso, las dependencias se construyen desde el dominio hasta
el transporte:

```text
Laser
  -> CommandDispatcher
  -> CommandProcessor
  -> LaserTCPServer
```

En cambio, durante una petición, el comando viaja desde el servidor hacia el
láser y la respuesta vuelve desde el láser hacia el servidor.

Esta separación permite probar el dominio sin red, probar el protocolo con
bytes en memoria y probar el servidor TCP como una capa independiente.
