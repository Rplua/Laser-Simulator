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

**Phase 1 — Domain and state-machine design**

No application code has been created yet. The first deliverable is the domain
design described in [the project roadmap](docs/ROADMAP.md).

## Working method

Randy acts as the Software Engineer responsible for design and implementation.
The AI assistant acts as Tech Lead and reviewer: it provides requirements,
constraints, acceptance criteria, questions and progressive hints without
implementing the core solution by default.
