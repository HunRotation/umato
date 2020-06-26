"""
Utils

This includes quantitative measures to compare how the high-dimensional data and its low embedding result are similar.

Provides
  0. Root Mean Squared Error (RMSE)
  1. Kruskal stress measure
  2. Sammon's stress
  3. Spearman's Rho
  4. Trustworthiness & Continuity
  5. Mean Relative Rank Error (MRRE)
  6. Global density distribution
  7. KL Divergence between density distributions
  8. Set difference (TODO)
  9. Projection precision score (PPS) (TODO)
  10. Distance Consistency (TODO)
  11. ClustMe (TODO)

References
----------
.. [1] Kruskal's Stress Measure (1964)
    - J. Kruskal, Multidimensional scaling by optimizing goodness of fit to a nonmetric hypothesis, Psychometrika 29 (1964) 1-27.
    - J. Kruskal, Nonmetric multidimensional scaling: a numerical method, Psychometrika 29 (1964) 115-129. 

.. [2] Sammon's Stress (1969)
    - J.W. Sammon, A nonlinear mapping for data structure analysis, IEEE Trans. Comput. C-18 (1969). 
    - https://en.wikipedia.org/wiki/Sammon_mapping

.. [3] Spearman's Rho
    - Corder, G. W. & Foreman, D. I. (2014). Nonparametric Statistics: A Step-by-Step Approach, Wiley. ISBN 978-1118840313.
    - https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient

.. [4] Trustworthiness & Continuity (2001)
    - J. Venna, S. Kaski, Local multidimensional scaling, Neural Networks 19 (2006) 889-899.

.. [5] MRRE (2007)
    - J.A. Lee, M. Verleysen, Nonlinear dimensionality reduction, Springer, New York, London, 2007.
    - J.A. Lee, M. Verleysen, Rank-based quality assessment of nonlinear dimensionality reduction, in: ESANN, 2008, pp. 49-54.
    - J.A. Lee, M. Verleysen, Quality assessment of dimensionality reduction: rank-based criteria, Neurocomput 72 (2009) 1431-1443.
    - http://www.ecmlpkdd2008.org/files/pdf/workshops/fsdm/2.pdf 

.. [6] Global density distribution
    - Frédéric Chazal, David Cohen-Steiner, and Quentin Mérigot. Geometric inference for probability measures.
    Foundations of Computational Mathematics, 11(6):733–751, 2011.
    - Frédéric Chazal, Brittany T. Fasy, Fabrizio Lecci, Bertrand Michel, Alessandro Rinaldo, and Larry Wasserman.
    Robust topological inference: Distance to a measure and kernel distance. arXiv e-prints, art. arXiv:1412.7197, 2014b.

.. [7] KL Divergence between density distributions
    - Moor, M., Horn, M., Rieck, B., & Borgwardt, K. (2020). Topological autoencoders. ICML.

.. [8] Set difference (2015) - focuses on neighborhood preservation
    - R. M. Martins, R. Minghim, and A. C. Telea, “Explaining Neighborhood Preservation for Multidimensional Projections,”
    in Proceedings of the Computer Graphics & Visual Computing (CGVC ’15). Eurographics, 2015, pp. 121–128.

.. [9] Projection precision score (2010) - local measure
    - T. Schreck, T. von Landesberger, and S. Bremm, “Techniques for Precision-Based Visual Analysis of Projected Data,”
    Information Visualization, vol. 9, no. 3, pp. 181–193, 2010.

.. [10] Distance consistency (2009)
    - M. Sips, B. Neubert, J. Lewis, and P. Hanrahan, “Selecting Good Views of High-Dimensional Data Using Class Consistency,”
    Computer Graphics Forum, vol. 28, no. 3, pp. 831–838, 2009.

.. [11] ClustMe (2019) - perception based measure
    - M. M. Abbas, M. Aupetit, M. Sedlmair, and H. Bensmail, “ClustMe: A Visual Quality Measure for Ranking Monochrome Scatterplots based on Cluster Patterns,”
    Computer Graphics Forum, vol. 38, no. 3, pp. 225–236, 2019.

.. [Survey]
    - L. G. Nonato and M. Aupetit, “Multidimensional Projection for Visual Analytics: Linking Techniques with Distortions, Tasks, and Layout Enrichment,”
    IEEE Transactions on Visualization and Computer Graphics, vol. 25, no. 8, pp. 2650–2673, 2019.
    - Gracia, A., González, S., Robles, V., & Menasalvas, E. (2014).
    A methodology to compare dimensionality reduction algorithms in terms of loss of quality. Information Sciences, 270, 1-27.


"""

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr


class Measure:
    def __init__(self, x, z, k):
        self.k = k  # number of nearest neighbors
        self.n_data = x.shape[0]  # number of data
        self.pdist_x = pdist(x)
        self.pdist_z = pdist(z)
        self.adjacency_matrix_x = squareform(self.pdist_x)
        self.adjacency_matrix_z = squareform(self.pdist_z)
        self.nnidx_x, self.rank_x = self.get_nnidx_rank(self.adjacency_matrix_x)
        self.nnidx_z, self.rank_z = self.get_nnidx_rank(self.adjacency_matrix_z)

    def rmse(self):
        """
        Root Mean Squared Error (RMSE)
        - Lower is BETTER
        - Global
        """
        sum_of_squared_differences = np.square(
            self.adjacency_matrix_x - self.adjacency_matrix_z
        ).sum()
        return np.sqrt(sum_of_squared_differences / self.n_data ** 2)

    def kruskal_stress_measure(self):
        """
        Kruskal Stress Measure

        A measure to capture the deviation from monotonicity
        - Lower is BETTER
        - Global
        """
        sum_of_squared_diff = np.square(self.pdist_x - self.pdist_z).sum() * 2
        sum_of_squares_z = np.square(self.pdist_z).sum() * 2
        return np.sqrt(sum_of_squared_diff / sum_of_squares_z)

    def sammon_stress(self):
        """
        Sammon's Stress

        An error measure used to test structure preservation
        - Lower is BETTER
        - Global
        """
        squared_diff = np.square(self.pdist_x - self.pdist_z)
        sum_of_squares_x = np.square(self.pdist_x)
        return (squared_diff / sum_of_squares_x).sum() / sum_of_squares_x.sum()

    def get_nnidx_rank(self, arr):
        """
        Get the index of NNs and ranks
        """
        idx = arr.argsort()
        return idx[:, 1 : self.k + 1], idx.argsort()

    def spearmans_rho(self):
        """
        Spearman's Rho

        This measure estimates the correlation of rank order data.
        It is defined as the Pearson correlation coefficient between the rank variables, 
        and can be viewed as one of the local neighborhood preservation measures.
        - Higher is BETTER (Preserved)
        - Local
        """

        ranks_list_x = []
        ranks_list_z = []
        for n in range(self.n_data):
            # get NNs in n-th row (in terms of high-dimensional space)
            rx = self.rank_x[n][self.nnidx_x[n]]
            rz = self.rank_z[n][self.nnidx_x[n]]
            # append them at once
            ranks_list_x.extend(rx)
            ranks_list_z.extend(rz)
        coeff, _ = spearmanr(ranks_list_x, ranks_list_z)

        return coeff

    def trustworthiness(self):
        """
        Trustworthiness

        A measure to check what extent the k nearest neighbours of a point are preserved when going from the original space to the latent space.
        If it is low it means that the data points originally farther away are captured as NNs of the embedding
        - Higher is BETTER (Preserved)
        - Local
        """
        return self._tc_calculation(
            self.nnidx_x, self.rank_x, self.nnidx_z, self.n_data, self.k
        )

    def continuity(self):
        """
        Continuity

        If it is low it means that data points that are originally close in high-dim are not captured as NNs in the embedding.
        - Higher is BETTER (Preserved)
        - Local
        """
        return self._tc_calculation(
            self.nnidx_z, self.rank_z, self.nnidx_x, self.n_data, self.k
        )

    @staticmethod
    def _tc_calculation(nnidx_base, rank, nnidx_target, n_data, k):
        value = 0.0

        # Calculate NNs comparing base and target space
        for n in range(n_data):
            # get NNs in lower dimension that was NOT NNs in high dimension
            missings = np.setdiff1d(nnidx_target[n], nnidx_base[n])

            for missing in missings:
                value += rank[n, missing] - k

        return 1 - 2 / (n_data * k * (2 * n_data - 3 * k - 1)) * value

    def mrre(self, ratio=0.5):
        """
        Mean Relative Rank Error (MRRE)

        Parameters
        ----------
        ratio : float
            ratio between 'mrre_zx' and 'mrre_xz',
            where mrre_zx ~= continuity and mrre_xz ~= trustworthiness

        Similar to trustworthiness & continuity but uses normalizing factor
        It denotes how well the NNs are preserved in terms of one space to another.
        - Higher is BETTER (Preserved)
        - Local
        """
        mrre_xz = self._mrre_caculation(
            self.nnidx_x, self.rank_x, self.rank_z, self.n_data, self.k
        )
        mrre_zx = self._mrre_caculation(
            self.nnidx_z, self.rank_z, self.rank_x, self.n_data, self.k
        )
        return mrre_xz * ratio + mrre_zx * (1 - ratio)

    @staticmethod
    def _mrre_caculation(nnidx_base, rank_base, rank_target, n_data, k):
        mrre_temp = 0.0
        for n in range(n_data):
            rank_targets = rank_target[n][nnidx_base[n]]
            rank_bases = rank_base[n][nnidx_base[n]]
            rank_norm = abs(rank_targets - rank_bases) / rank_bases
            mrre_temp += rank_norm.sum()

        # normalizing constant
        c = n_data * sum([abs(n_data - 2 * i + 1) / i for i in range(1, k + 1)])
        return 1 - mrre_temp / c
