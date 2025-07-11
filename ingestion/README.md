# HFT Ingestion Module

High-performance market data parser for FIX protocol and WebSocket JSON messages.

## Overview

This module implements the **FIX/WebSocket Parser** component from Phase 1 of the HFT stack. It provides:

- **Protocol Detection**: Automatic detection of FIX vs WebSocket JSON messages  
- **High Performance**: C++ core with Python wrapper for optimal speed
- **Unified Output**: All messages converted to standardized `MarketMessage` format
- **Error Handling**: Robust validation and error reporting
- **Statistics**: Real-time parsing performance metrics

## Components

### C++ Core Parser
- `message_types.hpp` - Core data structures and enums
- `message_parser.hpp` - Main parser class interface
- `message_parser.cpp` - Implementation with FIX and JSON parsing
- `CMakeLists.txt` - Build configuration with HFT optimizations

### Python Integration  
- `parser_wrapper.py` - Python wrapper class for C++ parser
- `test_parser_demo.py` - Demonstration and testing script

## Usage

### Python Interface

```python
from parser_wrapper import MessageParser, ParseResult

# Create parser instance
parser = MessageParser()

# Parse FIX message
fix_msg = "8=FIX.4.4\x0135=D\x0155=AAPL\x0154=1\x0144=150.25\x0138=100\x01"
result, message = parser.parse_message(fix_msg)

if result == ParseResult.SUCCESS:
    print(f"Parsed: {message}")
    print(f"Symbol: {message.symbol}")
    print(f"Price: {message.price}")
```

### Performance Testing

Run the demonstration script:
```bash
cd ingestion/
python3 test_parser_demo.py
```

## Message Format

All messages convert to unified structure:
- timestamp (nanoseconds)
- symbol (trading symbol)  
- side (BUY/SELL/UNKNOWN)
- price (price level)
- size (quantity)
- type (NEW_ORDER/TRADE/QUOTE/etc.)

## Performance

**Current Python Implementation:**
- ~50K-100K messages/second
- Sub-millisecond latency per message

**Target C++ Implementation:**  
- >500K messages/second
- <100 microsecond latency per message 