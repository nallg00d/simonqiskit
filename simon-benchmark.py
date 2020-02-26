import sys
import matplotlib.pyplot as plt
import numpy as np
import operator
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute,Aer, IBMQ
#from qiskit.providers.ibmq.managed import IBMQJobManager
from qiskit.tools.monitor import job_monitor
from qiskit.tools.visualization import plot_histogram
from qiskit.tools.visualization import circuit_drawer
from sympy import Matrix, pprint, MatrixSymbol, expand, mod_inverse

from qjob import QJob

def blackbox(period_string):
        #### Blackbox Function #####
        # QP's don't care about this, we do#
        #############################

        # Copy first register to second by using CNOT gates
        for i in range(n):
                #simonCircuit.cx(qr[i],qr[n+i])
                simonCircuit.cx(qr[i],qr[n+i])
                
        # get the small index j such it's "1"
        j = -1
        #reverse the string so that it takes
        s = period_string[::-1]
        for i, c in enumerate(s):
                if c == "1":
                        j = i
                        break
                        
        # 1-1 and 2-1 mapping with jth qubit 
        # x is control to xor 2nd qubit with a
        for i, c in enumerate(s):
                if c == "1" and j >= 0:
                        #simonCircuit.x(qr[j])
                        simonCircuit.cx(qr[j], qr[n+i]) #the i-th qubit is flipped if s_i is 1
                        #simonCircuit.x(qr[j])
                        
                        
        # Random peemutation
        # This part is how we can get by with 1 query of the oracle and better
        # simulates quantum behavior we'd expect
        perm = list(np.random.permutation(n))

        # init position
        init = list(range(n))

        i = 0

        while i < n:
                if init[i] != perm[i]:
                        k = perm.index(init[i])
                        simonCircuit.swap(qr[n+i],qr[n+k])  #swap gate on qubits
                        init[i], init[k] = init[k], init[i] # mark the swapped qubits
                else:
                        i += 1
                        
        # Randomly flip qubit
        for i in range(n):
                if np.random.random() > 0.5:
                        simonCircuit.x(qr[n+i])

        simonCircuit.barrier()
        ### END OF BLACKBOX FUNCTION 
        
        return simonCircuit
        
def run_circuit(circuit,backend):
        # Default for this backend seems to be 1024 ibmqx2
        shots = 1024

        job = execute(simonCircuit,backend=backend, shots=shots)
        job_monitor(job,interval=2)
        results = job.result()
        return results

'''
        counts = results.get_counts()
        #print("Getting Results...\n")
        #print(qcounts)
        #print("")
        print("Submitting to IBM Q...\n")


        print("\nIBM Q Backend %s: Resulting Values and Probabilities" % qbackend)
        print("===============================================\n")
        print("Simulated Runs:",shots,"\n")

        # period, counts, prob,a0,a1,...,an
        #
        for key, val in qcounts.items():
                   prob = val / shots
                   print("Period:", key, ", Counts:", val, ", Probability:", prob)
                   
        print("")
'''

        
def guass_elim(results):
        # Classical post processing via Guassian elimination for the linear equations
        # Y a = 0
        # k[::-1], we reverse the order of the bitstring
        equations = list()
        lAnswer = [ (k[::-1],v) for k,v in results.get_counts().items() if k != "0"*n ]

        # Sort basis by probabilities
        lAnswer.sort(key = lambda x: x[1], reverse=True)

        Y = []
        for k, v in lAnswer:
                        Y.append( [ int(c) for c in k ] )

        Y = Matrix(Y)

        Y_transformed = Y.rref(iszerofunc=lambda x: x % 2==0)

        # convert rational and negatives in rref
        def mod(x,modulus):
                        numer,denom = x.as_numer_denom()
                        return numer*mod_inverse(denom,modulus) % modulus

        # Deal with negative and fractial values
        Y_new = Y_transformed[0].applyfunc(lambda x: mod(x,2))

        #print("\nThe hidden period a0, ... a%d only satisfies these equations:" %(n-1))
        #print("===============================================================\n")
        rows,cols = Y_new.shape
        for r in range(rows):
                        Yr = [ "a"+str(i)+"" for i,v in enumerate(list(Y_new[r,:])) if v==1]
                        if len(Yr) > 0:
                                tStr = " xor ".join(Yr)

                                #single value is 0, only xor with perid string 0 to get
                                if len(tStr) == 2:
                                        equations.append("period xor" + " 0 " + " = 0")
                                else:
                                        equations.append("period" + " xor " + tStr + " = 0")

        return equations
                                        
def print_list(results):
# Sort list by value
        sorted_x = sorted(qcounts.items(), key=operator.itemgetter(1), reverse=True)
        print("Sorted list of result strings by counts")
        print("======================================\n")
        for i in sorted_x:
                print(i)
        #print(sorted_x)
        print("")


## function to get dot product of result string with the period string to verify, result should be 0
#check the wikipedia for simons formula 
# DOT PRODUCT IS MOD 2 !!!!
# Result XOR ?? = 0   -- this is what we're looking for!

# We have to verify the period string with the ouptput using mod_2 addition aka XOR
# Simply xor the period string with the output string    
# Simply xor the period string with the output string, result must be 0 or 0b0
def verify_string(ostr, pstr):
    """
    Verify string with period string
    Does dot product and then mod2 addition
    """
    temp_list = list()
    # loop through outstring, make into numpy array
    for o in ostr:
        temp_list.append(int(o))
    
    ostr_arr = np.asarray(temp_list)
    temp_list.clear()
    
    # loop through period string, make into numpy array
   
    for p in pstr:
        temp_list.append(int(p))
        
    pstr_arr = np.asarray(temp_list)
    
    temp_list.clear()
    
    # Per Simosn, we do the dot product of the np arrays and then do mod 2
    results = np.dot(ostr_arr, pstr_arr)
    
    if results % 2 == 0:
        return True
     
    return False

#### START ####         
# hidden stringsn
# We omit 00 as it's a trivial answer/solution

period_strings_5qubit = list()
s0 = "00"
s1 = "01"
s2 = "10"
s3 = "11"
s4 = "000"
s5 = "001"
s6 = "010"
s7 = "011"
s8 = "100"
s9 = "101"
s10 = "110"
s11 = "111"


s12 = "0000"
s13 = "0001"
s14 = "0010"
s15 = "0011"
s16 = "0100"
s17 = "0101"
s18 = "0110"
s19 = "0111"
s20 = "1000"
s21 = "1001"
s22 = "1010"
s23 = "1011"
s24 = "1100"
s25 = "1101"
s26 = "1110"
s27 = "1111"


s28 = "10000"
s29 = "10001"
s30 = "10010"
s31 = "10011"
s32 = "10100"
s33 = "10101"
s34 = "10110"
s35 = "10111"
s36 = "11000"
s37 = "11001"
s38 = "11010"
s39 = "11011"
s40 = "11100"
s41 = "11101"
s42 = "11110"
s43 = "11111"


period_strings_5qubit.append(s0)
period_strings_5qubit.append(s1)
period_strings_5qubit.append(s2)
period_strings_5qubit.append(s3)

"""
period_strings_5qubit.append(s4)
period_strings_5qubit.append(s5)
period_strings_5qubit.append(s6)
period_strings_5qubit.append(s7)
period_strings_5qubit.append(s8)
period_strings_5qubit.append(s9)
period_strings_5qubit.append(s10)
period_strings_5qubit.append(s11)

period_strings_5qubit.append(s12)
period_strings_5qubit.append(s13)
period_strings_5qubit.append(s14)
period_strings_5qubit.append(s15)
period_strings_5qubit.append(s16)
period_strings_5qubit.append(s17)
period_strings_5qubit.append(s18)
period_strings_5qubit.append(s19)
period_strings_5qubit.append(s20)
period_strings_5qubit.append(s21)
period_strings_5qubit.append(s22)
period_strings_5qubit.append(s23)
period_strings_5qubit.append(s24)
period_strings_5qubit.append(s25)
period_strings_5qubit.append(s26)
period_strings_5qubit.append(s27)

period_strings_5qubit.append(s28)
period_strings_5qubit.append(s29)
period_strings_5qubit.append(s30)
period_strings_5qubit.append(s31)
period_strings_5qubit.append(s32)
period_strings_5qubit.append(s33)
period_strings_5qubit.append(s34)
period_strings_5qubit.append(s35)
period_strings_5qubit.append(s36)
period_strings_5qubit.append(s37)
period_strings_5qubit.append(s38)
period_strings_5qubit.append(s39)
period_strings_5qubit.append(s40)
period_strings_5qubit.append(s41)
period_strings_5qubit.append(s42)
period_strings_5qubit.append(s43)
"""

# IBM Q stuff..
IBMQ.load_account()
provider = IBMQ.get_provider(hub='ibm-q')

# 15 qubit (broken?)
melbourne = provider.get_backend('ibmq_16_melbourne')

#5 qubit backends
ibmqx2 = provider.get_backend('ibmqx2')     # Yorktown
london = provider.get_backend('ibmq_london')
essex = provider.get_backend('ibmq_essex')
burlington = provider.get_backend('ibmq_burlington')
ourense = provider.get_backend('ibmq_ourense')
vigo = provider.get_backend('ibmq_vigo')

# 32 qubit qasm simulator
ibmq_sim = provider.get_backend('ibmq_qasm_simulator')

# Local Simulator, 
local_sim = Aer.get_backend('qasm_simulator')

circuitList = list()

backend_list = dict()
backend_list['local_sim'] = local_sim

#backend_list['ibmqx2'] = ibmqx2
#backend_list['london'] = london
#backend_list['essex'] = essex
#backend_list['burlington'] = burlington
#backend_list['ourense'] = ourense
#backend_list['vigo'] = vigo


# Make Circuits for all period strings!
for p in period_strings_5qubit:

	# Circuit name = Simon_+ period string
    #circuitName = "Simon-" + p

    circuitName = p
    n = len(p)
    # For simons, we use the first n registers for control qubits
    # We use the last n registers for data qubits.. which is why we need 2*n
    qr = QuantumRegister(2*n)
    cr = ClassicalRegister(n)
    simonCircuit = QuantumCircuit(qr,cr,name=circuitName)

    # Apply hadamards prior to oracle 
    for i in range(n):
        simonCircuit.h(qr[i])
        simonCircuit.barrier()

    #call oracle for period string
    simonCircuit = blackbox(p)

    # Apply hadamards after blackbox
    for i in range(n):
        simonCircuit.h(qr[i])

    simonCircuit.barrier()

    # Measure qubits, maybe change to just first qubit to measure
    simonCircuit.measure(qr[0:n],cr)
    
    circuitList.append(simonCircuit)


# Run loop to send circuits to IBMQ..
print("===== SENDING DATA TO IBMQ BACKENDS... =====\n")    
ranJobs = list() 

for circuit in circuitList:

        # Send all circuits to all backends
        # name -> backend object
        for name in backend_list:
            #results = run_circuit(circuit,backend)
            # Put circuit in enhanced QJob class, and execute / return Job
			# default 1024 shots
            job = execute(circuit,backend=backend_list[name],shots=1024)
            print("Running job on backend: " + name)
            job_monitor(job,interval=5)
            
            # Custom object to hold the job, circuit, and backend
            qj = QJob(job,circuit,name)

            # We have the job now, we can verify the string


            # Append finished / ran job to list of jobs
            ranJobs.append(qj)


correct = 0
incorrect = 0

for qjob in ranJobs:
        # Results from each job
        results = qjob.job.result()
        # equations from each job
        equations = guass_elim(results)

        #period string encoded into name
        pstr = qjob.circuit.name

        #list of observed strings
        obs_strings = list()
    
        # Sorted strings from each job
        sorted_str = sorted(results.get_counts().items(), key=operator.itemgetter(1), reverse=True)

        # Get just the observed strings
        for string in sorted_str:
                obs_strings.append(string[0])

        # go through and verify strings
        for o in obs_strings:
                # Remember to re-reverse string so it's back to normal due to IBMQ Endianness
                if verify_string(o,pstr):
                        qjob.setCorrect()
                        correct += 1
                else:
                        qjob.setIncorrect()
                        incorrect += 1

"""
Move this to new method

total = correct + incorrect
pcorrect = 100*(correct / total)

# Fix divide by 0 for simulation, since simulations should never have incorrect results
# Due to no quantum noise
if correct == total:
    pincorrect = 0
else:
    pincorrect = 100*(incorrect / total)

print("\n===== RESULTS =====\n")
print("Total Results: " + str(total))
print("Total Correct Results: " + str(correct) + " -- " + str(pcorrect) + "%") 
print("Total Inorrect Results: " + str(incorrect) + " -- " + str(pincorrect) + "%")
print("\n===================\n")
"""
        
