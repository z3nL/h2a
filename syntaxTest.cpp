#include <iostream>
#include "testClass.h"
using namespace std;

int main(void) {
    testClass obj;
    
    obj.changeVal(17);
    obj.changeVal2(38);
    obj.changeName("ay");

    cout << obj.getVal() << " " << obj.getVal2() << " " << obj.getName();

    return 0;
}