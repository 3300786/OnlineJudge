#include <bits/stdc++.h>

int dfs(int x){
return dfs(x-1)+dfs(x-2);}

int main(){
while(1){std::cout<<dfs(10);}
}