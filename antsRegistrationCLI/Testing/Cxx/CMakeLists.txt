
#-----------------------------------------------------------------------------
get_filename_component(BASELINE ${CMAKE_CURRENT_SOURCE_DIR}/../../Data/Baseline ABSOLUTE)
get_filename_component(INPUT ${CMAKE_CURRENT_SOURCE_DIR}/../../Data/Input ABSOLUTE)
set(TEMP "${CMAKE_BINARY_DIR}/Testing/Temporary")

set(CLP ${MODULE_NAME})

#-----------------------------------------------------------------------------
ctk_add_executable_utf8(${CLP}Test ${CLP}Test.cxx)
target_link_libraries(${CLP}Test ${CLP}Lib ${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES})
set_target_properties(${CLP}Test PROPERTIES LABELS ${CLP})
set_target_properties(${CLP}Test PROPERTIES FOLDER ${${CLP}_TARGETS_FOLDER})

#-----------------------------------------------------------------------------
set(testname ${CLP}Test)
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
  --compare "${BASELINE}/${CLP}Test.nii.gz"
  "${TEMP}/${CLP}Test.nrrd"
  --compareIntensityTolerance 20000
  ModuleEntryPoint
  --antsCommand "--dimensionality 3 --use-histogram-matching 0 --winsorize-image-intensities [0.005,0.995] --float $useFloat --verbose 1 --interpolation Linear --output [$outputBase,$outputVolume] --write-composite-transform 1 --collapse-output-transforms 1 --transform Rigid[0.1] --metric MI[$inputVolume01,$inputVolume02,1,32,Random,0.25] --convergence [1000x500x250x100x0,1e-6,10] --smoothing-sigmas 4x3x2x1x1vox --shrink-factors 12x8x4x2x1 --use-estimate-learning-rate-once"
  --inputVolume01 "${INPUT}/MRBrainTumor1.nii.gz"
  --inputVolume02 "${INPUT}/MRBrainTumor2.nii.gz"
  --outputVolume "${TEMP}/${CLP}Test.nrrd"
  --useFloat
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

