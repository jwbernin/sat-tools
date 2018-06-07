# sat-tools
You will need to create a credentials.json file that contains the hostname,
username, and password used to connect to the Satellite.

To do so, copy the examplecredentials.json file to credentials.json and edit
it to reflect the correct values for your environment.

## System prep 
You will need a couple PyPI packages before running these scripts. They are:
- xlsxwriter
- pyexcel-ods

## Notes
The satellite.py file is an encapsulation of a Red Hat Satellite Server 
as seen through it's API. It is not, nor is it intended to be, a 
feature-complete replacement for the hammer CLI or for the GUI interface.

It will be expanded at need, but is not guaranteed to work with versions of 
Satellite other than 6.3.x.