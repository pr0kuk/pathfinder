import sys
grammar_in = open(sys.argv[1]).readlines()
grammar_out = open("grammar.iggy", "w+")
nontdic = {}
n = int(grammar_in[0][0])
nont = [[] for i in range(n)]
i = 0
for simb in grammar_in:
    if i == 0:
        i = 1
        continue
    if simb[0] not in nontdic:
        nontdic[simb[0]] = i - 1
        pres = simb[0]
    nont[nontdic.get(pres)].append(simb[simb.find(" ")+1:-1])
    i += 1 

for key in nontdic.keys():
    grammar_out.write(key)
    grammar_out.write("\n  : ")
    for i in range(len(nont[nontdic.get(key)])):
        grammar_out.write(nont[nontdic.get(key)][i])
        if (i != len(nont[nontdic.get(key)]) - 1):
            grammar_out.write("\n  | ")
    grammar_out.write("\n\n")