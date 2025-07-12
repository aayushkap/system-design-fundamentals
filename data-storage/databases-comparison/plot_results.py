import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def main(insert_data=None, query_data=None):
    def prepare_data(insert_data=None, query_data=None):
        # Prepare insert data
        insert_df = pd.DataFrame([
            {'DB': 'Cassandra', 'Operation': 'Device', 'Time': insert_data['cas_dev']},
            {'DB': 'ClickHouse', 'Operation': 'Device', 'Time': insert_data['ch_dev']},
            {'DB': 'Postgres', 'Operation': 'Device', 'Time': insert_data['pg_dev']},
            {'DB': 'TimescaleDB', 'Operation': 'Device', 'Time': insert_data['ts_dev']},
            {'DB': 'MongoDB', 'Operation': 'Device', 'Time': insert_data['mg_dev']},

            {'DB': 'Cassandra', 'Operation': 'Sensor', 'Time': insert_data['cas_sen']},
            {'DB': 'ClickHouse', 'Operation': 'Sensor', 'Time': insert_data['ch_sen']},
            {'DB': 'Postgres', 'Operation': 'Sensor', 'Time': insert_data['pg_sen']},
            {'DB': 'TimescaleDB', 'Operation': 'Sensor', 'Time': insert_data['ts_sen']},
            {'DB': 'MongoDB', 'Operation': 'Sensor', 'Time': insert_data['mg_sen']},

            {'DB': 'Cassandra', 'Operation': 'Reading', 'Time': insert_data['cas_read']},
            {'DB': 'ClickHouse', 'Operation': 'Reading', 'Time': insert_data['ch_read']},
            {'DB': 'Postgres', 'Operation': 'Reading', 'Time': insert_data['pg_read']},
            {'DB': 'TimescaleDB', 'Operation': 'Reading', 'Time': insert_data['ts_read']},
            {'DB': 'MongoDB', 'Operation': 'Reading', 'Time': insert_data['mg_read']}
        ])

        # Prepare query data
        query_df = pd.DataFrame([
            {'DB': 'Postgres', 'Query': 'Simple COUNT', 'Time': query_data['pg_query_1']},
            {'DB': 'TimescaleDB', 'Query': 'Simple COUNT', 'Time': query_data['ts_query_1']},
            {'DB': 'ClickHouse', 'Query': 'Simple COUNT', 'Time': query_data['ch_query_1']},
            {'DB': 'MongoDB', 'Query': 'Simple COUNT', 'Time': query_data['mg_query_1']},
            {'DB': 'Cassandra', 'Query': 'Simple COUNT', 'Time': query_data['cas_query_1']},

            {'DB': 'Postgres', 'Query': 'Complex Agg', 'Time': query_data['pg_query_2']},
            {'DB': 'TimescaleDB', 'Query': 'Complex Agg', 'Time': query_data['ts_query_2']},
            {'DB': 'ClickHouse', 'Query': 'Complex Agg', 'Time': query_data['ch_query_2']},
            {'DB': 'MongoDB', 'Query': 'Complex Agg', 'Time': query_data['mg_query_2']},
            {'DB': 'Cassandra', 'Query': 'Complex Agg', 'Time': query_data['cas_query_2']}
        ])

        return insert_df, query_df

    insert_df, query_df = prepare_data(insert_data, query_data)

    # Visualization 1: Insert Performance Comparison
    plt.figure(figsize=(12, 8))
    sns.barplot(data=insert_df, x='Operation', y='Time', hue='DB',
                palette='viridis', edgecolor='black')

    plt.title('Insert Latency by Operation Type', fontsize=16, pad=20)
    plt.ylabel('Time (ms)', fontsize=12)
    plt.xlabel('Operation Type', fontsize=12)
    plt.yscale('log')  # Log scale for better visualization of wide ranges
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Database', title_fontsize=12, fontsize=10)
    plt.tight_layout()
    plt.savefig('insert_performance.png', dpi=300)
    plt.show()

    # Visualization 2: Query Performance Comparison
    plt.figure(figsize=(12, 8))
    sns.barplot(data=query_df, x='DB', y='Time', hue='Query',
                palette='rocket', edgecolor='black')

    plt.title('Query Performance Comparison', fontsize=16, pad=20)
    plt.ylabel('Time (ms)', fontsize=12)
    plt.xlabel('Database', fontsize=12)
    plt.yscale('log')  # Log scale for better visualization
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Query Type', title_fontsize=12, fontsize=10)
    plt.tight_layout()
    plt.savefig('query_performance.png', dpi=300)
    plt.show()

    # Visualization 3: Speedup Factor Comparison
    def calculate_speedup(df, baseline_db='Postgres'):
        speedup_df = df.copy()
        baseline = speedup_df[speedup_df['DB'] == baseline_db].set_index('Query')['Time']
        speedup_df['Speedup'] = speedup_df.apply(
            lambda row: baseline[row['Query']] / row['Time'] if row['DB'] != baseline_db else 1,
            axis=1
        )
        return speedup_df

    speedup_df = calculate_speedup(query_df)

    plt.figure(figsize=(12, 8))
    sns.barplot(data=speedup_df, x='DB', y='Speedup', hue='Query',
                palette='coolwarm', edgecolor='black')

    plt.axhline(1, color='red', linestyle='--', alpha=0.7)  # Baseline reference
    plt.title('Speedup Relative to Postgres', fontsize=16, pad=20)
    plt.ylabel('Speedup Factor (Higher is better)', fontsize=12)
    plt.xlabel('Database', fontsize=12)
    plt.yscale('log')  # Log scale for better visualization
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Query Type', title_fontsize=12, fontsize=10)
    plt.tight_layout()
    plt.savefig('speedup_comparison.png', dpi=300)
    plt.show()