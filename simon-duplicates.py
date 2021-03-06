import sys
import logging
import matplotlib.pyplot as plt
import numpy as np
import operator
import itertools
#from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute, IBMQ
from qiskit.providers.ibmq import least_busy
from collections import OrderedDict

# AER is for simulators
from qiskit import Aer
from qiskit import QuantumCircuit
from qiskit import ClassicalRegister
from qiskit import QuantumRegister
from qiskit import execute
from qiskit import IBMQ
#from qiskit.providers.ibmq.managed import IBMQJobManager
from qiskit.tools.monitor import job_monitor
from qiskit.tools.visualization import plot_histogram
from qiskit.tools.visualization import circuit_drawer
from sympy import Matrix, pprint, MatrixSymbol, expand, mod_inverse

from qjob import QJob

unitary_sim = Aer.get_backend('unitary_simulator')

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

def blackbox(simonCircuit, uni_list, period_string):
        #### Blackbox Function #####
        # QP's don't care about this, we do#
        #############################
        
        #bbqr = QuantumRegister(2*n, 'q')
        #bbcr = ClassicalRegister(n, 'c') 
        #bbcirc = QuantumCircuit(bbqr,bbcr)
        flag = True

        while flag:
            bbqr = QuantumRegister(2*n, 'q')
            bbcr = ClassicalRegister(n, 'c') 
            bbcirc = QuantumCircuit(bbqr,bbcr)
            # Copy first register to second by using CNOT gates
            for i in range(n):
                    #simonCircuit.cx(qr[i],qr[n+i])
                    #bbcirc.cx(qr[i],qr[n+i])
                    bbcirc.cx(bbqr[i],bbqr[n+i])
                
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
                    bbcirc.cx(bbqr[j], bbqr[n+i]) #the i-th qubit is flipped if s_i is 1
                    #simonCircuit.x(qr[j])

            # Added to expand function space so that we get enough random
            # functions for statistical sampling
            # Randomly add a CX gate

            for i in range(n):
                for j in range(i+1, n):
                    if np.random.random() > 0.5:
                        bbcirc.cx(bbqr[n+i],bbqr[n+j])
                        
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
                    bbcirc.swap(bbqr[n+i], bbqr[n+k])    #swap gate on qubits
                    init[i], init[k] = init[k], init[i] # mark the swapped qubits
                else:
                    i += 1
                        
            # Randomly flip qubit
            # Seed random numbers for predictability / benchmark
            for i in range(n):
                if np.random.random() > 0.5:
                    bbcirc.x(bbqr[n+i])

            # Added for duplicate checking
            # We get the unitary matrix of the blackbox generated circuit
            bb_sim_result = execute(bbcirc, unitary_sim).result()
            bb_uni = bb_sim_result.get_unitary(bbcirc, decimals=15)
        
			# Duplicate flag
            dup = False

            # Handle empty list
            if len(uni_list) == 0:
                #uni_list.append(bb_uni)
                # Set flag to false to break out of main loop
                flag = False
                dup = False 
                print("adding first generated")
            else:
                # Check for duplicates
                # If duplicate oracle query, re-run oracle 
                #print(np.array_equal(bb_uni, uni_list[0]))
                for i, uni in enumerate(uni_list):
                    if (bb_uni == uni).all():
                    #if np.array_equal(bb_uni, uni):
					# Break out of for loop because we founhd a duplicate, re-run to get new blackbox circuit
                        print("Duplicates Found, restarting loop")
                        dup = True
                        break    # breaks out of for loop to start over, 
                    else:
                        dup = False

            # If duplicate flag not set after we searched the list...
            if not dup:
                # No duplicate unitary matricies, we can add to list
				# and break out
                uni_list.append(bb_uni)
                flag = False
                print("No Duplicates - Added another to list")

		### End While
        
        # Combine input circuit with created blackbox circuit 
        simonCircuit = simonCircuit + bbcirc
        simonCircuit.barrier()

        print("Ending blackbox")
        
        return simonCircuit
        
                                        
## easily create period strings
## We want to avoid using anything with all 0's as that gives us false results
## because anything mod2 00 will give results
def create_period_str(strlen):
    str_list = list()
    for i in itertools.product([0,1],repeat=strlen):
        if "1" in ("".join(map(str,i))):
            #print("".join(map(str,i)))
            str_list.append("".join(map(str,i)))

    return str_list



#### START ####            
# hidden stringsn

period_strings_5qubit = list()
period_strings_5qubit = create_period_str(2)

period_strings_2bit = list()
period_strings_3bit = list()
period_strings_4bit = list()
period_strings_5bit = list()
period_strings_6bit = list()
period_strings_7bit = list()

# 2-bit strings
period_strings_2bit = create_period_str(2)

# 3-bit strings
period_strings_3bit = create_period_str(3)

# 4-bit strings
period_strings_4bit = create_period_str(4)

# 5-bit strings
period_strings_5bit = create_period_str(5)

# 6-bit strings
period_strings_6bit = create_period_str(6)

# 7-bit strings
period_strings_7bit = create_period_str(7)


# IBM Q stuff..
IBMQ.load_account()
provider = IBMQ.get_provider(hub='ibm-q')

circuitList = list()

## DO NOT USE ITERATION FORMULA JUST HERE FOR REF
# Iterations = # of backends tested
# iteration formula = floor(log2(num_backends * num_shots)) = 14 here
# 2-bit period strings
ranJobs = list()
backname = "local_sim"
#2bit = 12 = 36 random functions
#3bit = 54 = 372+ random functions
#4bit 
#5bit 
#6bit
#7bit
#o Jobs total = # of strings * iterations
#total_jobs = iterations * len(period_strings_5bit)
#job_start_idx = 1

circs = list()

def find_duplicates(circs):
    k = 0
    dup_count = 0
    while k < len(circs)-1:
        if circs[k].count_ops() == circs[k+1].count_ops():
            #print("\n=== Duplicates Found! ===")
            #print("Index:" + str(k))
            #print("Index:" + str(k+1))
            dup_count = dup_count + 1
            #print(circs[k].count_ops())
            #print(circs[k+1].count_ops())
            #print("=== End Duplcates ===")
            k = k+2
        else:
            k = k+1
            
    return dup_count
            

def generate_simon(simonCircuit, uni_list, period):
    # Generate circuit
	# Assumes global simoncircuit

    # Hadamards prior to oracle
    for i in range(n):
        simonCircuit.h(qr[i])
        
    simonCircuit.barrier()
    # Oracle query
    simonCircuit = blackbox(simonCircuit, uni_list, period)
    # Apply hadamards again
    for i in range(n):
        simonCircuit.h(qr[i])
        
    simonCircuit.barrier()
    # Measure qubits, maybe change to just first qubit to measure
    simonCircuit.measure(qr[0:n],cr)
    
    return simonCircuit

i = 0  
z = 0
not_done = True
np.random.seed(0)

n = len(period_strings_2bit[0])
qr = QuantumRegister(2*n, 'q')
cr = ClassicalRegister(n, 'c')
simonCircuit = QuantumCircuit(qr,cr)
uni_list = list()

outfile = open("sim-results/simulations-2bit-12iter.txt", "w")
iterations = 12   #2-bit
#iterations = 54   #3-bit
#iterations = 26   #4-bit 
#iterations = 13    #5-bit
#iterations = 7    #6-bit 
#iterations = 4    #7-bit 
local_sim = Aer.get_backend('qasm_simulator')

while not_done:
    while i < len(period_strings_2bit):
        #print("Started main block..")
        #print(str(period_strings_6bit[i]))
        n = len(period_strings_2bit[i])
        print("Period strings: " + str(i+1) + "/" + str(len(period_strings_2bit)))
        while z < iterations:
            qr = QuantumRegister(2*n, 'q')
            cr = ClassicalRegister(n, 'c')
            simonCircuit = QuantumCircuit(qr,cr)
            # Duplicates are checked in blackbox function
            simon = generate_simon(simonCircuit, uni_list, period_strings_2bit[i])
            circs.append(simon)
            z = z + 1
            print("Iterations:" + str(z) + "/" + str(iterations))
        i = i + 1
        z = 0
    not_done = False

dup_flag = False
print("\nDouble checking heuristically...\n")
# Double checking all items in list are not duplicate
for x in range(0,len(uni_list)-1):
    for y in range(1,len(uni_list)):
        # Handle condition when x and y overlap and are eachother
        if x != y:
            if np.array_equal(uni_list[x], uni_list[y]):
                print("Duplicates found at indexes:" + str(x) + "," + str(y))
                dup_flag = True
                #print("\nDuplicates in set, not valid\n")

if dup_flag:
    print("\nDuplicates Found, see above.\n")
else:
    print("\nNo duplicates found in 2nd pass\n")

print("\nRunning final check of dot product between period string and observed strings...")
### Now to run on simulator ####
iter_cnt = 0 
pstr_cnt = 0 
ranJobs = list()

for circ in circs:
    job = execute(circ, backend=local_sim, shots=1024, optimization_level=3, seed_transpiler=0)
    # create Qjob, store info 
    qj = QJob(job, circ, "local_sim", period_strings_2bit[pstr_cnt])
    ranJobs.append(qj)
    result = job.result()    
    counts = result.get_counts()
    # We advance to next period string when we iterate through all
    # the circuits per period strings
    if iter_cnt == iterations-1:
        pstr_cnt += 1
        iter_cnt = 0
    else:
        iter_cnt += 1
    
   # outfile.write(str(counts) + "\n")

outfile.close()

# Go through and get correct vs incorrect in jobs
## This will verify all the strings we get back are correct from the non
# duplicate circuits
for qjob in ranJobs:
    results = qjob.job.result()
    counts = results.get_counts()
    #equations = guass_elim(results)
    # Get period string
    pstr = qjob.getPeriod()

    # Verify observed string vs peroid string by doing dot product
    for ostr, count in counts.items():
        if verify_string(ostr, pstr):
            qjob.setCorrect(count)
        else:
            qjob.setIncorrect(count)
            
total_correct = 0
total_incorrect = 0
total_runs = (1024 * iterations) * len(period_strings_2bit)

for qjob in ranJobs:
    total_correct += qjob.getCorrect()
    total_incorrect += qjob.getIncorrect() 

print("\nTotal Runs: " + str(total_runs))
print("Total Correct: " + str(total_correct))
print("Prob Correct: " + str(float(total_correct) / float(total_runs)))
print("Total Incorrect: " + str(total_incorrect))
print("Prob Incorrect: " + str(float(total_incorrect) / float(total_runs)))
print("")


