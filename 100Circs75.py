import os

import qiskit
from qiskit import IBMQ, execute
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.tools.visualization import plot_histogram,plot_state_city
from qiskit.tools.monitor import job_monitor
from qiskit import IBMQ

import time

import numpy as np
from numpy import random

from tempfile import TemporaryFile

#IBMQ.delete_accounts()
IBMQ.save_account('ce6ac405337d2ce0db0d8836372d276b4403b92d78a01e7270a411e53ebc8094a7f5a82ef266ddafbf26a5d5247b6f6d05c60bf076ad1e1cd43530c748df7280', overwrite=True)
IBMQ.load_account()

provider = IBMQ.get_provider(hub='ibm-q-ncsu', group='unm', project='crosstalk')
#provider = IBMQ.get_provider(hub='ibm-q', group='open', project='main')

#Some of these imports are unnecessary


idle_circuit = QuantumCircuit(1)
for i in range(30):
	idle_circuit.id(0)

#L is circuit depth
def CircuitBagGenerator(N_Circs,depth, l, Partitions):
	N_Partitions = len(Partitions)
	FullCircList = []
	FullGates = []
	for l in range(N_Partitions):      #Choose a partition: [[0],[1]] in the 2 qubit/2 region case
		RpP = len(Partitions[l])       #Regions/Partition
		tmpCircList1 = []
		tmpcirclist3Full = []
		for m in range(RpP):           #Choose a region "m"
			Gates = []
			N_QBit = len(Partitions[l][m])         #Qubits/Region
			tmpCircList2 = []
			for n in range(N_Circs):               #Generate 10 subcircuits
				GList = []
				subcirc = QuantumCircuit(1)
				for o in range(1):
					for p in range(int(depth)):         #May need depth/2 if we count idles as gates
						GateRand1 = np.random.randint(0,4) #Randomizes gate selection (I, X or Y)
						GList.append(GateRand1)
						if GateRand1 == 1:
							subcirc.rz(np.pi/2,o)
						elif GateRand1 == 2:
							subcirc.sx(o)
						elif GateRand1 == 3:
							subcirc.x(o)
						else:
							subcirc.id(0)
				Gates.append(GList)
				tmpCircList2.append(subcirc)
			FullGates.append(Gates)
			tmpCircList1.append(tmpCircList2)
		FullCircList.append(tmpCircList1)
	return FullCircList, FullGates

def BagGen(N_Circs,depth, l,Partitions,Gates):
	N_Partitions = len(Partitions)
	FullCircList = []
	for l in range(N_Partitions):      #Choose a partition: [[0],[1]] in the 2 qubit/2 region case
		RpP = len(Partitions[l])       #Regions/Partition
		tmpCircList1 = []
		tmpcirclist3Full = []
		for m in range(RpP):           #Choose a region "m"
			N_QBit = len(Partitions[l][m])         #Qubits/Region
			tmpCircList2 = []
			for n in range(N_Circs):               #Generate 10 subcircuits
				GList = []
				subcirc = QuantumCircuit(1)
				for p in range(int(depth)):
					GateRand1 = Gates[m][n][p]       
					if GateRand1 == 1:
						subcirc.rz(np.pi/2,0)
					elif GateRand1 == 2:
						subcirc.sx(0)
					elif GateRand1 == 3:
						subcirc.x(0)
					else:
						subcirc.id(0)
				tmpCircList2.append(subcirc)
			tmpCircList1.append(tmpCircList2)
		FullCircList.append(tmpCircList1)
	return FullCircList

#A list of 20 Circuits is returned in the case of 2 regions (with 10 selected per region)
#It is structured as such: [[Region 1 Setting Subcircuits], [Region 2 Setting Subcircuits]]
#Next we choose 5 of regions 2 subcircuits to match with each subcircuit in region 1 and vice versa

#Partitions should be formatted as such P = [[[0],[1],[2]], [[0,1],[2]], etc.]

def ContextGenerator(N_Circs,depth,p_idle,Partitions,CText,Gates,ReGen):
	#Generate the Full Circuits with Context
	if ReGen:
		Circuits = CircuitBagGenerator(N_Circs,depth, p_idle, Partitions)    #Run the above program
	else:
		Circuits = [BagGen(N_Circs,depth, p_idle, Partitions, Gates)]
		GateList = []
	N_Partitions = len(Partitions)
	circsFull = []
	circsFull2 = []
	ValsFull = []
	if ReGen:
		GateList = Circuits[1]
	for l in range(N_Partitions):      #Here and above, partitions won't apply to 2 qubits
		RpP = len(Partitions[l])       #Regions/Partition
		tmp = Partitions[l]
		circsRegtmp = []
		for m in range(RpP):
			circs10tmp = []
			CircVals = []
			for n in range(N_Circs):  #Choose a Subcircuit in region m
				Circs = Circuits[0][l]#Regions
				randTest = 2000
				if randTest < int(p_idle*1000.) and p_idle != 0.:
					circPart1 = idle_circuit
					circPart1.to_instruction()
				else:
					circPart1 = Circs[m][n]
					circPart1.to_instruction()
				circsContext = []
				CircVals2 = []
				for o in range(int(N_Circs/2)):           #Contexts per Region
					Circ_Tot = QuantumCircuit(5,2)
					Circ_Tot.append(circPart1,Partitions[l][m])
					for p in range(RpP):
						if (p!=m):
							#randInt = np.random.randint(1000)
							randInt = 10000
							if randInt < int(1000.) and p_idle != 0.:
								rand = 10
								tmpPart = idle_circuit
								tmpPart.to_instruction()
								Circ_Tot.append(tmpPart, Partitions[l][p])
							else:
								if ReGen:
									randContext = np.random.randint(0,10)
								else:
									randContext = CText[m][n][o]
								rand = randContext
								tmpPart = Circs[p][rand]               #define distinct circuits
								tmpPart.to_instruction()
								Circ_Tot.append(tmpPart,Partitions[l][p])
								#randVals.remove(rand)
					#for c in range(40):
					#    Circ_Tot.cx(1,0)
					#Circ_Tot.measure_all()
					circsFull2.append(Circ_Tot)
					circsContext.append(Circ_Tot)
					CircVals2.append(rand)
				circs10tmp.append(circsContext)
				CircVals.append(CircVals2)
			ValsFull.append(CircVals)
			circsRegtmp.append(circs10tmp)
		circsFull.append(circsRegtmp)
	return circsFull, circsFull2, ValsFull, GateList

#2 QBit system                                
Partitions = [[[0],[3]]]

#BE = provider.get_backend('ibmq_bogota')

def BatchedJobs(JN,QBits,DirName,Processor):
	BE = provider.get_backend('ibmq_' + Processor)
	try:
		os.mkdir(Processor + '/' + DirName)
		print("Directory created:", DirName)
	except FileExistsError:
		print("Directory already exists ya dingus!")

	Hundred_Circuits = []
	CTexts = []
	GateLists = []
	ReGen = True
	if ReGen==False:
		GateLists = np.load(Processor + '/' + DirName + '/' + 'GList'+ '.npy')
		CTexts = np.load(Processor + '/' + DirName + '/' + 'CTexts'+ '.npy')
	for i in range(JN):
		print(np.shape(GateLists))
		Circs2 = ContextGenerator(10,50,0.1,Partitions,[],[],ReGen)
		Hundred_Circuits.append(Circs2)
		if ReGen:
			CTexts.append(Circs2[2])
			GateLists.append(Circs2[3])
	if ReGen:
		np.save(Processor + '/' + DirName + '/' + 'CTexts'+ '.npy', CTexts)
		np.save(Processor + '/' + DirName + '/' + 'GList'+ '.npy', GateLists)

	print("fini")
	RomeCircsTot = []
	for ii in range(JN):
		RomeCircs = []
		print(ii)
		for i in range(100):
			N=Hundred_Circuits[ii][1][i]
			N.measure(QBits[0], 0)
			N.measure(QBits[1], 1)
			layout = [0,1,2,3,4]
			transN = qiskit.compiler.transpile(N, BE, optimization_level = 0)
			RomeCircs.append(transN)
		print(RomeCircs[5])
		RomeCircsTot.append(RomeCircs)
	ResultsTot = []
	Job_Ids = []
	for ii in range(JN):
		job1Circs = []
		job2Circs = []
		for i in range(50):
			job1Circs.append(RomeCircsTot[ii][i])
			job2Circs.append(RomeCircsTot[ii][i+50])

		job1 = execute(job1Circs, BE, shots = 8192, optimization_level=0)
		job2 = execute(job2Circs, BE, shots = 8192, optimization_level=0)

		print("job1.ID_" + str(ii))
		print(job1.job_id())
		print("job2.ID_" + str(ii))
		print(job2.job_id())
		Job_Ids.append([job1.job_id(),job2.job_id()])
	
	#Results2 = job2.result()
	print(Job_Ids)
	np.save(Processor + '/' + DirName + '/' + 'IDs.npy', Job_Ids)

BatchedJobs(100, [0,3],'4_3_[0,3]','quito')
#TestID = 601b47c0fe855e29f16fc29a
#Gates = np.load('rome' + '/' + '2_27_[0,1]' + '/' + 'GList.npy')
#print(len(Gates[0][0]))

def FrmtResults(JN,DirName,Processor):
	BE = provider.get_backend('ibmq_' + Processor)
	ids = np.load(Processor + '/' + DirName + '/' + 'IDs.npy')
	cList = np.load(Processor + '/' + DirName + '/' + 'CTexts.npy')
	print("Here")
	print(len(cList))
	print(cList)
	print(ids)
	print(ids[0][0])
	for ll in range(JN):
		print(cList[ll])
		try:
			job1 = BE.retrieve_job(str(ids[ll][0]))
			job2 = BE.retrieve_job(str(ids[ll][1]))
		except:
			print("NoGo")
			print(JN)
			pass
		print(job2.status())
		if str(job2.status()) != 'JobStatus.DONE':
			continue
		Res1 = job1.result()
		Res2 = job2.result()
		ResultList = []
		for ii in range(50):
			ResultList.append(Res1.get_counts(ii))
		for ii in range(50):
			ResultList.append(Res2.get_counts(ii))
		ContextList = []
		for i in range(2):
			for j in range(10):
				for k in range(5):
					if i==0:
						ContextList.append([[j,cList[ll][i][j][k]]])
					else:
						ContextList.append([[cList[ll][i][j][k], j]])


		for i in range(100):
			if '00' in ResultList[i]:
				ContextList[i].append(ResultList[i]['00'])
			else:
				ContextList[i].append(0)
			if '01' in ResultList[i]:
				ContextList[i].append(ResultList[i]['01'])
			else:
				ContextList[i].append(0)
			if '10' in ResultList[i]:
				ContextList[i].append(ResultList[i]['10'])
			else:
				ContextList[i].append(0)
			if '11' in ResultList[i]:
				ContextList[i].append(ResultList[i]['11'])
			else:
				ContextList[i].append(0)
			#np.save('Rome/Rome_1_20_(2)_' + str(ii) + '.npy', ContextList)
		np.save(Processor + '/' + DirName + '/' + 'FCTexts_' + str(ll) + '.npy', ContextList)

#cList = np.load('bogota' + '/' + '2_3' + '/' + 'IDs.npy')
#print(cList)
#FrmtResults(100,'3_1_[0,1]','quito')