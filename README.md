# Precision Laser Control Platform

A simulated laser control and monitoring platform designed as an advanced
Python and React learning project.

The system will model a precision laser device, communicate with it through a
custom TCP protocol, execute control logic in Python and provide real-time
monitoring and commands from a React dashboard.

The project is intentionally based on simulated hardware. It is not intended to
control a real laser or replace certified hardware safety mechanisms.

## Target architecture

```text
React Control Panel
        |
   REST + WebSocket
        |
Python Control Service
        |
   TCP connection
        |
Laser Device Simulator
```

## Main learning objectives

- Design a domain before implementing it.
- Model industrial behaviour with a state machine.
- Create a documented TCP application protocol.
- Handle partial messages, timeouts, failures and reconnections.
- Separate device drivers, business rules and transport layers.
- Implement and test a basic closed-loop control algorithm.
- Stream measurements to a React and TypeScript interface.
- Build observable and containerized services.
- Defend the architecture and its trade-offs in a technical interview.

## Current status

**Phase 4 — Device TCP server and Python driver completed**

The domain model and deterministic laser simulator are implemented together
with a documented binary framing protocol. The protocol handles fragmented and
coalesced TCP data, validates JSON command contracts, dispatches commands to
the laser, correlates responses through request identifiers and returns framed
success or error responses.

The simulator now runs as an independent TCP process. A high-level asynchronous
Python driver provides connection management, bounded reconnection, timeouts,
command methods and typed snapshots without exposing socket or framing details
to its callers. Integration tests exercise real local TCP connections and clean
shutdown behaviour. The current implementation is covered by 112 passing
automated tests. The next step is **Phase 5 — FastAPI control service**, described
in [the project roadmap](docs/ROADMAP.md).

The asynchronous networking concepts used by the device server are explained
in [the asyncio and TCP server guide](docs/ASYNCIO_TCP_SERVER.md).
The completed request and response path is documented in
[the Phase 4 guide](docs/PHASE_4_TCP_SERVER_AND_DRIVER.md).

## Working method

Randy acts as the Software Engineer responsible for design and implementation.
The AI assistant acts as Tech Lead and reviewer: it provides requirements,
constraints, acceptance criteria, questions and progressive hints without
implementing the core solution by default.
