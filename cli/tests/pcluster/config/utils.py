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

import os
import tempfile

import configparser
import pytest
from configparser import NoOptionError, NoSectionError

from assertpy import assert_that
from pcluster.config.mapping import ALIASES, AWS, CLUSTER, GLOBAL
from pcluster.config.param_types import Param
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.defaults import CFN_CONFIG_NUM_OF_PARAMS, DefaultDict


def get_param_map(section_map, param_key):
    param_map = section_map.get("params").get(param_key)
    return param_map, param_map.get("type", Param)


def merge_dicts(*args):
    """Merge multiple dictionaries into a new dictionary as a shallow copy."""
    merged_dict = {}
    for input_dict in args:
        merged_dict.update(input_dict)
    return merged_dict


def get_pcluster_config_example():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", "..", "..", "pcluster", "examples", "config")


def assert_param_from_file(section_map, param_key, param_value, expected_value, expected_message):
    section_label = section_map.get("label")
    section_name = "{0} {1}".format(section_map.get("key"), section_label)
    config_parser = configparser.ConfigParser()
    config_parser.add_section(section_name)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    if param_value:
        config_parser.set(section_name, param_key, param_value)

    param_map, param_type = get_param_map(section_map, param_key)

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            param_type(
                section_map.get("key"),
                section_label,
                param_key,
                param_map,
                pcluster_config,
                config_parser=config_parser,
            )
    else:
        param = param_type(
            section_map.get("key"), section_label, param_key, param_map, pcluster_config, config_parser=config_parser
        )
        assert_that(param.value, description="{0} assert fail".format(param.key)).is_equal_to(expected_value)


def assert_param_validator(config_parser_dict, expected_message):
    config_parser = configparser.ConfigParser()
    config_parser.read_dict(config_parser_dict)

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _ = init_pcluster_config_from_configparser(config_parser)
    else:
        _ = init_pcluster_config_from_configparser(config_parser)


def assert_section_from_cfn(section_map, cfn_params_dict, expected_section_dict):

    cfn_params = []
    for cfn_key, cfn_value in cfn_params_dict.items():
        cfn_params.append({"ParameterKey": cfn_key, "ParameterValue": cfn_value})

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    section = section_type(section_map, pcluster_config, cfn_params=cfn_params)

    if section.label:
        assert_that(section.label).is_equal_to("default")

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_section_dict, dict):
        expected_dict.update(expected_section_dict)

    section_dict = {}
    for param_key, param in section.params.items():
        section_dict.update({param_key: param.value})

    assert_that(section_dict).is_equal_to(expected_dict)


def assert_section_from_file(section_map, config_parser_dict, expected_dict_params, expected_message):
    config_parser = configparser.ConfigParser()
    config_parser.read_dict(config_parser_dict)

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_dict_params, dict):
        expected_dict.update(expected_dict_params)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _ = section_type(section_map, pcluster_config, config_parser=config_parser)
    else:
        section = section_type(section_map, pcluster_config, config_parser=config_parser)
        section_dict = {}
        for param_key, param in section.params.items():
            section_dict.update({param_key: param.value})

        assert_that(section_dict).is_equal_to(expected_dict)


def assert_section_to_file(section_map, section_dict, expected_config_parser_dict, expected_message):
    expected_config_parser = configparser.ConfigParser()
    expected_config_parser.read_dict(expected_config_parser_dict)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    output_config_parser = configparser.ConfigParser()
    section_type = section_map.get("type")
    section = section_type(section_map, pcluster_config, section_label="default")

    for param_key, param_value in section_dict.items():
        param_map, param_type = get_param_map(section.map, param_key)
        param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)
        param.value = param_value
        section.add_param(param)

    section.to_file(output_config_parser)

    for section_key, section_params in expected_config_parser_dict.items():
        for param_key, param_value in section_params.items():

            assert_that(output_config_parser.has_option(section_key, param_key))
            if expected_message is not None:
                if "No section" in expected_message:
                    with pytest.raises(NoSectionError, match=expected_message):
                        assert_that(output_config_parser.get(section_key, param_key)).is_equal_to(param_value)
                else:
                    with pytest.raises(NoOptionError, match=expected_message):
                        assert_that(output_config_parser.get(section_key, param_key)).is_equal_to(param_value)

            else:
                assert_that(output_config_parser.get(section_key, param_key)).is_equal_to(param_value)


def assert_section_to_cfn(section_map, section_dict, expected_cfn_params):

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    section = section_type(section_map, pcluster_config)
    for param_key, param_value in section_dict.items():
        param_map, param_type = get_param_map(section_map, param_key)
        param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)
        param.value = param_value
        section.add_param(param)
    pcluster_config.add_section(section)

    cfn_params = section.to_cfn()
    assert_that(cfn_params).is_equal_to(expected_cfn_params)


def assert_section_params(mocker, pcluster_config_reader, settings_label, expected_cfn_params):
    mocker.patch.object(PclusterConfig, "_PclusterConfig__validate")
    if isinstance(expected_cfn_params, SystemExit):
        with pytest.raises(SystemExit):
            _ = PclusterConfig(
                cluster_label="default",
                config_file=pcluster_config_reader(settings_label=settings_label),
                file_sections=[AWS, GLOBAL, CLUSTER],
                fail_on_file_absence=True,
            )
    else:
        pcluster_config = PclusterConfig(
            config_file=pcluster_config_reader(settings_label=settings_label),
            file_sections=[AWS, GLOBAL, CLUSTER],
            fail_on_file_absence=True,
        )

        pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="mocked_avail_zone")
        cfn_params = pcluster_config.to_cfn()

        assert_that(len(cfn_params)).is_equal_to(CFN_CONFIG_NUM_OF_PARAMS)

        for param_key, param_value in cfn_params.items():
            assert_that(cfn_params.get(param_key), description=param_key).is_equal_to(
                expected_cfn_params.get(param_key)
            )


def init_pcluster_config_from_configparser(config_parser):
    with tempfile.NamedTemporaryFile(delete=False) as config_file:

        with open(config_file.name, "w") as cf:
            config_parser.write(cf)

        pcluster_config = PclusterConfig(
            config_file=config_file.name,
            cluster_label="default",
            file_sections=[AWS, GLOBAL, CLUSTER, ALIASES],
            fail_on_file_absence=True,
        )
    return pcluster_config
