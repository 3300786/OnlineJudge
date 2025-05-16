#include <bits/stdc++.h>

int dfs(int x){
return dfs(x-1)+dfs(x-2);}

int main(){
int a,b;
cin>>a>>b;
cout<<a+b<<endl;
}