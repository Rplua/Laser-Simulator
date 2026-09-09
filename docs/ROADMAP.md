# Roadmap del proyecto

Este documento define el trabajo desde la perspectiva del Tech Lead. Cada fase
contiene un objetivo, entregables y criterios de aceptación. No contiene la
solución ni código de implementación.

## Forma de trabajo

En cada fase, Randy deberá:

1. Explicar su propuesta antes de implementarla.
2. Dividir el problema en responsabilidades pequeñas.
3. Implementar la lógica principal.
4. Escribir las pruebas indicadas.
5. Explicar el flujo final con sus propias palabras.

La ayuda seguirá este orden: preguntas, pistas, pseudocódigo, sintaxis aislada y
solución completa únicamente cuando exista un bloqueo real.

---

## FASE 1 — Dominio y máquina de estados

**Estado: completada.**

### Objetivo

Diseñar el comportamiento del dispositivo sin pensar todavía en sockets,
FastAPI, React o Docker.

### Estados iniciales

- `IDLE`
- `ARMED`
- `RUNNING`
- `FAULT`

### Comandos del dominio

- Armar el dispositivo.
- Desarmar el dispositivo.
- Iniciar la emisión.
- Detener la emisión.
- Establecer la potencia objetivo.
- Ejecutar una parada de emergencia.
- Recuperar el dispositivo de un fallo.

### Mediciones

- Potencia actual en milivatios.
- Potencia objetivo en milivatios.
- Temperatura del diodo en grados Celsius.
- Corriente consumida en miliamperios.
- Estado actual del dispositivo.

### Reglas mínimas

- El dispositivo no puede iniciar la emisión desde `IDLE`.
- Solo puede pasar a `RUNNING` después de estar armado.
- Una temperatura peligrosa provoca `FAULT`.
- Una sobrecorriente provoca `FAULT`.
- Una parada de emergencia provoca `FAULT`.
- En `FAULT`, la potencia debe caer a cero.
- No se puede abandonar `FAULT` mientras continúe la condición peligrosa.
- La potencia objetivo debe respetar los límites del dispositivo.

### Entregable

Crear `docs/DOMAIN_DESIGN.md` con:

- Responsabilidad del dispositivo.
- Definición de cada estado.
- Tabla de transiciones permitidas y rechazadas.
- Comandos válidos en cada estado.
- Condiciones que provocan un fallo.
- Límites de potencia y temperatura, justificando los valores simulados.
- Recorrido futuro de un comando desde React hasta el dispositivo.

### Criterios de aceptación

- Todas las transiciones tienen un origen, evento y resultado.
- Se describe qué ocurre cuando un comando no es válido.
- Las reglas no dependen de FastAPI, TCP ni de una interfaz gráfica.
- Randy puede explicar el diseño sin leer el documento línea por línea.

---

## FASE 2 — Simulador del dispositivo

**Estado: completada.**

### Objetivo

Implementar en Python el dominio diseñado en la fase anterior, todavía sin
comunicación de red.

### Entregables

- Clase responsable del estado y las mediciones del láser simulado.
- Aplicación de comandos mediante métodos explícitos.
- Evolución simulada de temperatura, potencia y corriente.
- Errores de dominio claros para operaciones no permitidas.
- Pruebas unitarias de todas las transiciones importantes.

### Criterios de aceptación

- La lógica funciona sin FastAPI ni sockets.
- No es posible crear estados imposibles mediante la API pública de la clase.
- Las pruebas cubren el camino correcto y los rechazos.
- La parada de emergencia siempre deja la potencia a cero.

---

## FASE 3 — Protocolo TCP

**Estado: completada.**

### Objetivo

Diseñar un protocolo de aplicación que permita intercambiar comandos y
mediciones entre procesos mediante TCP.

### Entregables

- Documento con el formato de los mensajes.
- Estrategia para delimitar mensajes dentro del flujo TCP.
- Identificador de petición y respuesta.
- Representación de errores del dispositivo.
- Parser capaz de recibir mensajes fragmentados o varios mensajes juntos.
- Pruebas del encoder y del parser.

### Criterios de aceptación

- El diseño reconoce que TCP transporta un flujo de bytes, no mensajes.
- Los mensajes incompletos no se procesan antes de tiempo.
- Un mensaje inválido no detiene todo el servidor.
- Se puede relacionar cada respuesta con su petición.

---

## FASE 4 — Servidor del dispositivo y driver Python

**Estado: completada.**

### Objetivo

Ejecutar el simulador como un proceso independiente y controlarlo desde otro
proceso mediante TCP.

### Entregables

- Servidor TCP del dispositivo simulado.
- Driver cliente con métodos de alto nivel.
- Timeouts de conexión y lectura.
- Reconexión controlada.
- Traducción entre mensajes del protocolo y objetos del dominio.
- Pruebas de integración entre servidor y driver.

### Criterios de aceptación

- El código de negocio no conoce detalles de sockets.
- El driver ofrece operaciones como armar o establecer potencia, no bytes.
- Una desconexión genera un error comprensible y recuperable.
- No quedan sockets o tareas abiertos durante el apagado.

---

## FASE 5 — Servicio FastAPI

**Estado: siguiente fase.**

### Objetivo

Exponer el driver mediante una API y transmitir mediciones en tiempo real.

### Entregables

- Ciclo de vida explícito para conectar y cerrar el driver.
- Endpoints REST para consultar estado y enviar comandos.
- WebSocket para mediciones y cambios de estado.
- Modelos separados para transporte y dominio.
- Conversión de errores del dispositivo a respuestas HTTP adecuadas.
- Pruebas de endpoints y del ciclo de vida.

### Criterios de aceptación

- FastAPI no contiene directamente la lógica de seguridad del láser.
- Los recursos se cierran correctamente al detener el servicio.
- Los clientes WebSocket defectuosos no bloquean a los demás.
- Las respuestas tienen contratos documentados.

---

## FASE 6 — Algoritmo de control

### Objetivo

Implementar un controlador sencillo que acerque la potencia medida a una
potencia objetivo sin violar los límites de seguridad.

### Entregables

- Modelo matemático simplificado del dispositivo.
- Primera versión de control proporcional.
- Evolución posterior a un controlador PID básico si está justificado.
- Límites de salida y prevención de acumulación incorrecta.
- Gráficas o datos de respuesta ante distintos objetivos.
- Pruebas deterministas del controlador.

### Criterios de aceptación

- Se puede explicar el efecto de cada término utilizado.
- El algoritmo está separado del transporte y de FastAPI.
- La salida respeta siempre los límites del dispositivo.
- Se documentan estabilidad, error y limitaciones del modelo simulado.

---

## FASE 7 — Panel React y TypeScript

### Objetivo

Crear una estación de control clara, accesible y conectada al servicio Python.

### Entregables

- Estado de conexión visible.
- Visualización de potencia, temperatura, corriente y estado.
- Selección y envío de potencia objetivo.
- Controles de armado, inicio, parada y emergencia.
- Historial visual de mediciones recientes.
- Reconexión WebSocket y tratamiento de errores.
- Pruebas de la lógica crítica de interfaz.

### Criterios de aceptación

- La interfaz representa el estado real, no un estado optimista incorrecto.
- Las acciones no permitidas se deshabilitan o explican.
- La parada de emergencia es visible y deliberada.
- El diseño funciona en escritorio y móvil.

---

## FASE 8 — Persistencia, observabilidad y Docker

### Objetivo

Preparar el sistema para ejecución reproducible y diagnóstico técnico.

### Entregables

- Persistencia de sesiones o mediciones históricas.
- Logs estructurados y correlacionados por petición.
- Métricas básicas del servicio y del dispositivo.
- Dockerfiles separados y ejecución sin usuario root cuando corresponda.
- Docker Compose con healthchecks y dependencias saludables.
- Configuración mediante variables de entorno.

### Criterios de aceptación

- El entorno completo se inicia con un único comando.
- Los secretos no se incluyen en las imágenes ni en Git.
- Los logs permiten seguir un comando entre las diferentes capas.
- Los contenedores notifican si dejan de estar saludables.

---

## FASE 9 — Fallos, revisión y presentación profesional

### Objetivo

Demostrar que el sistema puede degradarse, recuperarse y ser defendido en una
entrevista técnica.

### Escenarios obligatorios

- El simulador no está disponible al arrancar.
- La conexión TCP se pierde durante una operación.
- Se recibe un mensaje parcial o inválido.
- Un cliente WebSocket desaparece.
- La temperatura supera el límite permitido.
- El servicio se apaga mientras existen recursos activos.

### Entregables

- Pruebas de integración de los fallos principales.
- README profesional en inglés.
- Diagrama de arquitectura final.
- Capturas de la interfaz.
- Explicación de decisiones y limitaciones.
- Guion breve para presentar el proyecto en una entrevista.

### Criterios de aceptaciónå

- Las pruebas, lint y builds terminan correctamente.
- No quedan procesos, sockets o tareas abandonados.
- Las limitaciones se declaran con honestidad.
- Randy puede explicar el flujo completo y las decisiones sin depender del
  código fuente.
