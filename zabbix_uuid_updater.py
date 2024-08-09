#!/bin/python

"""
Modules Utilized
    UUID - to generate UUIDv4 to match zabix UUID usage
    argparse - to easily create a cli entry
    zabbixconfigmodifier - utilize the 
"""
from uuid import uuid4 as uuid
import argparse
from zabbix_config_file_processor import ConfigFile

class ZabbixUUIDUpdater:
    """
    Modify the UUIDs based on a few options.
    
    Default behavior is only to add UUIDs to UUIDs that are missing.

    Options:
    Update - Updates the UUIDs both in blank UUIDs and already existing UUIDs
    Clear - Deletes all UUIDs and sets them to be "blank".
    """
    def __init__(self, infile: str, outfile: str = None) -> None:
        self.zabbix_config_file = ConfigFile(infile, outfile)

    @staticmethod
    def _uuid_generator() -> str:
        new_uuid = str(uuid())
        return "".join([x for x in new_uuid if x != '-'])

    def update_uuid(self, update: bool = False, clear: bool = False):
        all_uuid_paths = self.zabbix_config_file.find_path(search_key="^uuid$")

        if update is True:
            for path_item in all_uuid_paths:
                self.zabbix_config_file.update_item(path_item, self._uuid_generator())

        elif clear is True:
            for path_item in all_uuid_paths:
                self.zabbix_config_file.update_item(path_item, None)

        else:
            for path_item in all_uuid_paths:
                path_value = self.zabbix_config_file.stream_at_path(path_item)
                if(path_value is None or path_value == ''):
                    self.zabbix_config_file.update_item(path_item, self._uuid_generator())

        self.zabbix_config_file.write()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Zabbix Template UUID Generator',
                                     description='Replace all UUIDs inside a \
                                     Zabbix Template with new random ones')
    parser.add_argument('inFile', type=str,
                        help='Input Filename for Zabbix YAML Template file')
    parser.add_argument('outFile', type=str, default=None,
                        help='Output Filename if a copy with the changes should be made')

    args_excludegroup = parser.add_mutually_exclusive_group()
    args_excludegroup.add_argument('-U', '--update', action='store_true', dest="update_uuids",
                                   help="Generate new UUIDs over existing ones")
    args_excludegroup.add_argument('-c', '--clear', action='store_true', dest="clear_uuids",
                                   help="Delete all existing UUIDs and replace with \
                                   ''")

    args = parser.parse_args()

    zabtemplate = ZabbixUUIDUpdater(args.inFile, args.outFile)
    zabtemplate.update_uuid(args.update_uuids, args.clear_uuids)
