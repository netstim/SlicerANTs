# SlicerANTs

This extension implements [ANTs](https://github.com/ANTsX/ANTs) Registration into [Slicer](https://github.com/Slicer/Slicer)

## Modules

- [antsRegistration](antsRegistration/): provides an interface for doing registration with ANTs. Generates parameters passed to the antsCommand module.
- antsCommand: cli module to run ANTs executables.

## (Basic) Tutorial

- Load volumes to register (for example MRBrainTumor1 and MRBrainTumor2 from Sample Data module)
- Set the registration stages you want to perform using the **+** and **-** buttons and the drop down menu. For this example we'll keep the Rigid stage only.
- Each stage has settings described in the Settings Format panel.
- Each stage has its own properties, including Metrics, Levels and Masking. Let's keep the defaults for now and put MRBrainTumor1 as fixed and MRBrainTumor2 as moving using a Mutual Information metric. This will register MRBrainTumor2 to MRBrainTumor1.
- Under outputs, select a Transformed Volume Node. The output of the registration will be placed here.
- Click the Run Registration button and wait for the registration to finish.

## Example

The following is an example CT to MR rigid registration.

**Pre** <div align="right">**Post**

<div align="left">

![Example](Documentation/MR-CT_example.png?raw=true)

## References

- [ANTs](https://pubmed.ncbi.nlm.nih.gov/?term=%22Tustison+N%22+AND+%22Avants+B%22)
- [Slicer](https://www.slicer.org/wiki/CitingSlicer)