/*==================================================================================================
*   Project              : RTD AUTOSAR 4.9
*   Platform             : CORTEXM
*   Peripheral           :
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

#ifndef MPU_M7_IP_CFG_H_
#define MPU_M7_IP_CFG_H_

/**
*   @file Mpu_M7_Ip_Cfg.h
*
*   @addtogroup Mpu_M7_Ip Mpu M7 IPV Driver
*   @{
*/

#ifdef __cplusplus
extern "C"{
#endif
/*==================================================================================================
                                         INCLUDE FILES
==================================================================================================*/
#include "Mpu_M7_Ip_Types.h"
#include "Mpu_M7_Ip_Cfg_Defines.h"




/*==================================================================================================
*                              SOURCE FILE VERSION INFORMATION
==================================================================================================*/
#define CDD_PLATFORM_MPU_M7_IP_CFG_VENDOR_ID                    43
#define CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MAJOR_VERSION     4
#define CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MINOR_VERSION     9
#define CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_REVISION_VERSION  0
#define CDD_PLATFORM_MPU_M7_IP_CFG_SW_MAJOR_VERSION             7
#define CDD_PLATFORM_MPU_M7_IP_CFG_SW_MINOR_VERSION             0
#define CDD_PLATFORM_MPU_M7_IP_CFG_SW_PATCH_VERSION             1

/*==================================================================================================
                                      FILE VERSION CHECKS
==================================================================================================*/
/* Checks against Mpu_M7_Ip_Types.h */
#if (CDD_PLATFORM_MPU_M7_IP_CFG_VENDOR_ID != CDD_PLATFORM_MPU_M7_IP_TYPES_VENDOR_ID)
    #error "Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Types.h have different vendor ids"
#endif
#if (( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MAJOR_VERSION    != CDD_PLATFORM_MPU_M7_IP_TYPES_AR_RELEASE_MAJOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MINOR_VERSION    != CDD_PLATFORM_MPU_M7_IP_TYPES_AR_RELEASE_MINOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_REVISION_VERSION != CDD_PLATFORM_MPU_M7_IP_TYPES_AR_RELEASE_REVISION_VERSION))
     #error "AUTOSAR Version Numbers of Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Types.h are different"
#endif
#if (( CDD_PLATFORM_MPU_M7_IP_CFG_SW_MAJOR_VERSION != CDD_PLATFORM_MPU_M7_IP_TYPES_SW_MAJOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_SW_MINOR_VERSION != CDD_PLATFORM_MPU_M7_IP_TYPES_SW_MINOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_SW_PATCH_VERSION != CDD_PLATFORM_MPU_M7_IP_TYPES_SW_PATCH_VERSION))
    #error "Software Version Numbers of Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Types.h are different"
#endif

/* Checks against Mpu_M7_Ip_Cfg_Defines.h */
#if (CDD_PLATFORM_MPU_M7_IP_CFG_VENDOR_ID != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_VENDOR_ID)
    #error "Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Cfg_Defines.h have different vendor ids"
#endif
#if (( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MAJOR_VERSION    != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_AR_RELEASE_MAJOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_MINOR_VERSION    != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_AR_RELEASE_MINOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_AR_RELEASE_REVISION_VERSION != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_AR_RELEASE_REVISION_VERSION))
     #error "AUTOSAR Version Numbers of Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Cfg_Defines.h are different"
#endif
#if (( CDD_PLATFORM_MPU_M7_IP_CFG_SW_MAJOR_VERSION != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_SW_MAJOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_SW_MINOR_VERSION != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_SW_MINOR_VERSION) || \
     ( CDD_PLATFORM_MPU_M7_IP_CFG_SW_PATCH_VERSION != CDD_PLATFORM_MPU_M7_IP_CFG_DEFINES_SW_PATCH_VERSION))
    #error "Software Version Numbers of Mpu_M7_Ip_Cfg.h and Mpu_M7_Ip_Cfg_Defines.h are different"
#endif

/*==================================================================================================
                                       GLOBAL VARIABLES
==================================================================================================*/


#ifdef __cplusplus
}
#endif

/** @} */

#endif /* MPU_M7_IP_CFG_H_ */
