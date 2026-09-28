/*==================================================================================================
*   Project              : RTD AUTOSAR 4.9
*   Platform             : CORTEXM
*   Peripheral           : LPUART_FLEXIO
*   Dependencies         : none
*
*   Autosar Version      : 4.9.0
*   Autosar Revision     : ASR_REL_4_9_REV_0000
*   Autosar Conf.Variant :
*   SW Version           : 7.0.1
*   Build Version        : S32K3_RTD_7_0_1_D2602_ASR_REL_4_9_REV_0000_20260206
*
*   Copyright 2020 - 2026 NXP
*
*   NXP Confidential and Proprietary. This software is owned or controlled by NXP and may only be
*   used strictly in accordance with the applicable license terms. By expressly
*   accepting such terms or by downloading, installing, activating and/or otherwise
*   using the software, you are agreeing that you have read, and that you agree to
*   comply with and are bound by, such license terms. If you do not agree to be
*   bound by the applicable license terms, then you may not retain, install,
*   activate or otherwise use the software.
==================================================================================================*/

#ifndef LIN_43_LPUART_FLEXIO_DEFINES_H
#define LIN_43_LPUART_FLEXIO_DEFINES_H

/**
*   @file
*
*   @defgroup lin_driver LIN Driver
*   @addtogroup  lin_driver LIN Driver
*   @{
*/

#ifdef __cplusplus
extern "C"
{
#endif

/*==================================================================================================
*                                        INCLUDE FILES
* 1) system and project includes
* 2) needed interfaces from external units
* 3) internal and external interfaces from this unit
==================================================================================================*/
#include "Mcal.h"
/*==================================================================================================
*                              SOURCE FILE VERSION INFORMATION
==================================================================================================*/
#define LIN_43_LPUART_FLEXIO_DEFINES_VENDOR_ID                     43
#define LIN_43_LPUART_FLEXIO_DEFINES_AR_RELEASE_MAJOR_VERSION      4
#define LIN_43_LPUART_FLEXIO_DEFINES_AR_RELEASE_MINOR_VERSION      9
#define LIN_43_LPUART_FLEXIO_DEFINES_AR_RELEASE_REVISION_VERSION   0
#define LIN_43_LPUART_FLEXIO_DEFINES_SW_MAJOR_VERSION              7
#define LIN_43_LPUART_FLEXIO_DEFINES_SW_MINOR_VERSION              0
#define LIN_43_LPUART_FLEXIO_DEFINES_SW_PATCH_VERSION              1
/*==================================================================================================
*                                       FILE VERSION CHECKS
==================================================================================================*/
#ifndef DISABLE_MCAL_INTERMODULE_ASR_CHECK
    /* Checks against Mcal.h */
    #if ((LIN_43_LPUART_FLEXIO_DEFINES_AR_RELEASE_MAJOR_VERSION != MCAL_AR_RELEASE_MAJOR_VERSION) || \
         (LIN_43_LPUART_FLEXIO_DEFINES_AR_RELEASE_MINOR_VERSION != MCAL_AR_RELEASE_MINOR_VERSION) \
        )
        #error "AUTOSAR Version Numbers of Lin_43_LPUART_FLEXIO_Defines.h and Mcal.h are different"
    #endif
#endif

/*==================================================================================================
*                                          CONSTANTS
==================================================================================================*/
/**
* @brief          Pre-compile Support.
*
*
*/
#define LIN_43_LPUART_FLEXIO_PRECOMPILE_SUPPORT  (STD_OFF) 

/**
* @brief   No of Channels configured.
*
*
*/
#define LIN_43_LPUART_FLEXIO_HW_MAX_MODULES (1U)

/**
* @brief   Total number of available hardware lin channels.
*
*
*/
#define LIN_43_LPUART_FLEXIO_HW_MAX_AVAILABLE_MODULES (20U)

/**
* @brief   Switches the Development Error Detection and Notification ON or OFF.
*
*
*/
#define LIN_43_LPUART_FLEXIO_DEV_ERROR_DETECT (STD_OFF)   /* Disable Development Error Detection */

/**
* @brief   Switches the Production Error Detection and Notification OFF
*
*
*/
#define LIN_43_LPUART_FLEXIO_DISABLE_DEM_REPORT_ERROR_STATUS  (STD_ON) /* Disable Production Error Detection */ 

/**
* @brief          Lin Master Node Used
* @details        When LinGlobalConfig/LinChannel/LinNodeType contains at least one MASTER channel.
*
*
*/
#define LIN_43_LPUART_FLEXIO_MASTER_NODE_USED  (STD_ON) /* Used Master Node */

/**
* @brief          Support for version info API.
* @details        Switches the Lin_GetVersionInfo() API ON or OFF.
*
*
*/
#define LIN_43_LPUART_FLEXIO_VERSION_INFO_API (STD_OFF) /* Disable API Lin_GetVersionInfo     */

/**
* @brief        All PartitionIDs are supported by LIN driver.
*/

#define LIN_43_LPUART_FLEXIO_MAX_PARTITIONS     ((uint32)1U)

/**
* @brief          MultiPartition is enabled or not
*/
#define LIN_43_LPUART_FLEXIO_MULTIPARTITION_SUPPORT   (STD_OFF) /* MultiPartition is disabled */

/**
* @brief          Enable Non-Autosar API for Dual-Clock support.
* @details        Enable/Disable API Lin_SetClockMode() to set the
*                 clock to be used by the LIN driver (Normal clock: default mode;
*                 Alternate clock: when the driver is in Low-Power mode).
*                 This can be set to STD_ON only if it is activated from xdm file:
*                 LinClockRef_Alternate is enable.
*
* @api
*/

#define LIN_43_LPUART_FLEXIO_DUAL_CLOCK_MODE  (STD_OFF) /* Disable API Lin_SetClockMode */ 

#if (STD_ON == LIN_43_LPUART_FLEXIO_DEV_ERROR_DETECT)
/**
*
* @internal
* @brief          Instance number assigned to the driver
* @details        InstanceId of this module instance. If only one instance is present it shall have the Id 0
*
*/
#define LIN_43_LPUART_FLEXIO_DRIVER_INSTANCE             (0U)    /* Instance number assigned to the driver */
#endif

/*==================================================================================================
*                                      DEFINES AND MACROS
==================================================================================================*/
#define LIN_43_LPUART_FLEXIO_UNALLOCATEDPAR_ID  ((uint32)0x00U)

#if (STD_ON == LIN_43_LPUART_FLEXIO_MULTIPARTITION_SUPPORT)
    #define Lin_43_LPUART_FLEXIO_GetUserID() (OsIf_GetUserId())
#else
    #define Lin_43_LPUART_FLEXIO_GetUserID() (LIN_43_LPUART_FLEXIO_UNALLOCATEDPAR_ID)
#endif /* (STD_ON == LIN_43_LPUART_FLEXIO_MULTIPARTITION_SUPPORT) */

/**
* @brief          LIN driver status initialization variable.
*/
#define LIN_43_LPUART_FLEXIO_UNINIT_ARRAY  {LIN_43_LPUART_FLEXIO_UNINIT}


/**
*
* @internal
* @brief          Lin FlexIO Used
* @details        When LinGlobalConfig/LinChannel/LinHwChannel contains FLEXIO.
*
*
*/
#define LIN_43_LPUART_FLEXIO_FLEXIO_USED (STD_OFF) /* No Used Flexio */

/**
*
* @internal
* @brief          Lin Wakeup detection feature
* @details        It is set to STD_ON when LinGlobalConfig/LinChannel/WakeupDetectionSupport is enabled.
*
*
*/
#define LIN_43_LPUART_FLEXIO_WAKEUP_DETECTION (STD_OFF) /* Does not support wakeup detection */

/**
* @brief      Symbolic names of logic channel index.
*/
            
#define LIN1_LPUART9                                ((uint8)0U)            
/*==================================================================================================
*                                             ENUMS
==================================================================================================*/

/*==================================================================================================
*                                STRUCTURES AND OTHER TYPEDEFS
==================================================================================================*/

/*==================================================================================================
*                                GLOBAL VARIABLE DECLARATIONS
==================================================================================================*/

/*==================================================================================================
*                                    FUNCTION PROTOTYPES
==================================================================================================*/


#ifdef __cplusplus
}
#endif

/** @} */

#endif /* LIN_43_LPUART_FLEXIO_DEFINES_H */
