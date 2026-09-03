# TCP Application Protocol

## Frame format

Cada frame se compone de dos elementos: un encabezado y un payload.

El encabezado ocupa siempre 4 bytes y contiene la longitud del payload. Este
valor no incluye los 4 bytes del propio encabezado. El payload ocupa `N` bytes
y contiene un documento JSON codificado en UTF-8.

Por tanto, el tamaño total de un frame es:

```text
4 bytes de encabezado + N bytes de payload
```

## Byte order

El encabezado representa la longitud del payload mediante un entero sin signo
de 4 bytes. Este entero utiliza orden de bytes *big-endian*, también conocido
como orden de bytes de red.

El emisor y el receptor deben utilizar el mismo orden para interpretar la
longitud correctamente.

## Maximum message size

Un payload válido debe cumplir este límite:

```text
1 byte <= payload <= 65 536 bytes
```

Una longitud igual a `0` o superior a `65 536` bytes se considera inválida.
El receptor debe rechazar el frame antes de intentar reservar memoria o
decodificar el payload.

Este límite evita un consumo de memoria descontrolado y es suficiente para los
comandos y snapshots pequeños utilizados por el simulador.

## Command request

Una petición de comando utiliza siempre el mismo sobre JSON:

```json
{
  "protocol_version": 1,
  "message_type": "command",
  "request_id": "6d471ca2-f424-4c9c-9d09-e45d6a587db5",
  "command": "arm",
  "payload": {}
}
```

Todos los campos son obligatorios:

| Campo | Tipo JSON | Regla |
| --- | --- | --- |
| `protocol_version` | number | Debe ser el entero `1` |
| `message_type` | string | Debe ser `"command"` |
| `request_id` | string | UUID generado por el cliente |
| `command` | string | Uno de los comandos soportados |
| `payload` | object | Datos específicos del comando; puede estar vacío |

El cliente genera un `request_id` nuevo para cada petición. El servidor debe
copiar ese mismo identificador en la respuesta. El cliente utiliza el
identificador para relacionar respuestas, timeouts y logs con la petición
original.

Los tipos son estrictos. Por ejemplo, una potencia debe enviarse como número
JSON (`50`) y no como texto (`"50"`). Los campos desconocidos se rechazan en la
versión 1 del protocolo.

Ejemplo de configuración de potencia:

```json
{
  "protocol_version": 1,
  "message_type": "command",
  "request_id": "6d471ca2-f424-4c9c-9d09-e45d6a587db5",
  "command": "set_target_power",
  "payload": {
    "target_power_mw": 50
  }
}
```

## Successful response

Una operación aceptada devuelve `status: "ok"` y el snapshot resultante del
láser:

```json
{
  "protocol_version": 1,
  "message_type": "response",
  "request_id": "6d471ca2-f424-4c9c-9d09-e45d6a587db5",
  "status": "ok",
  "result": {
    "state": "idle",
    "actual_power_mw": 0,
    "target_power_mw": 50,
    "temperature_c": 25,
    "current_ma": 0,
    "fault_reason": null
  }
}
```

El `request_id` debe coincidir exactamente con el de la petición. El snapshot
describe el estado real después de ejecutar el comando; el cliente no debe
suponer el resultado antes de recibir esta respuesta.

El objeto `result` contiene siempre:

| Campo | Tipo JSON | Valores |
| --- | --- | --- |
| `state` | string | `idle`, `armed`, `running` o `fault` |
| `actual_power_mw` | number | Potencia actual en mW |
| `target_power_mw` | number o null | Potencia configurada o ausencia de objetivo |
| `temperature_c` | number | Temperatura actual en °C |
| `current_ma` | number | Corriente actual en mA |
| `fault_reason` | string o null | `emergency_stop`, `over_temperature`, `over_current` o `null` |

## Error response

Una petición válida a nivel de transporte puede ser rechazada por el contrato
o por las reglas del dominio. En ese caso, la respuesta utiliza
`status: "error"`:

```json
{
  "protocol_version": 1,
  "message_type": "response",
  "request_id": "6d471ca2-f424-4c9c-9d09-e45d6a587db5",
  "status": "error",
  "error": {
    "code": "invalid_state_transition",
    "message": "Cannot start laser from state 'idle'; expected 'armed'"
  }
}
```

El cliente debe tomar decisiones mediante `error.code`. `error.message` es una
explicación destinada a personas y puede mejorar sin cambiar la compatibilidad
del protocolo.

Cuando el servidor puede recuperar un `request_id` válido, debe repetirlo en la
respuesta de error. Si el frame no contiene JSON válido o no permite recuperar
el identificador, el error puede usar `request_id: null`.

Una respuesta contiene `result` cuando `status` es `"ok"` y contiene `error`
cuando `status` es `"error"`. Nunca debe contener ambos campos al mismo tiempo.

Códigos iniciales:

| Código | Significado |
| --- | --- |
| `invalid_frame_length` | La longitud es cero o supera el máximo permitido |
| `invalid_encoding` | El payload no contiene UTF-8 válido |
| `invalid_json` | El payload no contiene un documento JSON válido |
| `invalid_request` | Faltan campos o sus tipos no cumplen el contrato |
| `unsupported_protocol_version` | La versión del protocolo no está soportada |
| `unsupported_command` | El comando no existe en la versión actual |
| `invalid_state_transition` | El comando no es válido desde el estado actual |
| `target_power_not_configured` | Se necesita una potencia objetivo |
| `invalid_target_power` | La potencia solicitada está fuera del rango permitido |
| `unsafe_recovery` | Las mediciones todavía impiden recuperar el láser |
| `internal_error` | Error interno no esperado; no expone detalles sensibles |

## Supported commands

La versión 1 admite estos comandos:

| Comando | Payload | Resultado satisfactorio |
| --- | --- | --- |
| `set_target_power` | `{ "target_power_mw": number }` | Snapshot actualizado |
| `arm` | `{}` | Snapshot en `armed` |
| `start` | `{}` | Snapshot en `running` |
| `stop` | `{}` | Snapshot en `idle` |
| `disarm` | `{}` | Snapshot en `idle` |
| `emergency_stop` | `{}` | Snapshot en `fault` |
| `recover` | `{}` | Snapshot en `idle` si la recuperación es segura |
| `get_snapshot` | `{}` | Snapshot actual sin modificar el dispositivo |

Los comandos con payload vacío rechazan campos adicionales. `tick` no forma
parte del protocolo público: representa el avance interno de la simulación y
será ejecutado por el propio proceso del dispositivo.

Las transiciones y los límites físicos no se vuelven a decidir en esta capa.
El protocolo traduce el comando y deja que la clase `Laser` aplique las reglas
definidas por el dominio.

## Invalid frame handling

El parser debe distinguir entre datos incompletos y datos inválidos:

- Menos de 4 bytes de encabezado no constituyen un error. El parser conserva el
  fragmento y espera más bytes.
- Un encabezado completo seguido de un payload incompleto tampoco es un error.
  El parser conserva todo hasta recibir los bytes restantes.
- Si el buffer contiene varios frames completos, el parser devuelve todos en
  orden y conserva únicamente el fragmento final incompleto.
- Una longitud igual a cero o mayor que `65 536` bytes produce
  `invalid_frame_length`.
- Un payload completo que no puede decodificarse como UTF-8 produce
  `invalid_encoding`.
- Un texto UTF-8 que no contiene JSON válido produce `invalid_json`.
- Un JSON válido que no cumple el contrato produce `invalid_request`.

Ante una longitud inválida, el servidor rechaza el frame y cierra únicamente la
conexión responsable, porque no puede confiar en los límites anunciados. El
servidor principal continúa aceptando otras conexiones.

Cuando la longitud es válida y el frame completo ya está delimitado, un error
de UTF-8, JSON o validación descarta solamente ese frame. El servidor puede
enviar una respuesta de error y continuar procesando los frames posteriores de
la misma conexión.

Si la conexión termina mientras existe un frame incompleto, el fragmento se
descarta y se registra para diagnóstico. Nunca debe intentarse interpretar un
payload antes de haber recibido todos sus bytes.
