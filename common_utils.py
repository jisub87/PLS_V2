'''
    pickle 이용한 저장/출력
'''
import pickle

def read_data(path):
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}

def write_data(data, path):
    try:
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    except FileNotFoundError:
        print('save error')
