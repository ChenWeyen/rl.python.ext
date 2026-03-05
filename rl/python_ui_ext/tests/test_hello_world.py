# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.test
import omni.kit.ui_test as ui_test

import rl.python_ui_ext


class Test(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_hello_public_function(self):
        result = rl.python_ui_ext.some_public_function(4)
        self.assertEqual(result, 256)

    async def test_udp_ui_defaults(self):
        status_label = ui_test.find("RL Python UI Extension//Frame/**/Label[*].text=='UDP listener stopped'")
        count_label = ui_test.find("RL Python UI Extension//Frame/**/Label[*].text=='UDP packets received: 0'")
        reset_button = ui_test.find("RL Python UI Extension//Frame/**/Button[*].text=='Reset'")

        self.assertIsNotNone(status_label)
        self.assertIsNotNone(count_label)
        self.assertIsNotNone(reset_button)
