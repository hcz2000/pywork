#include <string.h>
#include <iostream>
using namespace std;
class stud 
{
    private:
        int num;
        char name[32];
        char sex;
    public:
        stud(int n,const char nam[],char s) //构造函数
        { 
            cout<<"construct stud "<<nam<<endl;
            num = n;
            strcpy(name, nam);
            sex = s;
        }

        stud(const stud& s) //拷贝构造函数,COPY对象时调用，
        {
            cout<<"copy stud "<<s.name<<endl;
            num = s.num;
            strcpy(name, s.name);
            strcat(name,"_copy");
            sex = s.sex;
        }
         
        ~stud() //析构函数
        {
            cout<<"stud "<<name<<" has been destructed!"<<endl;
        }
        
 
        void display()//成员函数，输出对象的数据
        {
            cout<<"num:"<<num<<endl;
            cout<<"name:"<<name<<endl;
            cout<<"sex:"<<sex<<endl;
        }
};

class par
{
    private:
        stud student;
    public:
        par():student(10012, "hcz", 'm'){
        }
        stud getStudent(){
            return student;
        }

};

void fun1(stud s)//传值调用，将导致stud的拷贝构造函数调用，调用结束时，所拷贝的参数对象销毁，自动调用其析构函数
{
    cout<<"-----FUNC1------"<<endl;
    s.display();
}

void fun2(stud& s)//引用调用，没有新对象产生
{
    cout<<"-----FUNC2------"<<endl;
    s.display();
}

static stud stud1(10011, "Wang-li", 'f');

int main()
{
    par p1;
    stud stud3=p1.getStudent();
    cout<<"--------STUD3-------"<<endl;
    stud3.display();//输出学生1的数据
    cout<<"-------Exiting-------"<<endl;
    cout<<flush;
    return 0;
}//
