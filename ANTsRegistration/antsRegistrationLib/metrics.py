
class antsMetric:
  def __init__(self):
    pass

class CC(antsMetric):
  def __init__(self):
    super().__init__()


class MI(antsMetric):
  def __init__(self):
    super().__init__()


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