# -*- coding: utf-8 -*-


CO_OD_H = '''
/*******************************************************************************

   File: CO{OD_info[reference]}_OD.h
   CANopen Object Dictionary.

   Copyright (C) 2004-2008 Janez Paternoster

   License: GNU Lesser General Public License (LGPL).

   <http://canopennode.sourceforge.net>

   (For more information see <CO_SDO.h>.)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 2.1 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.


   Author: Janez Paternoster


   This file was automatically generated with CANopenNode ODE.
   DON'T EDIT THIS FILE MANUALLY !!!!

*******************************************************************************/

#ifndef CO_OD{OD_info[reference]}_H
#define CO_OD{OD_info[reference]}_H


/*******************************************************************************
   CANopen DATA DYPES
*******************************************************************************/
typedef uint8_t      CO_UNSIGNED8;
typedef uint16_t     CO_UNSIGNED16;
typedef uint32_t     CO_UNSIGNED32;
typedef uint64_t     CO_UNSIGNED64;
typedef int8_t       CO_INTEGER8;
typedef int16_t      CO_INTEGER16;
typedef int32_t      CO_INTEGER32;
typedef int64_t      CO_INTEGER64;
typedef float32_t    CO_REAL32;
typedef float64_t    CO_REAL64;
typedef char_t       CO_VISIBLE_STRING;
typedef oChar_t      CO_OCTET_STRING;
typedef domain_t     CO_DOMAIN;


/*******************************************************************************
    FILE INFO:
        FileName:     {OD_info[name]}
        FileVersion:  {OD_info[version]}
        CreationTime: {OD_info[creation_time]}
        CreationDate: {OD_info[creation_date]}
        CreatedBy:    {OD_info[creator]}
*******************************************************************************/


/*******************************************************************************
    DEVICE INFO:
{OD_device_info}
*******************************************************************************/


/*******************************************************************************
    FEATURES
*******************************************************************************/
{OD_H_macros}


/*******************************************************************************
    OBJECT DICTIONARY
*******************************************************************************/
   #define CO{OD_info[reference]}_OD_NoOfElements             {OD_C_OD_length}


/*******************************************************************************
    TYPE DEFINITIONS FOR RECORDS
*******************************************************************************/
{OD_H_typedefs}


/*******************************************************************************
    STRUCTURES FOR VARIABLES IN DIFFERENT MEMORY LOCATIONS
*******************************************************************************/
#define  CO{OD_info[reference]}_OD_FIRST_LAST_WORD     0x55 //Any value from 0x01 to 0xFE. If changed, EEPROM will be reinitialized.

/***** Structure for RAM variables ********************************************/
struct sCO{OD_info[reference]}_OD_RAM{{
               CO_UNSIGNED32     FirstWord;

{OD_H_RAM}

               CO_UNSIGNED32     LastWord;
}};

/***** Structure for EEPROM variables *****************************************/
struct sCO{OD_info[reference]}_OD_EEPROM{{
               CO_UNSIGNED32     FirstWord;

{OD_H_EEPROM}

               CO_UNSIGNED32     LastWord;
}};


/***** Structure for ROM variables ********************************************/
struct sCO{OD_info[reference]}_OD_ROM{{
               CO_UNSIGNED32     FirstWord;

{OD_H_ROM}

               CO_UNSIGNED32     LastWord;
}};


/***** Declaration of Object Dictionary variables *****************************/
extern struct sCO{OD_info[reference]}_OD_RAM CO{OD_info[reference]}_OD_RAM;

extern struct sCO{OD_info[reference]}_OD_EEPROM CO{OD_info[reference]}_OD_EEPROM;

extern struct sCO{OD_info[reference]}_OD_ROM CO{OD_info[reference]}_OD_ROM;


/*******************************************************************************
    ALIASES FOR OBJECT DICTIONARY VARIABLES
*******************************************************************************/
{OD_H_aliases}

#endif
'''

CO_OD_C = '''
/*******************************************************************************

   File - CO{OD_info[reference]}_OD.c
   CANopen Object Dictionary.

   Copyright (C) 2004-2008 Janez Paternoster

   License: GNU Lesser General Public License (LGPL).

   <http://canopennode.sourceforge.net>

   (For more information see <CO_SDO.h>.)
*/
/*
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 2.1 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.


   Author: Janez Paternoster


   This file was automatically generated with CANopenNode ODE.
   DON'T EDIT THIS FILE MANUALLY !!!!

*******************************************************************************/


#include "CO_driver.h"
#include "CO{OD_info[reference]}_OD.h"
#include "CO_SDO.h"


/*******************************************************************************
    DEFINITION AND INITIALIZATION OF OBJECT DICTIONARY VARIABLES
*******************************************************************************/

/***** Definition for RAM variables *******************************************/
struct sCO{OD_info[reference]}_OD_RAM CO{OD_info[reference]}_OD_RAM = {{
    CO{OD_info[reference]}_OD_FIRST_LAST_WORD,

{OD_C_initRAM}

   CO{OD_info[reference]}_OD_FIRST_LAST_WORD,
}};


/***** Definition for EEPROM variables ****************************************/
struct sCO{OD_info[reference]}_OD_EEPROM CO{OD_info[reference]}_OD_EEPROM = {{
    CO{OD_info[reference]}_OD_FIRST_LAST_WORD,

{OD_C_initEEPROM}

    CO{OD_info[reference]}_OD_FIRST_LAST_WORD,
}};


/***** Definition for ROM variables *******************************************/
struct sCO{OD_info[reference]}_OD_ROM CO{OD_info[reference]}_OD_ROM = {{    //constant variables, stored in flash
    CO{OD_info[reference]}_OD_FIRST_LAST_WORD,

{OD_C_initROM}

    CO{OD_info[reference]}_OD_FIRST_LAST_WORD
}};


/*******************************************************************************
   STRUCTURES FOR RECORD TYPE OBJECTS
*******************************************************************************/
{OD_C_records}


/*******************************************************************************
   SDO SERVER ACCESS FUNCTIONS WITH USER CODE
*******************************************************************************/
#define WRITING (dir == 1)
#define READING (dir == 0)

{OD_C_functions}


/*******************************************************************************
   OBJECT DICTIONARY
*******************************************************************************/
const CO_OD_entry_t CO{OD_info[reference]}_OD[CO{OD_info[reference]}_OD_NoOfElements] = {{
{OD_C_OD}
}};
'''
