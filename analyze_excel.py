import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_excel():
    try:
        df = pd.read_excel('Tracking Smartphone - Free Remote Monitoring Tool For Android (11).xlsx')
        logger.info(f"Excel file columns: {df.columns.tolist()}")
        logger.info("\nFirst few rows:")
        logger.info(df.head().to_string())
        return df.columns.tolist(), len(df)
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        columns, row_count = analyze_excel()
        logger.info(f"\nTotal number of rows: {row_count}")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
