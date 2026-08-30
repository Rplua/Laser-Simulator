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

**Phase 2 — Device simulator completed**

The domain model and deterministic laser simulator are implemented. The
simulator includes explicit state transitions, power ramping, current and
temperature evolution, cooling, safety faults, recovery rules and validated
state snapshots. Its behaviour is covered by 36 passing unit-test cases.

The next milestone is **Phase 3 — TCP protocol design**, described in
[the project roadmap](docs/ROADMAP.md).

## Working method

Randy acts as the Software Engineer responsible for design and implementation.
The AI assistant acts as Tech Lead and reviewer: it provides requirements,
constraints, acceptance criteria, questions and progressive hints without
implementing the core solution by default.
