### Ascan datasets

Ascan datasets are the entry points for the description of data that is stored as time signals. The MFMC equivalent is '
SEQUENCE', and both names are allowed to ensure compatibility.

To allow continuity with existing HDF5 formats, the DATA field can be either a HDF5 dataset or a reference to a
dataset located in another part of the HDF5 structure.