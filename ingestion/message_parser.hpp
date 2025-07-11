#pragma once

#include "message_types.hpp"
#include <string_view>
#include <unordered_map>
#include <chrono>

namespace hft {
namespace ingestion {

class MessageParser {
public:
    MessageParser();
    ~MessageParser();
    
    // Main parsing interface
    ParseResult parse_message(const char* buffer, size_t length, MarketMessage& message, ParseContext& context);
    
    // Protocol-specific parsers
    ParseResult parse_fix_message(const char* buffer, size_t length, MarketMessage& message);
    ParseResult parse_websocket_json(const char* buffer, size_t length, MarketMessage& message);
    
    // Protocol detection
    ProtocolType detect_protocol(const char* buffer, size_t length);
    
    // Utility functions
    void reset_parser_state();
    uint64_t get_current_timestamp_ns();
    
private:
    // FIX parsing helpers
    ParseResult parse_fix_tag_value_pairs(const char* buffer, size_t length, MarketMessage& message);
    bool extract_fix_field(const char* buffer, size_t length, const std::string& tag, std::string& value);
    Side fix_side_to_enum(const std::string& side_str);
    MessageType fix_msgtype_to_enum(const std::string& msgtype_str);
    
    // JSON parsing helpers
    ParseResult parse_json_fields(const char* buffer, size_t length, MarketMessage& message);
    bool extract_json_field(const std::string& json, const std::string& key, std::string& value);
    bool extract_json_double(const std::string& json, const std::string& key, double& value);
    bool extract_json_int(const std::string& json, const std::string& key, int32_t& value);
    
    // Validation helpers
    bool is_valid_symbol(const std::string& symbol);
    bool is_valid_price(double price);
    bool is_valid_size(int32_t size);
    
    // FIX field mappings
    std::unordered_map<std::string, std::string> fix_tag_names_;
    
    // Performance tracking
    size_t messages_parsed_;
    size_t parse_errors_;
    
    // Constants
    static constexpr char FIX_DELIMITER = '\x01';  // SOH character
    static constexpr size_t MAX_MESSAGE_SIZE = 4096;
    static constexpr size_t MAX_SYMBOL_LENGTH = 16;
};

} // namespace ingestion
} // namespace hft 