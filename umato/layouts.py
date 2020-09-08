import numpy as np
import numba
import umato.distances as dist
from umato.utils import (
    tau_rand_int,
    adjacency_matrix,
    clip,
    rdist,
)
import matplotlib.pyplot as plt


def get_CE(P, Y, d_squared, a, b):
    Q = pow(1 + a * d_squared ** b, -1)
    loss = -P * np.log(Q + 0.001) - (1 - P) * np.log(1 - Q + 0.001)
    return loss.sum() / 1e5


def get_DTM(adj_x, adj_z, sigma=0.1):
    density_x = calc_DTM(adj_x, sigma)
    density_z = calc_DTM(adj_z, sigma)
    return np.abs(density_x - density_z).sum()


def calc_DTM(adj, sigma):
    density = np.sum(np.exp(-(adj ** 2) / sigma), axis=-1)
    return density / density.sum()


def optimize_global_layout(
    P,
    Z,
    a,
    b,
    alpha=0.01,
    max_iter=10,
    verbose=False,
    savefig=False,
    label=None
):

    costs = []

    for i in range(max_iter):

        d_squared = np.square(adjacency_matrix(Z))
        z_diff = np.expand_dims(Z, axis=1) - np.expand_dims(Z, axis=0)
        d_inverse = np.expand_dims(pow(1 + a * d_squared ** b, -1), axis=2)

        # Q is the normalized distance in low dimensional space 
        Q = pow(0.001 + d_squared, -1)
        np.fill_diagonal(Q, 0)
        Q = np.dot(1 - P, Q)
        Q /= np.sum(Q, axis=1, keepdims=True)
        # Q /= Q.max()

        grad = np.expand_dims(
            2 * a * b * P * (1e-12 + d_squared) ** (b - 1) - 2 * b * Q, axis=2
        )
        dZ = np.sum(grad * z_diff * d_inverse, axis=1)
        Z -= alpha * dZ

        if verbose:
            # cost = get_CE(P, Z, d_squared, a, b)
            cost = get_DTM(P, Q, sigma=0.1)
            costs.append(cost)
            print(
                f"[INFO] Current loss: {cost:.6f}, @ iteration: {i+1}/{max_iter}, alpha: {alpha}"
            )

        if savefig:
            if i % 4 == 1:
                from umato.umato_ import plot_tmptmp
                plot_tmptmp(data=Z, label=label, name=f"pic1_global{i}")

    return Z


def nn_layout_optimize(
    head_embedding,
    tail_embedding,
    head,
    tail,
    hub_info,
    n_epochs,
    n_vertices,
    epochs_per_sample,
    a,
    b,
    rng_state,
    gamma=1.0,
    initial_alpha=1.0,
    negative_sample_rate=5.0,
    parallel=False,
    verbose=False,
    label=None,
):

    (num, dim) = head_embedding.shape
    move_other = head_embedding.shape[0] == tail_embedding.shape[0]
    alpha = initial_alpha

    epochs_per_negative_sample = epochs_per_sample / negative_sample_rate
    epoch_of_next_negative_sample = epochs_per_negative_sample.copy()
    epoch_of_next_sample = epochs_per_sample.copy()

    optimize_fn = numba.njit(
        _nn_layout_optimize_single_epoch, fastmath=True, parallel=parallel
    )
    for n in range(n_epochs):
        optimize_fn(
            head_embedding,
            tail_embedding,
            head,
            tail,
            hub_info,
            n_vertices,
            epochs_per_sample,
            a,
            b,
            rng_state,
            gamma,
            dim,
            move_other,
            alpha,
            epochs_per_negative_sample,
            epoch_of_next_negative_sample,
            epoch_of_next_sample,
            n,
        )

        alpha = initial_alpha * (1.0 - (float(n) / float(n_epochs)))

        if verbose and n % 10 == 0:
            from umato.umato_ import plot_tmptmp

            plot_tmptmp(data=head_embedding, label=label, name=f"pic3_local{n}")
            # plot_tmptmp(data=tail_embedding, label=label, name=f"pic3_tail{n}")

        if verbose and n % 5 == 0:
            print("\tcompleted ", n, " / ", n_epochs, "epochs")

    plot_tmptmp(data=head_embedding, label=label, name=f"pic3_local{n}")
    return head_embedding


def _nn_layout_optimize_single_epoch(
    head_embedding,
    tail_embedding,
    head,
    tail,
    hub_info,
    n_vertices,
    epochs_per_sample,
    a,
    b,
    rng_state,
    gamma,
    dim,
    move_other,
    alpha,
    epochs_per_negative_sample,
    epoch_of_next_negative_sample,
    epoch_of_next_sample,
    n,
):
    for i in numba.prange(epochs_per_sample.shape[0]):
        if epoch_of_next_sample[i] <= n:
            j = head[i]  # j == source index
            k = tail[i]  # k == target index

            current = head_embedding[j]  # current == source location
            other = tail_embedding[k]  # other == target location

            dist_squared = rdist(current, other)  # get distance between them

            if dist_squared > 0.0:
                grad_coeff = -2.0 * a * b * pow(dist_squared, b - 1.0)
                grad_coeff /= a * pow(dist_squared, b) + 1.0
            else:
                grad_coeff = 0.0

            for d in range(dim):
                grad_d = clip(grad_coeff * (current[d] - other[d]), 10.0)

                grad_other = 0.0
                grad_current = 0.0
                grad_neg = 0.001
                if hub_info[k] == 1:
                    grad_current = 0.01
                    grad_other = 0.01
                elif hub_info[k] == 2:
                    grad_current = 0.01
                    grad_other = 0.001

                current[d] += grad_d * alpha * grad_current

                if move_other:
                    other[d] += -grad_d * alpha * grad_other

            epoch_of_next_sample[i] += epochs_per_sample[i]

            n_neg_samples = int(
                (n - epoch_of_next_negative_sample[i]) / epochs_per_negative_sample[i]
            )

            for p in range(n_neg_samples):
                while True:
                    k = tau_rand_int(rng_state) % n_vertices
                    if hub_info[k] > 0:
                        break

                other = tail_embedding[k]
                dist_squared = rdist(current, other)

                if dist_squared > 0.0:
                    grad_coeff = 2.0 * gamma * b
                    grad_coeff /= (0.001 + dist_squared) * (
                        a * pow(dist_squared, b) + 1
                    )
                elif j == k:
                    continue
                else:
                    grad_coeff = 0.0

                for d in range(dim):
                    if grad_coeff > 0.0:
                        grad_d = clip(grad_coeff * (current[d] - other[d]), 10.0)
                    else:
                        grad_d = 10.0

                    current[d] += grad_d * alpha * grad_neg

            epoch_of_next_negative_sample[i] += (
                n_neg_samples * epochs_per_negative_sample[i]
            )
