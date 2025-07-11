#pragma once

#include <string>
#include <cstdint>

namespace hft {
namespace ingestion {

// Trading side enumeration
enum class Side {
    BUY = 1,
    SELL = 2,
    UNKNOWN = 0
};

// Message type classification
enum class MessageType {
    NEW_ORDER = 1,
    CANCEL_ORDER = 2,
    MODIFY_ORDER = 3,
    TRADE = 4,
    QUOTE = 5,
    MARKET_DATA = 6,
    UNKNOWN = 0
};

// Protocol type detection
enum class ProtocolType {
    FIX = 1,
    WEBSOCKET_JSON = 2,
    UNKNOWN = 0
};

// Parse result status
enum class ParseResult {
    SUCCESS = 0,
    INVALID_FORMAT = 1,
    INCOMPLETE_MESSAGE = 2,
    UNKNOWN_PROTOCOL = 3,
    BUFFER_OVERFLOW = 4
};

// Standardized market message structure
struct MarketMessage {
    uint64_t timestamp;        // Nanoseconds since epoch
    std::string symbol;        // Trading symbol (e.g., "AAPL", "MSFT")
    Side side;                // BUY/SELL/UNKNOWN
    double price;             // Price level
    int32_t size;             // Quantity/Size
    MessageType type;         // Message classification
    
    // Constructor
    MarketMessage() : timestamp(0), side(Side::UNKNOWN), price(0.0), size(0), type(MessageType::UNKNOWN) {}
    
    // Reset for object reuse
    void reset() {
        timestamp = 0;
        symbol.clear();
        side = Side::UNKNOWN;
        price = 0.0;
        size = 0;
        type = MessageType::UNKNOWN;
    }
};

// Parsing context for maintaining state
struct ParseContext {
    ProtocolType detected_protocol;
    size_t bytes_processed;
    bool message_complete;
    
    ParseContext() : detected_protocol(ProtocolType::UNKNOWN), bytes_processed(0), message_complete(false) {}
    
    void reset() {
        detected_protocol = ProtocolType::UNKNOWN;
        bytes_processed = 0;
        message_complete = false;
    }
};

} // namespace ingestion
} // namespace hft 