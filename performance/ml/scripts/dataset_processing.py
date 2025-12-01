import pandas as pd
from sklearn.model_selection import train_test_split

def load_and_split_data(csv_path="../data/features.csv", test_size=0.2, random_state=42):

    # Load dataset
    df = pd.read_csv("performance/ml/data/features.csv")

    # Separate features (X) and target (y)
    X = df.drop("pass_fail", axis=1)
    y = df["pass_fail"]

    # Train-test split
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    return X_train, X_test, Y_train, Y_test


if __name__ == "__main__":
    X_train, X_test, Y_train, Y_test = load_and_split_data()
    print("Data loaded and split successfully!")
    print("Train:", X_train.shape)
    print("Test:", X_test.shape)
