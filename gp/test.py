import numpy as np
def binSplitDataSet(dataSet,feature,value):
    mat0 = dataSet[np.nonzero(dataSet[:,feature] > value)[0],:][0]
    mat1 = dataSet[np.nonzero(dataSet[:,feature] <= value)[0],:][0]
    return mat0,mat1

testMat=np.mat( np.eye(4))
#mat0,mat1=binSplitDataSet(testMat,1,0.5)
#print(testMat)
print(testMat[0])
print(testMat[0])