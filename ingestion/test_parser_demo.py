#!/usr/bin/env python3
"""
Demonstration script for the HFT message parser.
Shows parsing of both FIX and WebSocket JSON messages.
"""

import json
import time
from parser_wrapper import MessageParser, ParseResult, create_sample_messages


def test_fix_parsing():
    """Test FIX message parsing"""
    print("=== FIX Message Parsing Test ===")
    
    # Create sample FIX messages
    fix_messages = [
        # New Order message
        "8=FIX.4.4\x019=178\x0135=D\x0149=SENDER\x0156=TARGET\x0155=AAPL\x0154=1\x0144=150.25\x0138=100\x01",
        # Trade execution message
        "8=FIX.4.4\x019=165\x0135=8\x0149=EXCHANGE\x0156=TRADER\x0155=MSFT\x0154=2\x0144=300.50\x0138=50\x01",
        # Cancel order message
        "8=FIX.4.4\x019=145\x0135=F\x0149=TRADER\x0156=EXCHANGE\x0155=GOOGL\x0154=1\x0144=2500.00\x0138=25\x01"
    ]
    
    parser = MessageParser()
    
    for i, fix_msg in enumerate(fix_messages, 1):
        print(f"\nFIX Message {i}:")
        print(f"Raw: {fix_msg.replace(chr(1), '|')}")  # Replace SOH with | for display
        
        result, message = parser.parse_message(fix_msg)
        
        if result == ParseResult.SUCCESS:
            print(f"✓ Parsed successfully: {message}")
            print(f"  JSON: {json.dumps(message.to_dict(), indent=2)}")
        else:
            print(f"✗ Parse failed: {result.name}")


def test_websocket_parsing():
    """Test WebSocket JSON message parsing"""
    print("\n\n=== WebSocket JSON Parsing Test ===")
    
    # Create sample WebSocket messages
    websocket_messages = [
        # Trade message
        {
            "type": "trade",
            "symbol": "AAPL",
            "side": "buy",
            "price": 150.25,
            "size": 100,
            "timestamp": int(time.time() * 1_000_000_000)
        },
        # Quote message with bid/ask
        {
            "type": "quote",
            "symbol": "MSFT",
            "bid": 300.45,
            "ask": 300.55,
            "bid_size": 75,
            "ask_size": 25,
            "timestamp": int(time.time() * 1_000_000_000)
        },
        # Order message
        {
            "type": "order",
            "symbol": "GOOGL",
            "side": "sell",
            "price": 2500.00,
            "size": 10
        },
        # Market data message
        {
            "symbol": "TSLA",
            "price": 800.75,
            "size": 200,
            "last_trade_time": int(time.time() * 1000)
        }
    ]
    
    parser = MessageParser()
    
    for i, ws_msg in enumerate(websocket_messages, 1):
        print(f"\nWebSocket Message {i}:")
        json_str = json.dumps(ws_msg, indent=2)
        print(f"Raw JSON:\n{json_str}")
        
        result, message = parser.parse_message(json_str)
        
        if result == ParseResult.SUCCESS:
            print(f"✓ Parsed successfully: {message}")
            print(f"  Structured: {json.dumps(message.to_dict(), indent=2)}")
        else:
            print(f"✗ Parse failed: {result.name}")


def test_error_handling():
    """Test error handling with invalid messages"""
    print("\n\n=== Error Handling Test ===")
    
    invalid_messages = [
        # Invalid FIX (missing symbol)
        "8=FIX.4.4\x019=100\x0135=D\x0149=SENDER\x0156=TARGET\x0154=1\x0144=150.25\x01",
        # Invalid JSON
        '{"symbol": "AAPL", "price": "invalid_price"}',
        # Unknown protocol
        "INVALID_MESSAGE_FORMAT",
        # Empty message
        "",
        # Malformed JSON
        '{"symbol": "AAPL", "price": 150.25'
    ]
    
    parser = MessageParser()
    
    for i, invalid_msg in enumerate(invalid_messages, 1):
        print(f"\nInvalid Message {i}:")
        print(f"Raw: {invalid_msg}")
        
        result, message = parser.parse_message(invalid_msg)
        print(f"Expected failure: {result.name} (message: {message})")


def performance_test():
    """Simple performance test"""
    print("\n\n=== Performance Test ===")
    
    # Create test messages
    fix_msg, ws_msg = create_sample_messages()
    parser = MessageParser()
    
    # Test FIX parsing performance
    num_iterations = 10000
    start_time = time.time()
    
    for _ in range(num_iterations):
        parser.parse_message(fix_msg)
    
    fix_duration = time.time() - start_time
    fix_rate = num_iterations / fix_duration
    
    print(f"FIX Parsing:")
    print(f"  {num_iterations} messages in {fix_duration:.3f}s")
    print(f"  Rate: {fix_rate:,.0f} messages/second")
    
    # Reset parser stats
    parser.reset_statistics()
    
    # Test WebSocket parsing performance
    start_time = time.time()
    
    for _ in range(num_iterations):
        parser.parse_message(ws_msg)
    
    ws_duration = time.time() - start_time
    ws_rate = num_iterations / ws_duration
    
    print(f"\nWebSocket JSON Parsing:")
    print(f"  {num_iterations} messages in {ws_duration:.3f}s")
    print(f"  Rate: {ws_rate:,.0f} messages/second")
    
    # Show final statistics
    stats = parser.get_statistics()
    print(f"\nFinal Statistics:")
    print(f"  Messages parsed: {stats['messages_parsed']:,}")
    print(f"  Parse errors: {stats['parse_errors']:,}")
    print(f"  Error rate: {stats['error_rate']:.3%}")


def main():
    """Run all tests"""
    print("HFT Message Parser Demonstration")
    print("=" * 50)
    
    try:
        test_fix_parsing()
        test_websocket_parsing()
        test_error_handling()
        performance_test()
        
        print("\n\n=== Summary ===")
        print("✓ All tests completed successfully!")
        print("The parser supports:")
        print("  - FIX protocol message parsing")
        print("  - WebSocket JSON message parsing")
        print("  - Automatic protocol detection")
        print("  - Error handling and validation")
        print("  - Performance statistics")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 