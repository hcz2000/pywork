from numpy import *
def loadDataSet():
    return [[1,3,4],[2,3,5],[1,2,3,5],[2,5]]

def createC1(dataSet):
    C1=[]
    for transaction in dataSet:
        for item in transaction:
            if not [item] in C1:
                C1.append([item])
    C1.sort()
    return list(map(frozenset,C1))

def scanD(D,Ck,minSupport):
    ssCnt={}
    for tid in D:
        for can in Ck:
            if can.issubset(tid):
                if can in ssCnt:
                    ssCnt[can]+=1                    
                else:
                    ssCnt[can]=1
    numItems=float(len(D))
    retList=[]
    supportData={}
    for key in ssCnt:
        support = ssCnt[key]/numItems
        if support>=minSupport:
            retList.insert(0,key)
        #else:
        #    print(key)
        supportData[key]=support
    return retList,supportData

def aprioriGen(Lk,k):
    retList=[]
    lenLk=len(Lk)
    for i in range(lenLk):
        for j in range(i+1,lenLk):
            L1=list(Lk[i])[:k-2]
            L2=list(Lk[j])[:k-2]
            L1.sort()
            L2.sort()
            if(L1==L2):
                retList.append(Lk[i]|Lk[j])
    return retList

def apriori(dataSet,minSupport=0.5):
    C1=createC1(dataSet)
    D=list(map(set,dataSet))
    L1,supportData=scanD(D,C1,minSupport)
    L=[L1]
    k=2
    while(len(L[k-2])>0):
        Ck=aprioriGen(L[k-2],k)
        Lk,supK=scanD(D,Ck,minSupport)
        supportData.update(supK)
        L.append(Lk)
        k+=1
    return L,supportData

def generateRules(L,supportData,minConf=0.7):
    bigRuleList=[]
    for i in range(1,len(L)):
        for freqSet in L[i]:
            print("generateRules freqSet:",freqSet)
            H1=[frozenset([item]) for item in freqSet]
            if i>1:
                rulesFromConseq(freqSet,H1,supportData,bigRuleList,minConf)
            else:
                print("generateRules",i)
                calcConf(freqSet,H1,supportData,bigRuleList,minConf)
    return bigRuleList

def calcConf(freqSet,H,supportData,brl,minConf=0.7):
    prunedH=[]
    for conseq in H:
        print("calcConf freqSet:",freqSet)
        print(conseq)
        print(freqSet-conseq)
        conf=supportData[freqSet]/supportData[freqSet-conseq]
        if conf>=minConf:
            print(freqSet-conseq,"---->",conseq,"conf:",conf)
            brl.append((freqSet-conseq,conseq,conf))
            prunedH.append(conseq)
    return prunedH

def rulesFromConseq(freqSet,H,supportData,brl,minConf=0.7):
    m=len(H[0])
    if(len(freqSet)>(m+1)):
        print("rulsFromConseq")
        Hmpl=aprioriGen(H,m+1)
        Hmpl=calcConf(freqSet,Hmpl,supportData,brl,minConf)
        if(len(Hmpl)>1):
            rulesFromConseq(freqSet,Hmpl,supportData,brl,minConf)

def test1():
    dataSet=loadDataSet()
    C1=createC1(dataSet)
    D=list(map(set,dataSet))
    return scanD(D,C1,0.5)

def test2():
    dataSet=loadDataSet()
    L,supportData=apriori(dataSet)
    return L,supportData

def test3():
    dataSet=loadDataSet()
    L,supportData=apriori(dataSet,minSupport=0.5)
    print(L)
    rules=generateRules(L,supportData,minConf=0.5)
    return rules
   
