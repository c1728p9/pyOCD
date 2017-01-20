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

from .coresight_target import CoreSightTarget
import target_kinetis
import target_ke15z7
import target_ke18f16
import target_kl02z
import target_kl05z
import target_kl25z
import target_kl26z
import target_kl27z4
import target_kl28z
import target_kl43z4
import target_kl46z
import target_kv10z7
import target_kv11z7
import target_kw01z4
import target_kw40z4
import target_k22f
import target_k64f
import target_k66f18
import target_k82f25615
import target_k20d50m
import target_lpc800
import target_lpc11u24
import target_lpc1768
import target_lpc4330
import target_nRF51822_xxAA
import target_nRF51822_xxAB
import target_nRF51822_xxAC
import target_nRF51422_xxAC
import target_nrf52
import target_stm32f103rc
import target_stm32f051
import target_maxwsnenv
import target_max32600mbed
import target_w7500
import target_lpc11xx_32
import target_lpc824
import target_ncs36510
import semihost
import target_lpc4088
import target_lpc4088qsb
import target_lpc4088dm

TARGET = {
          #'cortex_m': CoreSightTarget,
          #'kinetis': target_kinetis.Kinetis,
          'MKE15Z256xxx7': target_ke15z7.KE15Z7,
          'MKE18F512xxx16': target_ke18f16.KE18F16,
          'MKL02Z32xxx4': target_kl02z.KL02Z,
          'MKL05Z32xxx4': target_kl05z.KL05Z,
          'MKL25Z128xxx4': target_kl25z.KL25Z,
          'MKL26Z128xxx4': target_kl26z.KL26Z,
          'MKL27Z64xxx4': target_kl27z4.KL27Z4,
          'MKL28Z512xxx7': target_kl28z.KL28x,
          'MKL43Z256xxx4': target_kl43z4.KL43Z4,
          'MKL46Z256xxx4': target_kl46z.KL46Z,
          'MKV10Z32xxx7': target_kv10z7.KV10Z7,
          'MKV11Z128xxx7': target_kv11z7.KV11Z7,
          'MKW01Z128xxx4': target_kw01z4.KW01Z4,
          'MKW40Z160xxx4': target_kw40z4.KW40Z4,
          'MK20DX128xxx5': target_k20d50m.K20D50M,
          'MK22FN512xxx12': target_k22f.K22F,
          'MK64FN1M0xxx12': target_k64f.K64F,
          'MK66FN2M0xxx18': target_k66f18.K66F18,
          'MK82FN256xxx15': target_k82f25615.K82F25615,
          'LPC11U35FHI33/501': target_lpc800.LPC800,
          'LPC11U24FBD64/401': target_lpc11u24.LPC11U24,
          'LPC1768': target_lpc1768.LPC1768,
          'LPC4330': target_lpc4330.LPC4330,
          'nRF51822_xxAA': target_nRF51822_xxAA.nRF51822_xxAA,
          'nRF51822_xxAB': target_nRF51822_xxAB.nRF51822_xxAB,
          'nRF51822_xxAC': target_nRF51822_xxAC.nRF51822_xxAC,
          'nRF51422_xxAC': target_nRF51422_xxAC.nRF51422_xxAC,
          'nRF52832_xxAA' : target_nrf52.NRF52,
          'STM32F103RC': target_stm32f103rc.STM32F103RC,
          'STM32F051T8': target_stm32f051.STM32F051,
          #'maxwsnenv': target_maxwsnenv.MAXWSNENV,
          #'max32600mbed': target_max32600mbed.MAX32600MBED,
          #'w7500': target_w7500.W7500,
          'LPC1114FN28/102': target_lpc11xx_32.LPC11XX_32,
          'LPC824M201JHI33': target_lpc824.LPC824,
          'LPC4088FBD144': target_lpc4088.LPC4088,
          #'ncs36510': target_ncs36510.NCS36510,
          #'lpc4088qsb': target_lpc4088qsb.LPC4088qsb,
          #'lpc4088dm': target_lpc4088dm.LPC4088dm,
         }
