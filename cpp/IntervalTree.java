package myapp;

public class IntervalTree {
	private Node root;
	//private Node nil;
	
	public IntervalTree(int [][]data){
		for(int i=0;i<data.length;i++){
			Node node=new Node();
			node.setLow(data[i][0]);
			node.setHigh(data[i][1]);
			insert(node);
		}
	}
	/**
	 * 中序遍历
	 */
	public void inorderTreeWalk(){
		innerInorderTreeWalk(root);
		System.out.println();
	}
	/**
	 * 中序遍历
	 */
	private void innerInorderTreeWalk(Node node){
		if(node!=null){
			innerInorderTreeWalk(node.left);
			System.out.print("-->{"+node.low+","+node.high+"}");
			innerInorderTreeWalk(node.right);
		}
	}
	/**
	 * 先序遍历
	 */
	public void preorderWalk(){
		System.out.println("      "+((root.color==Node.RED?"R":"B")+"{"+root.low+","+root.high+"-"+root.max+"}"));
		innerPreorderWalk(root,1);
		System.out.println();
	}
	private void innerPreorderWalk(Node node,int depth){
		if(node!=null){
			if(node.left!=null){
				for(int i=6-depth*2;i>0;i--){
					System.out.print(" ");
				}
				System.out.print((node.left.color==Node.RED?"R":"B")+"{"+node.left.low+","+node.left.high+"-"+node.left.max+"},{"+node.low+","+node.high+"}");
			}else{
				System.out.print("  ");
			}
			if(node.right!=null){
				System.out.print("  ");
				System.out.print((node.right.color==Node.RED?"R":"B")+"{"+node.right.low+","+node.right.high+"-"+node.right.max+"},{"+node.low+","+node.high+"}");
			}else{
				System.out.print("  ");
			}
			if(node.left!=null||node.right!=null){
				System.out.println();
			}
			innerPreorderWalk(node.left,depth+1);
			innerPreorderWalk(node.right,depth+1);
			
		}
		
	}
	/**
	 * 后续遍历
	 */
	public void postorderWalk(){
		innerPostorderWalk(root);
		System.out.println();
	}
	private void innerPostorderWalk(Node node){
		innerPostorderWalk(node.left);
		innerPostorderWalk(node.right);
		System.out.print("-->{"+node.low+","+node.high+"}");
	}
	/**
	 * 查找值为value的节�?
	 * @param value
	 * @return
	 */
	public Node search(int low,int high){
		if(low<high){
			int tmp=low;
			low=high;
			high=tmp;
		}
		return innerSearch(root,low,high);
	}
	private Node innerSearch(Node node,int low,int high){
		Node x=root;
		while(x!=null&&!(low<=x.high&&x.low<=high)){
			if(x.left!=null&&x.left.max>=low){
				x=x.left;
			}else{
				x=x.right;
			}
		}
		return x;
	}
	/**
	 * 返回�?小�?�节�?
	 * @return
	 */
	public Node minimum(){
		return innerMinimum(root);
	}
	private Node innerMinimum(Node node){
		if(node.left!=null){
			return innerMinimum(node.left);
		}
		return node;
	}
	/**
	 * 返回�?大�?�节�?
	 * @return
	 */
	public Node maximum(){
		return innerMaximum(root);
	}
	private Node innerMaximum(Node node){
		if(node.right!=null){
			return innerMaximum(node.right);
		}
		return node;
	}
	/**
	 * 返回给定节点的后继结�?
	 * @param node
	 * @return
	 */
	public Node successor(Node node){
		if(node.right!=null){
			return innerMinimum(node.right);
		}
		Node y=node.parent;
		while(y!=null&&y.right==node){
			node=y;
			y=y.parent;
		}
		return y;
	}
	/**
	 * 插入
	 * @param node
	 */
	private void insert(Node node){
		if(node.low>node.high){
			int tmp=node.low;
			node.low=node.high;
			node.high=tmp;
		}
		Node y=null;
		Node x=root;
		while(x!=null){
			y=x;
			if(node.low<x.low){
				x=x.left;
			}else{
				x=x.right;
			}
		}
		node.parent=y;
		if(y==null){
			root=node;
		}else if(y.low>node.low){
			y.left=node;
		}else{
			y.right=node;
		}
		node.max=node.high;
		Node z=node;
		while(z!=null){
			if(z.left==null&&z.right!=null){
				z.max=Math.max(z.right.max, z.high);
			}else if(z.right==null&&z.left!=null){
				z.max=Math.max(z.left.max, z.high);
			}else if(z.right==null&&z.left==null){
				z.max=z.high;
			}else{
				z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
			}
			z=z.parent;
		}
		root.parent=null;
		node.color=Node.RED;
		preorderWalk();
		insertFixUp(node);
		preorderWalk();

	}
	/**
	 * 插入修复颜色
	 * @param node
	 */
	private void insertFixUp(Node node){
		if(node.parent==null){
			node.color=Node.BLACK;
		}else if(node.parent.parent==null){
			node.color=Node.RED;
		}else {
			while(node.parent==null||node.parent.color==Node.RED){
				if(node.parent==null){
					node.color=Node.BLACK;
					return;
				}else if(node.parent==node.parent.parent.left){
					Node y=node.parent.parent.right;
					if(y==null||y.color==Node.RED){
						node.parent.color=Node.BLACK;
						if(y!=null){
							y.color=Node.BLACK;
						}else{
							node.parent.parent.color=Node.RED;
							rightRotate(node.parent.parent);
							return;
						}
						node.parent.parent.color=Node.RED;
						
						node=node.parent.parent;
					}else if(node==node.parent.right){
						node=node.parent;
						leftRotate(node);
					}else{
						node.parent.color=Node.BLACK;
						node.parent.parent.color=Node.RED;
						rightRotate(node.parent.parent);
					}
				}else{
					Node y=node.parent.parent.left;
					if(y==null||y.color==Node.RED){
						node.parent.color=Node.BLACK;
						if(y!=null){
							y.color=Node.BLACK;
						}else{
							node.parent.parent.color=Node.RED;
							leftRotate(node.parent.parent);
							return;
						}
						node.parent.parent.color=Node.RED;
						
						node=node.parent.parent;
					}else if(node==node.parent.left){
						node=node.parent;
						rightRotate(node);
					}else{
						node.parent.color=Node.BLACK;
						node.parent.parent.color=node.RED;
						leftRotate(node.parent.parent);
					}
				}
			}
		}
	}
	public void insert(int low,int high){
		Node node=new Node();
		node.setLow(low);
		node.setHigh(high);
		insert(node);
	}
	private void delete(Node node){
		Node y=node;
		int yoc=y.color;
		Node x;
		if(node.left==null&&node.right!=null){
			 x=node.right;
			transplant(node, node.right);
			Node z=x;
			while(z!=null){
				if(z.left==null&&z.right!=null){
					z.max=Math.max(z.right.max, z.high);
				}else if(z.right==null&&z.left!=null){
					z.max=Math.max(z.left.max, z.high);
				}else if(z.right==null&&z.left==null){
					z.max=z.high;
				}else{
					z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
				}
				z=z.parent;
			}
		}else if(node.right==null&&node.left!=null){
			 x=node.left;
			transplant(node, node.left);
			Node z=x;
			while(z!=null){
				if(z.left==null&&z.right!=null){
					z.max=Math.max(z.right.max, z.high);
				}else if(z.right==null&&z.left!=null){
					z.max=Math.max(z.left.max, z.high);
				}else if(z.right==null&&z.left==null){
					z.max=z.high;
				}else{
					z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
				}
				z=z.parent;
			}
		}else if(node.left==null&&node.right==null){
			if(node.parent==null){
				root=null;
				System.out.println("root is null");
				return;
			}
			x=node.parent;
			Node z=x;
			
			if(node==node.parent.left){
				node.parent.left=null;
				while(z!=null){
					if(z.left==null&&z.right!=null){
						z.max=Math.max(z.right.max, z.high);
					}else if(z.right==null&&z.left!=null){
						z.max=Math.max(z.left.max, z.high);
					}else if(z.right==null&&z.left==null){
						z.max=z.high;
					}else{
						z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
					}
					z=z.parent;
				}
				if(x.color==Node.RED){
					leftRotate(x);
					preorderWalk();
					return;
				}else if(x.color==Node.BLACK&&node.color==Node.BLACK){
					x=node.parent.right;
					deleteFixUp(x);
					return;
				}
			}else{
				node.parent.right=null;
				while(z!=null){
					if(z.left==null&&z.right!=null){
						z.max=Math.max(z.right.max, z.high);
					}else if(z.right==null&&z.left!=null){
						z.max=Math.max(z.left.max, z.high);
					}else if(z.right==null&&z.left==null){
						z.max=z.high;
					}else{
						z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
					}
					z=z.parent;
				}
				if(x.color==Node.RED){
					rightRotate(x);
					preorderWalk();
					return;
				}else if(x.color==Node.BLACK&&node.color==Node.BLACK){
					x=node.parent.left;
					deleteFixUp(x);
					return;
				}
			}
		}else{
			y=innerMinimum(node.right);
			yoc=y.color;
			 
			if(y.parent!=node){
				Node z=y.right;
				transplant(y, y.right);
				while(z!=null){
					if(z.left==null&&z.right!=null){
						z.max=Math.max(z.right.max, z.high);
					}else if(z.right==null&&z.left!=null){
						z.max=Math.max(z.left.max, z.high);
					}else if(z.right==null&&z.left==null){
						z.max=z.high;
					}else{
						z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
					}
					z=z.parent;
				}
				y.right=node.right;
				y.right.parent=y;
				
			}
			Node z=y;
			transplant(node, y);
			while(z!=null){
				if(z.left==null&&z.right!=null){
					z.max=Math.max(z.right.max, z.high);
				}else if(z.right==null&&z.left!=null){
					z.max=Math.max(z.left.max, z.high);
				}else if(z.right==null&&z.left==null){
					z.max=z.high;
				}else{
					z.max=Math.max(Math.max(z.high, z.left.max),z.right.max);
				}
				z=z.parent;
			}
			x=y.right;
			y.left=node.left;
			y.left.parent=y;
			y.color=node.color;
			if(x==null){
				preorderWalk();
				y.color=Node.RED;
				if(y.left!=null){
					y.left.color=Node.BLACK;
					rightRotate(y);
				}else if(y.right!=null){
					y.right.color=Node.RED;
					leftRotate(y);
				}else{
					y.color=Node.RED;
				}
				preorderWalk();
				return;
				
			}
		}
		
		preorderWalk();
		if(yoc==Node.BLACK){
			deleteFixUp(x);
			preorderWalk();
		}
		
	}
	private void deleteFixUp(Node node){
		if(node==null){
			
		}
		while(node!=root&&node.color==Node.BLACK){
			Node w;
			if(node==node.parent.left){
				w=node.parent.right;
				if(w.color==Node.RED){
					w.color=Node.BLACK;
					node.parent.color=Node.RED;
					leftRotate(node.parent);
					w=node.parent.right;
				}
				if(w.left.color==Node.BLACK&&w.right.color==Node.BLACK){
					w.color=Node.RED;
					node=node.parent;
				}else if(w.right.color==Node.BLACK){
					w.left.color=Node.BLACK;
					w.color=Node.RED;
					rightRotate(w);
					w=node.parent.right;
				}
				w.color=node.parent.color;
				node.parent.color=Node.BLACK;
				w.right.color=Node.BLACK;
				leftRotate(node.parent);
				node=root;
				
			}else{
				w=node.parent.left;
				if(w.color==Node.RED){
					w.color=Node.BLACK;
					node.parent.color=Node.RED;
					rightRotate(node.parent);
					w=node.parent.left;
				}
				if(w.right.color==Node.BLACK&&w.left.color==Node.BLACK){
					w.color=Node.RED;
					node=node.parent;
				}else if(w.left.color==Node.BLACK){
					w.left.color=Node.BLACK;
					w.color=Node.RED;
					leftRotate(w);
					w=node.parent.left;
				}
				w.color=node.parent.color;
				node.parent.color=Node.BLACK;
				w.left.color=Node.BLACK;
				rightRotate(node.parent);
				node=root;
			}
		}
		node.color=Node.BLACK;
		
	}
	/**
	 * 左旋�?
	 * @param node
	 */
	private void leftRotate(Node node){
		Node y=node.right;
		node.right=y.left;
		if(y.left!=null){
			y.left.parent=node;
		}
		y.parent=node.parent;
		if(node.parent==null){
			root=y;
		}else if(node==node.parent.left){
			node.parent.left=y;
		}else{
			node.parent.right=y;
		}
		y.left=node;
		node.parent=y;
		
		if(node.left==null&&node.right!=null){
			node.max=Math.max(node.right.max, node.high);
		}else if(node.right==null&&node.left!=null){
			node.max=Math.max(node.left.max, node.high);
		}else if(node.right==null&&node.left==null){
			node.max=node.high;
		}else{
			node.max=Math.max(Math.max(node.high, node.left.max),node.right.max);
		}
		if(y.left==null&&y.right!=null){
			y.max=Math.max(y.right.max, y.high);
		}else if(y.right==null&&y.left!=null){
			y.max=Math.max(y.left.max, y.high);
		}else if(y.right==null&&y.left==null){
			y.max=y.high;
		}else{
			y.max=Math.max(Math.max(y.high, y.left.max),y.right.max);
		}
	}
	/**
	 * 右旋�?
	 * @param node
	 */
	private void rightRotate(Node node){
		Node y=node.left;
		node.left=y.right;
		if(y.right!=null){
			y.right.parent=node;
		}
		y.parent=node.parent;
		if(node.parent==null){
			root=y;
		}else if(node==node.parent.left){
			node.parent.left=y;
		}else{
			node.parent.right=y;
		}
		y.right=node;
		node.parent=y;
		if(node.left==null&&node.right!=null){
			node.max=Math.max(node.right.max, node.high);
		}else if(node.right==null&&node.left!=null){
			node.max=Math.max(node.left.max, node.high);
		}else if(node.right==null&&node.left==null){
			node.max=node.high;
		}else{
			node.max=Math.max(Math.max(node.high, node.left.max),node.right.max);
		}
		if(y.left==null&&y.right!=null){
			y.max=Math.max(y.right.max, y.high);
		}else if(y.right==null&&y.left!=null){
			y.max=Math.max(y.left.max, y.high);
		}else if(y.right==null&&y.left==null){
			y.max=y.high;
		}else{
			y.max=Math.max(Math.max(y.high, y.left.max),y.right.max);
		}
	}
	private void transplant(Node u,Node v){
		if(u.parent==null){
			root=v;
		}else if(u==u.parent.left){
			u.parent.left=v;
		}else{
			u.parent.right=v;
		}
		if(v!=null){
			v.parent=u.parent;
		}
	}
	/**
	 * 删除节点
	 * @param value
	 */
	public void delete(int low,int high){
		delete(search(low,high));
	}
	private static class Node{
		public static final int RED=1;
		public static final int BLACK=2;
		private Node left;
		private Node right;
		private Node parent;
		private int low;
		private int high;
		private int color;
		private int max;
		public Node getLeft() {
			return left;
		}
		public void setLeft(Node left) {
			this.left = left;
		}
		public Node getRight() {
			return right;
		}
		public void setRight(Node right) {
			this.right = right;
		}
		public Node getParent() {
			return parent;
		}
		public void setParent(Node parent) {
			this.parent = parent;
		}
		
		public int getColor() {
			return color;
		}
		public void setColor(int color) {
			this.color = color;
		}
		public int getLow() {
			return low;
		}
		public void setLow(int low) {
			this.low = low;
		}
		public int getHigh() {
			return high;
		}
		public void setHigh(int high) {
			this.high = high;
		}
		public int getMax() {
			return max;
		}
		public void setMax(int max) {
			this.max = max;
		}
		
		
		
	}
	public static void main(String[] args) {
		int [][] data=new int[][]{{1,2},{3,5},{2,4},{6,11},{3,9},{9,15},{1,10},{10,12},{11,16}};
		IntervalTree tree=new IntervalTree(data);
		tree.inorderTreeWalk();
		System.out.println("===========");
		System.out.println(tree.search(9, 15).low+","+tree.search(9, 15).high);
		tree.delete(9, 15);
		System.out.println(tree.search(11, 16).low+","+tree.search(11, 16).high);
		tree.delete(11, 16);
		
	}

}

