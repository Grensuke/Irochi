import pandas as pd
import glob
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-dir', required=True)
    args = parser.parse_args()

    files = glob.glob(os.path.join(args.dataset_dir, '*.csv'))
    for f in files:
        try:
            df = pd.read_csv(f, usecols=['Label', ' Label'], skipinitialspace=True, encoding='latin1', low_memory=False)
            labels = df.iloc[:, 0].unique()
            print(f"{os.path.basename(f)}:")
            for l in labels:
                print(f"  - {l}")
        except Exception as e:
            try:
                df = pd.read_csv(f, usecols=['Label'], skipinitialspace=True, encoding='latin1', low_memory=False)
                labels = df['Label'].unique()
                print(f"{os.path.basename(f)}:")
                for l in labels:
                    print(f"  - {l}")
            except Exception as e:
                print(f"Failed to read {os.path.basename(f)}: {e}")

if __name__ == '__main__':
    main()
