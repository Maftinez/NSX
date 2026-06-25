from NSX_API import *
import urllib3

def generate_policy_object(original_policy:dict, original_policy_rules:list):
    arr_fields_to_remove = ["owner_id", "remote_path", "status"]

    for field in arr_fields_to_remove:
        if field in original_policy:
            original_policy.pop(field)

        for rule in original_policy_rules:
            if field in rule:
                rule.pop(field)

    original_policy["rules"] = original_policy_rules
    return original_policy

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("------------------------------------------")
    print("------ NSX DFW POLICY && RULE MIGRATION TOOL ----------")
    print("------------------------------------------")

    source_nsx_fqdn = input('Source NSX Fqdn:')
    source_nsx_username = input("Username:")
    source_nsx_password = input("Password:")

    destination_nsx_fqdn = input('Destination NSX Fqdn:')
    destination_nsx_username = input("Username:")
    destination_nsx_password = input("Password:")

    source_nsx = NSX_API(manager_fqdn=source_nsx_fqdn, username=source_nsx_username, password=source_nsx_password)
    destination_nsx = NSX_API(manager_fqdn=destination_nsx_fqdn, username=destination_nsx_username, password=destination_nsx_password)

    arr_dfw_policies = source_nsx.get_local_dfw_policies_none_vpc()
    for dfw_policy in arr_dfw_policies:
        if dfw_policy["is_default"]:
            continue

        policy_path = dfw_policy["path"]
        arr_policy_rules = source_nsx.get_rules(policy_path=policy_path)

        policy_to_create = generate_policy_object(original_policy=dfw_policy, original_policy_rules=arr_policy_rules)

        pprint(policy_to_create)

        destination_nsx.create_dfw_policy_from_dict(policy_object=policy_to_create)

if __name__ == "__main__":
    main()
  
