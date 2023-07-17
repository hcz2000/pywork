from stats import Pmf

class Cookie(Pmf):

    def __init__(self,hypos):
        Pmf.__init__(self)
        for hypo in hypos:
            self.Set(hypo,1)
        self.Normalize()

    def Update(self,data):
        for hypo in self.Values():
            like=self.Likelihood(data,hypo)
            self.Mult(hypo,like)
        self.Normalize()
        
    def Likelihood(self,data,hypo):
        mix=self.mixes[hypo]
        like=mix[data]
        return like

    mixes = {
        'Bowl1':dict(vanilla=0.75, chocolate=0.25),
        'Bowl2':dict(vanilla=0.5, chocolate=0.5),
        }
        
def main():
    hypos=['Bowl1','Bowl2']
    pmf=Cookie(hypos)
    pmf.Update('vanilla')
    for hypo,prob in pmf.Items():
        print(hypo,prob)

if __name__=='__main__':
    main()
