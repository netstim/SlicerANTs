#include "antsRegistrationCLICLP.h"

#include "antsRegistration.h"

#include <iostream>
#include <vector>
#include <string>

namespace
{

}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  const char * const * const ptr = &argv[1] ;
  // std::vector< std::string > command_line_args( ptr , ptr+argc-1 );
  std::vector< std::string > command_line_args;

  command_line_args.push_back("--help");

  std::ostream * command_stream = &std::cout;

  return ants::antsRegistration( command_line_args , command_stream ) ;
}
