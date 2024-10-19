import pandas as pd

def read_excel_file(file_path):
    try:
        df = pd.read_excel(file_path)
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst few rows:")
        print(df.head().to_string())
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

if __name__ == "__main__":
    read_excel_file('smsex.xlsx')
