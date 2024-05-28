import os
import numpy as np
import faiss
import faiss.contrib.torch_utils
from prettytable import PrettyTable
import torch
import warnings
warnings.filterwarnings("ignore")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def get_validation_recalls(r_list: np.ndarray,
                           q_list: np.ndarray,
                           k_values: list,
                           gt: list,
                           print_results: bool = True,
                           faiss_gpu: bool = False,
                           dataset_name: str = 'dataset without name ?'):
    """
    Function to calculate recall at different 'k' values for a given dataset.
    Parameters:
        r_list (numpy array): Array of reference embeddings.
        q_list (numpy array): Array of query embeddings.
        k_values (list): List of integers representing the 'k' values for recall calculation.
        gt (list): List of ground truth values.
        print_results (bool, optional): Whether to print the results. Defaults to True.
        faiss_gpu (bool, optional): Whether to use Faiss GPU for indexing. Defaults to False.
        dataset_name (str, optional): Name of the dataset. Defaults to 'dataset without name ?'.
    Returns:
        dict, numpy array: A dictionary containing recall values at different 'k' values, and an array of predictions.
    """

    embed_size = r_list.shape[1]

    r_list = torch.tensor(r_list, dtype=torch.float32)  # changed
    q_list = torch.tensor(q_list, dtype=torch.float32)  # changed

    if faiss_gpu:
        res = faiss.StandardGpuResources()
        flat_config = faiss.GpuIndexFlatConfig()
        flat_config.useFloat16 = True
        flat_config.device = 0
        faiss_index = faiss.GpuIndexFlatL2(res, embed_size, flat_config)
    # build index
    else:
        faiss_index = faiss.IndexFlatL2(embed_size)

    # print(r_list)
    # add references
    faiss_index.add(r_list)

    # search for queries in the index
    _, predictions = faiss_index.search(q_list, max(k_values))

    # start calculating recall_at_k
    correct_at_k = np.zeros(len(k_values))
    for q_idx, pred in enumerate(predictions):
        for i, n in enumerate(k_values):
            # if in top N then also in top NN, where NN > N
            if np.any(np.in1d(pred[:n], gt[q_idx])):
                correct_at_k[i:] += 1
                break

    correct_at_k = correct_at_k / len(predictions)
    d = {k: v for (k, v) in zip(k_values, correct_at_k)}

    if print_results:
        print('\n')  # print a new line
        table = PrettyTable()
        table.field_names = ['K']+[str(k) for k in k_values]
        table.add_row(['Recall@K'] + [f'{100*v:.2f}' for v in correct_at_k])
        print(table.get_string(title=f"Performance on {dataset_name}"))

    return d, predictions


if __name__ == '__main__':
    # dummy data
    r_list = np.random.rand(100, 512)
    q_list = np.random.rand(1, 512)
    k_values = [1, 5]
    gt = np.random.randint(0, 100, 100)
    r, p = get_validation_recalls(r_list, q_list, k_values, gt)
    print(r)
    print(p)
    print(p.shape)
