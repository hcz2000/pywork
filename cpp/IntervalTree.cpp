// IntervalTree.cpp: 定义控制台应用程序的入口点。
//

//#include "stdafx.h"
#include "iostream"
#include "stdlib.h"
#include <string>
using namespace std;

#define RED true
#define BLACK false

class IntervalTree
{
  private:
	class ITNode
	{
	  public:
		string CNumber, CName;
		int low, high;
		int key, max;
		bool color;
		ITNode *left, *right, *parent;
		inline ITNode(ITNode *p);
		inline ITNode() {};
		inline void SetNode(string number, string name, int start, int end, bool color, ITNode *left, ITNode *right, ITNode *parent);
	};
	ITNode *NIL, *Root;

  public:
	  inline IntervalTree(); 
	void LeftRotate(ITNode *x);
	void RightRotate(ITNode *y);
	void RBInsertFixup(ITNode *z);
	void RBDeleteFixup(ITNode *z);
	bool AddCourse(string number, string name, int start, int end);
	bool DeleteCourse(string number);
	ITNode* FindCourseByName(string number,ITNode* p);
};

inline IntervalTree::ITNode::ITNode(ITNode *p)
{
	left = p;
	right = p;
	parent = p;
}

inline IntervalTree::IntervalTree()
{
	Root = NULL;
	NIL = new ITNode(NULL);
	NIL->color = BLACK;
}
inline void IntervalTree::ITNode::SetNode(string number, string name, int start, int end, bool RB, ITNode *l, ITNode *r, ITNode *p)
{
	CNumber = number;
	CName = name;
	low = start;
	high = end;
	color = RB;
	left = l;
	right = r;
	parent = p;
}

void IntervalTree::LeftRotate(ITNode *x)
{
	ITNode *y = x->right;
	x->right = y->left;
	if (y->left != NULL)
		y->left->parent = x;
	if (x->parent == NULL)
		Root = y;
	else if (x == x->parent->left)
		x->parent->left = y;
	else
		x->parent->right = y;
	y->left = x;
	x->parent = y;
}

void IntervalTree::RightRotate(ITNode *x)
{
	ITNode *y = x->left;
	x->left = y->right;
	if (y->right != NULL)
		y->right->parent = x;
	if (x->parent == NULL)
		Root = y;
	else if (x == x->parent->left)
		x->parent->left = y;
	else
		x->parent->right = y;
	y->right = x;
	x->parent = y;
}

void IntervalTree::RBInsertFixup(ITNode *z)
{
	while (z->parent->color == RED)
	{
		if (z->parent == z->parent->parent->left)
		{
			ITNode *y = z->parent->parent->right;
			if (y->parent->color == RED)
			{
				z->parent->color = BLACK;
				y->color = BLACK;
				z->parent->parent->color = RED;
				z = z->parent->parent;
			}
			else if (z == z->parent->right)
			{
				z = z->parent;
				LeftRotate(z);
			}
			z->parent->color = BLACK;
			z->parent->parent->color = RED;
			RightRotate(z->parent->parent);
		}
		else	// z->parent == z->parent->parent->right
		{
			ITNode *y = z->parent->parent->left;
			if (y->parent->color == RED)
			{
				z->parent->color = BLACK;
				y->color = BLACK;
				z->parent->parent->color = RED;
				z = z->parent->parent;
			}
			else if (z == z->parent->left)
			{
				z = z->parent;
				RightRotate(z);
			}
			z->parent->color = BLACK;
			z->parent->parent->color = RED;
			LeftRotate(z->parent->parent);
		}
	}
}

bool IntervalTree::AddCourse(string number, string name, int start, int end)
{
	if (Root == NULL)
	{
		Root = new ITNode(NIL);
		Root->SetNode(number, name, start, end, BLACK, NULL, NULL, NULL);
		return Root == NULL ? true : false;
	}
	// Root! = NULL
	ITNode *p, *q;
	p = Root;
	q = start < p->key ? p->left : p->right;
	while (q != NULL)
	{
		p = q;
		q = start < p->key ? p->left : p->right;
	}
	if (start < p->key) //left
	{
		p->left = new ITNode(NIL);
		p->left->SetNode(number, name, start, end, RED, NULL, NULL, p);
		q = p->left;
	}
	else
	{
		p->right = new ITNode(NIL);
		p->right->SetNode(number, name, start, end, RED, NULL, NULL, p);
		q = p->right;
	}
	RBInsertFixup(q);
	return q == NULL ? true : false;
}

IntervalTree::ITNode* IntervalTree::FindCourseByName(string number,IntervalTree:: ITNode *p)
{
	if (p==NULL||p->CNumber==number)
		return p;
	ITNode *q;
	if ((q=FindCourseByName(number,p->left))!=NULL)
		return q;
	return FindCourseByName(number, p->right);
}
/*
void IntervalTree::DeleteCourse(string number)
{
	ITNode *p = Root;
	while (p->CNumber!=number)
	{
		if 
	}
}

/*
class test
{
  public:
	int x;
	void set(int x);
	void print() { cout << x << endl; }
};
void test::set(int x)
{
	x = x;
}
*/
int main()
{
	/*
	class test t;
	t.set(5);
	t.print();
	*/
	class IntervalTree tree;
	//class IntervalTree::ITNode *p;
	tree.AddCourse("123", "abc", 0, 1);
	tree.AddCourse("234", "def", 4, 5);
	tree.AddCourse("43", "dsf", 6, 9);
	tree.AddCourse("435", "3r", 1, 5);
	tree.AddCourse("129", "xcv", 3, 7);
	tree.AddCourse("090", "er", 6, 12);
	//p = tree.FindCourseByName("234", tree.Root);
	//tree.GetRootInfo();

	cout << "DONE\n";
	getchar();
	return 0;
}
