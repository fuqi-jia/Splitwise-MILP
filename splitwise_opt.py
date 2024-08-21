from pyscipopt import Model

### Input ###
# persons
persons = [
    'A',
    'B',
    'C',
]
# read payments
payments = dict()
payments['A'] = 0
payments['B'] = 9
payments['C'] = 15
mode = 'MILP' # or 'LP'
### Input done ###

assert mode == 'MILP' or mode == 'LP'

# build graph
graph = dict()
for person in persons:
    graph[person] = dict()
    for p in persons:
        if p != person:
            graph[person][p] = 0

TotalPay = sum(payments.values())
size = len(persons)

# calculate the graph
for p in persons:
    for q in persons:
        if p != q:
            # p -> q: p should pay q
            graph[p][q] = payments[q] / size

# print
owe = dict()
for p in persons:
    owe[p] = dict()
    for q in persons:
        if p != q:
            owe[p][q] = graph[p][q] - graph[q][p]

print("---Total Owe---")
oweTotal = dict()
for p in persons:
    oweTotal[p] = sum(owe[p].values())
    if oweTotal[p] < 0:
        print(f'{p} should get back {-oweTotal[p]:.2f}')
    elif oweTotal[p] > 0:
        print(f'{p} should pay {oweTotal[p]:.2f}')

# owe is the initial solution of the linear programming
# linear programming
model = Model()

# M
M = max(payments.values()) * 100

# make scipy variables
vars = dict()
for p in persons:
    for q in persons:
        if p != q:
            val = owe[p][q] if owe[p][q] > 0 else -owe[q][p]
            vars[(p, q)] = model.addVar(name=f'{p}->{q}', vtype='C', lb=-TotalPay, ub=TotalPay)
          
# results of the substraction
rvars = dict()
for p in persons:
    for q in persons:
        if p != q:
            rvars[(p, q)] = model.addVar(name=f'R:{p}->{q}', vtype='C', lb=0, ub=TotalPay)

# binary variables
bvars = dict()
for p in persons:
    for q in persons:
        if p != q:
            bvars[(p, q)] = model.addVar(name=f'B:{p}->{q}', vtype='B', lb=0, ub=1)

# add constraints
for p in persons:
    for q in persons:
        if p != q:
            # binary encoding: b == 0 -> (r == 0)
            model.addCons(owe[p][q] - vars[(p, q)] == rvars[(p, q)])
            if(mode=='MILP'): model.addCons(rvars[(p, q)] <= M * bvars[(p, q)])

for q in persons:
    in_pos_set = set()
    out_pos_set = set()
    for p in persons:
        if p != q:
            if owe[q][p] > 0:
                out_pos_set.add(p)
            elif owe[q][p] < 0:
                in_pos_set.add(p)
              
    if len(in_pos_set) > 0 and len(out_pos_set) > 0:
        model.addCons(
            sum(rvars[(q, p)] for p in out_pos_set) 
            -
            sum(rvars[(p, q)] for p in in_pos_set)
            == oweTotal[q]
        )
    elif len(in_pos_set) > 0:
        model.addCons(
            -sum(rvars[(p, q)] for p in in_pos_set)
            == oweTotal[q]
        )
    elif len(out_pos_set) > 0:
        model.addCons(
            sum(rvars[(q, p)] for p in out_pos_set)
            == oweTotal[q]
        )


# add objective
if(mode=='LP'): model.setObjective(sum(rvars[(p, q)] for p in persons for q in persons if p != q), sense='minimize')
elif(mode=='MILP'): model.setObjective(sum(bvars[(p, q)] for p in persons for q in persons if p != q), sense='minimize')

# solve
model.hideOutput(quiet=True)
model.optimize()

# output
print("---Solution Start---")
sol = dict()
for p in persons:
    for q in persons:
        if p != q:
            # print(f'{p}->{q}: {model.getVal(vars[(p, q)])}')
            sol[(p, q)] = model.getVal(rvars[(p, q)])
            if abs(sol[(p, q)]) <= 1e-8:
                pass
            elif sol[(p, q)] > 0:
                print(f'{p} should pay {q} {sol[(p, q)]:.2f}')
            elif sol[(p, q)] < 0:
                print(f'{p} should get back from {q} {-sol[(p, q)]:.2f}')
print("---Solution end---")

