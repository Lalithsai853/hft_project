#include "message_parser.hpp"
#include <algorithm>
#include <sstream>
#include <cstring>
#include <cctype>

namespace hft {
namespace ingestion {

MessageParser::MessageParser() : messages_parsed_(0), parse_errors_(0) {
    // Initialize FIX tag mappings for common fields
    fix_tag_names_["8"] = "BeginString";
    fix_tag_names_["35"] = "MsgType";
    fix_tag_names_["49"] = "SenderCompID";
    fix_tag_names_["56"] = "TargetCompID";
    fix_tag_names_["55"] = "Symbol";
    fix_tag_names_["54"] = "Side";
    fix_tag_names_["44"] = "Price";
    fix_tag_names_["38"] = "OrderQty";
    fix_tag_names_["52"] = "SendingTime";
}

MessageParser::~MessageParser() = default;

ParseResult MessageParser::parse_message(const char* buffer, size_t length, 
                                        MarketMessage& message, ParseContext& context) {
    if (!buffer || length == 0) {
        return ParseResult::INVALID_FORMAT;
    }
    
    if (length > MAX_MESSAGE_SIZE) {
        return ParseResult::BUFFER_OVERFLOW;
    }
    
    // Reset message for reuse
    message.reset();
    
    // Detect protocol if not already known
    if (context.detected_protocol == ProtocolType::UNKNOWN) {
        context.detected_protocol = detect_protocol(buffer, length);
        if (context.detected_protocol == ProtocolType::UNKNOWN) {
            parse_errors_++;
            return ParseResult::UNKNOWN_PROTOCOL;
        }
    }
    
    ParseResult result;
    
    // Route to appropriate parser
    switch (context.detected_protocol) {
        case ProtocolType::FIX:
            result = parse_fix_message(buffer, length, message);
            break;
        case ProtocolType::WEBSOCKET_JSON:
            result = parse_websocket_json(buffer, length, message);
            break;
        default:
            result = ParseResult::UNKNOWN_PROTOCOL;
            break;
    }
    
    if (result == ParseResult::SUCCESS) {
        messages_parsed_++;
        context.message_complete = true;
        context.bytes_processed = length;
        
        // Set timestamp if not provided in message
        if (message.timestamp == 0) {
            message.timestamp = get_current_timestamp_ns();
        }
    } else {
        parse_errors_++;
    }
    
    return result;
}

ProtocolType MessageParser::detect_protocol(const char* buffer, size_t length) {
    if (length < 2) {
        return ProtocolType::UNKNOWN;
    }
    
    // Check for FIX protocol (starts with "8=")
    if (buffer[0] == '8' && buffer[1] == '=') {
        return ProtocolType::FIX;
    }
    
    // Check for JSON (starts with '{')
    if (buffer[0] == '{') {
        return ProtocolType::WEBSOCKET_JSON;
    }
    
    // Skip whitespace and check for JSON
    for (size_t i = 0; i < length && i < 10; ++i) {
        if (std::isspace(buffer[i])) continue;
        if (buffer[i] == '{') {
            return ProtocolType::WEBSOCKET_JSON;
        }
        break;
    }
    
    return ProtocolType::UNKNOWN;
}

ParseResult MessageParser::parse_fix_message(const char* buffer, size_t length, MarketMessage& message) {
    return parse_fix_tag_value_pairs(buffer, length, message);
}

ParseResult MessageParser::parse_fix_tag_value_pairs(const char* buffer, size_t length, MarketMessage& message) {
    std::string symbol, side_str, price_str, size_str, msgtype_str, timestamp_str;
    
    // Extract key fields
    if (!extract_fix_field(buffer, length, "55", symbol)) {
        return ParseResult::INVALID_FORMAT;  // Symbol is required
    }
    
    extract_fix_field(buffer, length, "54", side_str);
    extract_fix_field(buffer, length, "44", price_str);
    extract_fix_field(buffer, length, "38", size_str);
    extract_fix_field(buffer, length, "35", msgtype_str);
    extract_fix_field(buffer, length, "52", timestamp_str);
    
    // Validate and convert fields
    if (!is_valid_symbol(symbol)) {
        return ParseResult::INVALID_FORMAT;
    }
    message.symbol = symbol;
    
    // Convert side
    message.side = fix_side_to_enum(side_str);
    
    // Convert price
    if (!price_str.empty()) {
        try {
            message.price = std::stod(price_str);
            if (!is_valid_price(message.price)) {
                return ParseResult::INVALID_FORMAT;
            }
        } catch (const std::exception&) {
            return ParseResult::INVALID_FORMAT;
        }
    }
    
    // Convert size
    if (!size_str.empty()) {
        try {
            message.size = std::stoi(size_str);
            if (!is_valid_size(message.size)) {
                return ParseResult::INVALID_FORMAT;
            }
        } catch (const std::exception&) {
            return ParseResult::INVALID_FORMAT;
        }
    }
    
    // Convert message type
    message.type = fix_msgtype_to_enum(msgtype_str);
    
    return ParseResult::SUCCESS;
}

bool MessageParser::extract_fix_field(const char* buffer, size_t length, 
                                     const std::string& tag, std::string& value) {
    value.clear();
    
    std::string search_pattern = tag + "=";
    const char* pos = std::search(buffer, buffer + length, 
                                 search_pattern.begin(), search_pattern.end());
    
    if (pos == buffer + length) {
        return false;  // Tag not found
    }
    
    // Move past the tag and '='
    pos += search_pattern.length();
    
    // Extract value until delimiter or end
    const char* value_start = pos;
    while (pos < buffer + length && *pos != FIX_DELIMITER) {
        pos++;
    }
    
    value.assign(value_start, pos - value_start);
    return true;
}

ParseResult MessageParser::parse_websocket_json(const char* buffer, size_t length, MarketMessage& message) {
    return parse_json_fields(buffer, length, message);
}

ParseResult MessageParser::parse_json_fields(const char* buffer, size_t length, MarketMessage& message) {
    std::string json(buffer, length);
    std::string symbol, side_str, type_str;
    double price = 0.0, bid = 0.0, ask = 0.0;
    int32_t size = 0, bid_size = 0, ask_size = 0;
    
    // Extract required fields
    if (!extract_json_field(json, "symbol", symbol)) {
        return ParseResult::INVALID_FORMAT;  // Symbol is required
    }
    
    if (!is_valid_symbol(symbol)) {
        return ParseResult::INVALID_FORMAT;
    }
    message.symbol = symbol;
    
    // Extract optional fields
    extract_json_field(json, "side", side_str);
    extract_json_field(json, "type", type_str);
    
    // Handle different JSON formats
    if (extract_json_double(json, "price", price)) {
        message.price = price;
        extract_json_int(json, "size", size);
        message.size = size;
    } else {
        // Handle bid/ask format
        if (extract_json_double(json, "bid", bid) && extract_json_double(json, "ask", ask)) {
            message.price = (bid + ask) / 2.0;  // Use mid-price
            extract_json_int(json, "bid_size", bid_size);
            extract_json_int(json, "ask_size", ask_size);
            message.size = bid_size + ask_size;  // Combined size
            message.type = MessageType::QUOTE;
        }
    }
    
    // Convert side
    if (!side_str.empty()) {
        if (side_str == "buy" || side_str == "BUY") {
            message.side = Side::BUY;
        } else if (side_str == "sell" || side_str == "SELL") {
            message.side = Side::SELL;
        }
    }
    
    // Set message type based on JSON type field
    if (type_str == "trade") {
        message.type = MessageType::TRADE;
    } else if (type_str == "quote") {
        message.type = MessageType::QUOTE;
    } else if (type_str == "order") {
        message.type = MessageType::NEW_ORDER;
    } else if (message.type == MessageType::UNKNOWN) {
        message.type = MessageType::MARKET_DATA;  // Default for market data
    }
    
    // Validate converted data
    if (!is_valid_price(message.price) || !is_valid_size(message.size)) {
        return ParseResult::INVALID_FORMAT;
    }
    
    return ParseResult::SUCCESS;
}

bool MessageParser::extract_json_field(const std::string& json, const std::string& key, std::string& value) {
    std::string search_key = "\"" + key + "\"";
    size_t pos = json.find(search_key);
    if (pos == std::string::npos) {
        return false;
    }
    
    // Find the colon after the key
    pos = json.find(":", pos);
    if (pos == std::string::npos) {
        return false;
    }
    pos++;
    
    // Skip whitespace
    while (pos < json.length() && std::isspace(json[pos])) pos++;
    
    if (pos >= json.length()) return false;
    
    // Extract string value (handle quotes)
    if (json[pos] == '"') {
        pos++;  // Skip opening quote
        size_t end_pos = json.find('"', pos);
        if (end_pos == std::string::npos) return false;
        value = json.substr(pos, end_pos - pos);
    } else {
        // Non-string value, find end (comma, brace, or end)
        size_t end_pos = pos;
        while (end_pos < json.length() && 
               json[end_pos] != ',' && 
               json[end_pos] != '}' && 
               json[end_pos] != ']') {
            end_pos++;
        }
        value = json.substr(pos, end_pos - pos);
        
        // Trim whitespace
        value.erase(0, value.find_first_not_of(" \t\n\r"));
        value.erase(value.find_last_not_of(" \t\n\r") + 1);
    }
    
    return true;
}

bool MessageParser::extract_json_double(const std::string& json, const std::string& key, double& value) {
    std::string str_value;
    if (!extract_json_field(json, key, str_value)) {
        return false;
    }
    
    try {
        value = std::stod(str_value);
        return true;
    } catch (const std::exception&) {
        return false;
    }
}

bool MessageParser::extract_json_int(const std::string& json, const std::string& key, int32_t& value) {
    std::string str_value;
    if (!extract_json_field(json, key, str_value)) {
        return false;
    }
    
    try {
        value = std::stoi(str_value);
        return true;
    } catch (const std::exception&) {
        return false;
    }
}

Side MessageParser::fix_side_to_enum(const std::string& side_str) {
    if (side_str == "1") return Side::BUY;
    if (side_str == "2") return Side::SELL;
    return Side::UNKNOWN;
}

MessageType MessageParser::fix_msgtype_to_enum(const std::string& msgtype_str) {
    if (msgtype_str == "D") return MessageType::NEW_ORDER;
    if (msgtype_str == "F") return MessageType::CANCEL_ORDER;
    if (msgtype_str == "G") return MessageType::MODIFY_ORDER;
    if (msgtype_str == "8") return MessageType::TRADE;
    return MessageType::UNKNOWN;
}

bool MessageParser::is_valid_symbol(const std::string& symbol) {
    return !symbol.empty() && 
           symbol.length() <= MAX_SYMBOL_LENGTH &&
           std::all_of(symbol.begin(), symbol.end(), 
                      [](char c) { return std::isalnum(c) || c == '.'; });
}

bool MessageParser::is_valid_price(double price) {
    return price >= 0.0 && std::isfinite(price);
}

bool MessageParser::is_valid_size(int32_t size) {
    return size >= 0;
}

void MessageParser::reset_parser_state() {
    messages_parsed_ = 0;
    parse_errors_ = 0;
}

uint64_t MessageParser::get_current_timestamp_ns() {
    auto now = std::chrono::high_resolution_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count();
}

} // namespace ingestion
} // namespace hft 