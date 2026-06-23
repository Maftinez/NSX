from NSX_API import *
import urllib3

def create_groups(arr_groups_to_create: list, target_nsx: NSX_API, target_nsx_existing_groups_map: set):
    arr_leftovers = []
    for group in arr_groups_to_create:
        group_path = group["path"]
        #does_group_already_exist = (target_nsx.get_group_by_path(path=group["path"]) != None)
        does_group_already_exist = group_path in target_nsx_existing_groups_map
        
        if does_group_already_exist:
            continue
            
        system_owned = group["_system_owned"]
        create_user = group["_create_user"]
        
        if system_owned or create_user == "system":
            continue
            
        if "owner_id" in group:
            group.pop("owner_id")
            
        if "remote_path" in group:
            group.pop("remote_path")
            
        if "has_change_restrictions" in group:
            group.pop("has_change_restrictions")
            
        if "status" in group:
            group.pop("status")
            
        if "effective_member_types" in group:
            group.pop("effective_member_types")
            
        if "expression" in group:
            expressions = group["expression"]
            
            for expression in expressions:
                if "remote_path" in expression:
                    expression.pop("remote_path")
                    
                if "expressions" in expression:
                    sub_expressions = expression["expressions"]
                    for sub_expression in sub_expressions:
                        if "remote_path" in sub_expression:
                            sub_expression.pop("remote_path")
                            
        try:
            target_nsx.create_group_from_dict(group_data=group)
            target_nsx_existing_groups_map.add(group_path)
        except Exception as e:
            arr_leftovers.append(group)
            
    return arr_leftovers

def map_existing_groups(target_nsx: NSX_API):
    arr_existing_groups = target_nsx.get_local_groups()
    mapping = set()
    
    for group in arr_existing_groups:
        group_path = group["path"]
        if group_path not in mapping:
            mapping.add(group_path)
            
    return mapping

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    retry_count = 0
    max_retry_count = 50
    
    print("----------------------------------------")
    print("------ NSX GROUP MIGRATION TOOL --------")
    print("----------------------------------------")
    
    source_nsx_fqdn = input('Source NSX Fqdn:')
    source_nsx_username = input("Username:")
    source_nsx_password = input("Password:")
    
    destination_nsx_fqdn = input('Destination NSX Fqdn:')
    destination_nsx_username = input("Username:")
    destination_nsx_password = input("Password:")
    
    source_nsx = NSX_API(manager_fqdn=source_nsx_fqdn, username=source_nsx_username, password=source_nsx_password)
    destination_nsx = NSX_API(manager_fqdn=destination_nsx_fqdn, username=destination_nsx_username, password=destination_nsx_password)
    
    arr_groups_to_migrate = source_nsx.get_local_groups()
    existing_groups_map = map_existing_groups(destination_nsx)
    
    arr_groups_to_revisit = create_groups(arr_groups_to_create=arr_groups_to_migrate, target_nsx=destination_nsx, target_nsx_existing_groups_map=existing_groups_map)

    # Note, Incase of a failure to create the services, code will retry 50 times before timing out - to prevent infinite loop.
    while len(arr_groups_to_revisit) > 0 && (retry_count < max_retry_count):
        arr_groups_to_revisit = create_groups(arr_groups_to_create=arr_groups_to_revisit, target_nsx=destination_nsx, target_nsx_existing_groups_map=existing_groups_map)
        retry_count += 1

if __name__ == "__main__":
    main()
  
