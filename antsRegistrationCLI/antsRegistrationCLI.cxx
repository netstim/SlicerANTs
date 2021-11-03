#include "antsRegistrationCLICLP.h"

#include "antsRegistration.h"
#include "antsApplyTransforms.h"

#include <iostream>
#include <vector>
#include <string>

namespace
{
  std::string getReferenceVolumeFromMetric(std::string metric)
  {
  int start = metric.find("[",0) + 1;
  return metric.substr(start, metric.find(",",0)-start);
  }
  void printAntsCommand(const char * antsExecutable, std::vector< std::string > * commandArguments)
  {
    std::cout << antsExecutable << " ";
    for(const auto& cla: *commandArguments) {
      std::cout << cla << " ";
    }
    std::cout << std::endl;
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
    outputCompositeTransform.replace(outputCompositeTransform.end()-5, outputCompositeTransform.end(), "Composite.h5");
  } else if (!useCompositeTransform && useDisplacementField){
    outputCompositeTransform = outputDisplacementField; 
    outputCompositeTransform.replace(outputCompositeTransform.end()-7, outputCompositeTransform.end(), "Composite.h5");
  }

  std::string outputBase = outputCompositeTransform.substr(0, outputCompositeTransform.length()-12);

  // Init command line args
  std::string referenceVolume;
  std::vector<std::string> commandArguments;
  commandArguments.push_back("--output");
  if (useOutputVolume){
    commandArguments.push_back("[" + outputBase + "," + outputVolume + "]");
    referenceVolume = outputVolume;
  }else{
    commandArguments.push_back(outputBase);
  }

  // Put rest of command line args
  std::stringstream ss(antsCommand);
  std::string tmp;
  while(std::getline(ss, tmp, ' ')){
    if (referenceVolume.empty() && commandArguments.back().compare("--metric") == 0){
      referenceVolume = getReferenceVolumeFromMetric(tmp);
    }
    commandArguments.push_back(tmp);
  }

  std::ostream * commandStream = &std::cout;
  printAntsCommand("antsRegistration", &commandArguments);
  int antsFailed = ants::antsRegistration(commandArguments, commandStream);

  if (antsFailed==0 && useDisplacementField){
    std::cout << "<filter-comment>" << "ANTs Apply Transforms " << "</filter-comment>" << std::endl << std::flush;
    std::cout << "<filter-progress>" << 0.99 << "</filter-progress>" << std::endl << std::flush;
    std::cout << "<filter-stage-progress>" << 1.0 << "</filter-stage-progress>" << std::endl << std::flush;
    commandArguments.clear();
    commandArguments.push_back("--transform");
    commandArguments.push_back(outputCompositeTransform);
    commandArguments.push_back("--reference-image");
    commandArguments.push_back(referenceVolume);
    commandArguments.push_back("--output");
    commandArguments.push_back("[" + outputDisplacementField + ",1]");
    commandArguments.push_back("--float");
    commandArguments.push_back("1");
    commandArguments.push_back("--verbose");
    commandArguments.push_back("1");
    printAntsCommand("antsApplyTransforms", &commandArguments);
    antsFailed = ants::antsApplyTransforms(commandArguments, commandStream);
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
