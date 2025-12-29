# ONDE-format

## Generalities
Specification of the ONDE (**Open Non Destructive Evaluation**) Format


This specification of the ONDE format results from a joint intiative by COFREND and EPRI to define a specification of open and efficient NDE formats in order to facilitate interoperability between softwares and to ensure ability to read the data in the long term. 

In order to achieve these objectives, it is based on the HDF5 library.

The present repository contains : 
* a [csv file](ONDE_fields/ONDE_fields.csv) describing the fields of the hdf5 structure
* a description of the ONDE [UT specification](UT_specification/UT_file_format.md)

It will be completed in the future by an extension to Eddy Current testing and by python tools allowing to check the compliance of a file to the specification.


## Instructions for contributors

New proposals can be submitted by using the github *Issue* functionality. The template to be used for these issue is provided here : [Issue template](./issue_template.md).

The git branches are created with the following conventions :
*	*main* is the branch containing the latest version of the specification
*	*next_minor* is the branch containing bug corrections or minor evolutions that are intended to become the next version of the specification
*	*next_major* is a working branch containing major evolutions
 
When a minor version is created, changes are merged from next_minor into main and from main into next_major
When a major version is created, changes are merged from next_major into main and from main into next_minor
 
Branches related to an issue are named in one of the following manners :
*	[Issue_short_title]_[issue_number]
*	[Common theme] (for multiple issues)

They are based on *next_minor* or *next_major* according to the type of issue.
