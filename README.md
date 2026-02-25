# juniper-ml

Meta-package for the Juniper-ML Project, a Research Platform for investigating dynamic neural networks and novel learning algorithms.  Prototype implementation uses Cascade Correlation neural networks.

## Installation

Install all client libraries and the distributed worker:

```bash
pip install juniper-ml[all]
```

Or install selectively:

```bash
pip install juniper-ml[clients]  # All client libraries
pip install juniper-ml[worker]   # Distributed training worker
```

## Ecosystem Compatibility

This meta-package is part of the [Juniper](https://github.com/pcalnon/juniper-ml) ecosystem.
Verified compatible service versions:

| juniper-data | juniper-cascor | juniper-canopy | data-client | cascor-client | cascor-worker |
|---|---|---|---|---|---|
| 0.4.x | 0.3.x | 0.2.x | >=0.3.1 | >=0.1.0 | >=0.1.0 |

For full-stack Docker deployment and integration tests, see [juniper-deploy](https://github.com/pcalnon/juniper-deploy).

## Packages

| Package | Description | Install |
|---------|-------------|---------|
| [juniper-data-client](https://github.com/pcalnon/juniper-data-client) | HTTP client for the JuniperData dataset generation service | `pip install juniper-data-client` |
| [juniper-cascor-client](https://github.com/pcalnon/juniper-cascor-client) | HTTP/WebSocket client for the JuniperCascor neural network training service | `pip install juniper-cascor-client` |
| [juniper-cascor-worker](https://github.com/pcalnon/juniper-cascor-worker) | Remote candidate training worker for distributed CasCor training | `pip install juniper-cascor-worker` |

## Extras

| Extra | Packages Included |
|-------|-------------------|
| `clients` | `juniper-data-client`, `juniper-cascor-client` |
| `worker` | `juniper-cascor-worker` |
| `all` | All of the above |

## About Juniper

Juniper is an AI/ML research platform implementing the Cascade Correlation Neural Network algorithm (Fahlman & Lebiere, 1990). The platform includes:

- **JuniperCascor** - Cascade Correlation neural network training service
- **JuniperData** - Dataset generation and management service
- **JuniperCanopy** - Real-time monitoring dashboard

## License

MIT License - Copyright (c) 2024-2026 Paul Calnon
