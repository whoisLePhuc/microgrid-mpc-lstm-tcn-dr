import numpy as np
from scipy import sparse
import osqp

class MPCController:
    def __init__(self, nx=5, nu=3, np_inner=2):
        self.nx, self.nu, self.np = nx, nu, np_inner
        self.Q = np.diag([10, 50, 10, 100, 1])
        self.QN = self.Q.copy()
        self.R = np.eye(nu) * 0.04
        self._build_qp()

    def _build_qp(self):
        N, nx, nu = self.np, self.nx, self.nu
        n_vars = (N+1)*nx + N*nu
        blocks = [sparse.csc_matrix(self.Q) for _ in range(N)]
        blocks.append(sparse.csc_matrix(self.QN))
        blocks.extend([sparse.csc_matrix(self.R) for _ in range(N)])
        self.P = sparse.block_diag(blocks, format='csc')
        self.q = np.zeros(n_vars)
        self.Aineq = sparse.eye(n_vars, format='csc')
        self.prob = None

    def _build_dynamics(self, Ad, Bd):
        N, nx, nu = self.np, self.nx, self.nu
        Ax = sparse.kron(sparse.eye(N+1), -sparse.eye(nx)) + \
             sparse.kron(sparse.eye(N+1, k=-1), sparse.csc_matrix(Ad))
        Bu = sparse.kron(
            sparse.vstack([sparse.csc_matrix((1, N)), sparse.eye(N)]),
            sparse.csc_matrix(Bd))
        return sparse.hstack([Ax, Bu], format='csc')

    def solve(self, x0, Ad, Bd, x_ref, u_min=None, u_max=None):
        N, nx, nu = self.np, self.nx, self.nu
        if u_min is None: u_min = np.zeros(nu)
        if u_max is None: u_max = np.ones(nu)
        self.q[:nx] = -2 * self.Q @ x_ref
        Aeq = self._build_dynamics(sparse.csc_matrix(Ad), sparse.csc_matrix(Bd))
        lineq = np.hstack([-x0, np.zeros(N * nx)])
        l = np.hstack([lineq, np.kron(np.ones(N+1), -1e3*np.ones(nx)), np.kron(np.ones(N), u_min)])
        u = np.hstack([lineq, np.kron(np.ones(N+1), 1e3*np.ones(nx)), np.kron(np.ones(N), u_max)])
        A = sparse.vstack([Aeq, self.Aineq], format='csc')
        if self.prob is None:
            self.prob = osqp.OSQP()
            self.prob.setup(self.P, self.q, A, l, u,
                           warm_starting=True, eps_abs=1e-4, eps_rel=1e-4)
        else:
            self.prob.update(Ax=A.data, l=l, u=u)
        res = self.prob.solve()
        if res.info.status != 'solved':
            return np.array([0.5, 0.5, 0.5])
        return np.clip(res.x[(N+1)*nx:(N+1)*nx + nu], 0, 1)
