from typing import Dict, Optional
from pydantic import BaseModel, validator
from ipaddress import IPv4Address
import yaml


class Connection(BaseModel):
    device_type: str
    host: str
    username: str
    password: str
    secret: Optional[str]

    @validator("host")
    def ip_address(cls, host):
        try:
            IPv4Address(host)
        except:
            raise ValueError(f"{host} - not IP address")
        return host.title()


class Device(BaseModel):
    name: Optional[str]
    role: Optional[str]
    connection: Connection


class Devices(BaseModel):
    devices: Dict[str, Device]


class Prerequisites(BaseModel):
    check_description: bool
    description: Optional[str]
    check_route: bool
    route: Optional[str]  # TODO


# class Config(BaseModel):
#     prerequisites: Dict[str, Prerequisites]
# devices: Dict[str, Devices]


class Config(BaseModel):
    prerequisites: dict
    devices: dict


def load_config(file):
    print(file)
    with open(file, "r") as stream:
        try:
            init_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    # print(init_config["prerequisites"])
    # print(init_config["devices"])
    return Config(
        prerequisites=init_config["prerequisites"], devices=init_config["devices"]
    )
