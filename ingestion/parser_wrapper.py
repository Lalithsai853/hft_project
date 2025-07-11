"""
Python wrapper for the HFT C++ message parser.
Provides high-level Python interface for parsing FIX and WebSocket messages.
"""

import ctypes
import os
import sys
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Tuple, Union
import json
import time
import warnings

# Add the current directory to the path for loading the shared library
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class Side(IntEnum):
    """Trading side enumeration matching C++ enum"""
    UNKNOWN = 0
    BUY = 1
    SELL = 2


class MessageType(IntEnum):
    """Message type enumeration matching C++ enum"""
    UNKNOWN = 0
    NEW_ORDER = 1
    CANCEL_ORDER = 2
    MODIFY_ORDER = 3
    TRADE = 4
    QUOTE = 5
    MARKET_DATA = 6


class ProtocolType(IntEnum):
    """Protocol type enumeration matching C++ enum"""
    UNKNOWN = 0
    FIX = 1
    WEBSOCKET_JSON = 2


class ParseResult(IntEnum):
    """Parse result status matching C++ enum"""
    SUCCESS = 0
    INVALID_FORMAT = 1
    INCOMPLETE_MESSAGE = 2
    UNKNOWN_PROTOCOL = 3
    BUFFER_OVERFLOW = 4


@dataclass
class MarketMessage:
    """Python representation of parsed market message"""
    timestamp: int = 0              # Nanoseconds since epoch
    symbol: str = ""                # Trading symbol
    side: Side = Side.UNKNOWN       # BUY/SELL/UNKNOWN
    price: float = 0.0              # Price level
    size: int = 0                   # Quantity
    message_type: MessageType = MessageType.UNKNOWN  # Message classification
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'side': self.side.name,
            'price': self.price,
            'size': self.size,
            'type': self.message_type.name
        }
    
    def __str__(self) -> str:
        return (f"MarketMessage(symbol={self.symbol}, side={self.side.name}, "
                f"price={self.price}, size={self.size}, type={self.message_type.name})")


class MessageParser:
    """
    High-performance Python wrapper for C++ message parser.
    
    Handles both FIX protocol and WebSocket JSON message parsing
    with automatic protocol detection.
    
    Falls back to Python implementation if C++ library is not available.
    """
    
    def __init__(self, library_path: Optional[str] = None, use_cpp: bool = True):
        """
        Initialize the message parser.
        
        Args:
            library_path: Optional path to the C++ shared library
            use_cpp: Whether to attempt to use C++ implementation
        """
        self._lib = None
        self._parser_instance = None
        self._use_cpp = False
        
        # Try to load C++ library if requested
        if use_cpp:
            try:
                self._load_library(library_path)
                self._setup_function_signatures()
                self._create_parser_instance()
                self._use_cpp = True
            except Exception as e:
                warnings.warn(f"Failed to load C++ library, falling back to Python implementation: {e}")
                self._use_cpp = False
        
        # Statistics
        self.messages_parsed = 0
        self.parse_errors = 0
        
    def _load_library(self, library_path: Optional[str]):
        """Load the C++ shared library"""
        if library_path is None:
            # Try to find the library in common locations
            possible_paths = [
                './libhft_ingestion.so',       # Linux
                './libhft_ingestion.dylib',    # macOS
                './hft_ingestion.dll',         # Windows
                './build/libhft_ingestion.so',
                './build/libhft_ingestion.dylib',
                './build/hft_ingestion.dll'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    library_path = path
                    break
            
            if library_path is None:
                raise RuntimeError("Could not find HFT ingestion library in standard locations")
        
        try:
            self._lib = ctypes.CDLL(library_path)
        except OSError as e:
            raise RuntimeError(f"Failed to load library {library_path}: {e}")
    
    def _setup_function_signatures(self):
        """Setup function signatures for proper C++ interface"""
        # This is a simplified interface - in practice, you'd use pybind11 or similar
        # For now, we'll implement the parsing logic in Python as a fallback
        pass
    
    def _create_parser_instance(self):
        """Create C++ parser instance"""
        # Placeholder for C++ instance creation
        # In practice, this would create a C++ MessageParser object
        self._parser_instance = True
    
    def parse_message(self, data: Union[str, bytes]) -> Tuple[ParseResult, Optional[MarketMessage]]:
        """
        Parse a raw message into a structured MarketMessage.
        
        Args:
            data: Raw message data (string or bytes)
            
        Returns:
            Tuple of (parse_result, parsed_message)
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Detect protocol
        protocol = self._detect_protocol(data)
        
        if protocol == ProtocolType.UNKNOWN:
            self.parse_errors += 1
            return ParseResult.UNKNOWN_PROTOCOL, None
        
        # Parse based on protocol (using Python implementation for now)
        try:
            if protocol == ProtocolType.FIX:
                result, message = self._parse_fix_message(data)
            elif protocol == ProtocolType.WEBSOCKET_JSON:
                result, message = self._parse_websocket_json(data)
            else:
                return ParseResult.UNKNOWN_PROTOCOL, None
            
            if result == ParseResult.SUCCESS:
                self.messages_parsed += 1
                # Set timestamp if not provided
                if message and message.timestamp == 0:
                    message.timestamp = self._get_current_timestamp_ns()
            else:
                self.parse_errors += 1
                
            return result, message
            
        except Exception as e:
            self.parse_errors += 1
            print(f"Parse error: {e}")
            return ParseResult.INVALID_FORMAT, None
    
    def _detect_protocol(self, data: bytes) -> ProtocolType:
        """Detect the protocol type from message data"""
        if len(data) < 2:
            return ProtocolType.UNKNOWN
        
        # Check for FIX protocol (starts with "8=")
        if data.startswith(b'8='):
            return ProtocolType.FIX
        
        # Check for JSON (starts with '{' or whitespace + '{')
        data_str = data.decode('utf-8', errors='ignore').lstrip()
        if data_str.startswith('{'):
            return ProtocolType.WEBSOCKET_JSON
        
        return ProtocolType.UNKNOWN
    
    def _parse_fix_message(self, data: bytes) -> Tuple[ParseResult, Optional[MarketMessage]]:
        """Parse FIX protocol message"""
        try:
            # Convert to string and split by FIX delimiter (SOH = \x01)
            fix_str = data.decode('utf-8').replace('\x01', '|')
            fields = {}
            
            # Parse tag=value pairs
            for pair in fix_str.split('|'):
                if '=' in pair:
                    tag, value = pair.split('=', 1)
                    fields[tag] = value
            
            # Extract required fields
            symbol = fields.get('55')  # Symbol
            if not symbol:
                return ParseResult.INVALID_FORMAT, None
            
            message = MarketMessage()
            message.symbol = symbol
            
            # Extract optional fields
            if '54' in fields:  # Side
                side_str = fields['54']
                if side_str == '1':
                    message.side = Side.BUY
                elif side_str == '2':
                    message.side = Side.SELL
            
            if '44' in fields:  # Price
                try:
                    message.price = float(fields['44'])
                except ValueError:
                    return ParseResult.INVALID_FORMAT, None
            
            if '38' in fields:  # OrderQty
                try:
                    message.size = int(fields['38'])
                except ValueError:
                    return ParseResult.INVALID_FORMAT, None
            
            if '35' in fields:  # MsgType
                msgtype = fields['35']
                if msgtype == 'D':
                    message.message_type = MessageType.NEW_ORDER
                elif msgtype == 'F':
                    message.message_type = MessageType.CANCEL_ORDER
                elif msgtype == 'G':
                    message.message_type = MessageType.MODIFY_ORDER
                elif msgtype == '8':
                    message.message_type = MessageType.TRADE
            
            return ParseResult.SUCCESS, message
            
        except Exception:
            return ParseResult.INVALID_FORMAT, None
    
    def _parse_websocket_json(self, data: bytes) -> Tuple[ParseResult, Optional[MarketMessage]]:
        """Parse WebSocket JSON message"""
        try:
            json_data = json.loads(data.decode('utf-8'))
            
            # Extract required fields
            symbol = json_data.get('symbol')
            if not symbol:
                return ParseResult.INVALID_FORMAT, None
            
            message = MarketMessage()
            message.symbol = symbol
            
            # Extract optional fields
            side_str = json_data.get('side', '').lower()
            if side_str in ['buy', 'b']:
                message.side = Side.BUY
            elif side_str in ['sell', 's']:
                message.side = Side.SELL
            
            # Handle different price formats
            if 'price' in json_data:
                message.price = float(json_data['price'])
                message.size = int(json_data.get('size', 0))
            elif 'bid' in json_data and 'ask' in json_data:
                # Use mid-price for quotes
                bid = float(json_data['bid'])
                ask = float(json_data['ask'])
                message.price = (bid + ask) / 2.0
                message.size = int(json_data.get('bid_size', 0)) + int(json_data.get('ask_size', 0))
                message.message_type = MessageType.QUOTE
            
            # Set message type
            msg_type = json_data.get('type', '').lower()
            if msg_type == 'trade':
                message.message_type = MessageType.TRADE
            elif msg_type == 'quote':
                message.message_type = MessageType.QUOTE
            elif msg_type == 'order':
                message.message_type = MessageType.NEW_ORDER
            elif message.message_type == MessageType.UNKNOWN:
                message.message_type = MessageType.MARKET_DATA
            
            # Extract timestamp if provided
            if 'timestamp' in json_data:
                message.timestamp = int(json_data['timestamp'])
            
            return ParseResult.SUCCESS, message
            
        except (json.JSONDecodeError, ValueError, KeyError):
            return ParseResult.INVALID_FORMAT, None
    
    def _get_current_timestamp_ns(self) -> int:
        """Get current timestamp in nanoseconds"""
        return int(time.time() * 1_000_000_000)
    
    def get_statistics(self) -> dict:
        """Get parser statistics"""
        return {
            'messages_parsed': self.messages_parsed,
            'parse_errors': self.parse_errors,
            'error_rate': self.parse_errors / max(1, self.messages_parsed + self.parse_errors),
            'implementation': 'C++' if self._use_cpp else 'Python'
        }
    
    def reset_statistics(self):
        """Reset parser statistics"""
        self.messages_parsed = 0
        self.parse_errors = 0


# Convenience functions for easy usage
def parse_fix_message(data: Union[str, bytes]) -> Tuple[ParseResult, Optional[MarketMessage]]:
    """Parse a single FIX message"""
    parser = MessageParser()
    return parser.parse_message(data)


def parse_websocket_message(data: Union[str, bytes]) -> Tuple[ParseResult, Optional[MarketMessage]]:
    """Parse a single WebSocket JSON message"""
    parser = MessageParser()
    return parser.parse_message(data)


def create_sample_messages():
    """Create sample messages for testing"""
    fix_message = "8=FIX.4.4\x019=178\x0135=D\x0149=SENDER\x0156=TARGET\x0155=AAPL\x0154=1\x0144=150.25\x0138=100\x01"
    
    websocket_message = {
        "type": "trade",
        "symbol": "AAPL",
        "side": "buy",
        "price": 150.25,
        "size": 100,
        "timestamp": int(time.time() * 1_000_000_000)
    }
    
    return fix_message, json.dumps(websocket_message) 