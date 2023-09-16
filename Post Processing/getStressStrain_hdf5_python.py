
import numpy as np
import h5py


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
        row_index = absIndex[0][0] + 1
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

def row_number(ElementID):
    pass


refcoOrd = [12.5, 12.5, -7]  # Reference CoOrdinates in X, Y and Z format
Tolerances = [0.5, 2, 5]  # Toleraces: Starting tolerance for check, tolerance increment, and maximum tolerance
component = 5
filepath = r"D:\Final Analysis\Extras\Nonlinear Analysis\test\L4_Hard_San Fernando.part-0.mpco"

def CheckValue(ele_ids):
    def ToleranceCheck(ref, tolerance, checkvalue):
        a = ref + tolerance
        b = ref - tolerance
        ab_mid = (a+b)/2
        Factor = 0

        if checkvalue >= a and checkvalue <= b:
            Factor = abs(ab_mid - checkvalue)/abs(a-b)
            return True, Factor
        elif checkvalue <= a and checkvalue >= b:
            Factor = abs(ab_mid - checkvalue)/abs(a-b)
            return True, Factor

        else:
            return False, Factor

    FinalFactor = []
    Elements = []
    tolerance = Tolerances[0]
    while tolerance <= Tolerances[2]:
        for ele_id in ele_ids:
            MidPoint = getMidPt(ele_id)
            print(ele_id, Elements, tolerance)

            Values = []
            Factors = []
            for index, point in enumerate(MidPoint):
                value, Factor = ToleranceCheck(refcoOrd[index], tolerance, point)
                Values.append(value)
                Factors.append(Factor)

            if len(set(Values)) == 1 and Values[0] == True:
                Elements.append(ele_id)
                finalVal = 1
                for val in Factors:
                    finalVal = finalVal * val
                FinalFactor.append(finalVal * tolerance)

        if len(Elements) >=1:
            break


        tolerance = tolerance * Tolerances[1]
    return Elements[FinalFactor.index( min(FinalFactor))]



with h5py.File(filepath, "r") as hdf:
    ls = list(hdf.keys())
    datastage = hdf.get('MODEL_STAGE[2]')
    results = datastage.get('RESULTS')
    elements = results.get('ON_ELEMENTS')
    stress = elements.get('stress')
    stressSoil = stress.get("121-SSPbrick[400:0:1]")

    # < KeysViewHDF5['META', 'ID', 'DATA'] >
    ids = np.array(stressSoil.get("ID"))
    stress_data = stressSoil.get("DATA")
    keys = list(stress_data.keys())


    # Element = CheckValue(ids)
    Element = 8560
    Element_ID = Element
    print(Element)

    absElementIndex = np.where(ids == Element_ID)
    stresses = np.empty(0)

    for data_index in keys:
        datavalues = np.array(stress_data.get(data_index))
        value = datavalues[absElementIndex, component]
        print(value,absElementIndex)
        print(value[0][0])

        stresses = np.append(stresses, value[0][0])


    strains = np.empty(0)
    elements = results.get('ON_ELEMENTS')
    strain = elements.get('strain')
    strainSoil = strain.get("121-SSPbrick[400:0:1]")
    ids = np.array(strainSoil.get("ID"))
    strain_data = strainSoil.get("DATA")
    keys = list(strain_data.keys())
    absElementIndex = np.where(ids == Element_ID)
    print(absElementIndex)
    strains = np.empty(0)
    for data_index in keys:
        datavalues = np.array(strain_data.get(data_index))
        value = datavalues[absElementIndex, component]
        strains = np.append(strains, value[0][0])



with open('data.txt', 'w') as file:
    # Write the headings
    file.write("Stress\tStrain\n")

    # Write the data
    for i in range(len(stresses)):
        file.write(f"{stresses[i]}\t{strains[i]}\n")

print("Data written to 'data.txt'")




print(stresses, strains)
import numpy as np
import matplotlib.pyplot as plt

# Sample data (replace these with your own arrays)

# Create a basic line plot
plt.plot(strains, stresses)

# Add labels and a title
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Simple Plot')

# Show the plot
plt.show()


