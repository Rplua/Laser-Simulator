# Fase 4: servidor TCP y driver Python

## Resultado

El simulador del láser ya puede ejecutarse como un proceso independiente. Un
segundo proceso puede conectarse mediante el `LaserDriver`, enviar comandos de
alto nivel y recibir un `LaserSnapshot` como respuesta.

```text
Proceso 1: device_driver
    |
    | TCP: frames con JSON UTF-8
    v
Proceso 2: simulated_device
```

## Piezas principales

### `LaserTCPServer`

Es la frontera de red del dispositivo. Sus responsabilidades son:

- Abrir un socket TCP de escucha.
- Crear un manejador asíncrono para cada cliente.
- Leer fragmentos de bytes sin bloquear las demás conexiones.
- Mantener un `FrameParser` independiente por conexión.
- Entregar payloads completos al `CommandProcessor`.
- Escribir los frames de respuesta.
- Cerrar conexiones, tareas y el socket de escucha durante el apagado.

El servidor no decide si un comando está permitido. Esa regla continúa dentro
de `Laser`.

### `CommandProcessor`

Une el protocolo con la aplicación:

```text
payload de petición
  -> validar comando
  -> ejecutar sobre Laser
  -> construir respuesta
  -> serializar JSON
  -> añadir encabezado
```

El servidor recibe del procesador un frame completo listo para escribir.

### `LaserDriver`

Es la interfaz que utilizará el futuro servicio FastAPI. Oculta los sockets y
los bytes detrás de operaciones comprensibles:

```python
await driver.connect()
await driver.set_target_power(50.0)
await driver.arm()
await driver.start()
snapshot = await driver.get_snapshot()
await driver.disconnect()
```

Todos los comandos devuelven el snapshot real enviado por el dispositivo. El
cliente no inventa ni adelanta el estado.

### `run_simulation`

Es una tarea asíncrona interna del proceso del dispositivo. Utiliza un reloj
monótono para calcular el tiempo transcurrido y llama periódicamente a
`laser.tick(delta_seconds)`.

El servidor y la simulación comparten el mismo objeto `Laser`, pero sus métodos
son síncronos y se ejecutan en un único bucle de eventos. Un método del dominio
termina antes de que otra tarea pueda continuar en un nuevo punto `await`.

### `simulated_device.main`

Es el punto donde se construye la aplicación desde dentro hacia fuera:

```text
Laser
  -> CommandDispatcher
  -> CommandProcessor
  -> LaserTCPServer
```

También inicia la tarea de simulación y garantiza su cancelación durante el
apagado.

## Recorrido completo de un comando

Cuando se ejecuta:

```python
await driver.arm()
```

ocurre lo siguiente:

```text
1. LaserDriver crea CommandRequest("arm") y un request_id nuevo.
2. Serializa el comando como JSON UTF-8.
3. encode_frame añade los cuatro bytes con la longitud.
4. El writer del driver envía el frame por TCP.
5. El reader del servidor recibe uno o varios fragmentos.
6. FrameParser reconstruye el payload completo.
7. CommandProcessor valida y despacha el comando.
8. Laser aplica sus reglas y produce LaserSnapshot.
9. CommandProcessor crea y enmarca la respuesta.
10. El servidor escribe la respuesta por TCP.
11. El driver lee primero el encabezado y luego el payload exacto.
12. Valida la respuesta y comprueba el request_id.
13. Devuelve LaserSnapshot al código que llamó a arm().
```

## Por qué el driver utiliza un lock

Una conexión TCP contiene un único flujo ordenado de bytes. Si dos tareas
escribieran comandos simultáneamente y ambas intentaran leer la siguiente
respuesta, una podría consumir la respuesta de la otra.

El driver utiliza `asyncio.Lock` para mantener una única petición en vuelo:

```text
Tarea A: escribir -> leer su respuesta -> liberar lock
Tarea B: esperar  -> escribir -> leer su respuesta -> liberar lock
```

Esto simplifica la versión 1 del protocolo. Una versión futura podría mantener
varias peticiones pendientes y correlacionarlas mediante `request_id`, pero no
es necesario para este dispositivo.

## Timeouts y conexión incierta

El driver tiene dos límites configurables:

- Timeout de conexión: cuánto espera al abrir el socket.
- Timeout de respuesta: cuánto espera al enviar o recibir una respuesta.

Si vence el timeout de respuesta, el driver descarta la conexión. Una respuesta
tardía podría quedar en el flujo y confundirse con el siguiente comando si se
reutilizara el mismo socket.

## Reconexión controlada

`reconnect(max_attempts, delay_seconds)` realiza un número limitado de intentos
y espera entre ellos. No existe un bucle infinito de reconexión.

El driver no repite automáticamente un comando después de una desconexión. Por
ejemplo, el dispositivo podría haber ejecutado `start`, pero la respuesta
podría haberse perdido. Repetir el comando sin conocer el estado real sería una
decisión insegura.

La recuperación correcta es:

```text
1. Informar del fallo al llamador.
2. Reconectar de forma explícita.
3. Consultar get_snapshot.
4. Reconciliar el estado real antes de decidir otra acción.
```

## Errores del driver

- `DriverNotConnectedError`: se pidió una operación sin conexión.
- `DriverConnectionError`: no pudo conectarse o perdió el socket.
- `DriverTimeoutError`: una operación superó su tiempo máximo.
- `DriverProtocolError`: la respuesta no cumple el protocolo o no corresponde
  al `request_id` enviado.
- `DeviceCommandError`: el dispositivo entendió el comando, pero el dominio lo
  rechazó. Conserva el `ErrorCode` enviado por el servidor.

## Apagado limpio

El orden importa, especialmente en Python 3.14:

```text
1. Dejar de aceptar conexiones nuevas.
2. Cerrar los writers de clientes activos.
3. Cancelar y esperar sus tareas.
4. Esperar el cierre completo del asyncio.Server.
5. Limpiar las colecciones internas.
```

Esperar al servidor antes de cerrar las conexiones activas produciría un
bloqueo, porque `Server.wait_closed()` también espera que esas conexiones
terminen.

## Ejecución en dos procesos

Desde la raíz del repositorio, iniciar el dispositivo:

```bash
.venv/bin/python -m simulated_device.main
```

En otra terminal, ejecutar el cliente de demostración:

```bash
.venv/bin/python -m device_driver.demo
```

El segundo proceso debe imprimir un snapshot recibido realmente a través de
TCP.

## Alcance de la siguiente fase

FastAPI no accederá directamente a `Laser`, `FrameParser` ni a los sockets.
Mantendrá una instancia de `LaserDriver` y utilizará sus métodos de alto nivel
durante el ciclo de vida del servicio y en los endpoints HTTP.
