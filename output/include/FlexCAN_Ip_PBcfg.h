/*==================================================================================================
*   Project              : RTD AUTOSAR 4.9
*   Platform             : CORTEXM
*   Peripheral           : FLEXCAN
*   Dependencies         :
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

#ifndef FLEXCAN_IP_PBCFG_H
#define FLEXCAN_IP_PBCFG_H

/**
*   @file FlexCAN_Ip_PBcfg.h
*
*   @brief    Configuration file for FlexCAN Ip
*   @details  Contains configuration definitions and structures for FlexCAN Ip
*
*   @addtogroup FlexCAN
*   @{
*/


#ifdef __cplusplus
extern "C"{
#endif

/*==================================================================================================
*                                        INCLUDE FILES
* 1) system and project includes
* 2) needed interfaces from external units
* 3) internal and external interfaces from this unit
==================================================================================================*/
/*==================================================================================================
*                              SOURCE FILE VERSION INFORMATION
==================================================================================================*/
#define FLEXCAN_IP_VENDOR_ID_PBCFG_H                     43
#define FLEXCAN_IP_AR_RELEASE_MAJOR_VERSION_PBCFG_H      4
#define FLEXCAN_IP_AR_RELEASE_MINOR_VERSION_PBCFG_H      9
#define FLEXCAN_IP_AR_RELEASE_REVISION_VERSION_PBCFG_H   0
#define FLEXCAN_IP_SW_MAJOR_VERSION_PBCFG_H              7
#define FLEXCAN_IP_SW_MINOR_VERSION_PBCFG_H              0
#define FLEXCAN_IP_SW_PATCH_VERSION_PBCFG_H              1
/*==================================================================================================
*                                     FILE VERSION CHECKS
==================================================================================================*/

/*==================================================================================================
*                                          CONSTANTS
==================================================================================================*/

/*==================================================================================================
*                                      DEFINES AND MACROS
==================================================================================================*/
#define FLEXCAN_IP_PB_CFG  \
    extern const Flexcan_Ip_ConfigType Flexcan_aCtrlConfigPB[1U];

#ifdef __cplusplus
}
#endif /* __cplusplus */

/** @} */

#endif /* FLEXCAN_IP_PBCFG_H */
