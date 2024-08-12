#!/bin/python


import argparse
from zabbix_config_file_processor import ConfigFile, YamlPath

class TemplateDuplicator:
    """
    Duplicate any template/sub_template/discovery_rules from a zabbix config file to a new area 
    or into another template.
    """

    def __init__(self, infile: str, outfile: str) -> None:
        self.zabbix_config_file = ConfigFile(infile, outfile)

    def duplicator(self, src_path: YamlPath, dst_path: YamlPath, **args):
        """ Do the duplicating of a zabbix template item into another location.
        """

        

        #Process item being copied, update UUID, update name...

        #Copy item into 



if __name__ == "__main__":
    parse = argparse("Duplicate a zabbix template item into another location. This can be inside \
                     the same parent template, or into another template")