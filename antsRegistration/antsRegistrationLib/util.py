

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

#
# Metric
#

class antsMetric(antsBase):
  def __init__(self):
    super().__init__()
    
class CC(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'ANTS neighborhood cross correlation'
    self.settingsFormat = '<b>metricWeight</b>, <b>radius</b>, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,4,Random,0.25'

class MI(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'Mutual Information'
    self.settingsFormat = '<b>metricWeight</b>, <b>numberOfBins</b>, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,32,Random,0.25'

class Mattes(antsMetric):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>metricWeight</b>, <b>numberOfBins</b>, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,32,Random,0.25'

class MeanSquares(antsMetric):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>metricWeight</b>, <b>radius</b>=NA, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,NA,Random,0.25'

class Demons(antsMetric):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>metricWeight</b>, <b>radius</b>=NA, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,NA,Random,0.25'

class GC(antsMetric):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>metricWeight</b>, <b>radius</b>=NA, &lt;<b>samplingStrategy</b>={None,Regular,Random}&gt;, &lt;<b>samplingPercentage</b>=[0,1]&gt;'
    self.settingsDefault = '1,NA,Random,0.25'

class ICP(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'Euclidean'
    self.settingsFormat = '<b>metricWeight</b>, &lt;<b>samplingPercentage</b>=[0,1]&gt;, &lt;<b>boundaryPointsOnly</b>=0&gt;'
    self.settingsDefault = '1,0.25,0'

class PSE(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'Point-set expectation'
    self.settingsFormat = '<b>metricWeight</b>, &lt;<b>samplingPercentage</b>=[0,1]&gt;, &lt;<b>boundaryPointsOnly</b>=0&gt;,&lt;<b>pointSetSigma</b>=1&gt;, &lt;<b>kNeighborhood</b>=50&gt;'
    self.settingsDefault = '1,0.25,0,1,50'

class JHCT(antsMetric):
  def __init__(self):
    super().__init__()
    self.details = 'Jensen-Havrda-Charvet-Tsallis'
    self.settingsFormat = '<b>metricWeight</b>, &lt;<b>samplingPercentage</b>=[0,1]&gt;, &lt;<b>boundaryPointsOnly</b>=0&gt;, &lt;<b>pointSetSigma</b>=1&gt;, &lt;<b>kNeighborhood</b>=50&gt;, &lt;<b>alpha</b>=1.1&gt;, &lt;<b>useAnisotropicCovariances</b>=1&gt;'
    self.settingsDefault = '1,0.25,0,1,50,1.1,1'

#
# Transforms
#

class antsTransform(antsBase):
  def __init__(self):
    super().__init__()
    self.details = ''
    self.settingsFormat = '<b>gradientStep</b>'
    self.settingsDefault = '0.1'

class Rigid(antsTransform):
  def __init__(self):
    super().__init__()

class Affine(antsTransform):
  def __init__(self):
    super().__init__()

class CompositeAffine(antsTransform):
  def __init__(self):
    super().__init__()

class Similarity(antsTransform):
  def __init__(self):
    super().__init__()

class Translation(antsTransform):
  def __init__(self):
    super().__init__()

class BSpline(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>meshSizeAtBaseLevel</b>'
    self.settingsDefault = '0.1,8'

class GaussianDisplacementField(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>updateFieldVarianceInVoxelSpace</b>, <b>totalFieldVarianceInVoxelSpace</b>'
    self.settingsDefault = '0.1,3,0'

class BSplineDisplacementField(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>updateFieldMeshSizeAtBaseLevel</b>, &lt;<b>totalFieldMeshSizeAtBaseLevel</b>=0&gt;, &lt;<b>splineOrder</b>=3&gt;'
    self.settingsDefault = '0.1,26,0,3'

class TimeVaryingVelocityField(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>numberOfTimeIndices</b>, <b>updateFieldVarianceInVoxelSpace</b>, <b>updateFieldTimeVariance</b>, <b>totalFieldVarianceInVoxelSpace</b>, <b>totalFieldTimeVariance</b>'
    self.settingsDefault = ''

class TimeVaryingBSplineVelocityField(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>velocityFieldMeshSize</b>, &lt;<b>numberOfTimePointSamples</b>=4&gt;, &lt;<b>splineOrder</b>=3&gt;'
    self.settingsDefault = ''

class SyN(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, &lt;<b>updateFieldVarianceInVoxelSpace</b>= 3&gt;, &lt;<b>totalFieldVarianceInVoxelSpace</b>=0&gt;'
    self.settingsDefault = '0.1,3,0'

class BSplineSyN(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>updateFieldMeshSizeAtBaseLevel</b>, &lt;<b>totalFieldMeshSizeAtBaseLevel</b>=0&gt;, &lt;<b>splineOrder</b>=3&gt;'
    self.settingsDefault = '0.1,26,0,3'

class Exponential(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>updateFieldVarianceInVoxelSpace</b>, <b>velocityFieldVarianceInVoxelSpace</b>, &lt;<b>numberOfIntegrationSteps</b>&gt;'
    self.settingsDefault = ''

class Exponential(antsTransform):
  def __init__(self):
    super().__init__()
    self.settingsFormat = '<b>gradientStep</b>, <b>updateFieldMeshSizeAtBaseLevel</b>, &lt;<b>velocityFieldMeshSizeAtBaseLevel</b>=0&gt;, &lt;<b>numberOfIntegrationSteps</b>&gt;, &lt;<b>splineOrder</b>=3&gt;'
    self.settingsDefault = ''
