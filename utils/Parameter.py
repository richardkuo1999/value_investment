import os

from utils.utils import txt_read, write2txt


default_Parameter = [3, 4.5, None]

def Parameter_read(file):
    txtdata = txt_read(file).split("\n")
    try:
        level = int(txtdata[0])
        year = float(txtdata[1])
        e_eps = float(txtdata[2]) if txtdata[2].lower() != "none" else None
    except:
        level, year, e_eps = default_Parameter
    return [level, year, e_eps]


"""
parameter -> sel
# Description: EPS year
# # N: This year
# # 0: N + 0
# # 1: N + 1
# # 2: N + 2

parameter -> level
Description: select forward eps value
# 0: high, 1: low, 2: average, 3: medium
"""


def ModifideParameter() -> list:
    msgList = [
        # "EPS year:  (default is 1)\nN: This year\n\t0: N + 0\n\t1: N + 1\n\t2: N + 2",
        "select forward eps value:  (default is 3)\n\t0: high\n\t1: low\n\t2: average\n\t3: medium",
        "Reference how many years: (default is 4.5)",
        "e_eps (default is None):",
    ]
    float_input = [2, 3]

    Parameter = []
    with open("Parameter.txt", "w") as pf:
        for i in range(3):
            os.system("cls")
            print(msgList[i])
            UserInput = input("Input: ")
            try:
                if i in float_input:
                    Parameter.append(float(UserInput))
                else:
                    Parameter.append(int(UserInput))
            except:
                print(f"Use default Value: {default_Parameter[i]}")
                Parameter.append(default_Parameter[i])
                input()
            write2txt(Parameter[i], pf)

        print(f"your Parameter: {Parameter}")
        input()
    return Parameter

