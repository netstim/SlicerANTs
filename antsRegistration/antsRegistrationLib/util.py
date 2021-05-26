

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
    self.settingsFormat = 'metricWeight, radius, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;'


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
    'Format': 'metricWeight, radius, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': ''},\
  'MI': {\
    'Details': 'Mutual Information',\
    'Format': 'metricWeight, numberOfBins, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': '1.25,32,Random,0.25'},\
  'Mattes': {\
    'Details': '',\
    'Format': 'metricWeight, numberOfBins, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': ''},\
  'MeanSquares': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': ''},\
  'Demons': {\
    'Details': '',\
    'Format': 'metricWeight, radius=NA, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': ''},\
  'GC': {\
    'Details': 'Global Correlation',\
    'Format': 'metricWeight, radius=NA, &lt;samplingStrategy={None,Regular,Random}&gt;, &lt;samplingPercentage=[0,1]&gt;',\
    'Default': ''},\
  'ICP': {\
    'Details': 'Euclidean',\
    'Format': 'metricWeight, &lt;samplingPercentage=[0,1]&gt;, &lt;boundaryPointsOnly=0&gt;',\
    'Default': ''},\
  'PSE': {\
    'Details': 'Point-set expectation',\
    'Format': 'metricWeight, &lt;samplingPercentage=[0,1]&gt;, &lt;boundaryPointsOnly=0&gt;,&lt;pointSetSigma=1&gt;, &lt;kNeighborhood=50&gt;',\
    'Default': ''},\
  'JHCT': {\
    'Details': 'Jensen-Havrda-Charvet-Tsallis',\
    'Format': 'metricWeight, &lt;samplingPercentage=[0,1]&gt;, &lt;boundaryPointsOnly=0&gt;, &lt;pointSetSigma=1&gt;, &lt;kNeighborhood=50&gt;, &lt;alpha=1.1&gt;, &lt;useAnisotropicCovariances=1&gt;',\
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
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, &lt;totalFieldMeshSizeAtBaseLevel=0&gt;, &lt;splineOrder=3&gt;',\
    'Default': ''},\
  'TimeVaryingVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, numberOfTimeIndices, updateFieldVarianceInVoxelSpace, updateFieldTimeVariance, totalFieldVarianceInVoxelSpace, totalFieldTimeVariance',\
    'Default': ''},\
  'TimeVaryingBSplineVelocityField': {\
    'Details': '',\
    'Format': 'gradientStep, velocityFieldMeshSize, &lt;numberOfTimePointSamples=4&gt;, &lt;splineOrder=3&gt;',\
    'Default': ''},\
  'SyN': {\
    'Details': '',\
    'Format': 'gradientStep, &lt;updateFieldVarianceInVoxelSpace= 3&gt;, &lt;totalFieldVarianceInVoxelSpace=0&gt;',\
    'Default': ''},\
  'BSplineSyN': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, &lt;totalFieldMeshSizeAtBaseLevel=0&gt;, &lt;splineOrder=3&gt;',\
    'Default': ''},\
  'Exponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldVarianceInVoxelSpace, velocityFieldVarianceInVoxelSpace, &lt;numberOfIntegrationSteps&gt;',\
    'Default': ''},\
  'BSplineExponential': {\
    'Details': '',\
    'Format': 'gradientStep, updateFieldMeshSizeAtBaseLevel, &lt;velocityFieldMeshSizeAtBaseLevel=0&gt;, &lt;numberOfIntegrationSteps&gt;, &lt;splineOrder=3&gt;',\
    'Default': ''}\
}