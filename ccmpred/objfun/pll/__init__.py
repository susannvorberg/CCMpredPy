import numpy as np

import ccmpred.raw
import ccmpred.regularization
import ccmpred.objfun
import ccmpred.objfun.pll.cext


class PseudoLikelihood(ccmpred.objfun.ObjectiveFunction):

    def __init__(self, msa, weights, regularization):

        self.msa = msa

        self.nrow, self.ncol = msa.shape
        self.nsingle = self.ncol * 20
        self.nsingle_padded = self.nsingle + 32 - (self.nsingle % 32)
        self.nvar = self.nsingle_padded + self.ncol * self.ncol * 21 * 32

        self.weights = weights

        self.regularization = regularization

        # memory allocation for intermediate variables
        self.g = np.empty((self.nsingle_padded + self.ncol * self.ncol * 21 * 32,), dtype=np.dtype('float64'))
        self.g2 = np.empty((self.ncol * self.ncol * 21 * 32,), dtype=np.dtype('float64'))

    @classmethod
    def init_from_default(cls, msa, weights, regularization):
        res = cls(msa, weights, regularization)

        if hasattr(regularization, "center_x_single"):
            ncol = msa.shape[1]
            x_pair = np.zeros((ncol, ncol, 21, 21), dtype="float64")
            x = structured_to_linear(regularization.center_x_single, x_pair)

        else:
            x = np.zeros((res.nvar, ), dtype=np.dtype('float64'))

        return x, res

    @classmethod
    def init_from_raw(cls, msa, weights, raw, regularization):
        res = cls(msa, weights, regularization)

        if msa.shape[1] != raw.ncol:
            raise Exception('Mismatching number of columns: MSA {0}, raw {1}'.format(msa.shape[1], raw.ncol))

        x = structured_to_linear(raw.x_single, raw.x_pair)
        res.v_centering[:] = raw.x_single.reshape(-1)

        return x, res

    def finalize(self, x):
        x_single, x_pair = linear_to_structured(x, self.ncol, clip=True)
        return ccmpred.raw.CCMRaw(self.ncol, x_single, x_pair, {})

    def evaluate(self, x):
        fx, g = ccmpred.objfun.pll.cext.evaluate(x, self.g, self.g2, self.weights, self.msa)

        x_single, x_pair = linear_to_structured(x, self.ncol)
        g_single, g_pair = linear_to_structured(g, self.ncol)

        fx_reg, g_single_reg, g_pair_reg = self.regularization(x_single, x_pair)

        v_centering = self.regularization.center_x_single


        fx += fx_reg
        g[:self.nsingle] += g_single_reg.reshape(-1)
        g[self.nsingle_padded:] += np.transpose(g_pair_reg, (3, 1, 2, 0)).reshape(-1)

        return fx, g


def linear_to_structured(x, ncol, clip=False):
    """Convert linear vector of variables into multidimensional arrays"""
    nsingle = ncol * 20
    nsingle_padded = nsingle + 32 - (nsingle % 32)

    x_single = x[:nsingle].reshape((20, ncol)).T
    x_pair = np.transpose(x[nsingle_padded:].reshape((21, ncol, 32, ncol)), (3, 1, 2, 0))

    if clip:
        x_pair = x_pair[:, :, :21, :21]

    return x_single, x_pair


def structured_to_linear(x_single, x_pair):
    """Convert structured variables into linear array"""
    ncol = x_single.shape[0]
    nsingle = ncol * 20
    nsingle_padded = nsingle + 32 - (nsingle % 32)
    nvar = nsingle_padded + ncol * ncol * 21 * 32

    out_x_pair = np.zeros((21, ncol, 32, ncol), dtype='float64')
    out_x_pair[:21, :, :21, :] = np.transpose(x_pair[:, :, :21, :21], (3, 1, 2, 0))

    x = np.zeros((nvar, ), dtype='float64')
    x[:nsingle] = x_single.T.reshape(-1)
    x[nsingle_padded:] = out_x_pair.reshape(-1)

    return x
