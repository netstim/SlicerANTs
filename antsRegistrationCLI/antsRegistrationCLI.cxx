#include "antsRegistrationCLICLP.h"

#include "antsRegistration.h"
#include "antsApplyTransforms.h"

#include <iostream>
#include <vector>
#include <string>

namespace
{
  void replaceAll(std::string& str, const std::string& from, const std::string& to) {
    if(from.empty())
        return;
    size_t start_pos = 0;
    while((start_pos = str.find(from, start_pos)) != std::string::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length();
    }
  }
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  bool useCompositeTransform = !outputCompositeTransform.empty();
  bool useDisplacementField = !outputDisplacementField.empty();
  bool useOutputVolume = !outputVolume.empty();

  if (!useCompositeTransform && !useDisplacementField && !useOutputVolume){
    std::cout << "ERROR: specify an output." << std::endl;
  } else if (!useCompositeTransform && !useDisplacementField){
    outputCompositeTransform = outputVolume;
    replaceAll(outputCompositeTransform, ".nrrd", "Composite.h5");
  } else if (!useCompositeTransform && useDisplacementField){
    outputCompositeTransform = outputDisplacementField;
    replaceAll(outputCompositeTransform, ".nrrd", "Composite.h5");
  }
  std::string outputBase = outputCompositeTransform;
  replaceAll(outputBase, "Composite.h5", "");

  replaceAll(antsCommand, "$outputBase", outputBase);
  replaceAll(antsCommand, "$inputTransform", inputTransform);
  replaceAll(antsCommand, "$outputVolume", outputVolume);

  if (!inputVolume01.empty()){replaceAll(antsCommand, "$inputVolume01", inputVolume01);}
  if (!inputVolume02.empty()){replaceAll(antsCommand, "$inputVolume02", inputVolume02);}
  if (!inputVolume03.empty()){replaceAll(antsCommand, "$inputVolume03", inputVolume03);}
  if (!inputVolume04.empty()){replaceAll(antsCommand, "$inputVolume04", inputVolume04);}
  if (!inputVolume05.empty()){replaceAll(antsCommand, "$inputVolume05", inputVolume05);}
  if (!inputVolume06.empty()){replaceAll(antsCommand, "$inputVolume06", inputVolume06);}
  if (!inputVolume06.empty()){replaceAll(antsCommand, "$inputVolume06", inputVolume06);}
  if (!inputVolume07.empty()){replaceAll(antsCommand, "$inputVolume07", inputVolume07);}
  if (!inputVolume08.empty()){replaceAll(antsCommand, "$inputVolume08", inputVolume08);}
  if (!inputVolume09.empty()){replaceAll(antsCommand, "$inputVolume09", inputVolume09);}
  if (!inputVolume10.empty()){replaceAll(antsCommand, "$inputVolume10", inputVolume10);}
  if (!inputVolume11.empty()){replaceAll(antsCommand, "$inputVolume11", inputVolume11);}

  std::vector<std::string> commandArguments;
  std::stringstream ss(antsCommand);
  std::string tmp;
  while(std::getline(ss, tmp, ' ')){
    commandArguments.push_back(tmp);
  }

  int antsFailed = ants::antsRegistration(commandArguments, &std::cout);

  if (antsFailed==0 && useDisplacementField){
    std::cout << "<filter-comment>" << "ANTs Apply Transforms " << "</filter-comment>" << std::endl << std::flush;
    std::cout << "<filter-progress>" << 0.99 << "</filter-progress>" << std::endl << std::flush;
    std::cout << "<filter-stage-progress>" << 1.0 << "</filter-stage-progress>" << std::endl << std::flush;
    commandArguments.clear();
    commandArguments.push_back("--transform");
    commandArguments.push_back(outputCompositeTransform);
    commandArguments.push_back("--reference-image");
    commandArguments.push_back(inputVolume01);
    commandArguments.push_back("--output");
    commandArguments.push_back("[" + outputDisplacementField + ",1]");
    commandArguments.push_back("--float");
    commandArguments.push_back("1");
    commandArguments.push_back("--verbose");
    commandArguments.push_back("1");
    antsFailed = ants::antsApplyTransforms(commandArguments, &std::cout);
  }

  if (!useCompositeTransform){
    std::remove(outputCompositeTransform.c_str());
  }

  std::remove(outputBase.append("InverseComposite.h5").c_str());

  if (antsFailed){
     return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
