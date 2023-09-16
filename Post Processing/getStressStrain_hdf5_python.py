import numpy as np
import h5py
import matplotlib.pyplot as plt



def getNodeCoOrdinates(Node):
    with h5py.File(filepath, "r") as hdf:
        ls = list(hdf.keys())
        datastage = hdf.get(ls[1])
        modelinfo = datastage.get(list(datastage.keys())[0])
        nodes = modelinfo.get(list(modelinfo.keys())[0])
        nodesID =  np.array(nodes.get(list(nodes.keys())[0]))
        nodesCoOrd = np.array(nodes.get(list(nodes.keys())[1]))

        nodeAbsIndex = np.where(nodesID == Node)
        row_index = nodeAbsIndex[0][0] + 1

        CoOrdinates = nodesCoOrd[nodeAbsIndex]
        return CoOrdinates[0]
def getEleNodes(ElementID):
    with h5py.File(filepath, "r") as hdf:
        ls = list(hdf.keys())
        datastage = hdf.get(ls[1])
        modelinfo = datastage.get(list(datastage.keys())[0])
        nodes = modelinfo.get(list(modelinfo.keys())[0])
        elements = modelinfo.get(list(modelinfo.keys())[1])

        sspbrick = np.array(elements.get(list(elements.keys())[1]))
        sspbrickid = sspbrick[:, 0]
        sspbricknode = sspbrick[:, 1:9]

        absIndex = np.where(sspbrickid == ElementID)
        row_index = absIndex[0][0]
        Nodes = sspbricknode[absIndex][0]

        return absIndex, Nodes
def getMidPt(ElementID):
    absIndex, Nodes = getEleNodes(ElementID)
    CoOrdinates = [[], [], []]
    for node in Nodes:
        CoOrd = getNodeCoOrdinates(node)
        X = CoOrd[0]
        Y = CoOrd[1]
        Z = CoOrd[2]
        CoOrdinates[0].append(X)
        CoOrdinates[1].append(Y)
        CoOrdinates[2].append(Z)

    MidPoint = [sum(CoOrdinates[0]) / len(CoOrdinates[0]), sum(CoOrdinates[1]) / len(CoOrdinates[1]),
                sum(CoOrdinates[2]) / len(CoOrdinates[2])]
    return MidPoint
def get_EleIds(key):
    with h5py.File(filepath, "r") as hdf:
        datastage = hdf.get('MODEL_STAGE[2]')
        results = datastage.get('RESULTS')
        elements = results.get('ON_ELEMENTS')
        stress = elements.get(key)
        stressSoil = stress.get("121-SSPbrick[400:0:1]")

        # < KeysViewHDF5['META', 'ID', 'DATA'] >
        ids = np.array(stressSoil.get("ID"))[:,0]
        return ids

def get_Elerow(key, element_id):
    with h5py.File(filepath, "r") as hdf:
        datastage = hdf.get('MODEL_STAGE[2]')
        results = datastage.get('RESULTS')
        elements = results.get('ON_ELEMENTS')
        stress = elements.get(key)
        stressSoil = stress.get("121-SSPbrick[400:0:1]")

        # < KeysViewHDF5['META', 'ID', 'DATA'] >
        ids = np.array(stressSoil.get("ID"))[:, 0]
        absrow = np.where(ids == element_id)[0][0]

        return absrow


def FactorReturn(a , b):
    Factor = abs(a - b)
    if Factor == 0:
        Factor = 1
    return  Factor



refcoOrd = [12.5, 12.5, -7]  # Reference CoOrdinates in X, Y and Z format
Tolerances = [0.5, 2, 5]  # Toleraces: Starting tolerance for check, tolerance increment, and maximum tolerance
component = 5
filepath = r"D:\Final Analysis\Extras\Nonlinear Analysis\test\L4_Hard_San Fernando.part-0.mpco"




#Get Element IDS
# IDS = get_EleIds("stress")
#
# #Get ids and their mid point co ordinates
# id_CoOrd = {}
# for id in IDS:
#     id_CoOrd[id] =  getMidPt(id)
#
# #Get nearest node with reference type
# Factors = []
#
# for key, CoOrdinates in id_CoOrd.items():
#     Factor = FactorReturn(CoOrdinates[0] , refcoOrd[0]) * FactorReturn(CoOrdinates[1] , refcoOrd[1]) * FactorReturn(CoOrdinates[2] , refcoOrd[2])
#     Factors.append(Factor)

# Index = Factors.index(min(Factors))
# keylist = list(id_CoOrd.keys())
# Element = keylist[Index]
# print(Element)
Element = 8949
#Stress
absrow = get_Elerow("stress", Element)
stresses = np.empty(0)
strains = np.empty(0)
with h5py.File(filepath, "r") as hdf:
    datastage = hdf.get('MODEL_STAGE[2]')
    results = datastage.get('RESULTS')
    elements = results.get('ON_ELEMENTS')




    stress = elements.get("stress")
    stressSoil = stress.get("121-SSPbrick[400:0:1]")
    stress_data = stressSoil.get("DATA")
    keys = list(stress_data.keys())
    for data_index in keys:
        datavalues = np.array(stress_data.get(data_index))
        value = datavalues[absrow, component]
        stresses = np.append(stresses, value)


    stress = elements.get("strain")
    stressSoil = stress.get("121-SSPbrick[400:0:1]")
    stress_data = stressSoil.get("DATA")
    keys = list(stress_data.keys())
    for data_index in keys:
        datavalues = np.array(stress_data.get(data_index))
        value = datavalues[absrow, component]
        strains = np.append(strains, value)





# Create a basic line plot
plt.plot(strains, stresses)

# Add labels and a title
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Simple Plot')

# Show the plot
plt.show()


