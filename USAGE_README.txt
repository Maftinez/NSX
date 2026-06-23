Scripts written by Martin Gutman.

-------------------------------------------------------------------------------
NSX_API class
-------------------------------------------------------------------------------
This class is represents NSX Local Manager ONLY in policy mode!
This class provides functions and methods that other scripts rely heavliy on this base class.
I have more functions and methods in my private environment if required, will be updated in the future.


-------------------------------------------------------------------------------
Migrate_Tags_Script
-------------------------------------------------------------------------------
This script creates a mapping of all VM names and their assigned NSX tags.
The script saves the mapping in a given file path.
The scripts allows to replenish missing tags based on the mapping file it created.

To migrate tags betweem 2 NSXs, run it once and choose action #1.
Give the source nsx and creds as inputs along with path for the file to be saved in.
The path should include the file name and the type (.txt)
Make sure the mapping is saved and exists before continuing to action #2.
Run as many times as required action #2 to replenish the missing tags.
Action #2 requires dest NSX fqdn and creds along with the existing mapping file path.

*NOTE*: Currently this script has its own NSX_API code inside of it because it was written before i made seperations.
        Also, if you require to migrate security groups and their tags, if the security groups have expressions using the tags - the tags will be migrated automatically along with the groups.
        You do not need to use this script to manually migrate tags if your intentions are to migrate groups that use tags - you can use the scripts bellow.

-------------------------------------------------------------------------------
Migrate_services_between_LMs
-------------------------------------------------------------------------------
This script migrates local services between 2 NSX Local Managers.
It operates by:
1. Extracting all local services from the source local manager.
2. filters what services actually needs to be migrated (excludes system and default built in services)
3. Creates a hashset of the current local services in the destination NSX by the services's path.
4. Using the hashset to check if service is already present in destination nsx by its path, if so it ignores that service.
5. loops through the list of services and tries to import them. Any service that is dependent on other services, thus failing to import gets into an array for later import.
6. Continuesly loop through the failed services array until all services were imported or until time-out.

-------------------------------------------------------------------------------
Migrate_groups_between_LMs
-------------------------------------------------------------------------------
This script migrates local groups between 2 NSX Local Managers.
It operates by:
1. Extracting all local groups from the source local manager.
2. filters what groups actually needs to be migrated (excludes system / default built-in and GM groups)
3. Creates a hashset of the current local groups in the destination NSX by the groups's path.
4. Using the hashset to check if groups is already present in destination nsx by its path, if so it ignores that group.
5. loops through the list of groups and tries to import them. Any group that is dependent on other groups (e.g nested-groups), thus failing to import gets into an array for later import.
6. Continuesly loop through the failed groups array until all groups were imported or until time-out.


*NOTE*
These scripts are not official VMware supported, They are tailored for specific enrionment use cases and were modified to be general. Could require code changes in different environments based on the environment. 
