

class antsBase:
  def __init__(self):
    self.details = ''
    self.settingsFormat = ''
    self.settingsDefault = ''

  @classmethod
  def getSubClassesNames(cls):
    return [subcls.__name__ for subcls in cls.__subclasses__()]

  @classmethod
  def getSubClassByName(cls, name):
    for subcls in cls.__subclasses__():
      if subcls.__name__ == name:
        return subcls()

class antsMetric(antsBase):
  def __init__(self):
    super().__init__()
    

class CC(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'ANTS neighborhood cross correlation'


class MI(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'Mutual Information'
    self.settingsDefault = '1.25,32,Random,0.25'


class Mattes(antsMetric):
  def __init__(self):
    super().__init__()




MetricsNameInfo = {\
  'CC': {\
    'Details': 'ANTS neighborhood cross correlation',\
    'Format': 'metricWeight, radius, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'MI': {\
    'Details': 'Mutual Information',\
    'Format': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': '1.25,32,Random,0.25'},\
  'Mattes': {\
    'Details': '',\
    'Format': 'metricWeight, numberOfBins, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'MeanSquares': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'Demons': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'GC': {\
    'Details': 'Global Correlation',\
    'Format': 'metricWeight, radius=NA, <samplingStrategy={None,Regular,Random}>, <samplingPercentage=[0,1]>',\
    'Default': ''},\
  'ICP': {\
    'Details': 'Euclidean',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>',\
    'Default': ''},\
  'PSE': {\
    'Details': 'Point-set expectation',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>,<pointSetSigma=1>, <kNeighborhood=50>',\
    'Default': ''},\
  'JHCT': {\
    'Details': 'Jensen-Havrda-Charvet-Tsallis',\
    'Format': 'metricWeight, <samplingPercentage=[0,1]>, <boundaryPointsOnly=0>, <pointSetSigma=1>, <kNeighborhood=50>, <alpha=1.1>, <useAnisotropicCovariances=1>',\
    'Default': ''}\
}





class antsTransform(antsBase):
  def __init__(self):
    super().__init__()
    self.settingsDefault = '0.1'


class Rigid(antsTransform):
  def __init__(self):
    super().__init__()

class Affine(antsTransform):
  def __init__(self):
    super().__init__()










TransformsNameInfo = {\
  'Rigid': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': '0.1'},\
  'Affine': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'CompositeAffine': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'Similarity': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'Translation': {\
    'Details': '',\
    'Format': 'gradientStep',\
    'Default': ''},\
  'BSpline': {\
    'Details': '',\
    'Format': 'gradientStep, meshSizeAtBaseLevel',\
    'Default': ''},\
  'GaussianDisplacementField': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldVarianceInVoxelSpace, totalFieldVarianceInVoxelSpace',\
    'Default': ''},\
  'BSplineDisplacementField': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
    'Default': ''},\
  'TimeVaryingVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, numberOfTimeIndices, updateFieldVarianceInVoxelSpace, updateFieldTimeVariance, totalFieldVarianceInVoxelSpace, totalFieldTimeVariance',\
    'Default': ''},\
  'TimeVaryingBSplineVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, velocityFieldMeshSize, <numberOfTimePointSamples=4>, <splineOrder=3>',\
    'Default': ''},\
  'SyN': {\
    'Details': '',\
    'Format': 'gradientStep, <updateFieldVarianceInVoxelSpace= 3>, <totalFieldVarianceInVoxelSpace=0>',\
    'Default': ''},\
  'BSplineSyN': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <totalFieldMeshSizeAtBaseLevel=0>, <splineOrder=3>',\
    'Default': ''},\
  'Exponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldVarianceInVoxelSpace, velocityFieldVarianceInVoxelSpace, <numberOfIntegrationSteps>',\
    'Default': ''},\
  'BSplineExponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, <velocityFieldMeshSizeAtBaseLevel=0>, <numberOfIntegrationSteps>, <splineOrder=3>',\
    'Default': ''}\
}