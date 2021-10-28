#include "antsApplyTransformsCLICLP.h"

#include "antsApplyTransforms.h"

#include <iostream>
#include <vector>
#include <string>

namespace
{
  void printAntsApplyTransformsCommand(std::vector< std::string > * command_line_args)
  {
    std::cout << "antsApplyTransforms ";
    for(const auto& cla: *command_line_args) {
      std::cout << cla << " ";
    }
    std::cout << std::endl;
  }
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  if (referenceVolume.empty())
  {
    std::cout << "ERROR: missing reference volume" << std::endl;
    return EXIT_FAILURE;
  }

  if (transform.empty() && transformFile.empty())
  {
    std::cout << "ERROR: missing transform" << std::endl;
    return EXIT_FAILURE;
  }

  if (!transform.empty() && !transformFile.empty())
  {
    std::cout << "ERROR: specify either a transform node or a transform file." << std::endl;
    return EXIT_FAILURE;
  }

  if (!outputDisplacementField.empty() && !outputVolume.empty())
  {
    std::cout << "ERROR: specify either an output volume or an output transform (not both)" << std::endl;
    return EXIT_FAILURE;
  }

  const char * const * const ptr = &argv[1] ;
  std::vector< std::string > command_line_args( ptr , ptr+argc-1 );

  for(std::size_t i = 0; i < command_line_args.size(); i=i+2) {
    if (command_line_args[i].compare("--outputDisplacementField") == 0){
      command_line_args[i] = "--output";
      command_line_args[i+1] = "[" + command_line_args[i+1] + ",1]";
    }
    else if (command_line_args[i].compare("--transformFile") == 0){
      command_line_args[i] = "--transform";
    }
  }

  command_line_args.push_back("--v");
  command_line_args.push_back("1");

  printAntsApplyTransformsCommand(&command_line_args);

  std::ostream * command_stream = &std::cout;

  return ants::antsApplyTransforms( command_line_args , command_stream ) ;
}
