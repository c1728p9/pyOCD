"""
 mbed CMSIS-DAP debugger
 Copyright (c) 2006-2015 ARM Limited

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

#from flash_cortex_m import Flash_cortex_m
#from flash_klxx import Flash_klxx
import flash_MKE15Z256xxx7
import flash_MKE18F512xxx16
import flash_MKL02Z32xxx4
import flash_MKL05Z32xxx4
import flash_MKL25Z128xxx4
import flash_MKL26Z128xxx4
import flash_MKL27Z64xxx4
import flash_MKL28Z512xxx7
import flash_MKL43Z256xxx4
import flash_MKL46Z256xxx4
import flash_MKV10Z32xxx7
import flash_MKV11Z128xxx7
import flash_MKW01Z128xxx4
import flash_MKW40Z160xxx4
import flash_MK20DX128xxx5
import flash_MK22FN512xxx12
import flash_MK64FN1M0xxx12
import flash_MK66FN2M0xxx18
import flash_MK82FN256xxx15
import flash_LPC11U35FHI33_501
import flash_LPC11U24FBD64_401
import flash_LPC1768
import flash_LPC4330
import flash_nRF51822_xxAA
import flash_nRF51822_xxAB
import flash_nRF51822_xxAC
import flash_nRF51422_xxAC
import flash_nRF52832_xxAA
import flash_STM32F103RC
import flash_STM32F051T8
#'maxwsnenv': flash_maxwsnenv,
#'max32600mbed': flash_max32600mbed,
#'w7500': flash_w7500,
import flash_LPC1114FN28_102
import flash_LPC824M201JHI33
import flash_LPC4088FBD144
#'ncs36510': flash_ncs36510,
#'lpc4088qsb': flash_lpc4088qsb_dm,
#'lpc4088dm': flash_lpc4088qsb_dm,


FLASH = {
        #'cortex_m': Flash_cortex_m,
        #'kinetis': Flash_cortex_m,
        'MKE15Z256xxx7': flash_MKE15Z256xxx7.flash_algo,
        'MKE18F512xxx16': flash_MKE18F512xxx16.flash_algo,
        'MKL02Z32xxx4': flash_MKL02Z32xxx4.flash_algo,
        'MKL05Z32xxx4': flash_MKL05Z32xxx4.flash_algo,
        'MKL25Z128xxx4': flash_MKL25Z128xxx4.flash_algo,
        'MKL26Z128xxx4': flash_MKL26Z128xxx4.flash_algo,
        'MKL27Z64xxx4': flash_MKL27Z64xxx4.flash_algo,
        'MKL28Z512xxx7': flash_MKL28Z512xxx7.flash_algo,
        'MKL43Z256xxx4': flash_MKL43Z256xxx4.flash_algo,
        'MKL46Z256xxx4': flash_MKL46Z256xxx4.flash_algo,
        'MKV10Z32xxx7': flash_MKV10Z32xxx7.flash_algo,
        'MKV11Z128xxx7': flash_MKV11Z128xxx7.flash_algo,
        'MKW01Z128xxx4': flash_MKW01Z128xxx4.flash_algo,
        'MKW40Z160xxx4': flash_MKW40Z160xxx4.flash_algo,
        'MK20DX128xxx5': flash_MK20DX128xxx5.flash_algo,
        'MK22FN512xxx12': flash_MK22FN512xxx12.flash_algo,
        'MK64FN1M0xxx12': flash_MK64FN1M0xxx12.flash_algo,
        'MK66FN2M0xxx18': flash_MK66FN2M0xxx18.flash_algo,
        'MK82FN256xxx15': flash_MK82FN256xxx15.flash_algo,
        'LPC11U35FHI33/501': flash_LPC11U35FHI33_501.flash_algo,
        'LPC11U24FBD64/401': flash_LPC11U24FBD64_401.flash_algo,
        'LPC1768': flash_LPC1768.flash_algo,
        'LPC4330': flash_LPC4330.flash_algo,
        'nRF51822_xxAA': flash_nRF51822_xxAA.flash_algo,
        'nRF51822_xxAB': flash_nRF51822_xxAB.flash_algo,
        'nRF51822_xxAC': flash_nRF51822_xxAC.flash_algo,
        'nRF51422_xxAC': flash_nRF51422_xxAC.flash_algo,
        'flash_nRF52832_xxAA': flash_nRF52832_xxAA.flash_algo,
        'STM32F103RC': flash_STM32F103RC.flash_algo,
        'STM32F051T8': flash_STM32F051T8.flash_algo,
        #'maxwsnenv': flash_maxwsnenv,
        #'max32600mbed': flash_max32600mbed,
        #'w7500': flash_w7500,
        'LPC1114FN28/102': flash_LPC1114FN28_102.flash_algo,
        'LPC824M201JHI33': flash_LPC824M201JHI33.flash_algo,
        'LPC4088FBD144': flash_LPC4088FBD144.flash_algo,
        #'ncs36510': flash_ncs36510,
        #'lpc4088qsb': flash_lpc4088qsb_dm,
        #'lpc4088dm': flash_lpc4088qsb_dm,
         }
