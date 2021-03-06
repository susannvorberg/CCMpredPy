import numpy as np
import json
import gzip
import os
import sys

def frobenius_score(x):
    """
    Compute frobenius norm of couplig matrix

    :param x:   pair potentials of dimension [ L x L x 20 x 20 ]
    :param squared:
    :return:
    """

    return np.sqrt(np.sum(x * x, axis=(2, 3)))

def apc(cmat):
    """
    Compute average product correction (APC) according to Dunn et al 2004

    :param cmat: contact matrix
    :return:    corrected contact matrix
    """
    print("Apply Average Product Correction (APC)")

    mean = np.mean(cmat, axis=0)
    apc_term = mean[:, np.newaxis] * mean[np.newaxis, :] / np.mean(cmat)

    return cmat - apc_term

def compute_scaling_factor(x_pair, uij, nr_states, squared=True):
    """
    Set the strength of the entropy correction by optimization eta with least squares

    Minimize sum_i,j sum_a,b (w_ijab^2 -  eta * u_ia * u_jb)^2

    :param x_pair:      raw coupling scores
    :param uij:
    :param nr_states:   normalize entropy wrt 20 or 21 characters
    :param squared:
    :return:
    """

    squared_sum_couplings = np.sum(x_pair[:,:,:20,:20] * x_pair[:,:,:20,:20], axis=(3,2))

    if squared:

        squared_sum_entropy = np.sum(uij[:,:,:nr_states,:nr_states], axis=(3,2))
        scaling_factor = np.sum(squared_sum_couplings * squared_sum_entropy)

        denominator = np.sum(uij * uij)
        scaling_factor /= denominator

    else:

        #According to Stefan's CCMgen paper
        #both are LxL matrices
        c_ij =  np.sqrt(squared_sum_couplings)
        e_ij =  np.sqrt(np.sum(uij[:,:,:nr_states,:nr_states], axis=(3,2)))

        scaling_factor = np.sum(c_ij  * e_ij)
        denominator = np.sum(uij[:,:,:nr_states,:nr_states])
        scaling_factor /= denominator

    return scaling_factor

def compute_local_correction(
        single_freq, x_pair, Neff, lambda_w, squared=True,
        entropy=False, nr_states=20, log=np.log2):

    print("Apply entropy correction (using {0} states and {1})".format(nr_states, log.__name__))


    if entropy:
        N_factor = 1
        ui = N_factor * single_freq[:, :nr_states] * log(single_freq[:, :nr_states])
    else:
        #correct for fractional counts
        N_factor = np.sqrt(Neff) * (1.0 / lambda_w)
        ui = N_factor * single_freq[:, :nr_states] * (1 - single_freq[:, :nr_states])
    uij = np.transpose(np.multiply.outer(ui, ui), (0,2,1,3))

    ### compute optimal scaling factor
    scaling_factor = compute_scaling_factor(x_pair, uij, nr_states, squared=squared)

    if not squared:
        mat = frobenius_score(x_pair)
        correction = scaling_factor * np.sqrt(np.sum(uij, axis=(3, 2)))
    else:
        mat = np.sum(x_pair * x_pair, axis=(2, 3))
        correction = scaling_factor * np.sum(uij, axis=(3, 2))

    return scaling_factor, mat - correction


def write_matrix(matfile, mat, meta):

    if matfile.endswith(".gz"):
        with gzip.open(matfile, 'wb') as f:
            np.savetxt(f, mat)
            #f.write("#>META> ".encode("utf-8") + json.dumps(meta).encode("utf-8") + "\n".encode("utf-8"))
            f.write("#>META> " + json.dumps(meta) + "\n")
        f.close()
    else:
        np.savetxt(matfile, mat)
        with open(matfile,'a') as f:
            f.write("#>META> " + json.dumps(meta) + "\n")
        f.close()

def read_matrix(matfile):
    """
    Read matrix file
    :param mat_file: path to matrix file
    :return: matrix
    """

    if not os.path.exists(matfile):
        raise IOError("Matrix File " + str(matfile) + "cannot be found. ")


    ### Read contact map (matfile can also be compressed file)
    mat = np.genfromtxt(matfile, comments="#")

    ### Read meta data from mat file
    meta = {}
    with open(matfile) as f:
        for line in f:
            if '#>META>' in line:
                meta = json.loads(line.split("> ")[1])

    if len(meta) == 0:
        print(str(matfile) + " does not contain META info. (Line must start with #META!)")

    return mat, meta