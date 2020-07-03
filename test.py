import umato
from sklearn.datasets import load_digits
from evaluation.models.dataset import get_data, save_csv


if __name__ == "__main__":
    # x = load_digits()  # (1797, 64 dim)
    x, label = get_data("mnist")  # spheres, mnist, fmnist, cifar10

    # Synthetic data to check the # of connected components
    # import numpy as np
    # x = np.array([[1,1,1,1,1]]*50 + [[7,7,7,7,7]]*50)

    # UMTO
    embedding = umato.UMATO(verbose=True).fit_transform(x)

    print(embedding)
