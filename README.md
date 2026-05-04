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
|--------------|----------------|----------------|-------------|---------------|---------------|
| 0.4.x        | 0.3.x          | 0.2.x          | >=0.3.1     | >=0.1.0       | >=0.1.0       |

For full-stack Docker deployment and integration tests, see `juniper-deploy`.

## Packages

| Package                                                                   | Description                                                                 | Install                             |
|---------------------------------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------|
| [juniper-data-client](https://github.com/pcalnon/juniper-data-client)     | HTTP client for the JuniperData dataset generation service                  | `pip install juniper-data-client`   |
| [juniper-cascor-client](https://github.com/pcalnon/juniper-cascor-client) | HTTP/WebSocket client for the JuniperCascor neural network training service | `pip install juniper-cascor-client` |
| [juniper-cascor-worker](https://github.com/pcalnon/juniper-cascor-worker) | Remote candidate training worker for distributed CasCor training            | `pip install juniper-cascor-worker` |

## Sibling Package

This repository also contains [`juniper-observability`](juniper-observability/README.md), a separately versioned package for shared health models, request-ID logging, Starlette middleware, Prometheus helpers, and Sentry setup. It is not installed by `juniper-ml[all]`; install it directly when a service needs the shared observability primitives:

```bash
pip install "juniper-observability[all]"
```

`juniper-observability` publishes from `.github/workflows/publish-observability.yml` when a `juniper-observability-vX.Y.Z` tag is pushed. See the package README for the release checklist and workflow constraints.

## Extras

| Extra     | Packages Included                              |
|-----------|------------------------------------------------|
| `clients` | `juniper-data-client`, `juniper-cascor-client` |
| `worker`  | `juniper-cascor-worker`                        |
| `all`     | All of the above                               |

## About Juniper

Juniper is an AI/ML research platform implementing the Cascade Correlation Neural Network algorithm (Fahlman & Lebiere, 1990). The platform includes:

- **JuniperCascor** - Cascade Correlation neural network training service
- **JuniperData** - Dataset generation and management service
- **juniper-canopy** - Real-time monitoring dashboard

## License

MIT License - Copyright (c) 2024-2026 Paul Calnon
