from typing import Dict, Optional
from pydantic import BaseModel, validator
from ipaddress import IPv4Address
import yaml
from loguru import logger


class MailConfig(BaseModel):
    enabled: bool
    subject: str
    send_from: str
    send_to: list[str]
    server: str


class Connection(BaseModel):
    device_type: str
    host: str
    username: str
    fast_cli: bool
    # password: str
    enable_required: bool

    @validator("host")
    def ip_address(cls, host):
        try:
            IPv4Address(host)
        except:
            raise ValueError(f"{host} - not IP address")
        return host.title()


class Device(BaseModel):
    name: str
    role: Optional[str]
    connection: Connection


class Devices(BaseModel):
    devices: Dict[str, Device]


class Prerequisites(BaseModel):
    check_description: bool
    description: Optional[str]
    check_route: bool
    inventory_must_contain_all_contexts: Optional[bool]
    route: Optional[str]  # TODO


# class Config(BaseModel):
#     prerequisites: Dict[str, Prerequisites]
# devices: Dict[str, Devices]


class Config(BaseModel):
    multicontext: bool
    prerequisites: dict
    contexts_role_check: dict
    devices: dict


def load_inventory(file):
    # print(file)
    with open(file, "r", encoding="utf-8") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    # print(cfg["prerequisites"])
    # print(cfg["devices"])
    return Config(prerequisites=cfg.get("prerequisites"), 
        devices=cfg.get("devices"), 
        contexts_role_check = cfg.get("contexts_role_check"),
        multicontext = cfg.get("multicontext"))


def load_mail_config(file):
    # print(file)
    with open(file, "r", encoding="utf-8") as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return MailConfig(**cfg.get("mail_reports"))
