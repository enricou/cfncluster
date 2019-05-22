# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.
import pytest

from pcluster.config.mapping import CLUSTER, EBS, EFS, FSX, SCALING, RAID, VPC
from tests.pcluster_config.utils import get_param_map
from tests.pcluster_config.defaults import DefaultDict


@pytest.mark.parametrize(
    "section_map, param_key, param_value, expected_message",
    [
        (VPC, "vpc_id", "wrong_value", ".* has an invalid value .*"),
        (VPC, "master_subnet_id", "wrong_value", ".* has an invalid value .*"),
        (VPC, "ssh_from", "wrong_value", None),
        (VPC, "additional_sg", "wrong_value", ".* has an invalid value .*"),
        (VPC, "compute_subnet_id", "wrong_value", ".* has an invalid value .*"),
        (VPC, "compute_subnet_cidr", "wrong_value", None),
        (VPC, "use_public_ips", "wrong_value", None),
        (VPC, "vpc_security_group_id", "wrong_value", ".* has an invalid value .*"),
    ]
)
def test_param_validator(section_map, param_key, param_value, expected_message):
    param_map, param_type = get_param_map(section_map, param_key)
    default_dict = DefaultDict[section_map.get("key")].value

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            param_type(param_key, param_map).validate(param_value, default_dict, DefaultDict["pcluster"].value)
    else:
        param_type(param_key, param_map).validate(param_value, default_dict, DefaultDict["pcluster"].value)
