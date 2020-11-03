"""
Sophos Partner Cli

Author: Matthew Jenkins
Email: matt.jenkins@dataprise.com

Version 1.0.0
"""
from typing import Optional
from sophosApi.apiClient import *
import configparser
import argparse
import logging
import shelve
from pathlib import Path

client: ApiClient
identity: Optional[str] = None
config_file = Path.home() / 'sophosCli.ini'
cache = shelve.open(str(Path.home() / 'sophosCache'))


def get_tenants():
    pass


def create_config():
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'Client_id': "",
                         'Client_token': "",
                         'log_level': "WARNING"}
    with open(config_file, 'w') as f:
        config.write(f)


def get_config():
    try:
        Path.stat(config_file)
    except FileNotFoundError:
        create_config()
        print(f'Please enter configuration in {config_file}')
        exit(1)
    config = configparser.ConfigParser()
    config.read(config_file)
    vals = config.defaults()
    return vals


def parse_config(vals):
    if vals.get('client_id') is None or vals.get('client_id') == '':
        raise ValueError("client_id is a required config item")
    if vals.get('client_token') is None or vals.get('client_token') == '':
        raise ValueError("client_token is a required config item")
    global client
    client = ApiClient(vals['client_id'], vals['client_token'])
    levels = ['DEBUG', 'INFO', 'WARNING']
    if vals.get('log_level') is None or vals.get('log_level') not in levels:
        raise ValueError(f'log_level is a required value and must be one of {levels}')
    eval(f"""logging.basicConfig(level=logging.{vals['log_level']}, 
             format='%(asctime)s:%(levelname)s:%(message)s')""")
    if vals.get('identity') is not None and vals.get('identity') != '':
        global identity
        identity = vals['identity']


def update_config(key, value):
    config = configparser.ConfigParser()
    config['DEFAULT'] = get_config()
    config['DEFAULT'][key] = value
    with open(config_file, 'w') as f:
        config.write(f)


def parse_cli():
    parser = argparse.ArgumentParser(description="Manage sophos alerts and endpoints via cli.")
    subparsers = parser.add_subparsers(title="commands")

    alert = subparsers.add_parser('alert', help='List alerts or manage alert.')
    alert = alert.add_subparsers(title='alert commands')
    alert_list = alert.add_parser('list', help="List all alerts")
    alert_list.set_defaults(func=falert_list)
    alert_detail = alert.add_parser('detail', help="Show detailed information about an alert")
    alert_detail.add_argument('id', help="id from alert list to show details for.")
    alert_detail.set_defaults(func=falert_detail)
    alert_action = alert.add_parser('action', help='Perform allowed action on an alert.')
    alert_action.add_argument('id', help="id from alert to action.")
    alert_action.add_argument('action', help='Allowed action to perform on alert.')
    alert_action.set_defaults(func=falert_action)

    endpoint = subparsers.add_parser('endpoint', help='List endpoints or manage endpoints.')
    endpoint = endpoint.add_subparsers(title='endpoint/managedAgent commands')
    endpoint_list = endpoint.add_parser('list', help='list all endpoints for a client')
    endpoint_list.set_defaults(func=fendpoint_list)
    endpoint_detail = endpoint.add_parser('detail', help='Show detailed information about an endpoint')
    endpoint_detail.add_argument('id', help='id from endpoint list to show details for.')
    endpoint_detail.set_defaults(func=fendpoint_detail)
    endpoint_scan = endpoint.add_parser('scan', help='Queue a scan of the endpoint.')
    endpoint_scan.add_argument('id', help="id of endpoint to scan")
    endpoint_scan.set_defaults(func=fendpoint_scan)
    endpoint_update = endpoint.add_parser('update', help='Queue updates for Sophos.')
    endpoint_update.add_argument('id', help='id of endpoint to update')
    endpoint_update.set_defaults(func=fendpoint_update)

    cache = subparsers.add_parser('cache', help='Manage local cli cache.')
    cache = cache.add_subparsers(title='Cache management commands')
    cache_clear = cache.add_parser('clear', help='Delete cache. Next run will take longer.')
    cache_clear.set_defaults(func=fcache_clear)

    tenant = subparsers.add_parser('tenant', help='List tenants or become tenant.')
    tenant = tenant.add_subparsers(title='tenant commands.')
    tenant_list = tenant.add_parser('list', help="List all tenants. [CACHED!]")
    tenant_list.set_defaults(func=ftenant_list)
    tenant_enter = tenant.add_parser('enter', help="Enter tenant for managing alerts and endpoints. You can switch "
                                                   "directly between tenants without exiting.")
    tenant_enter.set_defaults(func=ftenant_enter)
    tenant_enter.add_argument('id', help='id of tenant to enter.')
    tenant_exit = tenant.add_parser('exit', help="Leave the current tenant and become partner level.")
    tenant_exit.set_defaults(func=ftenant_exit)
    args = parser.parse_args()
    if hasattr(args, 'func'):
        print(args.func(args))
    else:
        print("use -h or --help for information on how to use this program.")


def fcache_clear(args) -> str:
    for k in cache.keys():
        del cache[k]
    cache.sync()
    return 'Cache cleared!'


def fendpoint_list(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before listing endpoints!')
    endpoints = client[identity].endpoints.fetch_all()
    val = val + f"{'Id'.ljust(36)}\tHostname\n"
    for endpoint in endpoints:
        val = val + f"{endpoint.id}\t{endpoint.hostname or getattr(endpoint, 'ipAddresses', '??????')}\n"
    return val


def fendpoint_detail(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before listing endpoints!')
    endpoint = client[identity].endpoints[args.id]
    pad = max([len(k) for k in endpoint.__annotations__.keys()]) + 1
    for x in list(endpoint.__annotations__.keys()):
        val = val + f"{x.ljust(pad)}\t{getattr(endpoint, x)}\n"
    return val


def fendpoint_scan(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before scanning endpoints!')
    endpoint = client[identity].endpoints[args.id]
    result = client[identity].endpoints.scan(args.id)
    if result:
        val = val + "Sophos reported scan is queued."
    else:
        val = val + "Sophos reported scan failed to queue."
    return val


def fendpoint_update(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before updating endpoints!')
    endpoint = client[identity].endpoints[args.id]
    result = client[identity].endpoints.update_agent(args.id)
    if result:
        val = val + "Sophos reported update is queued."
    else:
        val = val + "Sophos reported update failed to queue."
    return val


def falert_action(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before actioning alerts!')
    alert = client[identity].alerts[args.id]
    if args.action not in alert.allowedActions:
        raise ValueError(f"{args.action} not allowed on alert {alert.id}. Choose from {alert.allowedActions}")
    result = client[identity].alerts.action(alert.id, args.action)
    if result:
        val = val + f"Sophos reported action {args.action} is queued."
    else:
        val = val + f"Sophos report action {args.action} failed to be queued."
    return val


def falert_detail(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before viewing alerts!')
    alert = client[identity].alerts[args.id]
    pad = max([len(k) for k in alert.__annotations__.keys()]) + 1
    for x in list(alert.__annotations__.keys()):
        val = val + f"{x.ljust(pad)}\t{getattr(alert, x)}\n"
    return val


def main():
    parse_config(get_config())
    if cache.get('tenants') is None:
        d = dict([(t.id, {'name': t.name, 'apiHost': t.apiHost, 'id': t.id}) for t in client.tenants.values()])
        cache['tenants'] = d
        cache.sync()
    parse_cli()


def ftenant_list(args) -> str:
    val = ""
    tenants = cache['tenants'].values()
    val = val + f"{'Id'.ljust(36)}\tName\n"
    for tenant in tenants:
        val = val + f"{tenant['id']}\t{tenant['name']}\n"
    return val


def falert_list(args) -> str:
    val = ""
    if identity is None:
        raise Exception('Must become tenant before viewing alerts!')
    alerts = client[identity].alerts.fetch_all()
    val = val + f"{'Id'.ljust(36)}\tDesc\n"
    for alert in alerts:
        val = val + f"{alert.id}\t{alert.description}\n"
    return val


def ftenant_enter(args) -> None:
    update_config('identity', args.id)


def ftenant_exit(args) -> None:
    update_config('identity', '')


if __name__ == '__main__':
    main()
