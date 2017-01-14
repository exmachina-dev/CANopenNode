# -*- coding: utf-8 -*-
from enum import Enum, unique


@unique
class MemoryType(Enum):
    ROM     = 0x01
    RAM     = 0x02
    EEPROM  = 0x03


@unique
class ObjectType(Enum):
    VAR     = 0x07
    ARRAY   = 0x08
    RECORD  = 0x09


@unique
class DataType(Enum):
    BOOL        = (0x01, 1,  'BOOLEAN')
    INT8        = (0x02, 1,  'INTEGER8')
    INT16       = (0x03, 2,  'INTEGER16')
    INT32       = (0x04, 4,  'INTEGER32')
    UINT8       = (0x05, 1,  'UNSIGNED8')
    UINT16      = (0x06, 2,  'UNSIGNED16')
    UINT32      = (0x07, 4,  'UNSIGNED32')
    REAL32      = (0x08, 4,  'REAL32')
    VSTRING     = (0x09, -1, 'VISIBLE_STRING')
    OSTRING     = (0x0A, -1, 'OCTET_STRING')
    USTRING     = (0x0B, -1, 'UNICODE_STRING')
    TIMEOD      = (0x0C, 6,  'TIME_OF_DAY')
    TIMEDIFF    = (0x0D, 6,  'TIME_DIFFERENCE')
    DOMAIN      = (0x0F, -1, 'DOMAIN')
    INT24       = (0x10, 3,  'INTEGER24')
    REAL64      = (0x11, 8,  'REAL64')
    INT40       = (0x12, 5,  'INTEGER40')
    INT48       = (0x13, 6,  'INTEGER48')
    INT56       = (0x14, 7,  'INTEGER56')
    INT64       = (0x15, 8,  'INTEGER64')
    UINT24      = (0x16, 3,  'UNSIGNED24')
    UINT40      = (0x18, 5,  'UNSIGNED40')
    UINT48      = (0x19, 6,  'UNSIGNED48')
    UINT56      = (0x1A, 7,  'UNSIGNED56')
    UINT64      = (0x1B, 8,  'UNSIGNED64')

    def __init__(self, ident, bsize, cname):
        self.ident = ident
        self.bsize = bsize
        self.cname = cname

    @property
    def is_signed_integer(self):
        if self in (DataType.INT8, DataType.INT16, DataType.INT24, DataType.INT32,
                    DataType.INT40, DataType.INT48, DataType.INT56, DataType.INT64):
            return True

        return False

    @property
    def is_unsigned_integer(self):
        if self in (DataType.UINT8, DataType.UINT16, DataType.UINT24, DataType.UINT32,
                    DataType.UINT40, DataType.UINT48, DataType.UINT56, DataType.UINT64):
            return True

        return False

    @property
    def is_integer(self):
        return self.is_unsigned_integer or self.is_signed_integer

    @property
    def is_array(self):
        if self in (DataType.VSTRING, DataType.OSTRING, DataType.USTRING):
            return True

        return False

    @property
    def clen(self):
        if self.is_array:
            return len(self.value)

        return self.data_type.bsize


class AccessType(Enum):
    CONST   = 0x01     # Constant
    RO      = 0x01     # Read-only
    WO      = 0x01     # Write-only
    RW      = 0x01     # Read-write


class PDOMapping(Enum):
    OPT     = 0x01     # Optionnal
    RPDO    = 0x02     # RPDO
    TPDO    = 0x03     # TPDO
