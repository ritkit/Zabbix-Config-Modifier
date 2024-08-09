#!/bin/python

"""

"""


class TemplateDuplicator:
    """
    Duplicate any template/sub_template/discovery_rules from a zabbix config file to a new area 
    or into another template.
    """

    def __init__(self, infile: str, outfile: str) -> None:
        self.zabbix_config_file = ConfigFile(infile, outfile)

    