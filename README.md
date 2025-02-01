![Python Version](https://img.shields.io/badge/python-3.10%2B-green)

# Network Configuration XML Parser

This tool is parsing network devices configurations stored in the XML format.

# Installation and Usage

## On the host system

Code in the repo could be run directly on the system (with virtual environment or not).
Installation is standard. Use pip to install dependencies from file:

`pip install -r requirements.txt`

And use uvicorn to process API calls, for example:

`uvicorn main:xml_parser_app --port 58000 --reload`

Tool will try to look for configs in the relative directory **/configurations**.

## As a container

Another way is - to run the tool as a Docker container.

To build an image from the Dockerfile:

`docker build -t xml-parser-api .`

To start an application:

`docker run -d --mount type=bind,source=/absolute_path_to_the/directory_with_configuration_files,target=/xml_parser_app/configurations,readonly --name xml_parser_api -p 58000:58000 xml-parser-api`

In the **source=** portion, there should be a directory where configuration files are stored.

# Incoming data structure

It is expected to receive API calls in the following format:

1. **device_list** - the list of configuration files names as strings.
2. **xpath** - the list of XPath elements in a hierarchy. With mandatory attribute **name** and optional **filters**.
Filters - are the list of elements with **filter_path** and **regexp** in their structure.

For example:

    {'device_list': ['r2.xml', 'r1.xml'],
     'xpath': [{'name': 'card'},
               {'name': 'mda',
                    'filters': [
                                {'filter_path': 'mda-slot', 'regexp': ''},
                                {'filter_path': 'mda-type', 'regexp': '10g'}
                    ]
                }
            ]
        }


Note: Tested only on a NOKIA XML configurations.