Written by Martin Gutman.
This script creates a mapping of all VM names and their assigned NSX tags.
The script saves the mapping in a given file path.
The scripts allows to replenish missing tags based on the mapping file it created.

To migrate tags betweem 2 NSXs, run it once and choose action #1.
Give the source nsx and creds as inputs along with path for the file to be saved in.
The path should include the file name and the type (.txt)
Make sure the mapping is saved and exists before continuing to action #2.
Run as many times as required action #2 to replenish the missing tags.
Action #2 requires dest NSX fqdn and creds along with the existing mapping file path.

This is not official VMware supported script!
