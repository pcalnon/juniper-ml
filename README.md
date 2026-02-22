# juniper

Meta-package for the Juniper Cascade Correlation Neural Network Research Platform.

## Installation

Install all client libraries and the distributed worker:

```bash
pip install juniper[all]
```

Or install selectively:

```bash
pip install juniper[clients]  # All client libraries
pip install juniper[worker]   # Distributed training worker
```

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
