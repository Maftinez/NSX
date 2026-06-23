from NSX_API import *
import urllib3

def create_services(arr_services_to_create:list, target_nsx: NSX_API, target_nsx_existing_services_map:set):
    print(f"going over {len(arr_services_to_create)} services...")
    arr_leftovers = []
    for service in arr_services_to_create:
        service_path = service["path"]
        does_service_already_exist = service_path in target_nsx_existing_services_map

        if does_service_already_exist:
            continue
            
        system_owned = service["_system_owned"]
        create_user = service["_create_user"]
        
        if system_owned or create_user == "system":
            continue
            
        if "owner_id" in service:
            service.pop("owner_id")
            
        if "service_entries" in service:
            for entry in service["service_entries"]:
                if "owner_id" in entry:
                    entry.pop("owner_id")
                if "remote_path" in entry:
                    entry.pop("remote_path")
                    
        if "remote_path" in service:
            service.pop("remote_path")
            
        if "status" in service:
            service.pop("status")
            
        try:
            target_nsx.create_service_from_dict(service_data=service)
            target_nsx_existing_services_map.add(service_path)
        except Exception as e:
            arr_leftovers.append(service)
            
    return arr_leftovers

def map_existing_services(target_nsx:NSX_API):
    arr_existing_services = target_nsx.get_local_services()
    mapping = set()
    
    for service in arr_existing_services:
        service_path = service["path"]
        if service_path not in mapping:
            mapping.add(service_path)
            
    return mapping

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    
    print("---------------------------------------")
    print("------ NSX SERVICE MIGRATION TOOL -----")
    print("---------------------------------------")
    
    source_nsx_fqdn = input('Source NSX Fqdn:')
    source_nsx_username = input("Username:")
    source_nsx_password = input("Password:")
    
    destination_nsx_fqdn = input('Destination NSX Fqdn:')
    destination_nsx_username = input("Username:")
    destination_nsx_password = input("Password:")
    
    source_nsx = NSX_API(manager_fqdn=source_nsx_fqdn, username=source_nsx_username, password=source_nsx_password)
    destination_nsx = NSX_API(manager_fqdn=destination_nsx_fqdn, username=destination_nsx_username, password=destination_nsx_password)
    
    arr_services_to_migrate = source_nsx.get_local_services()
    existing_services_map = map_existing_services(destination_nsx)
    
    arr_services_to_revisit = create_services(arr_services_to_create=arr_services_to_migrate, target_nsx=destination_nsx, target_nsx_existing_services_map=existing_services_map)
    
    while len(arr_services_to_revisit) > 0:
        arr_services_to_revisit = create_services(arr_services_to_create=arr_services_to_revisit, target_nsx=destination_nsx, target_nsx_existing_services_map=existing_services_map)

if __name__ == "__main__":
    main()
  
