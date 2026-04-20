# ONDE Data Model and HDF5 transcription

## Introduction
The ONDE Data Model is defined by classes, which group together named fields. When implemented in the ONDE file, these classes translate into HDF5 groups. This section of the documentation describes :
- the principles used to define the classes (including subclasses and accessory classes) and the fields in the data model,
- the transcription of this data model in the reference csv file (see https://github.com/COFREND/ONDE-format/blob/main/ONDE_fields/ONDE_fields.csv),
- the way in which this data model translates into an HDF5 implementation in the ONDE file.

## Classes and subclasses

The ONDE Data model defines the notions of classes, subclasses. 

The attribute of a class can be :
- a elementary type (integer, float, string),
- a link to another class, 
- a multidimensional array of the previous types

### HDF5 implementation
In ONDE, an object corresponding to a class in the data model translates into an HDF5 group. The class of the object is given by a particular HDF5 attribute of the HDF5 group. This attribute is named `ONDE:TYPE` and contains a 1D array of strings. The name of the group is left free for the implementation decision.

The strings contained in the TYPE attribute describe the hierarchy of classes to which the object belongs, starting with the base class.

**Example** 

The ONDE format contains a `COMPONENT` class describing the inspected component. It has a `PLANE_COMPONENT` subclass. The HDF5 file will contain a group with n HDF5 attribute ONDE:TYPE that will contain  : `['COMPONENT', 'PLANAR_COMPONENT']`.

In the HDF5 implementation, the fields of a class can translate either into HDF5 attributes or in HDF5 datasets. This is defined for each field in the specification. Attrbutes will typically be used for fields that have a small size (scalar, string or small arrays), while datasets will be used for  arrays with a significant size.

### Accessory classes

Accessory classes make up for a flexible way to reuse frequently used patterns in the data model or to regroup fields that are linked together, so that the mandatory/optional nature of these fields appears clearly. These accessory classes are always referenced inside another class (referencing class). 

In the HDF5 implementation, these accessory classes result in HDF5 fields that are contained in the group of the object of the referencing class.

In the referencing class, a specific `ONDE:TYPE_TAGS` attribute will contain a string that gives the name of the accessory class.

**Example**

Let class `A` contain an accessory class `Z`, `Z` containing fields `FIELD_Z_1` and `FIELD_Z_2`. Let us also suppose that `A` contains another field `FIELD_A_1`.
A single HDF5 group will have the following attributes :

    ONDE:TYPE : ['A']
    ONDE:TYPE_TAGS : ['Z']
    A:FIELD_A_1 : ...
    Z:TYPE_TAGS : ['Z']
    Z:FIELD_Z_1 : ...
    Z:FIELD_Z_2 : ...


### Naming convention
The previous examples introduce the naming conventions used in ONDE :
- the name of the group used for the HDF5 implementation is free
- each class contains a mandatory attribute `ONDE:TYPE`
- accessory classes are defined through an attribute `ONDE:TYPE_TAGS`. If declared present in the specification, it is mandatory. The actual presence of accessory classes pointed by this attribute can however be optional
- except for the specific `ONDE:TYPE` and `ONDE:TYPE_TAGS` attributes, the fields of a class named `A` are prefixed with `A:`
- ONDE classes have names starting with 'ONDE_' prefix. This allows to separate clearly ONDE classes from vendor-specific extensions.

## Data model representation in the csv specification

### General notes on the csv tables
The specification of the format is provided in a [dedicated csv file](/ONDE_fields/ONDE_fields.csv) organized with the following columns :

•	*Class* – The name of the class (typically same as value of TYPE string); used to indicate inheritance (see later example)
•	*Name* – the physical name of the dataset or attribute in the HDF5 group
•	*M/O* – Mandatory or Optional
•	*D/A* – Dataset of Attribute
•	*Type* – The HDF5 class type including H5T_INTEGER and H5T_FLOAT which are generic
•	*Content* – Required content if relevant (essential for TYPE, potential useful for string enumerations to give list of allowed possibilities)
•	*Dimensions* – Can be either actual values or symbols to indicate variable sizes and relationships between dimensions of different members of class
•	*Min, Max* – Minimum and maximum values of numeric quantities if relevant.

### Representation of a class in the csv table

The following example indicates how a simple class is represented in the csv table.

*Example*

Let `ONDE_MYCLASS` be a class with optional field `COORDINATES` (an XYZ triplet ) , a field `DIMENSION` and a field `TABLE` (of size `[DIMENSION, 3]`).
The csv table will look like this :

|Class|Name|M/O|D/A|Type|Content|Dimensions|Min|Max|
|---|---|---|---|---|---|---|---|---|
|ONDE_MYCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS"]|[1]||||
|ONDE_MYCLASS|ONDE_MYCLASS:COORDINATES|O|A|H5T_FLOAT||[3]|||
|ONDE_MYCLASS|ONDE_MYCLASS:DIMENSION|M|A|H5T_INTEGER||1|1||
|ONDE_MYCLASS|ONDE_MYCLASS:TABLE|M|D|H5T_FLOAT||[ONDE_MYCLASS:DIMENSION,3]|||

### Representation of a subclass in the csv table

In the csv file, the class hierarchy is described in the Class column. The class and its ancestor  classes are separated by colons, starting from the base class. As indicated above, the ONDE:TYPE attribute will contain the class hierarchy.

Let `ONDE_MYSUBCLASS` be a subclass of `ONDE_MYCLASS`, adding the extra attribute `MY_VALUE`.
The csv table will look like this :

|Class|Name|M/O|D/A|Type|Content|Dimensions|Min|Max|
|---|---|---|---|---|---|---|---|---|
|ONDE_MYCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS"]|[1]||||
|ONDE_MYCLASS|ONDE_MYCLASS:COORDINATES|O|A|H5T_FLOAT||[3]|||
|ONDE_MYCLASS|ONDE_MYCLASS:DIMENSION|M|A|H5T_INTEGER||1|1||
|ONDE_MYCLASS|ONDE_MYCLASS:TABLE|M|D|H5T_FLOAT||[ONDE_MYCLASS:DIMENSION,3]|||
|ONDE_MYCLASS:ONDE_MYSUBCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS","ONDE_MYSUBCLASS"]|[2]||||
|ONDE_MYCLASS:ONDE_MYSUBCLASS:MY_VALUE|M|A|H5T_FLOAT||1|||

The HDF5 file will contain an HDF5 group with attribute `ONDE_TYPE` (containing ["ONDE_MYCLASS","ONDE_MYSUBCLASS"]), and with attributes `ONDE_MYCLASS:COORDINATES`, `ONDE_MYCLASS:DIMENSION`, `ONDE_MYCLASS:ONDE_MYSUBCLASS:MY_VALUE` and with an HDF5 dataset named `ONDE_MYCLASS:TABLE` 

