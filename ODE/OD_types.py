# -*- coding: utf-8 -*-
from enum import Enum, unique


@unique
class MemoryType(Enum):
    RAM     = 0x01
    EEPROM  = 0x02
    ROM     = 0x03


@unique
class ObjectType(Enum):
    VAR     = 0x07
    ARRAY   = 0x08
    RECORD  = 0x09


@unique
class DataType(Enum):
    BOOL        = 0x01    # Boolean
    INT8        = 0x02    # Integer 8
    INT16       = 0x03    # Integer 16
    INT32       = 0x04    # Integer 32
    UINT8       = 0x05    # Unsigned integer 8
    UINT16      = 0x06    # Unsigned integer 16
    UINT32      = 0x07    # Unsigned integer 32
    REAL32      = 0x08    # Real 32
    VSTRING     = 0x09    # Visible string
    OSTRING     = 0x0A    # Octet string
    USTRING     = 0x0B    # Unicode string
    TIMEOD      = 0x0C    # Time of day
    TIMEDIFF    = 0x0D    # Time difference
    DOMAIN      = 0x0F    # Domain
    INT24       = 0x10    # Integer 24
    REAL64      = 0x11    # Real 64
    INT40       = 0x12    # Integer 40
    INT48       = 0x13    # Integer 48
    INT56       = 0x14    # Integer 56
    INT64       = 0x15    # Integer 64
    UINT24      = 0x16    # Unsigned integer 24
    UINT40      = 0x18    # Unsigned integer 40
    UINT48      = 0x19    # Unsigned integer 48
    UINT56      = 0x1A    # Unsigned integer 56
    UINT64      = 0x1B    # Unsigned integer 64


class AccessType(Enum):
    CONST   = 0x01     # Constant
    RO      = 0x01     # Read-only
    WO      = 0x01     # Write-only
    RW      = 0x01     # Read-write
