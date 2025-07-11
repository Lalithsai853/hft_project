# Mini HFT Stack

A private mini-HFT system with end-to-end market data ingestion, limit order book, algorithmic strategies, backtesting, live mode deployment, monitoring, and ML-driven alpha overlay.

## Overview

This project implements a complete high-frequency trading stack designed for:
- ≥100K messages/sec market data ingestion
- ≤1ms latency limit order book with price-time matching
- Algorithmic strategy execution (TWAP, VWAP)
- Comprehensive backtesting with P&L analysis
- Real-time monitoring and profiling
- Streaming ML models for predictive order placement

## Performance Targets

- **Throughput:** ≥100K msg/sec ingestion & parsing
- **Latency:** ≤1 ms book update & match
- **Strategy Performance:** P&L improvement vs naive baseline
- **ML Alpha Lift:** 5-10% reduction in slippage

## Technology Stack

- **Core Engine:** C++ (for LOB, matching, ingestion)
- **Orchestration:** Python 3.11+ (asyncio, testing, ML)
- **Messaging:** TCP sockets or Kafka
- **Serialization:** FlatBuffers or custom binary structs
- **Monitoring:** Prometheus + Grafana
- **ML:** scikit-learn, river, PyTorch

## Requirements

- **Python:** 3.11+ (3.11 or 3.12 recommended for optimal HFT performance)
- **Operating System:** Linux (recommended), macOS, Windows
- **Memory:** ≥8GB RAM (16GB+ recommended)
- **Storage:** SSD recommended for low-latency data access

## Installation

1. **Ensure Python 3.11+ is installed:**
   ```bash
   python3 --version  # Should show Python 3.11.x or 3.12.x
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/Lalithsai853/hft_project.git
   cd hft_project
   ```

3. **Install dependencies:**
   ```bash
   # Using pip
   pip3 install -r requirements.txt
   
   # Or using the project file
   pip3 install -e .
   ```

## Project Structure

```
├── ingestion/            # Feed handlers, parsers, replay scripts
├── lob/                  # Limit order book & matching engine
├── strategy/             # Strategy interface & built-in algos (TWAP, VWAP)
├── backtester/           # Historical data runner, performance metrics
├── live/                 # Live feed connector & adapter
├── monitoring/           # Prometheus exporters, Grafana dashboards
├── profiling/            # Perf and gprof scripts, analysis reports
├── ml_alpha/             # Feature extraction, streaming model, evaluation
├── tests/                # Unit, integration, and regression tests
├── docker/               # Dockerfiles & docker-compose setups
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Project configuration
```

## Quick Start

Coming soon - implementation in progress following the development milestones outlined in the project plan.

## Development Phases

1. **Phase 1:** Ingestion + lock-free queue
2. **Phase 2:** LOB + matching engine  
3. **Phase 3:** Strategy interface + TWAP/VWAP
4. **Phase 4:** Backtester + core metrics
5. **Phase 5:** Live mode connector
6. **Phase 6:** Monitoring + profiling
7. **Phase 7:** ML-alpha overlay

## License

Private project - All rights reserved 