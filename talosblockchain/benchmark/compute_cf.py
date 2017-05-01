import numpy as np

with open("./compression_smartmeter_data.log",'r') as in_f, open("./compression_smartmeter_data_cf.log", 'w') as out_f:
    result = []
    for idx, line in enumerate(in_f):
        if idx > 0:
            result.append(map(float, line.split(",")))
    result_mat = np.asarray(result)
    result_mat[:, 1] = result_mat[:, 1] / result_mat[:, 2]
    out_f.write("Chunk Size, CF Plain\n")
    for i in range(len(result)):
        out_f.write("%d, %0.2f\n" % (int(result_mat[i, 0]), result_mat[i, 1]))

