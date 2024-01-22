
import math
import random
import time

import lessons.QiskitUtils as qutils

from qiskit import Aer, QuantumCircuit, transpile, QuantumRegister

DEBUG = False

# ---- Function for DEBUG -----
def get_variable_name(var, namespace):
    for name, value in namespace.items():
        if value is var:
            return name
    return None

def debug(var, locals):
    if DEBUG:
        print(f"{get_variable_name(var, locals)}: {var}")
# -----------------------------


def run_circuit(circuit, shots):
    # Use Aer's qasm_simulator
    #results = aer_sim.run(dj_circuit).result()
    #answer = results.get_counts()

    #simulator = QasmSimulator()
    simulator = Aer.get_backend('aer_simulator')

    # compile the circuit down to low-level QASM instructions
    # supported by the backend (not needed for simple circuits)
    compiled_circuit = transpile(circuit, simulator)

    # Execute the circuit on the qasm simulator
    job = simulator.run(compiled_circuit, shots=shots)
    
    # Grab results from the job
    result = job.result()  
    cnt = result.get_counts(compiled_circuit)

    return cnt

def Compare(n: int, k: int, yi: str):
    """
    n: number of bits rappressenting index
    k: number of bits rappressenting space of values
    chk: qubits to check value to find 0 positions
    """
    qc = QuantumCircuit(n+k+1)
    # Build chk
    chk = []
    zero_found = False
    b = False
    for i, s in enumerate(yi):
        chk.append(i)
        if s == '0':
            zero_found = True
        if s == '1' and zero_found:
            b = True
            break
    if not b:
        chk = [0]
    # --------
    
    for elem in chk:
        qc.x(n+elem)
    
    targets=[]
    [targets.append(n+elem) for elem in chk]

    qc.mcx(targets, n + k)
    for elem in chk:
        qc.x(n+elem)
    
    if DEBUG:
        qutils.draw_circuit(qc)
    else:
        qc = qc.to_gate(label="Compare")
        return qc

def Generate_Oracle(db: list, bits_of_value: int):
     
    N = len(db)
    bits_index = int(math.ceil(math.log2(N)))

    qc = QuantumCircuit(bits_index + bits_of_value)

    if DEBUG:
        qc.barrier()

    for index, value in enumerate(db):

        str_index = str(bin(index))[2:].zfill(bits_index)
        for i in range(len(str_index)):
            if str_index[i] == "0":
                qc.x(i)
        
        for i in range(bits_of_value):
            if value[i] == "1":
                qc.mcx(list(range(bits_index)), bits_index + i)
        
        for i in range(len(str_index)):
            if str_index[i] == "0":
                qc.x(i)
        if DEBUG:
            qc.barrier()
    
    if DEBUG:
        qutils.print_circuit(qc)
    else:
        qc = qc.to_gate(label="Oracle")
        return qc

def Diffuser(n: int):
    
    qc = QuantumCircuit(n)
    for i in range(n):
        qc.h(i)
        qc.x(i)
    qc.h(n-1)
    qc.mcx(list(range(n-1)),n-1)
    qc.h(n-1)
    for i in range(n):
        qc.x(i)
        qc.h(i)
    qc = qc.to_gate(label='Diffuser')
    return qc

def end(value, min):
    print(f"Quantum Algorithm result: {value}")
    print(f"Classical minimum: {min}")
    exit()

if __name__ == "__main__":
    
    n_chars = 16
    array_len = 16

    db = []
    db_int = []

    # Initialize memory
    for i in range(array_len):
        value = random.randint(0,2**(n_chars-1)-1)
        db_int.append(value)
        db.append(str(bin(value))[2:].zfill(n_chars))
    min = min(db_int)
    # -----------------

    ### Extends elements for Gorver algorithm
    for i in range(array_len):
        db.append('1' * n_chars)
    print(db)
    # ---------------------------------------

    ### Select random Yi
    first_index = int(random.randint(0,int((len(db)-1) / 2)))
    print(f"first index: {first_index}")
    value_yi = db[first_index]
    # ----------------

    bits_index = int(math.ceil(math.log2(len(db))))
    
    # Prepare parts of Grover that's no change during cycles
    U  = Generate_Oracle(db, n_chars)
    W = Diffuser(bits_index)

    while True:

        # GROVER Algorithm
        qc = QuantumCircuit(bits_index + n_chars + 1, bits_index)

        for i in range(bits_index):
            qc.h(i)
        qc.x(bits_index + n_chars)
        qc.h(bits_index + n_chars)

        P  = Compare(bits_index, n_chars, value_yi)

        qc = qc.compose(U)
        qc = qc.compose(P)
        qc = qc.compose(U)
        qc = qc.compose(W)

        for i in range(bits_index):
            qc.measure(i,i)
        # End GROVER Algorithm

        res = run_circuit(qc, 1000)
        # qutils.print_circuit(qc)

        # qutils.revcounts(res)

        found = False
        for key, value in res.items():
            if value > 240:
                end(int('0b'+ db[int('0b' + key[::-1], base = 0)], base = 0), min)

            if value > 100:
                found = True
                value_yi = db[int('0b'+key[::-1], base = 0)]
                print(f"new index: {int('0b'+key[::-1], base = 0)}")
                break

        if not found:
            end(int('0b'+ value_yi, base = 0), min)