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


/**
*   @file   Lpuart_Lin_Ip_PBcfg.c
*   @implements Lpuart_Lin_Ip_PBcfg.c_Artifact
*
*   @addtogroup LPUART_LIN
*   @{
*/

#ifdef __cplusplus
extern "C"{
#endif

/*==================================================================================================
*                                          INCLUDE FILES
* 1) system and project includes
* 2) needed interfaces from external units
* 3) internal and external interfaces from this unit
==================================================================================================*/

#include "Lpuart_Lin_Ip_Cfg.h"
#if (LPUART_LIN_IP_HAS_DMA_ENABLED == STD_ON)
#include "Dma_Ip.h"
#endif
/*==================================================================================================
*                                 SOURCE FILE VERSION INFORMATION
==================================================================================================*/

#define LPUART_LIN_IP_PBCFG_VENDOR_ID_C                     43
#define LPUART_LIN_IP_PBCFG_AR_RELEASE_MAJOR_VERSION_C      4
#define LPUART_LIN_IP_PBCFG_AR_RELEASE_MINOR_VERSION_C      9
#define LPUART_LIN_IP_PBCFG_AR_RELEASE_REVISION_VERSION_C   0
#define LPUART_LIN_IP_PBCFG_SW_MAJOR_VERSION_C              7
#define LPUART_LIN_IP_PBCFG_SW_MINOR_VERSION_C              0
#define LPUART_LIN_IP_PBCFG_SW_PATCH_VERSION_C              1

/*==================================================================================================
*                                       FILE VERSION CHECKS
==================================================================================================*/

/* Checks against Lpuart_Lin_Ip_Cfg.h */
#if (LPUART_LIN_IP_PBCFG_VENDOR_ID_C != LPUART_LIN_IP_CFG_VENDOR_ID)
    #error "Lpuart_Lin_Ip_PBcfg.c and Lpuart_Lin_Ip_Cfg.h have different vendor ids"
#endif
/* Check if current file and Lpuart_Lin_Ip_Cfg header file are of the same Autosar version */
#if ((LPUART_LIN_IP_PBCFG_AR_RELEASE_MAJOR_VERSION_C    != LPUART_LIN_IP_CFG_AR_RELEASE_MAJOR_VERSION) || \
     (LPUART_LIN_IP_PBCFG_AR_RELEASE_MINOR_VERSION_C    != LPUART_LIN_IP_CFG_AR_RELEASE_MINOR_VERSION) || \
     (LPUART_LIN_IP_PBCFG_AR_RELEASE_REVISION_VERSION_C != LPUART_LIN_IP_CFG_AR_RELEASE_REVISION_VERSION) \
    )
    #error "AutoSar Version Numbers of Lpuart_Lin_Ip_PBcfg.c and Lpuart_Lin_Ip_Cfg.h are different"
#endif
/* Check if current file and Lpuart_Lin_Ip_Cfg header file are of the same Software version */
#if ((LPUART_LIN_IP_PBCFG_SW_MAJOR_VERSION_C != LPUART_LIN_IP_CFG_SW_MAJOR_VERSION) || \
     (LPUART_LIN_IP_PBCFG_SW_MINOR_VERSION_C != LPUART_LIN_IP_CFG_SW_MINOR_VERSION) || \
     (LPUART_LIN_IP_PBCFG_SW_PATCH_VERSION_C != LPUART_LIN_IP_CFG_SW_PATCH_VERSION) \
    )
    #error "Software Version Numbers of Lpuart_Lin_Ip_PBcfg.c and Lpuart_Lin_Ip_Cfg.h are different"
#endif
#ifndef DISABLE_MCAL_INTERMODULE_ASR_CHECK
    /* Checks against Dma_Ip.h */
    #if (LPUART_LIN_IP_HAS_DMA_ENABLED == STD_ON)
        #if ((LPUART_LIN_IP_PBCFG_AR_RELEASE_MAJOR_VERSION_C != DMA_IP_AR_RELEASE_MAJOR_VERSION) || \
             (LPUART_LIN_IP_PBCFG_AR_RELEASE_MINOR_VERSION_C != DMA_IP_AR_RELEASE_MINOR_VERSION) \
            )
            #error "AutoSar Version Numbers of Lpuart_Lin_Ip_PBcfg.c and Dma_Ip.h are different"
        #endif
    #endif
#endif
/*==================================================================================================
*                                 GLOBAL FUNCTIONS DECLARATIONS
==================================================================================================*/

/*==================================================================================================
*                           LOCAL TYPEDEFS (STRUCTURES, UNIONS, ENUMS)
==================================================================================================*/

/*==================================================================================================
*                                          LOCAL MACROS
==================================================================================================*/

/*==================================================================================================
*                                         LOCAL CONSTANTS
==================================================================================================*/

/*==================================================================================================
*                                         LOCAL VARIABLES
==================================================================================================*/

/*==================================================================================================
*                                        GLOBAL CONSTANTS
==================================================================================================*/

/*==================================================================================================
*                                        GLOBAL VARIABLES
==================================================================================================*/



#define LIN_43_LPUART_FLEXIO_START_SEC_CONFIG_DATA_UNSPECIFIED
#include "Lin_43_LPUART_FLEXIO_MemMap.h"


/**
* @brief          Hardware configuration for Lin Hardware Instance LPUART_IP_9 - Configuration:
*
*
*/
const Lpuart_Lin_Ip_UserConfigType Lpuart_Lin_Ip_pxHwConfigPB_0 =
{

    9U, /*!< Hardware instance */

    0xA2U, /*!< Baudrate divisor */

    16U, /*!< Baudrate OSR */

    (boolean)LPUART_LIN_IP_MASTER, /*!< Master node */

    LPUART_LIN_IP_USING_INTERRUPTS,
#if (LPUART_LIN_IP_HAS_DMA_ENABLED == STD_ON)
    /* DMA channel number for DMA-based rx. */
    255,
#endif

    LPUART_LIN_IP_BREAK_CHAR_13_BIT_MINIMUM_U8, /*!< Break character length is transmitted */

    (uint8)1U,    /*!< Detect break character at 11 bits */
#if (LPUART_LIN_IP_AUTO_BAUD == STD_ON)
    (boolean)FALSE, /*!<  Autobaudrate feature */
#endif
    (Lpuart_Lin_Ip_CallbackType)&Lin_43_LPUART_FLEXIO_Ipw_Callback, /*!< Callback function to invoke after receiving a byte or transmitting a byte. */

    &Lpuart_Lin_Ip_axStateStructure[0U], /*!< Runtime state structure referrence */
#if (LPUART_LIN_IP_FRAME_TIMEOUT_DISABLE == STD_OFF)
#ifdef LPUART_LIN_IP_START_TIMER_NOTIFICATION
    2292U,           /*!< HeaderTimeoutValue in microseconds */

    730U,         /*!< ResponseTimeoutValue in microseconds for 1 byte */
#endif
#endif /* (LPUART_LIN_IP_START_TIMER_NOTIFICATION == STD_OFF) */
    (uint8)0x80, /*!< Wakeup byte */

    50000000U            /*!< Channel clock */
};


#define LIN_43_LPUART_FLEXIO_STOP_SEC_CONFIG_DATA_UNSPECIFIED
#include "Lin_43_LPUART_FLEXIO_MemMap.h"

/*==================================================================================================
*                                    LOCAL FUNCTION PROTOTYPES
==================================================================================================*/

/*==================================================================================================
*                                         LOCAL FUNCTIONS
==================================================================================================*/

/*==================================================================================================
*                                        GLOBAL FUNCTIONS
==================================================================================================*/

#ifdef __cplusplus
}
#endif

/** @} */
