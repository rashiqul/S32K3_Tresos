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

#ifndef LIN_43_LPUART_FLEXIO_IPW_CFG_H
#define LIN_43_LPUART_FLEXIO_IPW_CFG_H

/**
*   @file
*
*   @internal
*   @addtogroup LIN_IPW
*   @{
*/

#ifdef __cplusplus
extern "C"
{
#endif

/*==================================================================================================
*                                         INCLUDE FILES
* 1) system and project includes
* 2) needed interfaces from external units
* 3) internal and external interfaces from this unit
==================================================================================================*/

#include "Lin_43_LPUART_FLEXIO_Ipw_PBcfg.h"
#include "Lin_43_LPUART_FLEXIO_Ipw_Types.h"

/*==================================================================================================
*                              SOURCE FILE VERSION INFORMATION
==================================================================================================*/

#define LIN_43_LPUART_FLEXIO_IPW_CFG_VENDOR_ID                    43
#define LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MAJOR_VERSION     4
#define LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MINOR_VERSION     9
#define LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_REVISION_VERSION  0
#define LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MAJOR_VERSION             7
#define LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MINOR_VERSION             0
#define LIN_43_LPUART_FLEXIO_IPW_CFG_SW_PATCH_VERSION             1

/*==================================================================================================
*                                     FILE VERSION CHECKS
==================================================================================================*/
/* Checks against Lin_43_LPUART_FLEXIO_Ipw_PBcfg.h */
#if (LIN_43_LPUART_FLEXIO_IPW_CFG_VENDOR_ID != LIN_43_LPUART_FLEXIO_IPW_PBCFG_VENDOR_ID)
    #error "Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_PBcfg.h have different vendor ids"
#endif
#if ((LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MAJOR_VERSION    != LIN_43_LPUART_FLEXIO_IPW_PBCFG_AR_RELEASE_MAJOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MINOR_VERSION    != LIN_43_LPUART_FLEXIO_IPW_PBCFG_AR_RELEASE_MINOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_REVISION_VERSION != LIN_43_LPUART_FLEXIO_IPW_PBCFG_AR_RELEASE_REVISION_VERSION) \
    )
     #error "AUTOSAR Version Numbers of Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_PBcfg.h are different"
#endif
#if ((LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MAJOR_VERSION != LIN_43_LPUART_FLEXIO_IPW_PBCFG_SW_MAJOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MINOR_VERSION != LIN_43_LPUART_FLEXIO_IPW_PBCFG_SW_MINOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_SW_PATCH_VERSION != LIN_43_LPUART_FLEXIO_IPW_PBCFG_SW_PATCH_VERSION) \
    )
    #error "Software Version Numbers of Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_PBcfg.h are different"
#endif


/* Checks against Lin_43_LPUART_FLEXIO_Ipw_Types.h */
#if (LIN_43_LPUART_FLEXIO_IPW_CFG_VENDOR_ID != LIN_43_LPUART_FLEXIO_IPW_TYPES_VENDOR_ID)
    #error "Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_Types.h have different vendor ids"
#endif
#if ((LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MAJOR_VERSION    != LIN_43_LPUART_FLEXIO_IPW_TYPES_AR_RELEASE_MAJOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_MINOR_VERSION    != LIN_43_LPUART_FLEXIO_IPW_TYPES_AR_RELEASE_MINOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_AR_RELEASE_REVISION_VERSION != LIN_43_LPUART_FLEXIO_IPW_TYPES_AR_RELEASE_REVISION_VERSION) \
    )
     #error "AUTOSAR Version Numbers of Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_Types.h are different"
#endif
#if ((LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MAJOR_VERSION != LIN_43_LPUART_FLEXIO_IPW_TYPES_SW_MAJOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_SW_MINOR_VERSION != LIN_43_LPUART_FLEXIO_IPW_TYPES_SW_MINOR_VERSION) || \
     (LIN_43_LPUART_FLEXIO_IPW_CFG_SW_PATCH_VERSION != LIN_43_LPUART_FLEXIO_IPW_TYPES_SW_PATCH_VERSION) \
    )
    #error "Software Version Numbers of Lin_43_LPUART_FLEXIO_Ipw_Cfg.h and Lin_43_LPUART_FLEXIO_Ipw_Types.h are different"
#endif
/*==================================================================================================
*                                            CONSTANTS
==================================================================================================*/

/*==================================================================================================
*                                      DEFINES AND MACROS
==================================================================================================*/
#define LIN_43_LPUART_FLEXIO_IPW_CONFIG_EXT \
    LIN_43_LPUART_FLEXIO_IPW_CONFIG_PB
#if (LIN_43_LPUART_FLEXIO_WAKEUP_DETECTION == STD_ON)

/**
* @brief          None EcuMWakeUpSource was referrd when LinChannelWakeupSupport is disable
*/
#define LIN_43_LPUART_FLEXIO_NONE_ECUM_WAKEUP_SOURCE_REF     ((uint32)0UL)
#endif

/**
* @brief Macro which shows if at least one slave is present in the configuration
*/
#define LIN_43_LPUART_FLEXIO_IPW_DRIVER_HAS_SLAVE_NODE     (STD_OFF)


/*==================================================================================================
*                                             ENUMS
==================================================================================================*/

/*==================================================================================================
*                                STRUCTURES AND OTHER TYPEDEFS
==================================================================================================*/

/*==================================================================================================
*                                  GLOBAL VARIABLE DECLARATIONS
==================================================================================================*/

/*==================================================================================================
*                                       FUNCTION PROTOTYPES
==================================================================================================*/


#ifdef __cplusplus
}
#endif

/** @} */

#endif /* LIN_43_LPUART_FLEXIO_IPW_CFG_H */
