# ONDE Data Model and HDF5 transcription

## Introduction
The ONDE Data Model is defined by classes, which group together named fields. When implemented in the ONDE file, these classes translate into HDF5 groups. This section of the documentation describes:

- the principles used to define the classes (including subclasses and accessory classes) and the fields in the data model,
- the transcription of this data model in the reference csv file (see https://github.com/COFREND/ONDE-format/blob/main/ONDE_fields/ONDE_fields.csv),
- the way in which this data model translates into an HDF5 implementation in the ONDE file.



## Classes and subclasses

The ONDE Data model defines the notions of classes, subclasses. 

Classes define fields that can be:

- an elementary type (integer, float, string),
- a link to an object of another class, 
- a multidimensional array of the previous types

## HDF5 implementation

### File type
The extension of the HDF5 file is ".onde" (for Open Non Destructive Evaluation format).
The HDF5 root group must contain an attribute called `ONDE:FILETYPE` and a `ONDE:VERSION` attribute. The file is identified as a UT ONDE file because of the `ONDE:FILETYPE` attribute which is given at the root of the structure. The version of the file points to the version of the present specification.

### HDF5 implementation of classes
In ONDE, an object corresponding to a class in the data model translates into an HDF5 group. The class of the object is given by a particular HDF5 attribute of the HDF5 group. This attribute is named `ONDE:TYPE` and contains a 1D array of strings. The HDF5 name of the group is left free for the implementation decision.

The strings contained in the TYPE attribute describe the hierarchy of classes to which the object belongs, starting with the base class.

**Example** 

The ONDE format contains a `ONDE_COMPONENT` class describing the inspected component. It has a `ONDE_PLANE` subclass. The HDF5 file will contain a group with n HDF5 attribute ONDE:TYPE that will contain: `['ONDE_COMPONENT', 'ONDE_PLANE']`.

### HDF5 implementation of class fields

In the HDF5 implementation, the fields of a class can translate either into HDF5 attributes or in HDF5 datasets. This is defined for each field in the specification. Attrbutes will typically be used for fields that have a small size (scalar, string or small arrays), while datasets will be used for  arrays with a significant size. Their optional or mandatory natrure is also defined, as well as the constraints on their dimensions and the range of accessible values (minimum and maximum for scalar values or allowed values for some strings).

For the fields corresponding to integer and floats, the specification generally points to HDF5 generic types H5T_FLOAT and H5T_INTEGER. That implies that the freedom is given to the data producer to choose the actual implementation type (8, 16, 32, 64 bits, signed/unsigned, etc) for the corresponding field. 

For arrays (which are stored as HDF5 datasets), the specification give the dimensions of the array in row-major order (the
  last dimension corresponds to contiguous data in the file). Compression of arrays through the native compression schemes of the HDF5 libary
  (gzip3, Szip).

Readers should be robust to mandatory fields being missing, as the specification is likely to evolve in the future with current mandatory fields possibly being deprecated and replaced, or being made non-mandatory because of use cases where correct values cannot be determined.

### Accessory classes

Accessory classes make up for a flexible way to reuse frequently used patterns in the data model or to regroup fields that are linked together, so that the mandatory/optional nature of these fields appears clearly. These accessory classes are always referenced inside another class (referencing class). 

In the HDF5 implementation, these accessory classes result in HDF5 attributes and datasets that are contained in the group of the object of the referencing class.

In the referencing class, a specific `ONDE:TYPE_TAGS` attribute will contain a string that gives the name of the accessory class.

**Example**

Let class `A` contain an accessory class `Z`, `Z` containing fields `FIELD_Z_1` and `FIELD_Z_2`. Let us also suppose that `A` contains another field `FIELD_A_1`.
A single HDF5 group will have the following attributes:

    ONDE:TYPE: ['A']
    ONDE:TYPE_TAGS: ['Z']
    A:FIELD_A_1: ...
    Z:FIELD_Z_1: ...
    Z:FIELD_Z_2: ...


### Naming convention
The previous examples introduce the naming conventions used in ONDE:

- the name of the group used for the HDF5 implementation is free
- each class contains a mandatory attribute `ONDE:TYPE`
- accessory classes are defined through an attribute `ONDE:TYPE_TAGS`. If declared present in the specification, it is mandatory. The actual presence of accessory classes pointed by this attribute can however be optional
- except for the specific `ONDE:TYPE` and `ONDE:TYPE_TAGS` attributes, the fields of a class named `A` are prefixed with `A:`
- ONDE classes have names starting with 'ONDE_' prefix. This allows to separate clearly ONDE classes from vendor-specific extensions.

## Data model representation in the YAML specification

### General notes on the YAML schemas
The specification of the format is defined by a Single Source of Truth located in the `class_definitions/` directory. This directory contains a series of YAML files. Each YAML file defines a single class and contains both the human-readable description and the machine-readable metadata. 

For each class, the YAML schema defines:

- **inherits**: The parent class this class inherits from, if any.
- **allowed_classes**: If this is a root class, the permissible subclasses that can be instantiated.
- **fields**: The individual data fields (attributes or datasets) belonging to this class.

Each field is defined with the following properties:

- `full_name` – The physical name of the field (dataset or attribute) in the HDF5 group
- `required` – A boolean indicating whether the field is mandatory (`true`) or optional (`false`)
- `storage` – Specifies whether it is stored as a `dataset` or `attribute`
- `hdf5_type` – The HDF5 class type, including `H5T_INTEGER` and `H5T_FLOAT`
- `description` / `short_description` – Human-readable explanations of the field
- `dimensions` – Can be actual values or symbols to indicate variable sizes
- `allowed_values` – A list of permissible string values, if applicable
- `min_value` / `max_value` – Minimum and maximum values for numeric quantities, if relevant

### Representation of a class in the YAML schemas

The following example indicates how a simple class is represented in YAML.

*Example*

Let `ONDE_MYCLASS` be a class with an optional field `COORDINATES` (an XYZ triplet), a mandatory field `DIMENSION`, and a mandatory dataset `TABLE` (of size `[DIMENSION, 3]`).
The YAML file (`onde_myclass.yaml`) will look like this:

```yaml
name: ONDE_MYCLASS
description: A custom ONDE class.
fields:
  COORDINATES:
    full_name: ONDE_MYCLASS:COORDINATES
    required: false
    storage: attribute
    hdf5_type: H5T_FLOAT
    dimensions: '[3]'
  DIMENSION:
    full_name: ONDE_MYCLASS:DIMENSION
    required: true
    storage: attribute
    hdf5_type: H5T_INTEGER
    dimensions: '1'
    min_value: 1
  TABLE:
    full_name: ONDE_MYCLASS:TABLE
    required: true
    storage: dataset
    hdf5_type: H5T_FLOAT
    dimensions: '[ONDE_MYCLASS:DIMENSION,3]'
```

### Representation of a subclass in the YAML schemas

Class inheritance is defined using the `inherits` array. The `ONDE:TYPE` attribute in the generated HDF5 file will automatically contain the class hierarchy starting from the base class.

Let `ONDE_MYSUBCLASS` be a subclass of `ONDE_MYCLASS`, adding an extra attribute `MY_VALUE`.
The YAML file (`onde_mysubclass.yaml`) will look like this:

```yaml
name: ONDE_MYSUBCLASS
inherits:
  - ONDE_MYCLASS
description: A subclass extending ONDE_MYCLASS.
fields:
  MY_VALUE:
    full_name: ONDE_MYSUBCLASS:MY_VALUE
    required: true
    storage: attribute
    hdf5_type: H5T_FLOAT
    dimensions: '1'
```

The HDF5 file will contain an HDF5 group with the attribute `ONDE_TYPE` containing `["ONDE_MYCLASS", "ONDE_MYSUBCLASS"]`, attributes `ONDE_MYCLASS:COORDINATES`, `ONDE_MYCLASS:DIMENSION`, `ONDE_MYSUBCLASS:MY_VALUE`, and an HDF5 dataset named `ONDE_MYCLASS:TABLE`.

### Representation of an accessory class in the YAML schemas

An accessory class is defined like any other class, but it includes an `is_accessory: true` boolean. 
Another class will refer to this accessory class to aggregate its content through an `ONDE:TYPE_TAGS` attribute that contains a list of accessory classes.

Let `ONDE_MY_ACCESSORY_CLASS` be an accessory class having a string attribute `MY_STRING`. The YAML will look like this:

```yaml
name: ONDE_MY_ACCESSORY_CLASS
is_accessory: true
description: A custom accessory class.
fields:
  MY_STRING:
    full_name: ONDE_MY_ACCESSORY_CLASS:MY_STRING
    required: true
    storage: attribute
    hdf5_type: H5T_STRING
    dimensions: '1'
```

When this accessory is aggregated in an `ONDE_MYCLASS` group, the HDF5 group will contain an `ONDE:TYPE_TAGS` attribute listing `["ONDE_MY_ACCESSORY_CLASS"]`, and the fields of the accessory class will be present alongside the fields of the base class.

### Legacy CSV Specification

While the Single Source of Truth for the data model is defined in the YAML schemas, a legacy CSV representation can still be generated for compatibility or external tooling.

To generate the legacy CSV format, users can run the provided Python script:
```bash
python tools/generate_csv.py
```
This will parse the YAML files in the `class_definitions/` directory and output a `ONDE_fields.csv` file in the `build/` directory, formatted according to the legacy table structure.

#### General notes on the legacy csv table
The generated csv file is organized with the following columns:

- *Class* – The name of the class (typically same as value of TYPE string); used to indicate inheritance (see later example)
- *Name* – the physical name of the field (dataset or attribute in the HDF5 group)
- *M/O* – Mandatory or Optional
- *D/A* – Dataset or Attribute
- *Type* – The HDF5 class type including H5T_INTEGER and H5T_FLOAT which are generic
- *Content* – Required content if relevant (essential for TYPE, potential useful for string enumerations to give list of allowed possibilities)
- *Dimensions* – Can be either actual values or symbols to indicate variable sizes and relationships between dimensions of different members of class
- *Min, Max* – Minimum and maximum values of numeric quantities if relevant.
- *Accessory Class* - Specifies wether a class is an accessory class

The csv separator that is used in the file is a semicolon.

In some cases, several values are admissible for a given column (D or A in the Dataset/Attribute column, several possible values for a string). The specification uses either "or" or "|" to specify this.

#### Representation of a class in the csv table

The following example indicates how a simple class is represented in the csv table.

*Example*

Let `ONDE_MYCLASS` be a class with optional field `COORDINATES` (an XYZ triplet), a field `DIMENSION` and a field `TABLE` (of size `[DIMENSION, 3]`).
The csv table will look like this:

|Class|Name|M/O|D/A|Type|Content|Dimensions|Min|Max|Accessory Class|
|---|---|---|---|---|---|---|---|---|---|
|ONDE_MYCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS"]|[1]|||||
|ONDE_MYCLASS|ONDE_MYCLASS:COORDINATES|O|A|H5T_FLOAT||[3]||||
|ONDE_MYCLASS|ONDE_MYCLASS:DIMENSION|M|A|H5T_INTEGER||1|1|||
|ONDE_MYCLASS|ONDE_MYCLASS:TABLE|M|D|H5T_FLOAT||[ONDE_MYCLASS:DIMENSION,3]||||

#### Representation of a subclass in the csv table

In the csv file, the class hierarchy is described in the Class column. The class and its ancestor classes are separated by colons, starting from the base class. As indicated above, the ONDE:TYPE attribute will contain the class hierarchy.

Let `ONDE_MYSUBCLASS` be a subclass of `ONDE_MYCLASS`, adding the extra attribute `MY_VALUE`.
The csv table will look like this:

|Class|Name|M/O|D/A|Type|Content|Dimensions|Min|Max|Accessory Class|
|---|---|---|---|---|---|---|---|---|---|
|ONDE_MYCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS"]|[1]|||||
|ONDE_MYCLASS|ONDE_MYCLASS:COORDINATES|O|A|H5T_FLOAT||[3]||||
|ONDE_MYCLASS|ONDE_MYCLASS:DIMENSION|M|A|H5T_INTEGER||1|1|||
|ONDE_MYCLASS|ONDE_MYCLASS:TABLE|M|D|H5T_FLOAT||[ONDE_MYCLASS:DIMENSION,3]||||
|ONDE_MYSUBCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS","ONDE_MYSUBCLASS"]|[2]|||||
|ONDE_MYSUBCLASS:MY_VALUE|M|A|H5T_FLOAT||1||||

The HDF5 file will contain an HDF5 group with attribute `ONDE_TYPE` (containing `["ONDE_MYCLASS","ONDE_MYSUBCLASS"]`), and with attributes `ONDE_MYCLASS:COORDINATES`, `ONDE_MYCLASS:DIMENSION`, `ONDE_MYCLASS:ONDE_MYSUBCLASS:MY_VALUE` and with an HDF5 dataset named `ONDE_MYCLASS:TABLE`.

#### Representation of an accessory class in the csv table

In the csv file, an accessory class is defined in the same way as any other class, with the exception that it has a `ONDE:ACCESSORY_CLASS` attribute refering to its own name.
Another class will refer to this accessory class to aggregate its content through an `ONDE:TYPE_TAGS` attribute that contains a list of accessory classes.

Let `ONDE_MY_ACCESSORY_CLASS` be an accessory class having a string attribute `MY_STRING` aggregated in `ONDE_MYCLASS`.
The csv table will look like this:

|Class|Name|M/O|D/A|Type|Content|Dimensions|Min|Max|Accessory Class|
|---|---|---|---|---|---|---|---|---|---|
|ONDE_MYCLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MYCLASS"]|[1]|||||
|ONDE_MYCLASS|ONDE:TYPE_TAGS|M|A|H5T_STRING|["ONDE_MY_ACCESSORY_CLASS"]|[1]|||||
|ONDE_MYCLASS|ONDE_MYCLASS:COORDINATES|O|A|H5T_FLOAT||[3]||||
|ONDE_MYCLASS|ONDE_MYCLASS:DIMENSION|M|A|H5T_INTEGER||1|1|||
|ONDE_MYCLASS|ONDE_MYCLASS:TABLE|M|D|H5T_FLOAT||[ONDE_MYCLASS:DIMENSION,3]||||
|ONDE_MY_ACCESSORY_CLASS|ONDE:TYPE|M|A|H5T_STRING|["ONDE_MY_ACCESSORY_CLASS"]|[1]|||True|
|ONDE_MY_ACCESSORY_CLASS|ONDE:ACCESSORY_CLASS|M|A|H5T_STRING|"ONDE_MY_ACCESSORY_CLASS"|1|||||
|ONDE_MY_ACCESSORY_CLASS|ONDE_MY_ACCESSORY_CLASS:MY_STRING|M|A|H5T_STRING||1||||

The HDF5 file will contain an HDF group with attribute `ONDE_TYPE` (containing `['ONDE_MYCLASS']`) and with attributes `ONDE_MYCLASS:COORDINATES`, `ONDE_MYCLASS:DIMENSION`, `ONDE_MY_ACCESSORY_CLASS:MY_STRING` and with an HDF5 dataset named `ONDE_MYCLASS:TABLE`.