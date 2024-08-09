#!/bin/python

"""Utilizes a alternative version of PyYAML, called ruamel.yaml"""
import argparse
import re
from io import StringIO
from ruamel.yaml import YAML

# Create the YAML loader/dumper for use in the class.
yaml = YAML(pure=True)
# These set the various variables in ruamel, to closely duplicate format zabbix follows.
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True
yaml.allow_unicode=True
yaml.default_flow_style=False
yaml.preserve_quotes = True
yaml.sort_keys=False
yaml.allow_unicode=True
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.width = 4096
yaml.compact(seq_map=2)

class YamlPath(list):
    """
    Object to store a yaml path formatted as expected with helpers to convert text to path.
    """

    def __init__(self, *args: any, **kw: any) -> None:

        if len(args) == 1 and isinstance(args[0], str):

            args[0].removeprefix("[")
            args[0].removesuffix("]")
            super().__init__([x for x in YamlPath.text_to_yamlpath(args[0])])

        else:
            super().__init__(self, *args, **kw)

    def __repr__(self) -> str:
        return "["+".".join([repr(x) for x in self])+"]"

    def __str__(self) -> str:
        return ".".join([str(x) for x in self])

    @staticmethod
    def valid(path: any) -> bool:
        """
        Check to see if the yaml_path passed to it is valid.
        """
        invalid_chars = "#>-<$"

        if isinstance(path, str):
            for letter in path:
                if not (letter.isalnum() or letter not in invalid_chars):
                    return False

        elif isinstance(path, list):
            for item in path:
                if not isinstance(item, (int,str)):
                    return False

                if isinstance(item, str):
                    for letter in item:
                        if not (letter.isalnum() or letter not in invalid_chars):
                            return False

        elif not isinstance(path, (str, list)):
            return False

        return True

    @staticmethod
    def text_to_yamlpath(yaml_path_as_text: str) -> 'YamlPath':
        """
        Convert provided path string to a usable path object.
        Makes path items that are exclusively numeric into integers for referencing lists.
        """

        if not YamlPath.valid(yaml_path_as_text):
            raise ValueError("Not a valid yaml path")

        temp_list = yaml_path_as_text.split(".")

        new_yamlpath = YamlPath()

        for item in temp_list:
            if item.isnumeric():
                new_yamlpath.append(int(item))

            else:
                new_yamlpath.append(item)

        return new_yamlpath

class ConfigFile:
    """
    This class manages reading, and writing the a Zabbix YAML Config File. 
    All other classes can inherit it and the config stream created may be modified as needed.
    """
    def __init__(self, infile: str, outfile: str = None) -> None:
        self.__readfile = infile
        if outfile is None:
            self.__writefile = infile
        else:
            self.__writefile = outfile

        self._config_stream = self.__read()

    def __str__(self) -> str:
        return self.return_formattted_stream()

    def stream_at_path(self, path: YamlPath) -> any:
        target_stream = self._config_stream
        for path_item in path:
            target_stream = target_stream[path_item]

        return target_stream

    def return_formattted_stream(self) -> str:
        """
        Print the Config YAML string with the YAML Format to CLI
        """
        with StringIO() as string_stream:
            yaml.dump(self._config_stream, string_stream)
            output_str = string_stream.getvalue()

        return output_str

    def __read(self) -> any:
        """
        Read the zabbix config exported.
        """
        with open(self.__readfile, "r", encoding="utf-8") as infile:
            stream = yaml.load(infile)

        return stream

    def write(self) -> None:
        """
        Write the zabbix config with YAML.
        """
        with open(self.__writefile, "w", encoding="utf-8") as outfile:
            yaml.dump(self._config_stream, outfile)

    def update_item(self, path: YamlPath, new_value: any) -> None:
        """
        Update value at specific path.
        """
        target_stream = self._config_stream
        for item in path[:-1]:
            target_stream = target_stream[item]

        target_stream[path[-1]] = new_value

    def find_path(self, stream = None, current_path = YamlPath(), search_key: str = None,
                  search_value: str = None) -> list[YamlPath]:
        """
        Will return a list of all YAML paths to a specified key, tag, or value at or 
        below a certain path.
        
        All search values support regex matching.

        Optional_arguments:
        stream - provide a shortened stream or stream to continue search
        current_path - the path to get to where the stream is provided
        """

        if stream is None:
            stream = self._config_stream

        path_list = []

        if isinstance(stream, dict):
            for key, value in stream.items():
                path = current_path.copy()
                path.append(key)

                if (search_key is None or re.match(search_key, key) is not None ) \
                and (search_value is None or re.match(search_value, value) is not None):
                    path_list.append(path)

                if isinstance(value, (dict,list)):
                    path_list.extend(self.find_path(stream=value, current_path=path, \
                                                search_key=search_key, \
                                                search_value=search_value))

        elif isinstance(stream, list):

            for i, value in enumerate(stream):
                path = current_path.copy()
                path.append(i)

                if (search_key is None or re.match(search_key, str(i)) is not None) \
                and (search_value is None or re.match(search_value, value) is not None):
                    path_list.append(path)

                if isinstance(value, (dict,list)):
                    path_list.extend(self.find_path(stream=value, current_path=path, \
                                                search_key=search_key, \
                                                search_value=search_value))

        return path_list

class ZabbixConfigWorker:
    """
    The interactive CLI portion of the zabbix config modifier
    """
    def __init__(self, parser: argparse) -> None:

        self.zabconfig = None

        parser.add_argument('infile', type=str,
                    help='Input Filename for Zabbix YAML Template file')

        self.__subparsers = parser.add_subparsers(title='Subcommands', description="Various \
                                            functions of the zabbix config modifier",
                                            required=True)

        self.__find_parser()
        self.__update_item_parser()

        self.__args = parser.parse_args()
        self.__args.func()

    def __find_parser(self) -> None:
        find_parser = self.__subparsers.add_parser('find',
                        aliases=['f'], description="Find a path with supplied args any flags can \
                        be added in combination with each other. \nIf multiple args provided, \
                        search will be an \"AND\" of all terms ")
        find_parser.set_defaults(func=self.__find)
        find_parser.add_argument('-k', '--key', dest='key', nargs='?', help="Match with regex")
        #find_parser.add_argument('-t', '--tag', dest='tag', nargs=1)
        find_parser.add_argument('-v', '--value', dest='value', nargs='?', help="Match with regex")

        find_parser.add_argument('outfile', nargs='?', type=str, help="Output list of paths to \
                                 file, instead of stdout")

    def __find(self) -> None:

        self.zabconfig = ConfigFile(infile=self.__args.infile)

        path_list = self.zabconfig.find_path(search_key=self.__args.key, \
                                            search_value=self.__args.value)

        if self.__args.outfile is not None:
            with open(self.__args.outfile, 'w', encoding='utf-8') as file:
                for path in path_list:

                    file.write(f"{path}\n")

        else:
            print(path_list)

    def __update_item_parser(self) -> None:
        update_item_sp = self.__subparsers.add_parser('update',
                                aliases=['u'], description="Update the value at the specified \
                                path location")

        update_item_sp.set_defaults(func=self.__update)
        update_item_sp.add_argument('-p', '--path', dest='path', help='<yaml.path.style>')
        update_item_sp.add_argument('-v', '--value', dest='value')

        update_item_sp.add_argument('outfile', nargs='?', type=str, help="Output new zabbix config \
                                    with changes.")

    def __update(self) -> None:
        self.zabconfig = ConfigFile(infile=self.__args.infile, outfile=self.__args.outfile)
        ypath = YamlPath(self.__args.path)

        self.zabconfig.update_item(ypath, self.__args.value)
        self.zabconfig.write()

if __name__ == "__main__":
    parse = argparse.ArgumentParser(description='Accomplish various tasks including updating a \
                                    specific key, find a yaml path, or grab a specific section \
                                    of config.')

    worker = ZabbixConfigWorker(parse)
