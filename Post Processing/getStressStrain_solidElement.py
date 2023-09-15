from PyMpc import *
from PyMpc import MpcOdbVirtualResult as vr

# USER INPUT
database_id = 1
component = 5  # from 0 to 6 (example 2 = Szz)

# clear terminal and get the stress.6 output for PDMY material model
App.clearTerminal()
doc = App.postDocument()
db = doc.getDatabase(database_id)

import math
from matplotlib import pyplot as plt

# BEGIN USER-PARAMETERS ==================================

# Database ID
db_id = 1

# Stage-id for mesh evaluation
stage_for_mesh = 2

# nodal result to extract
result_name = 'Reaction Force'
result_comp = 2


# some user-define function to test for a node
def test_node_id(node):
    return node.id == 100


def test_node_in_radius(node):
    x = 0.0
    y = 0.0
    z = 0.0
    radius = 10.0
    dist = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2 + (node.z - z) ** 2)
    return dist <= radius


def test_node_in_radius_2d(node):
    x = 0.0
    y = 0.0
    z = 0.0
    radius = 10.0
    dist = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
    return dist <= radius and (node.z - z) < 1.0e-10


# the user-define function to test for a node
use_this_node = test_node_in_radius_2d

# END USER-PARAMETERS ==================================


if db is None:
    raise Exception('Database {} is not available'.format(db_id))

# we need a mesh
# we need a random result to get the mesh
U = db.getNodalResult('Displacement', match=MpcOdb.Contains)
# create evaluation options
all_stages = db.getStageIDs()
if not stage_for_mesh in all_stages:
    raise Exception('Stage {} is not available'.format(stage_for_mesh))
all_steps = db.getStepIDs(stage_for_mesh)
if len(all_steps) == 0:
    raise Exception('No steps available in Stage {}'.format(stage_for_mesh))
opt = MpcOdbVirtualResultEvaluationOptions()
opt.stage = stage_for_mesh
opt.step = all_steps[0]
# evaluate the result
field = U.evaluate(opt)
mesh = field.mesh




refcoOrd = [12.5,12.5,-7]       # Reference CoOrdinates in X, Y and Z format
Tolerances = [1e-7, 1.5, 5]      #Toleraces: Starting tolerance for check, tolerance increment, and maximum tolerance

def getMidPt(element_obj):
    CoOrdinates = [[], [], []]
    for node in element_obj.nodes:
        X = node.position.x
        Y = node.position.y
        Z = node.position.z
        CoOrdinates[0].append(X)
        CoOrdinates[1].append(Y)
        CoOrdinates[2].append(Z)

    MidPoint = [sum(CoOrdinates[0])/len(CoOrdinates[0]), sum(CoOrdinates[1])/len(CoOrdinates[1]), sum(CoOrdinates[2])/len(CoOrdinates[2])]
    return MidPoint


def CheckValue(ele):
    def ToleranceCheck(ref, tolerance, checkvalue):
        a = ref + tolerance
        b = ref - tolerance

        if checkvalue >= a and checkvalue <= b:
            return True
        elif checkvalue <= a and checkvalue >= b:
            return True
        else:
            return False

    MidPoint = getMidPt(ele)

    tolerance = Tolerances[0]
    while tolerance <= Tolerances[2]:
        Values = []
        for index, point in enumerate(MidPoint):
            value = ToleranceCheck(refcoOrd[index], tolerance, point)
            Values.append(value)

        if len(set(Values)) == 1 and Values[0] == True:
            return True

        tolerance = tolerance * Tolerances[1]






Elements = []
for ele_id, ele in mesh.elements.items():
    if CheckValue(ele):
        Elements.append(ele_id)
        break




strain = db.getElementalResult('strain (Volumes; 6', match=MpcOdb.Contains)
stress = db.getElementalResult('stress (Volumes; 6', match=MpcOdb.Contains)

# find all selected elements
elements = []
selection = doc.scene.plotSelection
for plot_id, selection_data in selection.items():
    for i in selection_data.info.elements:
        elements.append(i)
elements = list(set(elements))
elements = Elements

# make an evaluation option
opt = MpcOdbVirtualResultEvaluationOptions()

# X-Y data for each element
XY_lists = [([], []) for i in range(len(elements))]

# parse all stages and all steps
for stage_id in db.getStageIDs():
    all_steps = db.getStepIDs(stage_id)
    for step_id in all_steps:
        opt.stage = stage_id
        opt.step = step_id
        # evaluate the field
        stress_field = stress.evaluate(opt)
        strain_field = strain.evaluate(opt)
        # process each element
        for i in range(len(elements)):
            ele_id = elements[i]
            x, y = XY_lists[i]
            row = MpcOdbResultField.gauss(ele_id, 0)
            ix = strain_field[row, component]
            iy = stress_field[row, component]
            print(ele_id, ix, iy)
            x.append(ix)
            y.append(iy)

# make charts for each selected element
for i in range(len(elements)):
    # element data
    ele_id = elements[i]
    x, y = XY_lists[i]

    # create a new chart data
    cdata = MpcChartData()
    cdata.id = doc.genNextIdForChartData()
    cdata.name = "Element {} - Compoenent {}".format(ele_id, component)
    cdata.xLabel = strain.componentLabels()[component]
    cdata.yLabel = stress.componentLabels()[component]
    cdata.x = x
    cdata.y = y
    doc.addChartData(cdata)

    # create a chart data item to put in the chart
    cdata_item = MpcChartDataGraphicItem(cdata)
    cdata_item.color = MpcQColor(255, 150, 0, 255)
    cdata_item.thickness = 1.5
    cdata_item.penStyle = MpcQPenStyle.SolidLine

    # create a new chart
    chart = MpcChart()
    chart.id = doc.genNextIdForChart()
    chart.name = "Element {} - Compoenent {}".format(ele_id, component)
    chart.addItem(cdata_item)
    doc.addChart(chart)

# done
doc.commitChanges()
doc.dirty = True
print('Done')

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
