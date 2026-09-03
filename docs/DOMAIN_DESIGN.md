# Domain Design


## 1. Responsabilidad del dominio

El dominio representa el comportamiento de un dispositivo láser simulado.
Debe conocer:

- el estado actual del dispositivo;
- las mediciones actuales;
- la potencia objetivo;
- los comandos que pueden ejecutarse en cada estado;
- las reglas que protegen al dispositivo ante condiciones peligrosas;
- la configuración de la potencia cuando está en `IDLE`.

El dominio no debe conocer React, FastAPI, HTTP, WebSocket, TCP ni JSON. Estas
tecnologías transportarán información, pero no decidirán si el láser puede
arrancar, detenerse o recuperarse de un fallo.

## 2. Estados

Los estados formarán un conjunto cerrado. Durante la implementación podrán
representarse mediante un `Enum`, evitando estados escritos incorrectamente o
valores no contemplados.

### `IDLE`

El dispositivo está disponible, pero no está preparado para emitir. La potencia
actual debe ser cero.

### `ARMED`

El dispositivo está preparado para emitir, pero todavía no está emitiendo. La
potencia actual debe continuar siendo cero.

### `RUNNING`

El dispositivo está emitiendo y trata de alcanzar la potencia objetivo sin
superar sus límites de seguridad.

### `FAULT`

El dispositivo ha detectado una condición peligrosa. La emisión debe detenerse
y la potencia actual debe pasar a cero. Mientras exista la condición peligrosa,
no se podrá recuperar el funcionamiento normal.


## 3. Comandos del dominio

Los comandos representan intenciones del usuario o del sistema. Más adelante
podrán llegar desde React y FastAPI, pero pertenecen al dominio y deben poder
utilizarse sin esas capas.

### Armar el dispositivo

Prepara el dispositivo para emitir. Solo se puede armar si la potencia está
configurada y no existe ninguna condición peligrosa.

### Iniciar la emisión

Inicia la emisión utilizando la potencia objetivo configurada.

### Detener la emisión

Detiene la emisión de forma controlada sin representar una emergencia.

### Establecer la potencia objetivo

Recibe una potencia en milivatios. El dominio debe validar que el valor esté
dentro del rango permitido. La potencia objetivo solo se puede configurar en
`IDLE`.

### Parada de emergencia

Detiene inmediatamente la emisión y lleva el dispositivo a `FAULT`.

### Recuperar de un fallo

Solicita abandonar `FAULT`. Solo puede aceptarse cuando ya no exista ninguna
condición peligrosa. Al recuperarse, el dispositivo vuelve a `IDLE`.

### Desarmar el dispositivo

Solicita abandonar `ARMED` sin iniciar la emisión. Solo puede aceptarse cuando
el dispositivo está en `ARMED` y hace que vuelva a `IDLE`.


## 4. Mediciones y datos del dispositivo

El dispositivo mantendrá como mínimo:

- estado actual;
- potencia actual en milivatios;
- potencia objetivo en milivatios;
- temperatura del diodo en grados Celsius;
- corriente consumida en miliamperios.

Las mediciones describen el estado del dispositivo. No son simplemente un
modelo del frontend: posteriormente podrán convertirse a JSON, almacenarse o
mostrarse sin cambiar las reglas del dominio.

## 5. Transiciones de estado

| Estado inicial | Evento o comando | Condición | Estado resultante |
| --- | --- | --- | --- |
| `IDLE` | Configurar potencia | Potencia objetivo entre `1` y `100 mW` | `IDLE` |
| `IDLE` | Armar | Existe una potencia objetivo válida y no existe una condición peligrosa | `ARMED` |
| `ARMED` | Iniciar | Existe una potencia objetivo válida | `RUNNING` |
| `RUNNING` | Detener | Parada controlada | `IDLE` |
| `ARMED` | Desarmar | Siempre | `IDLE` |
| Cualquier estado | Temperatura peligrosa | Temperatura por encima del límite | `FAULT` |
| Cualquier estado | Sobrecorriente | Corriente igual o superior al límite | `FAULT` |
| Cualquier estado | Parada de emergencia | Siempre | `FAULT` |
| `FAULT` | Recuperar | La condición peligrosa ha desaparecido | `IDLE` |

Las transiciones `IDLE → RUNNING` y `FAULT → RUNNING` no están permitidas.

## 6. Comandos rechazados

Cuando se intente ejecutar un comando no permitido:

- el estado actual no debe cambiar;
- las mediciones no deben quedar parcialmente modificadas;
- el dominio debe devolver o lanzar un error que explique el motivo;
- la capa de transporte decidirá posteriormente cómo representar ese error en
  HTTP, TCP o la interfaz.

Ejemplos:

- intentar iniciar desde `IDLE`;
- intentar iniciar desde `FAULT`;
- establecer una potencia fuera del rango permitido;
- intentar recuperar el dispositivo mientras continúa sobrecalentado.

## 7. Condiciones que generan `FAULT`

Inicialmente se contemplan:

- temperatura superior al límite permitido;
- parada de emergencia solicitada;
- corriente igual o superior al límite de sobrecorriente.

Al entrar en `FAULT`:

- la potencia actual pasa a cero;
- la emisión queda desactivada;
- la potencia objetivo se conserva temporalmente para facilitar el diagnóstico;
- se conserva el motivo del fallo para poder diagnosticarlo;
- se rechazan los comandos que intenten iniciar o armar el dispositivo.

### Limpieza al detener y recuperar

Una parada controlada desde `RUNNING` inicia un ciclo nuevo. Al ejecutarla:

- el estado cambia a `IDLE`;
- la potencia actual pasa a `0 mW`;
- la potencia objetivo queda sin configurar;
- la corriente pasa a `0 mA`;
- la emisión queda desactivada;
- la temperatura no se borra: conserva su valor y podrá descender con la
  simulación del enfriamiento.

Por tanto, para volver a emitir será necesario configurar otra potencia,
armar el dispositivo e iniciar la emisión.

Al entrar en `FAULT`, la configuración y el motivo del fallo se conservan
temporalmente para el diagnóstico. Cuando una recuperación sea segura y se
acepte:

- el dispositivo vuelve a `IDLE`;
- la potencia objetivo queda sin configurar;
- la potencia actual y la corriente quedan a cero;
- se limpia el motivo del fallo;
- la temperatura conserva el valor medido.

## 8. Límites simulados

Estos valores son ficticios y se utilizan únicamente para el simulador. No son
especificaciones de seguridad válidas para controlar un láser real.

| Parámetro | Rango normal o permitido | Entrada en `FAULT` | Recuperación segura | Justificación |
| --- | ---: | ---: | ---: | --- |
| Potencia objetivo | `1–100 mW` | No provoca `FAULT`; se rechaza el comando si está fuera del rango | No aplica | Mantiene una escala sencilla para observar el controlador |
| Potencia actual | `0–100 mW` | Se fuerza a `0 mW` al entrar en `FAULT` | `0 mW` | El dispositivo puede estar encendido sin emitir |
| Temperatura del diodo | `20–45 °C` | `>= 60 °C` | `<= 45 °C` | Introduce margen entre funcionamiento, fallo y recuperación |
| Corriente consumida | `0–400 mA` | `>= 450 mA` | `<= 400 mA` | Reserva un margen antes de considerar que existe sobrecorriente |

La diferencia entre la temperatura de fallo y la de recuperación introduce
histéresis. De esta manera, una pequeña oscilación cerca de `60 °C` no permite
que el dispositivo salga y vuelva a entrar en `FAULT` repetidamente.

Una potencia objetivo fuera del rango no representa una avería física: es un
comando inválido y debe rechazarse sin modificar el estado. La sobretemperatura
y la sobrecorriente sí representan condiciones del dispositivo y provocan
`FAULT`.

## 9. Recorrido futuro de un comando

El recorrido previsto será:

```text
Usuario
  → componente React
  → petición HTTP a FastAPI
  → servicio de aplicación
  → driver del dispositivo
  → mensaje TCP
  → simulador
  → reglas del dominio
```

