<p align="center">
  <img src="./ui/assets/icons/logo.svg" width="200" alt="ProtoFlow logo"/>
</p>

<p align="center">
  <b>Stop sending bytes. Start executing protocols.</b>
</p>
<p align="center">
ProtoFlow is a communication runtime engine that transforms UART / TCP / Modbus / XMODEM interactions from scattered byte operations into programmable and executable protocol workflows.
</p>


---

[涓枃](./README.md)

<p align="center">
  <a href="https://github.com/11cookies11/ToolOfCom/actions/workflows/ci.yml"><img alt="build" src="https://img.shields.io/github/actions/workflow/status/11cookies11/ToolOfCom/ci.yml?branch=main&label=build&style=for-the-badge"/></a>
  <a href="https://github.com/11cookies11/ToolOfCom/releases"><img alt="release" src="https://img.shields.io/github/v/release/11cookies11/ToolOfCom?label=release&style=for-the-badge"/></a>
  <a href="./LICENSE"><img alt="license" src="https://img.shields.io/github/license/11cookies11/ToolOfCom?style=for-the-badge"/></a>
</p>
<p align="center">
  <a href="https://github.com/11cookies11/ToolOfCom/releases"><img alt="downloads" src="https://img.shields.io/github/downloads/11cookies11/ToolOfCom/total?label=downloads&style=for-the-badge"/></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-orange?style=for-the-badge"/>
  <img alt="language" src="https://img.shields.io/badge/language-Python%203.11%2B%20%2B%20Qt-7F3FBF?style=for-the-badge"/>
</p>

## 馃寪 Overview

ProtoFlow is not a 鈥渟erial assistant鈥?tool 鈥?it is a **communication logic runtime**.

Traditional debugging tools can only send and receive raw bytes. ProtoFlow, however, describes complete communication flows using a DSL and executes them through a state-machine runtime, enabling **configurable, orchestrated, and extensible protocol behaviors**.

```lua
                                鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                                鈹?YAML DSL 鈹? 鈫?Human-readable description of communication logic
                                鈹斺攢鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹?
                                      鈫?
                                鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                                鈹?  AST    鈹? 鈫?Structured semantic tree (protocol/state/event/action)
                                鈹斺攢鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹?
                                      鈫?
                                鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                                鈹?Executor 鈹? 鈫?Runtime on PC / MCU
                                鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

Traditional serial or communication tools focus on only one thing:

**Send some bytes, then wait.**

But real device communication is never a single request鈥搑esponse action.
 It is a **protocol lifecycle**, including:

- Handshake and negotiation
- Multi-frame data exchange
- CRC validation
- Retries and timeout handling
- Conditional branching and execution flow
- Final actions and transitions

**ProtoFlow redefines communication**:

You no longer write scripts or click UI buttons.
 You describe protocol behaviors declaratively using DSL,
 and the runtime engine executes the communication flow automatically.

In other words:

```
Communication 鈫?no longer an operation
Communication 鈫?becomes state-driven executable logic
```

## 馃 Why ProtoFlow?

Existing communication tools suffer from fundamental limitations:

| Pain Point         | Current Situation                          |
| ------------------ | ------------------------------------------ |
| Low abstraction    | Stuck at byte-level operations             |
| Fragile logic      | Maintained through scripts or manual input |
| Stateless          | Cannot express protocol sequences          |
| Poor extensibility | Each new protocol requires new code        |

The communication world is inherently a **state machine**, not a collection of byte dumps.

ProtoFlow unlocks:

- Protocol logic 鈫?declarative DSL
- Communication sequence 鈫?state-machine executor
- Device interaction 鈫?orchestrated workflow

**From now on, protocols are not code 鈥?they are data.**

------

## 馃殌 Features

| Feature             | Description                                         |
| ------------------- | --------------------------------------------------- |
| 馃З Declarative DSL   | Describe communication flows in YAML, no scripting  |
| 馃攣 State runtime     | Executes send/receive, wait, branching, retry鈥?     |
| 馃攲 Protocol layer    | UART / TCP / Modbus / XMODEM / Custom protocols     |
| 馃П Layered design    | Channels, drivers, and actions fully decoupled      |
| 鈴?Deterministic     | No uncertain waits; predictable execution path      |
| 馃 Extensible        | Register custom actions without modifying core code |
| 馃摗 Multi-device flow | Orchestrate workflows across multiple channels      |

------

## 馃П Architecture

                                           +----------------+
                                           |   Workflow     |  <-- YAML DSL
                                           +----------------+
                                                    |
                                                    v
                                          +---------------------+
                                          |  State Machine Core |
                                          +---------------------+
                                           /        |        \
                                          v         v         v
                                    +---------+ +---------+ +---------+
                                    | Driver  | | Driver  | | Driver   | <-- Modbus / XMODEM / TCP / UART
                                    +---------+ +---------+ +---------+
                                                    |
                                                    v
                                                +---------+
                                                | Channel | <-- Serial / Network / Custom endpoint
                                                +---------+

**Communication is no longer about 鈥渨hat to send鈥?
 but about 鈥渨hat should happen next鈥?**

------

## 鈿?Quick Start

Download the release and run directly.
 (Linux version currently unverified.)

------

## 馃攲 Supported Protocols

| Protocol        | Status |
| --------------- | ------ |
| UART            | 鉁旓笍      |
| TCP             | 鉁旓笍      |
| Modbus RTU      | 鉁旓笍      |
| XMODEM          | 鉁旓笍      |
| Custom Protocol | 鉁旓笍      |

------

## 馃洠 Roadmap

- Web-based visual flow editor
- Enhanced binary data transfer
- Firmware update templates
- MQTT adapter layer
- Device topology and discovery

------

## 馃 Contribute

PRs, issues, and protocol extension plugins are warmly welcome.
 The long-term goal of ProtoFlow is to become the **execution layer of communication protocols**.

------

## 馃搫 License

This project is licensed under the MIT License.  
See the [LICENSE](./LICENSE) file for details.

------



## Learn More

See `docs/USER_GUIDE.md` for the full DSL grammar, state-machine semantics, protocol actions, extension methods, and best practices.
