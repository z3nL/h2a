#ifndef TESTCLASS_H
#define TESTCLASS_H

#include <string>

class testClass {
    private:
        int val;
        int val2;
        std::string name;
    public:
        void changeVal(int newV) {
            val = newV;
        }
        void changeVal2(int newV) {
            val2 = newV;
        }
        void changeName(std::string newName) {
            name = newName;
        }

        int getVal() {
            return val;
        }
        int getVal2() {
            return val2;
        }
        std::string getName() {
            return name;
        }
};

#endif