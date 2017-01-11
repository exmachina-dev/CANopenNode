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
    BOOL        = (0x01, 1)    # Boolean
    INT8        = (0x02, 1)    # Integer 8
    INT16       = (0x03, 2)    # Integer 16
    INT32       = (0x04, 4)    # Integer 32
    UINT8       = (0x05, 1)    # Unsigned integer 8
    UINT16      = (0x06, 2)    # Unsigned integer 16
    UINT32      = (0x07, 4)    # Unsigned integer 32
    REAL32      = (0x08, 4)    # Real 32
    VSTRING     = (0x09, -1)    # Visible string
    OSTRING     = (0x0A, -1)    # Octet string
    USTRING     = (0x0B, -1)    # Unicode string
    TIMEOD      = (0x0C, 6)    # Time of day
    TIMEDIFF    = (0x0D, 6)    # Time difference
    DOMAIN      = (0x0F, -1)    # Domain
    INT24       = (0x10, 3)    # Integer 24
    REAL64      = (0x11, 8)    # Real 64
    INT40       = (0x12, 5)    # Integer 40
    INT48       = (0x13, 6)    # Integer 48
    INT56       = (0x14, 7)    # Integer 56
    INT64       = (0x15, 8)    # Integer 64
    UINT24      = (0x16, 3)    # Unsigned integer 24
    UINT40      = (0x18, 5)    # Unsigned integer 40
    UINT48      = (0x19, 6)    # Unsigned integer 48
    UINT56      = (0x1A, 7)    # Unsigned integer 56
    UINT64      = (0x1B, 8)    # Unsigned integer 64

    def __init__(self, ident, bsize):
        self.ident = ident
        self.bsize = bsize


class AccessType(Enum):
    CONST   = 0x01     # Constant
    RO      = 0x01     # Read-only
    WO      = 0x01     # Write-only
    RW      = 0x01     # Read-write


class PDOMapping(Enum):
    OPT     = 0x01     # Optionnal
    RPDO    = 0x02     # RPDO
    TPDO    = 0x03     # TPDO
