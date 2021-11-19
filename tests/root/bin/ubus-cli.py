#!/usr/bin/env python3

from argparse import ArgumentParser
import json

DHCP_DATA="""{
    "device": {
        "br-lan": {
            "leases": [
                {
                    "duid": "0001000126f109de283926dcaa43",
                    "iaid": 86522150,
                    "hostname": "DESKTOP-67NOH93",
                    "accept-reconf": false,
                    "assigned": 3267,
                    "flags": [
                        "bound"
                    ],
                    "ipv6-addr": [
                        {
                            "address": "79f7:88ad:823c:9cf::cc3",
                            "preferred-lifetime": 230199,
                            "valid-lifetime": 256119
                        }
                    ],
                    "valid": 43082
                },
                {
                    "duid": "0003000104f021241989",
                    "iaid": 1,
                    "hostname": "turris",
                    "accept-reconf": true,
                    "assigned": 3821,
                    "flags": [
                        "bound"
                    ],
                    "ipv6-addr": [
                        {
                            "address": "79f7:88ad:823c:9cf::eed",
                            "preferred-lifetime": 230199,
                            "valid-lifetime": 256119
                        }
                    ],
                    "valid": 40515
                },
                {
                    "duid": "0003000104f021241989",
                    "iaid": 1,
                    "hostname": "turris",
                    "accept-reconf": true,
                    "assigned": 4,
                    "flags": [
                            "bound"
                    ],
                    "ipv6-prefix": [
                        {
                            "address": "79f7:88ad:823c:9cf::",
                            "preferred-lifetime": 230199,
                            "valid-lifetime": 256119,
                            "prefix-length": 62
                        }
                    ],
                    "valid": 40515
                }
            ]
        }
    }
}"""

def main():
    parser = ArgumentParser(prog="ubus")
    parser.add_argument("command")
    parser.add_argument("object")
    parser.add_argument("method")
    # parser.add_argument("message")

    args = parser.parse_args()

    if args.command != "call":
        print({})

    if args.object != "dhcp":
        print({})

    if args.method != "ipv6leases":
        print({})


    print(DHCP_DATA)


if __name__ == "__main__":
    main()
