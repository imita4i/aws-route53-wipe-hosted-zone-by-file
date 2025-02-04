#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imita4i'

import boto3
import sys

client = boto3.client('route53')

def get_hosted_zone_id(domain_name):
    response = client.list_hosted_zones_by_name(DNSName=domain_name)
    for zone in response['HostedZones']:
        if zone['Name'].strip('.') == domain_name:
            return zone['Id']
    return None

def show_list_resource_record_sets(zone_id):
    response = client.list_resource_record_sets(HostedZoneId=zone_id)
    for record in response['ResourceRecordSets']:
        print(record)

def delete_hosted_zone(zone_id):
    try:
        client.delete_hosted_zone(Id=zone_id)
        print(f"Zone {zone_id} successfully deleted")
    except Exception as e:
        print(f"Error deleting zone {zone_id}: {e}")

def delete_zones_from_file(filename):
    try:
        with open(filename, 'r') as file:
            domains = file.readlines()
            for domain in domains:
                domain = domain.strip()
                print(f"Looking zone for the domain: {domain}")
                zone_id = get_hosted_zone_id(domain)
                if zone_id:
                    show_list_resource_record_sets(zone_id)
                    while (check := input("Do you want to delete this zone? (Y/N) ")\
                        .lower()) not in ['y', 'n']: print("Invalid input!")
                    if check == 'y':
                        delete_all_records(zone_id)
                        delete_hosted_zone(zone_id)
                else:
                    print(f"Zone for the domain {domain} not found")
    except FileNotFoundError:
        print(f"File {filename} not found :c")
    except Exception as e:
        print(f"Error: {e}")

def delete_all_records(zone_id):
    next_token = None
    all_records = []

    while True:
        if next_token:
            response = client.list_resource_record_sets(
                HostedZoneId=zone_id,
                MaxItems='100',
                NextToken=next_token
            )
        else:
            response = client.list_resource_record_sets(
                HostedZoneId=zone_id,
                MaxItems='100'
            )
        
        all_records.extend(response['ResourceRecordSets'])
        next_token = response.get('NextToken')

        if not next_token:
            break
    
    changes = []
    for record in all_records:
        if record['Type'] not in ['NS', 'SOA']:
            changes.append({
                'Action': 'DELETE',
                'ResourceRecordSet': record
            })

    if changes:
        change_batch = {'Changes': changes}
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch=change_batch
        )
        print(f"Removed {len(changes)} records")
    else:
        print("Records not found")

def main() -> int:
    if (len(sys.argv) != 2):
        print(sys.argv[0] + " filename")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())