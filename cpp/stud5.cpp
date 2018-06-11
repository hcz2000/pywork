#include <string.h>
#include <iostream>
using namespace std;

class par
{
    static int val;
    private:
        int student;
    public:
        par(){
        }
        int getStudent(){
            return student;
        }


};

int par::val=10;

int main()
{
    par p1;

    cout<<"--------STUD3-------"<<endl;
    cout<<"-------Exiting-------"<<endl;
    cout<<flush;
    return 0;
}//
