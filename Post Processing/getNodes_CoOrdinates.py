from PyMpc import *
import math
from matplotlib import pyplot as plt

# BEGIN USER-PARAMETERS ==================================

# Database ID
db_id = 1

# Stage-id for mesh evaluation
stage_for_mesh = 1

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
	dist = math.sqrt((node.x-x)**2 + (node.y-y)**2 + (node.z-z)**2)
	return dist <= radius
def test_node_in_radius_2d(node):
	x = 0.0
	y = 0.0
	z = 0.0
	radius = 10.0
	dist = math.sqrt((node.x-x)**2 + (node.y-y)**2)
	return dist <= radius and (node.z-z)<1.0e-10
 # the user-define function to test for a node
use_this_node = test_node_in_radius_2d

# END USER-PARAMETERS ==================================

# clear terminal
App.clearTerminal()

# get document
doc = App.postDocument()
# get database
db = doc.getDatabase(db_id)
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

for ele_id, ele in mesh.elements.items():
    #print(ele_id)
    if ele_id>8377:
    	print(ele_id, ele.nodes[0].position.x, ele.nodes[0].position.y, ele.nodes[0].position.z)
    	#print(ele_id, ele.position.x, ele.position.y, ele.position.z)
