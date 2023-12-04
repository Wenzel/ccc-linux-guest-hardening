import os
import sys
import yaml
import json
import re
import copy
from pprint import pprint
from typing import Dict

with open('.github/campaign_harness.yml') as f:
    campaign_config = yaml.safe_load(f.read())

def set_harness_kernel_config(harness) -> Dict:
    # set default config
    harness['kernel_config'] = campaign_config['default_tdxfuzz_kafl_config']
    # update config based on harness type
    if harness['name'].startswith("BOOT_"):
        basename = harness['name'][len("BOOT_"):]
        harness['kernel_config'].update({f"CONFIG_TDX_FUZZ_HARNESS_{basename}": "y"})
    elif harness['name'].startswith("DOINITCALLS_LEVEL"):
        level = harness['name'][len("DOINITCALLS_LEVEL_"):]
        harness['kernel_config'].update({
            "CONFIG_TDX_FUZZ_HARNESS_DOINITCALLS": "y",
            "CONFIG_TDX_FUZZ_HARNESS_DOINITCALLS_LEVEL": level
        })
    elif harness['name'].startswith("BPH_"):
        harness['kernel_config'].update(campaign_config['default_bph_options'])
    elif harness['name'].startswith("US_"):
        harness['kernel_config'].update(campaign_config['default_us_options'])
        # set harness specific configs, if any
        harness['kernel_config'].update(campaign_config['harness_options'].get(harness['name'], {}))

    return harness

def set_kafl_config(harness) -> Dict:
    default_config = copy.deepcopy(campaign_config['default_kafl_config'])
    default_config.update(harness.get('kafl_config', {}))
    # TODO: default boot params KAFL_CONFIG_FILE
    # TODO: seed dir
    kernel_boot_params = harness.get('kernel_params', None)
    if kernel_boot_params:
        default_config['qemu_append'] = kernel_boot_params
    harness['kafl_config'] = default_config
    return harness

# filter harnesses and set their kernel_config
pattern = 'BPH'
filtered_harnesses = [h_config for h_config in campaign_config['harnesses'] if pattern in h_config['name']]
# set kernel_config
filtered_harnesses = [set_harness_kernel_config(h_config) for h_config in filtered_harnesses]
# set kafl config
filtered_harnesses = [set_kafl_config(h_config) for h_config in filtered_harnesses]

# write matrix in GITHUB_OUTPUT
with open(os.environ['GITHUB_OUTPUT'], 'a') as o:
    matrix_include = {
    'include': filtered_harnesses
    }
    o.write(f"matrix={json.dumps(matrix_include)}")
    pprint(matrix_include, indent=4)
