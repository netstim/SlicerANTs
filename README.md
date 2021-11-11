*This repository is not maintained by ANTs developers*

# SlicerANTs

This extension implements [ANTs](https://github.com/ANTsX/ANTs) Registration into [Slicer](https://github.com/Slicer/Slicer)

## Dev

CDash: [SlicerPreview](https://slicer.cdash.org/index.php?project=SlicerPreview&filtercount=1&showfilters=1&field1=buildname&compare1=63&value1=SlicerANTs)
## Instalation

Install from the Slicer Extension Manager from nightly build.

## Modules

- antsRegistration: provides an interface for doing registration with ANTs. Generates parameters passed to the antsRegistrationCLI module.
- antsRegistrationCLI: cli module that runs the command generated from antsRegistration module.

## (Basic) Tutorial

- Load volumes to register (for example MRBrainTumor1 and MRBrainTumor2 from Sample Data module)
- Set MRBrainTumor1 in the fixed image selector, MRBrainTumor2 in the moving image selector and select Rigid from the Stages (Presets).
- Choose a Transformed Volume to specify the output
- Click the Run Registration button and wait for the registration to finish.

## Example

The following is an example CT to MR rigid registration.

**Pre** <div align="right">**Post**

<div align="left">

![Example](Documentation/MR-CT_example.png?raw=true)

## References

- [ANTs](https://pubmed.ncbi.nlm.nih.gov/?term=%22Tustison+N%22+AND+%22Avants+B%22)
- [Slicer](https://www.slicer.org/wiki/CitingSlicer)