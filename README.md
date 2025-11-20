# ONDE-format
Specification of the ONDE (**Open Non Destructive Evaluation**) Format


This specification of the ONDE format results from a joint intiative by COFREND and EPRI to define a specification of open and efficient NDE formats in order to facilitate interoperability between softwares and to ensure ability to read the data in the long term. 

In order to achieve these objectives, it is based on the HDF5 library.

The present repository contains : 
* a [csv file](ONDE_fields/ONDE_fields.csv) describing the fields of the hdf5 structure
* a description of the ONDE [UT specification](UT_specification/UT_file_format.md)
* a description of the ONDE [ET specification](ET_Specification/ET_file_format.md)

It will be completed in the future by an extension to Eddy Current testing and by python tools allowing to check the compliance of a file to the specification.
